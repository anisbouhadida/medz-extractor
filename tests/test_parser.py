"""Tests for parser module.

Covers:
- Header detection with institutional header block present.
- Header not found → failure.
- Footer detection via F=, I=, Nb: markers.
- Footer detection via structural collapse (blank row + non-tabular rows).
- Zero data rows after parsing → failure.
"""

import pytest

from medz_extractor.parser import (
    count_non_empty_cells,
    is_footer_row,
    is_tabular_row,
    detect_header_row,
    extract_data,
)


# ── Helper function tests ───────────────────────────────────────


class TestCountNonEmptyCells:
    """Unit tests for ``count_non_empty_cells``."""

    def test_all_empty(self) -> None:
        """Row of None/empty values returns 0."""
        assert count_non_empty_cells((None, "", None, "")) == 0

    def test_all_populated(self) -> None:
        """Row with all values returns correct count."""
        assert count_non_empty_cells(("a", "b", "c")) == 3

    def test_mixed(self) -> None:
        """Row with a mix of empty and non-empty."""
        assert count_non_empty_cells(("a", None, "c", "")) == 2


class TestIsTabularRow:
    """Unit tests for ``is_tabular_row``."""

    def test_below_threshold(self) -> None:
        """Row with fewer non-empty cells than threshold."""
        row = ("a", None, None, None, None, None)
        assert is_tabular_row(row, 3) is False

    def test_at_threshold(self) -> None:
        """Row at exactly the threshold."""
        row = ("a", "b", "c", None, None, None)
        assert is_tabular_row(row, 3) is True

    def test_above_threshold(self) -> None:
        """Row above the threshold."""
        row = ("a", "b", "c", "d")
        assert is_tabular_row(row, 3) is True


class TestIsFooterRow:
    """Unit tests for ``is_footer_row``."""

    def test_f_equals(self) -> None:
        """Single-cell row starting with F= is a footer."""
        assert is_footer_row(("F= Fabricant",)) is True

    def test_i_equals(self) -> None:
        """Single-cell row starting with I= is a footer."""
        assert is_footer_row(("I= Importateur",)) is True

    def test_nb_colon(self) -> None:
        """Single-cell row starting with Nb: is a footer."""
        assert is_footer_row(("Nb: note",)) is True

    def test_footer_in_later_cell(self) -> None:
        """Footer marker can appear in any cell of a sparse row."""
        assert is_footer_row((None, "", "F= foo")) is True

    def test_footer_with_few_cells(self) -> None:
        """Row with ≤ 3 non-empty cells and a marker is footer."""
        assert is_footer_row(("F= Fab", "note", "x")) is True

    def test_non_footer(self) -> None:
        """Normal data row without markers is not a footer."""
        assert is_footer_row(("data", "123", "abc")) is False

    def test_empty_row_not_footer(self) -> None:
        """Empty row is not identified as a footer."""
        assert is_footer_row((None, None)) is False

    def test_data_row_with_i_equals_not_footer(self) -> None:
        """Data row with I= in a dosage column is NOT a footer.

        Real-world example: a row with 17 filled cells where one
        cell contains 'I=370MG/ML' (a concentration value).
        """
        row = (
            "630", "070/08", "08 C 010", "AMIDOTRIZOATE",
            "RADIOSELECTAN", "SOL.INJ  I.V.", "I=370MG/ML",
            "val8", "val9", "val10", "val11", "val12",
            "val13", "val14", "val15", "val16", "val17",
        )
        assert is_footer_row(row) is False

    def test_data_row_with_f_equals_not_footer(self) -> None:
        """Populated data row containing F= is not a footer."""
        row = tuple(["v"] * 6 + ["F=something"])
        assert is_footer_row(row) is False


# ── Header detection tests ──────────────────────────────────────


class TestDetectHeaderRow:
    """Unit tests for ``detect_header_row``."""

    def test_header_after_institutional_block(self) -> None:
        """Header is found after non-tabular institutional rows."""
        rows = [
            ("Ministry of Health",) + (None,) * 7,
            ("Republic of Algeria",) + (None,) * 7,
            ("",) * 8,
            ("A", "B", "C", "D", "E", "F", "G", "H"),  # header
            ("1", "2", "3", "4", "5", "6", "7", "8"),  # data
        ]
        assert detect_header_row(rows, threshold=8) == 3

    def test_header_at_first_row(self) -> None:
        """Header is at the very first row (no institutional block)."""
        rows = [
            ("A", "B", "C", "D", "E", "F"),  # header
            ("1", "2", "3", "4", "5", "6"),  # data
        ]
        assert detect_header_row(rows, threshold=6) == 0

    def test_header_not_found(self) -> None:
        """No row meets the threshold → ValueError."""
        rows = [
            ("x",) + (None,) * 7,
            ("y",) + (None,) * 7,
        ]
        with pytest.raises(ValueError, match="Header row not found"):
            detect_header_row(rows, threshold=8)

    def test_single_row_not_enough(self) -> None:
        """A single qualifying row without a tabular next row fails."""
        rows = [
            ("A", "B", "C", "D", "E", "F", "G", "H"),
        ]
        with pytest.raises(ValueError, match="Header row not found"):
            detect_header_row(rows, threshold=8)


# ── Data extraction tests ───────────────────────────────────────


class TestExtractData:
    """Unit tests for ``extract_data``."""

    def test_basic_extraction(self) -> None:
        """Rows after header are extracted up to the end."""
        rows = [
            ("A", "B"),
            ("1", "2"),
            ("3", "4"),
        ]
        headers, data = extract_data(rows, header_index=0)
        assert headers == ["A", "B"]
        assert data == [["1", "2"], ["3", "4"]]

    def test_footer_f_equals_stops(self) -> None:
        """Extraction stops at a sparse row containing F=."""
        rows = [
            ("Col1", "Col2"),
            ("a", "b"),
            ("F= Fabricant", None),
        ]
        headers, data = extract_data(rows, header_index=0)
        assert data == [["a", "b"]]

    def test_footer_i_equals_stops(self) -> None:
        """Extraction stops at a sparse row containing I=."""
        rows = [
            ("Col1", "Col2"),
            ("a", "b"),
            ("I= Importateur", None),
        ]
        _, data = extract_data(rows, header_index=0)
        assert data == [["a", "b"]]

    def test_footer_nb_colon_stops(self) -> None:
        """Extraction stops at a sparse row containing Nb:."""
        rows = [
            ("Col1", "Col2"),
            ("a", "b"),
            ("Nb: some note", None),
        ]
        _, data = extract_data(rows, header_index=0)
        assert data == [["a", "b"]]

    def test_data_row_with_footer_prefix_not_stopped(self) -> None:
        """A fully populated data row containing I= is kept."""
        rows = [
            ("C1", "C2", "C3", "C4", "C5", "C6", "C7"),
            ("a", "b", "c", "d", "e", "I=370MG/ML", "g"),
            ("h", "i", "j", "k", "l", "m", "n"),
        ]
        _, data = extract_data(rows, header_index=0)
        assert len(data) == 2
        assert data[0][5] == "I=370MG/ML"

    def test_structural_collapse(self) -> None:
        """Blank row followed by non-tabular rows stops extraction."""
        rows = [
            ("Col1", "Col2", "Col3"),
            ("a", "b", "c"),
            (None, None, None),  # blank row
            ("single note",),  # non-tabular
        ]
        _, data = extract_data(rows, header_index=0)
        assert data == [["a", "b", "c"]]

    def test_zero_rows_raises(self) -> None:
        """If extraction yields no data rows, ValueError is raised."""
        rows = [
            ("Col1", "Col2"),
            ("F= footer", None),  # sparse row → footer
        ]
        with pytest.raises(ValueError, match="0 rows"):
            extract_data(rows, header_index=0)

    def test_none_values_become_empty_string(self) -> None:
        """None cell values are converted to empty strings."""
        rows = [
            ("Col1", "Col2"),
            ("a", None),
        ]
        _, data = extract_data(rows, header_index=0)
        assert data == [["a", ""]]

    def test_blank_rows_inside_table_are_skipped(self) -> None:
        """Blank rows surrounded by tabular data are skipped.

        Real-world sheets occasionally contain an empty row
        between data sections.  When more tabular rows follow,
        the blank row must be silently skipped rather than
        triggering structural-collapse termination.
        """
        rows = [
            ("C1", "C2", "C3"),
            ("a", "b", "c"),
            (None, None, None),   # blank row inside data
            ("d", "e", "f"),     # tabular row after blank
            ("g", "h", "i"),
        ]
        _, data = extract_data(rows, header_index=0)
        assert data == [
            ["a", "b", "c"],
            ["d", "e", "f"],
            ["g", "h", "i"],
        ]

    def test_odd_footer_prefix_no_false_positive(self) -> None:
        """Sparse rows with text resembling — but not matching —
        footer prefixes must not stop extraction.

        Only exact prefixes ``F=``, ``I=``, ``Nb:`` qualify.
        Strings like ``"Fabricant"``, ``"Info"``, or ``"NB"``
        (without colon) are ordinary data.
        """
        rows = [
            ("C1", "C2"),
            ("Fabricant", None),   # sparse, but no "F="
            ("Info", None),       # sparse, but no "I="
            ("NB", None),         # sparse, no colon after NB
        ]
        _, data = extract_data(rows, header_index=0)
        assert len(data) == 3
