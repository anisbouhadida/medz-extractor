"""End-to-end CLI tests per sheet.

Run the full ``medz-extractor process`` command on every fixture
workbook via Typer's CliRunner and verify:

1. Exactly 3 CSV files are produced (nomenclature, non_renouveles,
   retraits).
2. Row counts match known expectations per fixture.
3. Key header names that form the DB-loader contract are present.

This locks the output schema so that downstream consumers (e.g. a
database loader) are never surprised by schema drift.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest
from typer.testing import CliRunner

from medz_extractor.cli import app

# ── Path constants ──────────────────────────────────────────────

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR / "fixtures"

runner = CliRunner()

# ── Expected CSV filenames ──────────────────────────────────────

CSV_FILENAMES: Tuple[str, ...] = (
    "nomenclature.csv",
    "non_renouveles.csv",
    "retraits.csv",
)

# ── Per-fixture expected row counts ─────────────────────────────
# Keys: fixture stem → { csv_filename: expected_data_rows }.

EXPECTED_ROW_COUNTS: Dict[str, Dict[str, int]] = {
    "2024-08": {
        "nomenclature.csv": 4898,
        "non_renouveles.csv": 1643,
        "retraits.csv": 2532,
    },
    "2024-12": {
        "nomenclature.csv": 5036,
        "non_renouveles.csv": 1603,
        "retraits.csv": 2522,
    },
    "2025-10": {
        "nomenclature.csv": 5176,
        "non_renouveles.csv": 1508,
        "retraits.csv": 2680,
    },
    "2025-12": {
        "nomenclature.csv": 5265,
        "non_renouveles.csv": 1503,
        "retraits.csv": 2680,
    },
}

# ── Contract headers (must always be present) ──────────────────
# These are the stable column names that a DB loader relies on.
# The first-column name varies (N vs N°) so it is excluded here.

CONTRACT_HEADERS: Dict[str, Tuple[str, ...]] = {
    "nomenclature.csv": (
        "N°ENREGISTREMENT",
        "CODE",
        "DENOMINATION COMMUNE INTERNATIONALE",
        "NOM DE MARQUE",
        "FORME",
        "DOSAGE",
        "LISTE",
        "P1",
        "P2",
        "OBS",
        "TYPE",
        "STATUT",
        "DUREE DE STABILITE",
    ),
    "non_renouveles.csv": (
        "N°ENREGISTREMENT",
        "CODE",
        "DENOMINATION COMMUNE INTERNATIONALE",
        "NOM DE MARQUE",
        "FORME",
        "DOSAGE",
        "LISTE",
        "P1",
        "P2",
        "OBS",
        "TYPE",
        "STATUT",
    ),
    "retraits.csv": (
        "N°ENREGISTREMENT",
        "CODE",
        "DENOMINATION COMMUNE INTERNATIONALE",
        "NOM DE MARQUE",
        "FORME",
        "DOSAGE",
        "LISTE",
        "P1",
        "P2",
        "TYPE",
        "STATUT",
        "DATE DE RETRAIT",
        "MOTIF DE RETRAIT",
    ),
}


# ── Helpers ─────────────────────────────────────────────────────


def _discover_fixtures() -> List[str]:
    """Return sorted fixture stems that have expected row counts."""
    return sorted(
        xlsx.stem
        for xlsx in FIXTURES_DIR.glob("*.xlsx")
        if xlsx.stem in EXPECTED_ROW_COUNTS
    )


def _read_csv(
    path: Path,
) -> Tuple[List[str], List[List[str]]]:
    """Read a CSV and return (headers, data_rows)."""
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh, delimiter=","))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _run_cli(
    fixture_name: str, output_dir: Path,
) -> None:
    """Invoke the CLI and assert a successful exit."""
    xlsx = FIXTURES_DIR / f"{fixture_name}.xlsx"
    result = runner.invoke(
        app,
        [str(xlsx), "--out", str(output_dir)],
    )
    assert result.exit_code == 0, (
        f"CLI failed for fixture '{fixture_name}' "
        f"(exit code {result.exit_code}).\n"
        f"Output:\n{result.output}"
    )


FIXTURE_NAMES: List[str] = _discover_fixtures()


# ── Tests ───────────────────────────────────────────────────────


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
class TestCLIProducesExactlyThreeCSVs:
    """The CLI must produce exactly the 3 expected CSV files."""

    def test_produces_three_csvs(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """CLI generates nomenclature, non_renouveles, retraits."""
        _run_cli(fixture_name, tmp_path)
        produced: Set[str] = {
            f.name for f in tmp_path.iterdir() if f.suffix == ".csv"
        }
        expected: Set[str] = set(CSV_FILENAMES)
        assert produced == expected, (
            f"[{fixture_name}] Expected CSVs {sorted(expected)}, "
            f"got {sorted(produced)}."
        )


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
class TestRowCounts:
    """CSV data row counts must match known expectations."""

    def test_nomenclature_row_count(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """nomenclature.csv row count matches expectation."""
        _assert_row_count(
            fixture_name, "nomenclature.csv", tmp_path,
        )

    def test_non_renouveles_row_count(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """non_renouveles.csv row count matches expectation."""
        _assert_row_count(
            fixture_name, "non_renouveles.csv", tmp_path,
        )

    def test_retraits_row_count(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """retraits.csv row count matches expectation."""
        _assert_row_count(
            fixture_name, "retraits.csv", tmp_path,
        )


def _assert_row_count(
    fixture_name: str,
    csv_filename: str,
    tmp_path: Path,
) -> None:
    """Run the CLI and compare row count to expectation."""
    _run_cli(fixture_name, tmp_path)
    _, data_rows = _read_csv(tmp_path / csv_filename)
    expected = EXPECTED_ROW_COUNTS[fixture_name][csv_filename]
    actual = len(data_rows)
    assert actual == expected, (
        f"[{fixture_name}/{csv_filename}] "
        f"Expected {expected} data rows, got {actual}."
    )


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
class TestContractHeaders:
    """Key header names that the DB loader relies on must be
    present in every output CSV."""

    def test_nomenclature_contract_headers(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """nomenclature.csv contains all contract headers."""
        _assert_contract_headers(
            fixture_name, "nomenclature.csv", tmp_path,
        )

    def test_non_renouveles_contract_headers(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """non_renouveles.csv contains all contract headers."""
        _assert_contract_headers(
            fixture_name, "non_renouveles.csv", tmp_path,
        )

    def test_retraits_contract_headers(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """retraits.csv contains all contract headers."""
        _assert_contract_headers(
            fixture_name, "retraits.csv", tmp_path,
        )


def _assert_contract_headers(
    fixture_name: str,
    csv_filename: str,
    tmp_path: Path,
) -> None:
    """Run the CLI and verify contract headers are present."""
    _run_cli(fixture_name, tmp_path)
    headers, _ = _read_csv(tmp_path / csv_filename)
    header_set: Set[str] = set(headers)
    missing: List[str] = [
        h for h in CONTRACT_HEADERS[csv_filename]
        if h not in header_set
    ]
    assert not missing, (
        f"[{fixture_name}/{csv_filename}] "
        f"Missing contract headers: {missing}.\n"
        f"Actual headers: {headers}"
    )


@pytest.mark.parametrize("fixture_name", FIXTURE_NAMES)
class TestFirstColumnIsRowNumber:
    """The first column must start at 1 and be sequential — a
    basic integrity check that no rows were dropped or reordered.
    Only the first and last values are checked for speed."""

    def test_nomenclature_row_numbering(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """nomenclature.csv first column starts at 1."""
        _assert_row_numbering(
            fixture_name, "nomenclature.csv", tmp_path,
        )

    def test_non_renouveles_row_numbering(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """non_renouveles.csv first column starts at 1."""
        _assert_row_numbering(
            fixture_name, "non_renouveles.csv", tmp_path,
        )

    def test_retraits_row_numbering(
        self, fixture_name: str, tmp_path: Path,
    ) -> None:
        """retraits.csv first column starts at 1."""
        _assert_row_numbering(
            fixture_name, "retraits.csv", tmp_path,
        )


def _assert_row_numbering(
    fixture_name: str,
    csv_filename: str,
    tmp_path: Path,
) -> None:
    """Verify first row starts at 1 and last row = total count."""
    _run_cli(fixture_name, tmp_path)
    _, data_rows = _read_csv(tmp_path / csv_filename)
    assert len(data_rows) > 0, (
        f"[{fixture_name}/{csv_filename}] No data rows."
    )

    def _to_int(val: str, row_label: str) -> int:
        """
        Convert a CSV cell value to int, with clear context on failure.

        This wraps the conversion in a try/except so that if the first
        column unexpectedly contains a non-numeric value, the resulting
        assertion error clearly identifies the fixture, CSV file, and
        row position being parsed.
        """
        try:
            return int(float(val.strip()))
        except (TypeError, ValueError) as exc:
            raise AssertionError(
                f"[{fixture_name}/{csv_filename}] "
                f"Invalid row number in {row_label} row: {val!r}. "
                "Expected a numeric value starting at 1 and sequential."
            ) from exc

    first_val = _to_int(data_rows[0][0], "first")
    last_val = _to_int(data_rows[-1][0], "last")
    expected_last = len(data_rows)

    assert first_val == 1, (
        f"[{fixture_name}/{csv_filename}] "
        f"First row number is {first_val}, expected 1."
    )
    assert last_val == expected_last, (
        f"[{fixture_name}/{csv_filename}] "
        f"Last row number is {last_val}, "
        f"expected {expected_last}."
    )


# ── Sanity: at least one fixture is discovered ──────────────────


class TestFixtureDiscovery:
    """Guard against empty parametrisation."""

    def test_at_least_one_fixture(self) -> None:
        """At least one fixture with expected row counts exists."""
        assert len(FIXTURE_NAMES) > 0, (
            "No fixtures found. Place .xlsx files in "
            f"'{FIXTURES_DIR}' with entries in "
            "EXPECTED_ROW_COUNTS."
        )
