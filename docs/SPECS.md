# SPECS.md — Nomenclature Pre-Processing Tool (v1)

## 1. Purpose

Implementation-level specification for converting official
nomenclature Excel files into normalized CSV outputs.

External consumer guarantees are defined in `docs/PRD.md` under Section 7.8
"External Contract" and are normative for downstream integrations.

---

## 2. Input Contract

- Accepted file type: `.xlsx`
- Input path convention: `input/YYYY-MM.xlsx` (required naming format)
- Release cadence may be irregular, but naming must strictly follow `YYYY-MM`.
- Workbook is opened read-only with computed values (`data_only=True`)

---

## 3. Required Sheets

The workbook must contain three expected logical sheets:

- Nomenclature
- Non Renouvelés
- Retraits

### 3.1 Matching Rules (implemented)

Sheet-name matching is based on normalized names:

- Lowercased
- Accent-stripped (Unicode decomposition)
- `_` and `-` treated as spaces
- Repeated whitespace collapsed
- Canonical match OR canonical prefix + suffix text

Examples that match:

- `NOMENCLATURE`
- `Non_Renouvelés`
- `Retraits AOUT 2024`

### 3.2 Failure

If one or more expected sheets are not found, processing fails with an error
listing missing canonical names and available sheet names.

---

## 4. Structural Parsing

## 4.1 Header Detection

Rows are scanned top-down. A row is selected as header when:

- non-empty cell count >= threshold
- next row is also tabular with same threshold

Thresholds:

- Nomenclature context: 8
- Other contexts: 6

If no row satisfies this: fail.

## 4.2 Data Start

Data extraction starts immediately after detected header row.

## 4.3 Footer and End-of-Table Detection

Extraction stops when one of these conditions is met:

1. Footer legend row:
   - row contains a cell starting with `F=`, `I=`, or `Nb:`
   - and row non-empty count <= 3
2. Structural collapse:
   - a blank row is encountered
   - and next significant row is not tabular (minimum 2 non-empty cells)

Blank rows inside data are skipped only when subsequent tabular data continues.

This sparse-row footer rule intentionally avoids false positives for dense
data rows containing values like `I=370MG/ML`.

## 4.4 Cell Value Normalization

During extraction, each cell value is:

1. Converted to string and stripped of leading/trailing whitespace.
2. Embedded newlines (`\r\n` → `\r` → `\n`) replaced with a single space.
3. Consecutive spaces collapsed to one.

This guarantees every CSV data row is a single line.

Affected fields observed in practice: CONDITIONNEMENT, DOSAGE (nomenclature
sheets contain cells with literal line breaks in the Excel source).

## 4.5 Empty Output Guard

If extraction yields 0 data rows: fail.

---

## 5. Schema Normalization

After extraction:

- Identify columns empty across all data rows
- Drop those columns from headers and every row
- Preserve original order of remaining columns
- Handle short rows safely (missing cells treated as empty)

---

## 6. CSV Output

For each detected expected sheet, write exactly one CSV with normalized name:

- `nomenclature.csv`
- `non_renouveles.csv`
- `retraits.csv`

Rules:

- UTF-8 encoding
- Newline handling compatible with CSV writer
- Configurable delimiter (default `,`)
- `csv.QUOTE_MINIMAL` quoting
- Output directories auto-created
- Existing files are overwritten

Write errors fail processing immediately.

---

## 7. CLI Contract

Primary command form:

```bash
medz-extractor input/YYYY-MM.xlsx --out output/YYYY-MM/
```

Arguments/options:

- positional `input_file` (must exist and be readable)
- required `--out` directory
- optional `--delimiter` (default `,`)

Exit behavior:

- `0` on success
- non-zero on failure

### 7.1 Failure and edge-case catalog

| Condition | Exit code | Representative error message |
| --- | ---: | --- |
| Missing expected sheet(s) | non-zero (`1`) | `Missing expected sheet(s): 'non renouveles'. Available sheets: 'NOMENCLATURE', 'Retraits'.` |
| Header row not found | non-zero (`1`) | `Header row not found: no row with >= 8 non-empty cells followed by another tabular row.` |
| Extracted data is empty | non-zero (`1`) | `Extracted data has 0 rows after removing header and footer blocks.` |
| CSV write error | non-zero (`1`) | `CSV write failed for '/.../nomenclature.csv': Failed to write CSV to '/.../nomenclature.csv': ...` |
| Invalid input path / unreadable input | non-zero (CLI argument validation) | `Invalid value for 'INPUT_FILE': Path '/.../input/2025-99.xlsx' does not exist.` |

---

## 8. Logging Contract

Execution logs include at minimum:

- Input path
- Output directory
- Detected sheet mapping
- Per-sheet processing progress
- Extracted row counts
- Dropped empty columns
- Written CSV paths
- Total execution time

---

## 9. Reproducibility and Security Constraints

- No randomness in processing
- No network access
- No macro execution
- No external service dependencies in processing
- Pure Excel-to-CSV transformation only

---

## 10. Tests Required

Minimum enforced test coverage:

1. Name normalization and fuzzy matching
2. Missing-sheet failure paths
3. Header detection success/failure
4. Footer detection markers and sparse-row logic
5. Structural-collapse stopping
6. Empty-column dropping and order preservation
7. CSV write behavior and input validation failures

---

## 11. CI Workflow Contract

The repository workflow (`.github/workflows/process.yml`) currently specifies:

- Trigger: push event on `main`
- Path filter: `input/**.xlsx`
- Job environment: `ubuntu-latest`, Python 3.14
- Processing command pattern:
   `for f in input/*.xlsx; do medz-extractor "$f" --out "output/<YYYY-MM>/"; done`
- Auto-commit scope: `output/**/*.csv`
