"""Tests for schema normalization module.

Covers:
- Entirely empty columns are dropped.
- Partially populated columns are kept.
- Column order is preserved.
- Schema expansion columns (all empty) are removed.
"""

import pytest

from medz_extractor.schema import drop_empty_columns, find_empty_columns


# ── find_empty_columns tests ────────────────────────────────────


class TestFindEmptyColumns:
    """Unit tests for ``find_empty_columns``."""

    def test_no_empty_columns(self) -> None:
        """All columns have at least one non-empty value."""
        headers = ["A", "B", "C"]
        rows = [["1", "2", "3"]]
        assert find_empty_columns(headers, rows) == set()

    def test_all_empty_columns(self) -> None:
        """Every column is entirely empty."""
        headers = ["A", "B"]
        rows = [["", ""], ["", ""]]
        assert find_empty_columns(headers, rows) == {0, 1}

    def test_mixed(self) -> None:
        """Some columns empty, others not."""
        headers = ["A", "B", "C"]
        rows = [
            ["x", "", ""],
            ["y", "", ""],
        ]
        assert find_empty_columns(headers, rows) == {1, 2}

    def test_partially_populated_kept(self) -> None:
        """A column with at least one value is not considered empty."""
        headers = ["A", "B"]
        rows = [
            ["", ""],
            ["x", ""],
            ["", "val"],
        ]
        assert find_empty_columns(headers, rows) == set()


# ── drop_empty_columns tests ───────────────────────────────────


class TestDropEmptyColumns:
    """Unit tests for ``drop_empty_columns``."""

    def test_drops_empty(self) -> None:
        """Entirely empty columns are removed from headers and data."""
        headers = ["A", "B", "C"]
        rows = [
            ["1", "", "3"],
            ["4", "", "6"],
        ]
        new_h, new_r = drop_empty_columns(headers, rows)
        assert new_h == ["A", "C"]
        assert new_r == [["1", "3"], ["4", "6"]]

    def test_preserves_order(self) -> None:
        """Non-empty columns retain their original order."""
        headers = ["X", "Y", "Z", "W"]
        rows = [
            ["a", "", "c", ""],
            ["d", "", "f", ""],
        ]
        new_h, _ = drop_empty_columns(headers, rows)
        assert new_h == ["X", "Z"]

    def test_no_columns_dropped(self) -> None:
        """When no columns are empty, output equals input."""
        headers = ["A", "B"]
        rows = [["1", "2"]]
        new_h, new_r = drop_empty_columns(headers, rows)
        assert new_h == headers
        assert new_r == rows

    def test_schema_expansion(self) -> None:
        """Extra empty columns (schema expansion) are dropped."""
        headers = ["A", "B", "C", "", ""]
        rows = [
            ["1", "2", "3", "", ""],
            ["4", "5", "6", "", ""],
        ]
        new_h, new_r = drop_empty_columns(headers, rows)
        assert new_h == ["A", "B", "C"]
        assert new_r == [["1", "2", "3"], ["4", "5", "6"]]

    def test_short_rows_handled(self) -> None:
        """Rows shorter than header length do not cause errors."""
        headers = ["A", "B", "C"]
        rows = [["1", "2"]]  # row shorter than header
        new_h, new_r = drop_empty_columns(headers, rows)
        # Column C is empty (missing from row) → dropped.
        assert new_h == ["A", "B"]
        assert new_r == [["1", "2"]]
