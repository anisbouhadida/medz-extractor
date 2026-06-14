"""Pipeline-level tests for the script extractor."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Tuple

import pytest

from scripts import extract_medz

TESTS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TESTS_DIR / "fixtures"

CSV_FILENAMES: Tuple[str, ...] = (
    "nomenclature.csv",
    "non_renouveles.csv",
    "retraits.csv",
)

EXPECTED_ROW_COUNTS = {
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

CONTRACT_HEADERS = {
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


def _copy_fixture(name: str, input_dir: Path) -> None:
    input_dir.mkdir(parents=True, exist_ok=True)
    (input_dir / f"{name}.xlsx").write_bytes(
        (FIXTURES_DIR / f"{name}.xlsx").read_bytes()
    )


def _read_csv(path: Path) -> Tuple[List[str], List[List[str]]]:
    with path.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh, delimiter=","))
    if not rows:
        return [], []
    return rows[0], rows[1:]


def test_process_all_creates_month_folders_for_multiple_inputs(tmp_path: Path) -> None:
    """One script call processes every workbook in the input directory."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    _copy_fixture("2024-08", input_dir)
    _copy_fixture("2024-12", input_dir)

    processed = extract_medz.process_all(input_dir, output_dir)

    assert processed == 2
    for month in ("2024-08", "2024-12"):
        produced = sorted(p.name for p in (output_dir / month).glob("*.csv"))
        assert produced == sorted(CSV_FILENAMES)


def test_existing_outputs_are_archived_before_replacement(tmp_path: Path) -> None:
    """Existing month CSVs are moved to archive/YYYY-MM/<timestamp>/."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    archive_root = tmp_path / "archive"
    _copy_fixture("2024-08", input_dir)
    current_dir = output_dir / "2024-08"
    current_dir.mkdir(parents=True)
    for filename in CSV_FILENAMES:
        (current_dir / filename).write_text(f"old {filename}\n", encoding="utf-8")

    extract_medz.process_all(
        input_dir,
        output_dir,
        archive_root=archive_root,
        clock=lambda: "20260614T153022Z",
    )

    archive_dir = archive_root / "2024-08" / "20260614T153022Z"
    assert sorted(p.name for p in archive_dir.glob("*.csv")) == sorted(CSV_FILENAMES)
    assert (archive_dir / "nomenclature.csv").read_text(encoding="utf-8") == (
        "old nomenclature.csv\n"
    )
    assert (current_dir / "nomenclature.csv").read_text(encoding="utf-8") != (
        "old nomenclature.csv\n"
    )


def test_default_archive_root_sits_beside_output_directory(tmp_path: Path) -> None:
    """Default archives go to output.parent/archive."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    _copy_fixture("2024-08", input_dir)
    current_dir = output_dir / "2024-08"
    current_dir.mkdir(parents=True)
    for filename in CSV_FILENAMES:
        (current_dir / filename).write_text(f"old {filename}\n", encoding="utf-8")

    extract_medz.process_all(
        input_dir,
        output_dir,
        clock=lambda: "20260614T153022Z",
    )

    assert (tmp_path / "archive" / "2024-08" / "20260614T153022Z").is_dir()


def test_archive_is_not_created_when_no_current_csvs_exist(tmp_path: Path) -> None:
    """Fresh months do not create empty archive directories."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    archive_root = tmp_path / "archive"
    _copy_fixture("2024-08", input_dir)

    extract_medz.process_all(
        input_dir,
        output_dir,
        archive_root=archive_root,
        clock=lambda: "20260614T153022Z",
    )

    assert not archive_root.exists()


def test_failed_extraction_leaves_existing_outputs_untouched(tmp_path: Path) -> None:
    """Staging is parsed before archiving so failures do not disturb old CSVs."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    archive_root = tmp_path / "archive"
    input_dir.mkdir()
    (input_dir / "2024-08.xlsx").write_bytes(b"not an xlsx")
    current_dir = output_dir / "2024-08"
    current_dir.mkdir(parents=True)
    for filename in CSV_FILENAMES:
        (current_dir / filename).write_text(f"old {filename}\n", encoding="utf-8")

    with pytest.raises(extract_medz.ExtractionError, match="Failed to open workbook"):
        extract_medz.process_all(input_dir, output_dir, archive_root=archive_root)

    assert not archive_root.exists()
    assert (current_dir / "nomenclature.csv").read_text(encoding="utf-8") == (
        "old nomenclature.csv\n"
    )


def test_invalid_input_filename_fails_clearly(tmp_path: Path) -> None:
    """Only YYYY-MM.xlsx input names are accepted."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    _copy_fixture("2024-08", input_dir)
    (input_dir / "bad-name.xlsx").write_bytes(
        (FIXTURES_DIR / "2024-08.xlsx").read_bytes()
    )

    with pytest.raises(extract_medz.ExtractionError, match="Invalid input filename"):
        extract_medz.process_all(input_dir, output_dir)


def test_no_xlsx_files_fails_clearly(tmp_path: Path) -> None:
    """The pipeline should fail instead of silently doing nothing."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    with pytest.raises(extract_medz.ExtractionError, match="No .xlsx files found"):
        extract_medz.process_all(input_dir, tmp_path / "output")


@pytest.mark.parametrize("fixture_name", sorted(EXPECTED_ROW_COUNTS))
class TestPipelineContract:
    """Directory processing preserves the downstream CSV contract."""

    def test_row_counts_match_expectations(
        self,
        fixture_name: str,
        tmp_path: Path,
    ) -> None:
        _copy_fixture(fixture_name, tmp_path / "input")
        extract_medz.process_all(tmp_path / "input", tmp_path / "output")

        for csv_filename, expected in EXPECTED_ROW_COUNTS[fixture_name].items():
            _, data_rows = _read_csv(tmp_path / "output" / fixture_name / csv_filename)
            assert len(data_rows) == expected

    def test_contract_headers_are_present(
        self,
        fixture_name: str,
        tmp_path: Path,
    ) -> None:
        _copy_fixture(fixture_name, tmp_path / "input")
        extract_medz.process_all(tmp_path / "input", tmp_path / "output")

        for csv_filename, expected_headers in CONTRACT_HEADERS.items():
            headers, _ = _read_csv(tmp_path / "output" / fixture_name / csv_filename)
            missing = [h for h in expected_headers if h not in set(headers)]
            assert not missing, (
                f"[{fixture_name}/{csv_filename}] Missing contract headers: {missing}"
            )
