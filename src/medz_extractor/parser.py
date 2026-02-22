"""Structural parser for nomenclature sheets.

Responsibilities:
- Detect the real header row (skip institutional header block).
- Extract tabular data rows.
- Stop extraction at footer markers (F=, I=, Nb:) or structural collapse.
"""

import logging
from typing import List, Optional, Tuple

from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger(__name__)

# Header detection thresholds (minimum non-empty cells in a row).
NOMENCLATURE_THRESHOLD: int = 8
DEFAULT_THRESHOLD: int = 6

# Footer marker prefixes (whitespace-tolerant).
FOOTER_PREFIXES: Tuple[str, ...] = ("F=", "I=", "Nb:")


def _cell_value_str(value: object) -> str:
    """Convert a cell value to a stripped string.

    Parameters:
        value: Raw cell value (may be None or any type).

    Returns:
        Stripped string representation, or empty string if None.
    """
    if value is None:
        return ""
    return str(value).strip()


def _count_non_empty(row: Tuple[object, ...]) -> int:
    """Count the number of non-empty cells in a row.

    Parameters:
        row: Tuple of cell values from openpyxl.

    Returns:
        Count of cells that are neither None nor blank strings.
    """
    return sum(1 for cell in row if _cell_value_str(cell) != "")


def _is_tabular(row: Tuple[object, ...], threshold: int) -> bool:
    """Check whether a row has enough non-empty cells to be tabular.

    Parameters:
        row: Tuple of cell values.
        threshold: Minimum non-empty cell count.

    Returns:
        True if the row meets or exceeds the threshold.
    """
    return _count_non_empty(row) >= threshold


# Maximum non-empty cells for a row to qualify as a footer.
# Real footer rows are legend lines (e.g. "F=Fabriqué localement")
# with very few populated cells; data rows with 6+ filled cells
# that happen to contain "I=370MG/ML" are not footers.
_FOOTER_MAX_NON_EMPTY: int = 3


def _is_footer_row(row: Tuple[object, ...]) -> bool:
    """Check whether a row is a footer legend line.

    A row is considered a footer only when **both** conditions hold:

    1. At least one cell starts with a known footer prefix
       (``F=``, ``I=``, ``Nb:``  — whitespace-tolerant).
    2. The row has very few non-empty cells (≤ 3), indicating it
       is a legend/note line rather than a regular data row.

    This avoids false positives on data rows that contain values
    such as ``I=370MG/ML`` in a dosage column.

    Parameters:
        row: Tuple of cell values.

    Returns:
        True if the row is a footer legend line.
    """
    if _count_non_empty(row) > _FOOTER_MAX_NON_EMPTY:
        return False
    for cell in row:
        text = _cell_value_str(cell)
        if text:
            for prefix in FOOTER_PREFIXES:
                if text.startswith(prefix):
                    return True
    return False


def detect_header_row(
    rows: List[Tuple[object, ...]],
    threshold: int,
) -> int:
    """Find the index of the real header row in a list of rows.

    The header row is the first row with ``>= threshold`` non-empty
    cells whose next row is also tabular (same threshold).

    Parameters:
        rows: All rows from the sheet (list of value tuples).
        threshold: Minimum non-empty cell count.

    Returns:
        0-based index of the header row within *rows*.

    Raises:
        ValueError: If no header row is found.
    """
    for i in range(len(rows) - 1):
        if _is_tabular(rows[i], threshold) and _is_tabular(
            rows[i + 1], threshold
        ):
            logger.info(
                "Header row detected at sheet row index %d.", i
            )
            return i

    raise ValueError(
        "Header row not found: no row with >= "
        f"{threshold} non-empty cells followed by another "
        "tabular row."
    )


def extract_data(
    rows: List[Tuple[object, ...]],
    header_index: int,
) -> Tuple[List[str], List[List[str]]]:
    """Extract header names and data rows, stopping at footer.

    Parameters:
        rows: All rows from the sheet.
        header_index: Index of the header row (from
            :func:`detect_header_row`).

    Returns:
        A tuple of ``(headers, data_rows)`` where *headers* is a
        list of column name strings and *data_rows* is a list of
        lists of string values.

    Raises:
        ValueError: If extracted data has zero rows.
    """
    header = [_cell_value_str(c) for c in rows[header_index]]
    data_rows: List[List[str]] = []

    i = header_index + 1
    while i < len(rows):
        row = rows[i]
        # Check for footer markers.
        if _is_footer_row(row):
            logger.info(
                "Footer marker detected at row index %d; "
                "stopping extraction.",
                i,
            )
            break
        # Check for structural collapse: blank row.
        if _count_non_empty(row) == 0:
            # Look ahead: if no more tabular rows, stop.
            has_more_tabular = False
            for j in range(i + 1, len(rows)):
                if _count_non_empty(rows[j]) == 0:
                    continue
                if _is_footer_row(rows[j]):
                    break
                # Check if the next non-empty row is tabular
                # (at least 2 non-empty cells as a minimal bar).
                if _count_non_empty(rows[j]) >= 2:
                    has_more_tabular = True
                break
            if not has_more_tabular:
                logger.info(
                    "Structural collapse detected at row "
                    "index %d; stopping extraction.",
                    i,
                )
                break
            # Blank row inside data — skip it.
            i += 1
            continue

        data_rows.append(
            [_cell_value_str(c) for c in row]
        )
        i += 1

    if not data_rows:
        raise ValueError(
            "Extracted data has 0 rows after removing "
            "header and footer blocks."
        )

    logger.info("Extracted %d data rows.", len(data_rows))
    return header, data_rows


def parse_sheet(
    ws: Worksheet,
    sheet_label: str,
    threshold: Optional[int] = None,
) -> Tuple[List[str], List[List[str]]]:
    """Parse a single worksheet into headers and data rows.

    Orchestrates header detection, data extraction, and footer
    removal for one sheet.

    Parameters:
        ws: An openpyxl Worksheet object.
        sheet_label: Human-readable label (e.g. ``"nomenclature"``),
            used to select the threshold when *threshold* is None.
        threshold: Override for the header-detection threshold.
            If None, uses 8 for nomenclature and 6 otherwise.

    Returns:
        A tuple of ``(headers, data_rows)``.

    Raises:
        ValueError: On header-not-found or zero-data-rows.
    """
    if threshold is None:
        if "nomenclature" in sheet_label.lower():
            threshold = NOMENCLATURE_THRESHOLD
        else:
            threshold = DEFAULT_THRESHOLD

    # Materialise all rows as value tuples.
    rows: List[Tuple[object, ...]] = [
        tuple(cell.value for cell in row)
        for row in ws.iter_rows()
    ]

    if not rows:
        raise ValueError(
            f"Sheet '{sheet_label}' is empty — no rows found."
        )

    header_index = detect_header_row(rows, threshold)
    return extract_data(rows, header_index)
