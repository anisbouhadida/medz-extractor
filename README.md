# medz-extractor

`medz-extractor` is a small Python script that converts official Algerian
pharmaceutical nomenclature Excel workbooks into stable CSV files.

It is built for Algerian developers who need reproducible, scriptable input for
data pipelines, batch loaders, dashboards, APIs, or local analysis.

This repository is open source and maintained by a solo software engineer. The
project intentionally stays small: one preprocessing script, clear tests, and
documented behavior.

## Why This Exists

Official nomenclature Excel files are useful, but they are not ready for direct
machine ingestion. They usually contain:

- institutional header rows before the real table,
- footer/legend rows after the data,
- accented and sometimes inconsistent sheet names,
- embedded newlines inside cells,
- occasional extra empty columns.

This script turns those files into clean CSVs that downstream systems can
consume deterministically.

## How It Fits In The Broader System

The intended pipeline is:

```text
Download official Excel files
        |
        v
input/YYYY-MM.xlsx
        |
        v
python3 scripts/extract_medz.py input output
        |
        v
output/YYYY-MM/*.csv
        |
        v
Spring Batch ETL application
        |
        v
Database
```

The Python extractor does not download files, call Java, connect to a database,
or know about the database schema. Its only responsibility is the Excel-to-CSV
preprocessing step.

## Features

- Processes every `YYYY-MM.xlsx` workbook in an input directory.
- Produces one output folder per release month.
- Detects the three required sheets with accent/case/spacing tolerant matching.
- Detects real table headers structurally instead of using fixed row numbers.
- Stops before footer/legend rows.
- Flattens embedded cell newlines so CSV consumers get one logical row per line.
- Drops columns that are empty across all data rows.
- Archives existing CSV outputs before replacing them.
- Fails fast with readable error messages.

## Requirements

- Python 3.14 or newer
- `openpyxl`

Install runtime dependencies:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

For development and tests:

```bash
.venv/bin/pip install -r requirements-dev.txt
```

## Quick Start

Put one or more official Excel files in `input/`:

```text
input/
├── 2025-11.xlsx
└── 2025-12.xlsx
```

Run the extractor:

```bash
.venv/bin/python scripts/extract_medz.py input output
```

Generated CSVs:

```text
output/
├── 2025-11/
│   ├── nomenclature.csv
│   ├── non_renouveles.csv
│   └── retraits.csv
└── 2025-12/
    ├── nomenclature.csv
    ├── non_renouveles.csv
    └── retraits.csv
```

Typical shell pipeline:

```bash
#!/usr/bin/env bash
set -euo pipefail

.venv/bin/python scripts/extract_medz.py input output
java -jar spring-batch-etl.jar output
```

## Output Contract

For every valid workbook, exactly three CSV files are produced:

| Workbook sheet | CSV file |
| --- | --- |
| `Nomenclature` | `nomenclature.csv` |
| `Non Renouvelés` | `non_renouveles.csv` |
| `Retraits` | `retraits.csv` |

CSV guarantees:

- UTF-8 encoding
- comma delimiter
- header row first
- deterministic output for identical workbook content

There is no `--delimiter` option. The delimiter is fixed so the Spring Batch
loader has one stable contract.

## Archive Behavior

If CSV files already exist for a month, they are archived before being replaced.

For normal repository usage:

```text
archive/
└── 2025-12/
    └── 20260614T153022Z/
        ├── nomenclature.csv
        ├── non_renouveles.csv
        └── retraits.csv
```

The script writes new CSVs to a staging directory first. Existing outputs are
archived only after the new workbook was parsed and all three replacement CSVs
were written. If extraction fails, current outputs are left untouched.

Technically, the default archive directory is created beside the selected
`output` directory. Running `scripts/extract_medz.py input output` creates
`archive/` in the repository root.

## Failure Modes

The script exits with code `1` when:

- the input directory does not exist,
- no `.xlsx` files are found,
- an input filename does not match `YYYY-MM.xlsx`,
- a workbook cannot be opened,
- a required sheet is missing,
- a header row cannot be detected,
- a sheet produces zero data rows,
- CSV writing fails,
- archiving or promotion fails.

Logs are written to stderr through Python's standard `logging` module.

## Project Layout

```text
scripts/
└── extract_medz.py       # extractor script and importable helper functions

tests/
├── fixtures/            # representative official-format workbooks
├── golden/              # expected CSV outputs for regression tests
└── test_*.py            # unit, pipeline, and regression tests

docs/
├── PRD.md               # project/product context
└── SPECS.md             # implementation-level behavior
```

## Development

Run tests:

```bash
.venv/bin/pytest
```

Run lint and format checks:

```bash
.venv/bin/ruff check scripts/ tests/
.venv/bin/ruff format --check scripts/ tests/
```

Run against the committed sample inputs:

```bash
.venv/bin/python scripts/extract_medz.py input output
```

The committed golden tests protect the CSV contract. If parser behavior changes,
review the generated CSVs carefully before updating golden files.

## CI And Releases

Pull requests run a focused CI workflow:

- Ruff lint check
- Ruff format check
- Pytest test suite

Releases are created from Git tags that look like `v1.2.3`. A release contains:

- `extract_medz.py`
- `requirements.txt`
- `README.md`
- `LICENSE`
- `docs/`
- SHA-256 checksums

Users who only need the script can download the release archive instead of
cloning the full repository.

## Contributing

Contributions are welcome, especially from Algerian developers using public
health data in real systems.

Good contributions include:

- support for new official workbook layout changes,
- clearer failure messages,
- additional representative fixtures,
- documentation improvements,
- tests for edge cases found in real releases.

Please keep the project focused on Excel-to-CSV preprocessing. Database loading,
web scraping, APIs, dashboards, and Spring Batch jobs belong in separate
projects.

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is licensed under the
[GNU Affero General Public License v3.0 or later](LICENSE)
(`AGPL-3.0-or-later`).

Why AGPL for this project:

- Algerian developers can use, study, copy, and modify the script freely.
- The maintainer copyright and license notices must be preserved.
- Modified versions that are distributed must remain under the same license.
- Modified versions used to provide a network service must offer their source
  code to the users of that service.
- Commercial use is allowed, including charging for hosting, support, or
  production infrastructure costs, as long as the license terms are respected.

This keeps the extractor open for the community while allowing sustainable
operation of broader systems built around it.
