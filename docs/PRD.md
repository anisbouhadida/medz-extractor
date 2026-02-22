# Nomenclature Pre-Processing Tool — PRD (v1)

## 1. Overview

This project provides a simple, open-source preprocessing tool that converts official monthly Excel nomenclature files into clean CSV datasets ready for database ingestion.

The system is designed for:

- Community contribution
- Deterministic processing
- Automation via GitHub Actions
- Downstream loading via Spring Batch (separate system)

The tool focuses only on:

- Reading Excel files
- Cleaning structural artifacts
- Exporting normalized CSV files

No database logic is included.

---

## 2. Problem Statement

Each month, an official Excel file is published containing pharmaceutical nomenclature data.

These files:

- Contain formatting blocks (institutional header, footer notes)
- Are not directly usable as structured datasets
- Include schema changes (e.g., new empty columns)
- Must be cleaned before ingestion into a database

Manual preparation is error-prone and not reproducible.

---

## 3. Objectives

Build a simple application that:

1. Reads a monthly Excel file
2. Detects and extracts the 3 expected sheets
3. Removes non-data blocks:
   - institutional header
   - footer notes
4. Handles schema changes:
   - drop empty columns
5. Outputs standardized CSV files
6. Runs automatically via GitHub Actions
7. Allows community contribution via PRs

---

## 4. Non-Goals (v1)

- No data enrichment
- No cross-month comparison
- No deduplication
- No database integration
- No schema registry
- No advanced validation
- No LLM usage

---

## 5. Users

**Primary:**

- Solo maintainer (project owner)
- Open-source contributors

**Secondary:**

- Systems consuming the CSV outputs
- Spring Batch ingestion pipeline

---

## 6. High-Level Workflow

### Contribution flow

1. Contributor submits Excel file via PR: `input/YYYY-MM.xlsx`
2. Maintainer merges PR
3. GitHub Action triggers:
   - runs preprocessing script
   - generates CSV files
4. Action commits outputs: `output/YYYY-MM/*.csv`

---

## 7. Functional Requirements

### 7.1 File Input

- Accept `.xlsx` file
- Located under: `input/`

---

### 7.2 Sheet Detection

Verify presence of 3 sheets (fuzzy name match):

- `Nomenclature`
- `Non Renouvelés`
- `Retraits`

Matching rules:

- Case-insensitive
- Ignore accents
- Allow extra spaces

Fail processing if any sheet is missing.

---

### 7.3 Structural Parsing

For each sheet:

#### Remove institutional header block

- Scan from top
- Find first row with tabular structure:
  - ≥ N non-empty cells
  - next row also tabular
- This row = true header

#### Extract data rows

- Data starts after header row

#### Remove footer

Stop reading when encountering a row containing:

- `F=`
- `I=`
- `Nb:`

OR a blank row followed by non-tabular rows.

---

### 7.4 Schema Handling

After extracting the table:

- Detect columns where all values are empty
- Drop those columns

---

### 7.5 CSV Output

For each sheet generate:

```
output/YYYY-MM/nomenclature.csv
output/YYYY-MM/non_renouveles.csv
output/YYYY-MM/retraits.csv
```

Requirements:

- UTF-8 encoding
- Consistent delimiter
- Header row preserved
- Fixed column order

---

### 7.6 Failure Conditions

Script must fail if:

- Sheet is missing
- Header is not detected
- Output row count = 0

---

## 8. Technical Stack

**Language:**

- Python 3.14+

**Libraries:**

- `openpyxl`
- `csv` (standard library)
- `typer`
- `logging`

**CI:**

- GitHub Actions

---

## 9. Repository Structure

```
input/
└── YYYY-MM.xlsx

output/
└── YYYY-MM/
    ├── nomenclature.csv
    ├── non_renouveles.csv
    └── retraits.csv

src/
tests/
.github/workflows/
```

---

## 10. GitHub Actions Workflow (v1)

**Trigger:** push to `main`

**Steps:**

1. Checkout repo
2. Setup Python
3. Install dependencies
4. Run preprocessing script
5. Commit CSV outputs if changed

---

## 11. Determinism Requirement

Given the same XLSX input:

- Output CSV must be identical
- No randomness
- No external API calls
