"""Tests for the CSV writer module.

Covers:
- Output directory is created if missing.
- CSV is written with UTF-8 encoding.
- Fields containing the delimiter are correctly quoted/escaped.
- Write failure raises a clear error.
"""

import csv
from pathlib import Path

import pytest

from medz_extractor.writer import write_csv


# ── write_csv tests ─────────────────────────────────────────────


class TestWriteCsv:
    """Unit tests for ``write_csv``."""

    def test_creates_output_directory(self, tmp_path: Path) -> None:
        """Parent directories are created when they do not exist."""
        out = tmp_path / "sub" / "dir" / "output.csv"
        write_csv(["A", "B"], [["1", "2"]], out)
        assert out.exists()

    def test_utf8_encoding(self, tmp_path: Path) -> None:
        """CSV is written as UTF-8 and special chars are preserved."""
        out = tmp_path / "utf8.csv"
        write_csv(
            ["Nom", "Détail"],
            [["Paracétamol", "comprimé"]],
            out,
        )
        content = out.read_text(encoding="utf-8")
        assert "Paracétamol" in content
        assert "Détail" in content

    def test_delimiter_quoting(self, tmp_path: Path) -> None:
        """Fields containing the delimiter are properly quoted."""
        out = tmp_path / "quoted.csv"
        write_csv(
            ["Name", "Description"],
            [["Drug A", "contains, comma"]],
            out,
            delimiter=",",
        )
        with out.open(encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            rows = list(reader)
        # The second data field must survive round-trip.
        assert rows[1][1] == "contains, comma"

    def test_semicolon_delimiter(self, tmp_path: Path) -> None:
        """A non-default delimiter is honoured."""
        out = tmp_path / "semi.csv"
        write_csv(
            ["A", "B"],
            [["1", "2"]],
            out,
            delimiter=";",
        )
        content = out.read_text(encoding="utf-8")
        assert "A;B" in content
        assert "1;2" in content

    def test_returns_path(self, tmp_path: Path) -> None:
        """The written file path is returned."""
        out = tmp_path / "ret.csv"
        result = write_csv(["A"], [["1"]], out)
        assert result == out

    def test_empty_headers_raises(self, tmp_path: Path) -> None:
        """Empty headers list raises ValueError."""
        out = tmp_path / "fail.csv"
        with pytest.raises(ValueError, match="headers"):
            write_csv([], [["1"]], out)

    def test_empty_data_raises(self, tmp_path: Path) -> None:
        """Empty data_rows list raises ValueError."""
        out = tmp_path / "fail.csv"
        with pytest.raises(ValueError, match="data_rows"):
            write_csv(["A"], [], out)

    def test_header_row_present(self, tmp_path: Path) -> None:
        """The CSV starts with the header row."""
        out = tmp_path / "hdr.csv"
        write_csv(["Col1", "Col2"], [["v1", "v2"]], out)
        with out.open(encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
        assert header == ["Col1", "Col2"]

    def test_correct_row_count(self, tmp_path: Path) -> None:
        """The number of data rows matches input."""
        out = tmp_path / "count.csv"
        data = [["a", "b"], ["c", "d"], ["e", "f"]]
        write_csv(["X", "Y"], data, out)
        with out.open(encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            all_rows = list(reader)
        # 1 header + 3 data rows
        assert len(all_rows) == 4
