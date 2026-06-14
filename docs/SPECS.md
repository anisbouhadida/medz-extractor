# Nomenclature Preprocessing Script — Specs

This document describes the implementation contract for
`scripts/extract_medz.py`.

For product context and system boundaries, see [PRD.md](PRD.md).

## Command Interface

```bash
python3 scripts/extract_medz.py input output
```

Arguments:

- `input`: directory containing `.xlsx` files named `YYYY-MM.xlsx`
- `output`: directory where month CSV folders are written

There are no optional runtime flags. The script is intentionally small because
it is called from a larger shell/Spring Batch pipeline.

## Directory Contract

Standard repository layout:

```text
input/
└── YYYY-MM.xlsx

output/
└── YYYY-MM/
    ├── nomenclature.csv
    ├── non_renouveles.csv
    └── retraits.csv

archive/
└── YYYY-MM/
    └── YYYYMMDDTHHMMSSZ/
        ├── nomenclature.csv
        ├── non_renouveles.csv
        └── retraits.csv
```

The archive root defaults to `output.parent / "archive"`. For the standard
command, that is the repository-level `archive/` directory.

## Input Discovery

- Discover files matching `input/*.xlsx`.
- Process workbooks in sorted filename order.
- Fail if the input directory does not exist.
- Fail if no `.xlsx` files are found.
- Fail if any `.xlsx` filename does not match `YYYY-MM.xlsx`.

The filename stem becomes the output month folder name.

## Workbook Loading

Each workbook is opened with:

```python
load_workbook(path, read_only=True, data_only=True)
```

Expected behavior:

- read-only workbook access
- computed cell values rather than formulas
- no macro execution
- no network or external service dependency

Unreadable workbooks fail the run.

## Required Sheets

Each workbook must contain three logical sheets:

- Nomenclature
- Non Renouvelés
- Retraits

Matching rules:

- lowercased comparison
- accent stripping through Unicode decomposition
- `_`, `-`, and repeated whitespace treated as spaces
- exact canonical match or canonical prefix plus suffix text

Examples that match:

- `NOMENCLATURE`
- `Non_Renouvelés`
- `Retraits AOUT 2024`

If any logical sheet is missing, processing fails and logs the available sheet
names.

## Header Detection

Rows are scanned top-down. A row is treated as the header when:

- it has at least the configured number of non-empty cells,
- the next row also meets that threshold.

Thresholds:

- `8` non-empty cells for nomenclature sheets
- `6` non-empty cells for non-renewed and withdrawn sheets

This avoids hardcoded row numbers and skips institutional header blocks.

## Data Extraction

Data starts immediately after the detected header row.

Extraction stops at the first of:

- a sparse footer row containing a cell that starts with `F=`, `I=`, or `Nb:`,
- structural collapse, where a blank row is followed by no more tabular data.

Footer rows are considered sparse only when they have at most three non-empty
cells. This avoids treating dense data rows containing values such as
`I=370MG/ML` as footers.

Blank rows inside the data are skipped when more tabular data follows.

If no data rows are extracted, processing fails.

## Cell Normalization

Each cell is normalized before CSV writing:

- `None` becomes an empty string,
- values are converted to strings,
- leading and trailing whitespace is stripped,
- embedded `\r\n`, `\r`, and `\n` are replaced with spaces,
- repeated spaces are collapsed.

This keeps each CSV record line-oriented for simple downstream consumers.

## Schema Normalization

After extraction:

- columns empty across all data rows are removed,
- remaining column order is preserved,
- rows shorter than the header are padded with empty missing values.

This handles official workbook layout changes that add blank columns.

## CSV Output

For each valid workbook, exactly three files are written:

```text
nomenclature.csv
non_renouveles.csv
retraits.csv
```

CSV settings:

- UTF-8
- comma delimiter
- `csv.QUOTE_MINIMAL`
- header row first

The delimiter is not configurable.

## Staging, Archive, And Promotion

For each month:

1. Write replacement CSVs into `output/.staging/YYYY-MM-<timestamp>/`.
2. Verify the staging directory contains exactly the three expected CSV files.
3. Move existing `output/YYYY-MM/*.csv` files into
   `archive/YYYY-MM/YYYYMMDDTHHMMSSZ/`.
4. Move staged files into `output/YYYY-MM/`.
5. Remove the staging directory.

If parsing, writing, or staging verification fails, existing current outputs are
not archived or changed.

If archiving or promotion fails after staging succeeds, the script fails with a
readable error. The operator should inspect `output/`, `archive/`, and
`output/.staging/` before rerunning.

## Logging

The script logs to stderr and includes:

- input directory,
- output directory,
- archive directory,
- workbook currently being processed,
- detected sheet mapping,
- extracted row counts per sheet,
- dropped empty-column count,
- archive path when old outputs are moved,
- final processed workbook count.

## Failure Modes

The script exits with code `1` for:

- missing input directory,
- no `.xlsx` inputs,
- invalid input filename,
- unreadable workbook,
- missing expected sheet,
- header row not found,
- zero extracted data rows,
- CSV write failure,
- archive failure,
- promotion failure.

## Test Coverage

The test suite covers:

- sheet-name normalization and fuzzy matching,
- missing-sheet errors,
- header detection success and failure,
- footer detection and false-positive protection,
- structural-collapse stopping,
- blank rows inside data,
- empty-column dropping,
- CSV writing,
- directory-level processing,
- archive behavior,
- failed extraction preserving current outputs,
- golden CSV regression outputs.
