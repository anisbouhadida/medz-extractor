"""Sheet detection — fuzzy matching of expected sheet names.

Responsibilities:
- Locate the 3 required sheets (Nomenclature, Non Renouvelés, Retraits)
  using case-insensitive, accent-insensitive, whitespace-tolerant matching.
- Raise a clear error if any expected sheet is missing.
"""

import logging
import re
import unicodedata
from typing import Dict, List

logger = logging.getLogger(__name__)

# Canonical names for the 3 expected sheets and their output filenames.
EXPECTED_SHEETS: Dict[str, str] = {
    "nomenclature": "nomenclature.csv",
    "non renouveles": "non_renouveles.csv",
    "retraits": "retraits.csv",
}


def normalize_sheet_name(name: str) -> str:
    """Normalize a sheet name for fuzzy comparison.

    Applies NFD decomposition to strip accents, lowercases the
    result, and collapses runs of whitespace / punctuation into
    a single space.  The output is suitable for direct equality
    or prefix comparison against canonical sheet identifiers.

    Parameters:
        name: The raw sheet name string from the workbook.

    Returns:
        A lowercased, accent-free, whitespace-collapsed string.
    """
    # NFD decomposition then strip combining marks (accents).
    decomposed = unicodedata.normalize("NFD", name)
    stripped = "".join(
        ch for ch in decomposed
        if unicodedata.category(ch) != "Mn"
    )
    # Lowercase.
    lowered = stripped.lower()
    # Replace punctuation and whitespace runs with a single space.
    collapsed = re.sub(r"[\s_\-]+", " ", lowered).strip()
    return collapsed


def detect_sheets(
    sheet_names: List[str],
) -> Dict[str, str]:
    """Match workbook sheet names to the 3 expected canonical sheets.

    Matching is case-insensitive, accent-insensitive, and tolerant
    of extra whitespace, underscores, and dashes.  A sheet name
    that starts with a canonical name (e.g. ``Nomenclature AOUT
    2024``) is also accepted.

    Parameters:
        sheet_names: Actual sheet names from the workbook
            (``wb.sheetnames``).

    Returns:
        Dict mapping each *original* sheet name to its output CSV
        filename, e.g. ``{"Nomenclature": "nomenclature.csv", ...}``.
        The dict preserves the original casing/accents in keys.

    Raises:
        ValueError: If one or more expected sheets cannot be found.
            The message lists both the missing canonicals and the
            available sheets for easy debugging.
    """
    # Build a lookup from normalized actual names to originals.
    normalized_actuals: Dict[str, str] = {
        normalize_sheet_name(sn): sn for sn in sheet_names
    }

    matched: Dict[str, str] = {}
    missing: List[str] = []

    for canonical, csv_name in EXPECTED_SHEETS.items():
        found = False
        for norm_actual, original in normalized_actuals.items():
            if (
                norm_actual == canonical
                or norm_actual.startswith(canonical + " ")
            ):
                matched[original] = csv_name
                logger.info(
                    "Sheet '%s' matched canonical '%s'.",
                    original,
                    canonical,
                )
                found = True
                break
        if not found:
            missing.append(canonical)

    if missing:
        raise ValueError(
            "Missing expected sheet(s): "
            + ", ".join(f"'{m}'" for m in missing)
            + ". Available sheets: "
            + ", ".join(f"'{s}'" for s in sheet_names)
            + "."
        )

    return matched
