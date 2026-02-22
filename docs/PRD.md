# Nomenclature Pre-Processing Tool — PRD (v1)

## 1. Overview

This project provides a rule-based preprocessing tool that converts
official Excel nomenclature release files into clean CSV datasets.

The system is designed for:

- Community contribution
- Reproducible processing
- Automation via GitHub Actions
- Downstream ingestion by external systems

The tool scope is strictly:

- Reading Excel `.xlsx` files
- Cleaning structural artifacts
- Exporting normalized CSV files

No database logic or network calls are included in the processing pipeline.

---

## 2. Problem Statement

Official Excel release files include non-tabular report structure that blocks
direct ingestion:

- Institutional header block above the table
- Footer notes/legend lines
- Occasional schema expansion (extra empty columns)

Manual cleanup is error-prone and non-reproducible.

---

## 3. Objectives

Build a simple application that:

1. Reads one Excel input file
2. Detects and validates the 3 expected sheets
3. Detects the true header row structurally
4. Extracts table rows and stops before footer blocks
5. Drops entirely empty columns
6. Writes standardized UTF-8 CSV outputs
7. Fails fast with actionable errors

---

## 4. Non-Goals (v1)

- No data enrichment
- No cross-release diffing
- No deduplication
- No database integration
- No web/API/UI layer

---

## 5. Users

Primary:

- Maintainer
- Open-source contributors

Secondary:

- Systems ingesting generated CSV files

---

## 6. High-Level Workflow

1. User provides `input/YYYY-MM.xlsx`
2. CLI loads workbook in read-only mode
3. Expected sheets are detected with fuzzy name matching
4. Each sheet is parsed structurally
5. Empty columns are removed
6. CSV files are written to `output/YYYY-MM/`

---

## 7. Functional Requirements

### 7.1 Input

- Accepted format: `.xlsx` only
- Typical location: `input/YYYY-MM.xlsx` (required naming format)
- Release cadence is irregular, but file naming must strictly remain `YYYY-MM`.

### 7.2 Sheet Detection

Workbook must contain expected sheets mapped to:

- `nomenclature.csv`
- `non_renouveles.csv`
- `retraits.csv`

Matching behavior:

- Case-insensitive
- Accent-insensitive
- Tolerant to repeated spaces, `_`, `-`
- Allows canonical-name suffixes (e.g., `Nomenclature AOUT 2024`)

If any expected sheet is missing: fail immediately.

### 7.3 Structural Parsing

For each sheet:

1. Detect header row as first row with at least threshold non-empty cells
   where the next row is also tabular.
2. Thresholds:
   - Nomenclature: 8
   - Other sheets: 6
3. Data starts at row immediately after header.
4. Stop extraction on:
   - Footer legend row (marker `F=`, `I=`, `Nb:`) when row is sparse
   - Structural collapse (blank row followed by no further tabular row)

If extracted data rows count is 0: fail.

### 7.4 Cell Value Normalization

During extraction, cell values are cleaned:

- Embedded newlines (`\n`, `\r`, `\r\n`) are replaced with a single space.
- Consecutive spaces are collapsed to one.
- This ensures every CSV data row occupies exactly one line.

Some Excel cells (e.g. CONDITIONNEMENT, DOSAGE) contain literal line breaks
from the source data. Without flattening, these produce multi-line CSV rows
that break simple line-oriented consumers.

### 7.5 Schema Normalization

After extraction:

- Remove columns where every data value is empty
- Preserve order of kept columns exactly

### 7.6 CSV Output

Generate exactly:

- `output/YYYY-MM/nomenclature.csv`
- `output/YYYY-MM/non_renouveles.csv`
- `output/YYYY-MM/retraits.csv`

Rules:

- UTF-8 encoding
- Stable delimiter (default `,`, configurable)
- Header row written first
- Correct CSV quoting/escaping
- Parent directories created if missing

### 7.7 CLI

Command is Typer-based and supports:

- `medz-extractor <input.xlsx> --out <output_dir>`

(With a single command, the installed CLI can also be invoked directly in
single-command mode.)

---

## 8. Failure Conditions

Processing must stop on:

- Missing expected sheet
- Header row not found
- Zero extracted data rows
- CSV write failure

Errors must be explicit and human-readable.

---

## 9. Reproducibility

Given identical workbook content, generated CSV content must be identical.

No randomness, network access, or time-dependent data transformation is used.
(Execution logs may include timestamps.)

---

## 10. Technical Stack

- Python 3.14+
- `openpyxl` (Excel reading)
- `typer` (CLI)
- Standard library `csv`, `logging`, `pathlib`

---

## 11. Testing Scope

`pytest` coverage includes:

- Sheet-name normalization/matching
- Header detection rules
- Footer detection rules and false-positive protection
- Structural-collapse stopping
- Empty-column dropping
- CSV writing behavior and validation errors

---

## 12. CI Automation Contract

Current repository automation (`.github/workflows/process.yml`) is:

- Trigger: push to `main`
- Path filter: `input/**.xlsx`
- Environment: `ubuntu-latest` with Python 3.14
- Processing step: iterates over `input/*.xlsx` and runs
   `medz-extractor <input.xlsx> --out output/<YYYY-MM>/`
- Output commit: commits updated `output/**/*.csv`
