"""Schema normalization utilities.

Responsibilities:
- Drop columns that are entirely empty (all values blank or null).
- Preserve column order from the detected header row.
"""

import logging
from typing import List, Set, Tuple

logger = logging.getLogger(__name__)


def find_empty_columns(
    headers: List[str],
    data_rows: List[List[str]],
) -> Set[int]:
    """Identify column indices where every data value is empty.

    Iterates once through the data and short-circuits as soon as
    all candidate columns are proven non-empty.

    Parameters:
        headers: Column header strings (used only for width).
        data_rows: Extracted data rows (each a list of strings).

    Returns:
        A set of 0-based column indices that are entirely empty
        across all rows.
    """
    num_cols = len(headers)
    empty: Set[int] = set(range(num_cols))

    for row in data_rows:
        # Iterate over a copy so we can discard during loop.
        for col_idx in list(empty):
            if col_idx < len(row) and row[col_idx] != "":
                empty.discard(col_idx)
        # Short-circuit: nothing left to check.
        if not empty:
            break

    return empty


def drop_empty_columns(
    headers: List[str],
    data_rows: List[List[str]],
) -> Tuple[List[str], List[List[str]]]:
    """Remove columns that are entirely empty from headers and data.

    Handles the Nov 2025 schema expansion (extra empty columns
    appended to the sheet) and any other all-blank columns.
    Column order is preserved for non-empty columns.  Rows that
    are shorter than the header are padded with ``""``.

    Parameters:
        headers: Original column header strings.
        data_rows: Original data rows.

    Returns:
        ``(cleaned_headers, cleaned_data_rows)`` with empty columns
        removed.  If no columns are empty the inputs are returned
        unchanged.
    """
    empty_indices = find_empty_columns(headers, data_rows)

    dropped_headers = [
        headers[i] for i in sorted(empty_indices)
    ]
    logger.info(
        "Dropping %d entirely-empty column(s): %s.",
        len(empty_indices),
        dropped_headers,
    )

    keep = [
        i for i in range(len(headers))
        if i not in empty_indices
    ]

    cleaned_headers = [headers[i] for i in keep]
    cleaned_rows: List[List[str]] = []
    for row in data_rows:
        cleaned_rows.append(
            [
                row[i] if i < len(row) else ""
                for i in keep
            ]
        )

    return cleaned_headers, cleaned_rows
