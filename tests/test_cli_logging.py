"""Regression test for trusted process logging.

This test captures logs from a successful ``process`` run and checks
that key observability fields remain present.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Iterable, List

from medz_extractor.cli import process


class _FakeCell:
    """Small cell-like object exposing a ``value`` attribute."""

    def __init__(self, value: object) -> None:
        """Store the raw value used by parser logic."""
        self.value = value


class _FakeWorksheet:
    """Small worksheet-like object exposing ``iter_rows``."""

    def __init__(self, rows: List[List[object]]) -> None:
        """Store raw row values."""
        self._rows = rows

    def iter_rows(self) -> Iterable[List[_FakeCell]]:
        """Yield rows as lists of fake cells."""
        for row in self._rows:
            yield [_FakeCell(value) for value in row]


class _FakeWorkbook:
    """Small workbook-like object used to avoid .xlsx fixtures."""

    def __init__(
        self,
        worksheets: Dict[str, _FakeWorksheet],
    ) -> None:
        """Store named worksheets and expose sheet names."""
        self._worksheets = worksheets
        self.sheetnames = list(worksheets.keys())

    def __getitem__(self, sheet_name: str) -> _FakeWorksheet:
        """Return a worksheet by name."""
        return self._worksheets[sheet_name]

    def close(self) -> None:
        """No-op close method for API compatibility."""


def _build_tabular_rows() -> List[List[object]]:
    """Return rows with a header, data rows, and a footer marker."""
    return [
        ["Ministère", "", "", "", "", "", "", "", ""],
        [
            "N",
            "CODE",
            "DCI",
            "MARQUE",
            "FORME",
            "DOSAGE",
            "LISTE",
            "EXTRA",
            "STATUT",
        ],
        [
            "1",
            "C1",
            "Mol A",
            "Brand A",
            "Comp",
            "10mg",
            "I",
            "",
            "Actif",
        ],
        [
            "2",
            "C2",
            "Mol B",
            "Brand B",
            "Comp",
            "20mg",
            "II",
            "",
            "Actif",
        ],
        ["Nb: note", "", "", "", "", "", "", "", ""],
    ]


def test_process_logs_key_observability_fields(
    monkeypatch,
    caplog,
    tmp_path: Path,
) -> None:
    """Process logs include required fields for trusted diagnostics."""
    input_file = tmp_path / "input.xlsx"
    input_file.write_bytes(b"placeholder")
    output_dir = tmp_path / "out"

    fake_wb = _FakeWorkbook(
        {
            "Nomenclature": _FakeWorksheet(_build_tabular_rows()),
            "Non Renouvelés": _FakeWorksheet(_build_tabular_rows()),
            "Retraits": _FakeWorksheet(_build_tabular_rows()),
        }
    )

    monkeypatch.setattr(
        "medz_extractor.cli.load_workbook",
        lambda *_args, **_kwargs: fake_wb,
    )

    caplog.set_level(logging.INFO)
    process(input_file=input_file, out=output_dir, delimiter=",")

    logs = caplog.text
    assert "Input file:" in logs
    assert "Detected sheets:" in logs
    assert "header row index" in logs
    assert "data rows extracted" in logs
    assert "Dropping 1 entirely-empty column(s): ['EXTRA']" in logs
    assert "Wrote 2 data rows to" in logs
    assert "nomenclature.csv" in logs
    assert "non_renouveles.csv" in logs
    assert "retraits.csv" in logs
    assert "Generated 3 CSV file(s) in" in logs
