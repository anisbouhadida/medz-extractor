# SPECS.md — Nomenclature Pre-Processing Tool (v1)

## Purpose

Technical specifications for the preprocessing application that converts official monthly Excel nomenclature files into clean CSV files ready for ingestion.

This document defines how the system **MUST** behave (implementation-level rules).

---

## 1. Input Specifications

### Accepted format

- `.xlsx` only

### Input location

```
input/YYYY-MM.xlsx
```

### File assumptions

- Excel produced by official authority
- Contains formatted report structure
- Includes:
  - institutional header block
  - tabular dataset
  - footer notes

---

## 2. Required Sheets

The file **MUST** contain the following sheets (fuzzy detection):

- `Nomenclature`
- `Non Renouvelés`
- `Retraits`

### Matching rules

- Case-insensitive
- Ignore accents
- Ignore extra spaces

### Failure

If any sheet is missing → abort processing.

---

## 3. Structural Parsing Rules

### 3.1 Institutional Header Removal

Scan rows from top until detecting the real header row.

A row qualifies as **HEADER** if:

- non-empty cells ≥ threshold
- next row is also tabular

Thresholds:

- Nomenclature: ≥ 8 non-empty cells
- Other sheets: ≥ 6 non-empty cells

All rows above the header → discard.

---

### 3.2 Data Region Detection

Data starts immediately after the header row.

---

### 3.3 Footer Detection

Stop data extraction when any row contains a value starting with:

- `F=`
- `I=`
- `Nb:`

OR when encountering a blank row followed by non-tabular rows.

Footer and all trailing rows → discard.

---

## 4. Schema Normalization

### Empty Column Removal

After table extraction, for each column:

- If all values are empty or null → drop column

Purpose:

- Handle schema expansion (Nov 2025+)
- Remove unused columns

---

## 5. CSV Output Specifications

For each sheet generate:

```
output/YYYY-MM/nomenclature.csv
output/YYYY-MM/non_renouveles.csv
output/YYYY-MM/retraits.csv
```

### CSV rules

- UTF-8 encoding
- Consistent delimiter (configurable)
- Preserve header order
- Escape quotes
- No extra blank lines

---

## 6. CLI Specifications

### Command

```bash
medz-extractor process input/YYYY-MM.xlsx --out output/YYYY-MM/
```

### Behavior

- Create output folder if missing
- Overwrite existing CSVs for same month
- Return exit code:
  - `0` — success
  - non-zero — failure

---

## 7. Logging Requirements

Per execution log:

- Input file path
- Sheets detected
- Header row index
- Data rows extracted
- Columns dropped
- CSV paths generated
- Execution time

---

## 8. Failure Conditions

Processing **MUST** stop if:

- Missing sheet
- Header not detected
- No data rows
- CSV write failure

Errors must be explicit and human-readable.

---

## 9. Determinism

Given identical XLSX input:

- CSV outputs **MUST** be identical
- No randomness
- No external API calls
- No time-dependent transformations

---

## 10. Configuration (future-ready)

Allow config file for:

- Sheet name patterns
- Header threshold values
- Footer keywords
- CSV delimiter

---

## 11. Testing Requirements

Test scenarios:

1. Header detection works
2. Footer removal works
3. Empty columns dropped
4. Schema expansion handled
5. Missing sheet → failure
6. Malformed file → failure

---

## 12. Performance Expectations

- File size: ~5k rows per sheet
- Target runtime: < 10 seconds per file
- Memory: must operate within typical CI limits

---

## 13. Security Constraints

- No execution of macros
- No external network calls
- Treat Excel as untrusted input
- Parse read-only

---

## 14. Future Extensions (Not v1)

- Schema mapping
- Diffing months
- Metadata manifest
- Dockerization
- Data validation layer
