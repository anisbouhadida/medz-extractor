# medz-extractor

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.14+](https://img.shields.io/badge/Python-3.14%2B-blue.svg)
![Open Source](https://img.shields.io/badge/Open%20Source-Community%20Driven-success)
[![CI](https://github.com/anisbouhadida/medz-extractor/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/anisbouhadida/medz-extractor/actions/workflows/ci.yml)
[![Process](https://github.com/anisbouhadida/medz-extractor/actions/workflows/process.yml/badge.svg?branch=main)](https://github.com/anisbouhadida/medz-extractor/actions/workflows/process.yml)
![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/anisbouhadida/052a1ce9644be82211ca077a0857bb0b/raw/medz-extractor-coverage.json)

`medz-extractor` is a rule-based CLI that converts official Algerian pharmaceutical nomenclature Excel reports into clean CSV datasets.

It is built for reproducible release-cycle processing, open-source collaboration, and reliable downstream ingestion.

Releases are irregular, but input and output naming must follow the `YYYY-MM` convention.

---

## Table of Contents

- [medz-extractor](#medz-extractor)
  - [Table of Contents](#table-of-contents)
  - [Why this project](#why-this-project)
  - [Features](#features)
  - [External contract](#external-contract)
  - [Quick start](#quick-start)
    - [1) Install](#1-install)
    - [2) Add an input file](#2-add-an-input-file)
    - [3) Run](#3-run)
  - [Usage](#usage)
    - [Failure modes](#failure-modes)
  - [How it works](#how-it-works)
  - [Project structure](#project-structure)
  - [Quality and CI](#quality-and-ci)
  - [Contributing](#contributing)
  - [AI-Augmented Development](#ai-augmented-development)
  - [License](#license)

---

## Why this project

Official nomenclature `.xlsx` releases are not directly usable as structured datasets:

- they include an institutional header block above the table,
- footer notes/legend rows at the end,
- and occasional schema drift (for example: extra empty columns).

This tool makes the extraction process consistent, explicit, and easy to automate.

---

## Features

- Fuzzy sheet detection for the 3 required sheets (`Nomenclature`, `Non Renouvelés`, `Retraits`)
- Structural header detection (instead of hardcoded row numbers)
- Footer-aware extraction with fail-fast behavior
- Empty-column cleanup while preserving column order
- UTF-8 CSV export with configurable delimiter
- CI-ready workflow for release-cycle processing

---

## External contract

For every valid input Excel workbook, `medz-extractor` guarantees exactly these
three CSV outputs for downstream consumers (including Spring Batch jobs):

- `Nomenclature` sheet → `nomenclature.csv`
- `Non Renouvelés` sheet → `non_renouveles.csv`
- `Retraits` sheet → `retraits.csv`

Contract guarantees:

- exactly these 3 files are produced per input workbook,
- UTF-8 encoding,
- stable delimiter (default `,`, configurable),
- header row always first in each CSV.

---

## Quick start

### 1) Install

```bash
git clone https://github.com/anisbouhadida/medz-extractor.git
cd medz-extractor
pip install -e .
```

### 2) Add an input file

```text
input/2025-11.xlsx
```

### 3) Run

```bash
medz-extractor input/2025-11.xlsx --out output/2025-11/
```

---

## Usage

Both CLI forms are supported:

```bash
medz-extractor input/2025-11.xlsx --out output/2025-11/
medz-extractor process input/2025-11.xlsx --out output/2025-11/
```

Optional delimiter:

```bash
medz-extractor input/2025-11.xlsx --out output/2025-11/ --delimiter ';'
```

Generated files:

```text
output/YYYY-MM/
├── nomenclature.csv
├── non_renouveles.csv
└── retraits.csv
```

### Failure modes

On failure, the CLI exits with a non-zero code and logs a clear error.
Typical cases include:

- missing required sheet(s) (`Missing expected sheet(s): ...`)
- header row not detected (`Header row not found: ...`)
- extracted table is empty (`Extracted data has 0 rows ...`)
- CSV write failure (`CSV write failed for '...': ...`)
- invalid/unreadable input path (`Invalid value for 'INPUT_FILE': Path '...' does not exist.`)

---

## How it works

1. Open workbook in read-only mode.
2. Detect expected sheets with accent/case/spacing tolerant matching.
3. Detect real table header row from structure (tabular thresholds).
4. Extract data rows and stop before footer/structural collapse.
5. Drop entirely empty columns.
6. Write normalized CSVs to the output folder.

If a required sheet is missing, header is not found, extracted data is empty, or CSV writing fails, the command exits with a clear non-zero error.

---

## Project structure

```text
src/medz_extractor/
├── cli.py             # Typer CLI entrypoint
├── sheet_detector.py  # fuzzy sheet matching
├── parser.py          # structural parsing (header/footer/table)
├── schema.py          # empty-column normalization
└── writer.py          # CSV writing

tests/
├── test_sheet_detector.py
├── test_parser.py
├── test_schema.py
└── test_writer.py
```

Detailed parsing/behavior rules: [docs/SPECS.md](docs/SPECS.md)

---

## Quality and CI

Run tests locally:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=medz_extractor --cov-report=term-missing
```

**Test coverage** focuses on sheet-name fuzzy matching, header/footer
detection, structural-collapse stopping, blank-row handling, empty-column
dropping, CSV writing, and end-to-end regression against golden outputs.

GitHub Actions workflows:

- **CI** (`.github/workflows/ci.yml`) — runs on every push/PR to `main`;
  lints with Ruff, runs the full test suite with coverage, and updates the
  coverage badge via a GitHub Gist.
- **Process** (`.github/workflows/process.yml`) — runs on push to `main` when
  `input/**.xlsx` changes; generates `output/<YYYY-MM>/*.csv` and auto-commits.

<details>
<summary>One-time setup for the dynamic coverage badge</summary>

1. Create a **public** GitHub Gist (content doesn't matter — it will be
   overwritten by CI). Copy its **Gist ID** from the URL.
2. Create a **classic Personal Access Token** with only the `gist` scope
   (Settings → Developer settings → Tokens (classic)).
3. In your repo → **Settings → Secrets and variables → Actions**:
   - Add a **secret** `GIST_TOKEN` with the PAT.
   - Add a **variable** `COVERAGE_GIST_ID` with the Gist ID.
4. Replace `COVERAGE_GIST_ID` in the badge URL in this README with the
   actual Gist ID.

After the first push to `main`, the badge updates automatically.
</details>

---

## Contributing

Contributions are welcome.

This project is currently maintained by a solo developer, so focused, well-scoped pull requests are especially appreciated.

1. Fork the repository.
2. Add/update an input file under `input/YYYY-MM.xlsx` (required naming format) or improve extraction logic/tests.
3. Open a pull request with a clear description of the change.

Before contributing, please read:

- [docs/PRD.md](docs/PRD.md)
- [docs/SPECS.md](docs/SPECS.md)

---

## AI-Augmented Development

This project uses an AI-augmented development workflow:

- ChatGPT (GPT-5.2, Thinking mode): early brainstorming and idea refinement.
- Perplexity: targeted technical research.
- GitHub Copilot (Claude Opus 4.6, GPT-5.3-Codex): implementation support and iteration.

All final design and code decisions were reviewed and validated by the maintainer.

---

## License

[MIT](LICENSE)
