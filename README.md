# medz-extractor

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.14+](https://img.shields.io/badge/Python-3.14%2B-blue.svg)

**medz-extractor** is a deterministic, open-source preprocessing tool that converts official Algerian pharmaceutical nomenclature Excel reports into clean, structured CSV datasets for reproducible data workflows.

---

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Output Structure](#output-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

Each month, an official `.xlsx` file is published containing pharmaceutical nomenclature data. These files include institutional header blocks, footer notes, and occasional schema changes that make them unsuitable for direct ingestion.

`medz-extractor` automates the cleaning process:

- Detects and validates the 3 expected sheets (`Nomenclature`, `Non Renouvelés`, `Retraits`)
- Strips institutional headers and footer notes
- Drops entirely empty columns
- Outputs standardized CSV files with consistent schema and encoding

No database logic, no LLM usage, no network access — purely deterministic file processing.

---

## Requirements

- Python 3.14+
- [`openpyxl`](https://openpyxl.readthedocs.io/)
- [`typer`](https://typer.tiangolo.com/)

---

## Installation

```bash
git clone https://github.com/your-org/medz-extractor.git
cd medz-extractor
pip install -e .
```

---

## Usage

Place the Excel file under `input/`:

```
input/2025-11.xlsx
```

Run the processing command:

```bash
medz-extractor process input/2025-11.xlsx --out output/2025-11/
```

On success, the tool logs the rows extracted, columns dropped, and CSV paths written, then exits with code `0`. On any failure (missing sheet, undetectable header, zero data rows), it exits with a non-zero code and a descriptive error message.

---

## Output Structure

```
output/
└── YYYY-MM/
    ├── nomenclature.csv
    ├── non_renouveles.csv
    └── retraits.csv
```

All CSV files use **UTF-8** encoding and a consistent delimiter. Column order matches the detected header row in the source workbook.

---

## Contributing

1. Fork the repository.
2. Add or update the Excel file under `input/YYYY-MM.xlsx`.
3. Open a pull request — GitHub Actions will run the preprocessing pipeline and commit the generated CSVs automatically.

Please read [docs/SPECS.md](docs/SPECS.md) before contributing to understand the parsing rules and failure conditions.

---

## License

[MIT](LICENSE)