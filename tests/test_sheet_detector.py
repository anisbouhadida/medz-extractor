"""Tests for sheet_detector module.

Covers:
- Exact sheet name matching.
- Case-insensitive matching.
- Accent-insensitive matching.
- Whitespace/punctuation tolerance.
- Missing sheet → failure.
"""

import pytest

from medz_extractor.sheet_detector import (
    detect_sheets,
    normalize_name,
)


# ── normalize_name tests ────────────────────────────────────────


class TestNormalizeName:
    """Unit tests for the ``normalize_name`` helper."""

    def test_lowercase(self) -> None:
        """Uppercased names are lowered."""
        assert normalize_name("NOMENCLATURE") == "nomenclature"

    def test_accent_removal(self) -> None:
        """Accented characters are reduced to base form."""
        assert normalize_name("Non Renouvelés") == "non renouveles"

    def test_extra_spaces(self) -> None:
        """Multiple spaces collapse to a single space."""
        assert normalize_name("Non   Renouvelés") == "non renouveles"

    def test_underscores_and_dashes(self) -> None:
        """Underscores and dashes are treated as spaces."""
        assert normalize_name("Non_Renouvelés") == "non renouveles"
        assert normalize_name("Non-Renouvelés") == "non renouveles"

    def test_leading_trailing_whitespace(self) -> None:
        """Leading/trailing whitespace is stripped."""
        assert normalize_name("  Retraits  ") == "retraits"


# ── detect_sheets tests ─────────────────────────────────────────


class TestDetectSheets:
    """Unit tests for ``detect_sheets``."""

    def test_exact_match(self) -> None:
        """Exact canonical names are matched."""
        names = ["Nomenclature", "Non Renouvelés", "Retraits"]
        result = detect_sheets(names)
        assert result == {
            "Nomenclature": "nomenclature.csv",
            "Non Renouvelés": "non_renouveles.csv",
            "Retraits": "retraits.csv",
        }

    def test_case_insensitive(self) -> None:
        """Sheet names in different cases are matched."""
        names = ["NOMENCLATURE", "NON RENOUVELES", "RETRAITS"]
        result = detect_sheets(names)
        assert len(result) == 3

    def test_accent_insensitive(self) -> None:
        """Accented and unaccented names both match."""
        names = ["nomenclature", "non renouveles", "retraits"]
        result = detect_sheets(names)
        assert len(result) == 3

    def test_extra_whitespace(self) -> None:
        """Extra spaces in sheet names are tolerated."""
        names = [
            "  Nomenclature  ",
            "Non   Renouveles",
            "Retraits",
        ]
        result = detect_sheets(names)
        assert len(result) == 3

    def test_missing_single_sheet(self) -> None:
        """Missing one expected sheet raises ValueError."""
        names = ["Nomenclature", "Non Renouvelés"]
        with pytest.raises(ValueError, match="retraits"):
            detect_sheets(names)

    def test_missing_all_sheets(self) -> None:
        """All sheets missing raises ValueError listing all."""
        with pytest.raises(ValueError, match="Missing expected"):
            detect_sheets(["Feuil1", "Feuil2"])

    def test_preserves_original_name(self) -> None:
        """Returned keys use the original sheet name, not normalised."""
        names = [
            "NOMENCLATURE",
            "Non Renouvelés",
            "  retraits  ",
        ]
        result = detect_sheets(names)
        assert "NOMENCLATURE" in result
        assert "Non Renouvelés" in result
        assert "  retraits  " in result

    def test_underscore_variant(self) -> None:
        """Sheet name with underscores is matched."""
        names = [
            "nomenclature",
            "non_renouveles",
            "retraits",
        ]
        result = detect_sheets(names)
        assert len(result) == 3

    def test_nomenclature_with_suffix(self) -> None:
        """Sheet named 'Nomenclature AOUT 2024' matches 'nomenclature'."""
        names = [
            "Nomenclature AOUT 2024",
            "Non Renouvelés ",
            "Retraits",
        ]
        result = detect_sheets(names)
        assert result["Nomenclature AOUT 2024"] == "nomenclature.csv"

    def test_retraits_with_suffix(self) -> None:
        """Sheet named 'Retraits AOUT 2024' matches 'retraits'."""
        names = [
            "Nomenclature",
            "Non Renouvelés",
            "Retraits AOUT 2024",
        ]
        result = detect_sheets(names)
        assert result["Retraits AOUT 2024"] == "retraits.csv"
