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


def normalize_name(name: str) -> str:
    """Normalize a sheet name for fuzzy comparison.

    Applies:
    - Unicode NFD decomposition to strip accents.
    - Lowercasing.
    - Collapsing whitespace and punctuation to single spaces.

    Parameters:
        name: The raw sheet name string.

    Returns:
        A normalized, comparable string.
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

    Uses fuzzy matching (case-insensitive, accent-insensitive,
    whitespace-tolerant) to locate each expected sheet.

    Parameters:
        sheet_names: List of actual sheet names from the workbook.

    Returns:
        A dict mapping each actual sheet name to its output CSV
        filename, e.g. ``{"Nomenclature": "nomenclature.csv", ...}``.

    Raises:
        ValueError: If one or more expected sheets cannot be found.
    """
    # Build a lookup from normalized actual names to originals.
    normalized_actuals: Dict[str, str] = {
        normalize_name(sn): sn for sn in sheet_names
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
