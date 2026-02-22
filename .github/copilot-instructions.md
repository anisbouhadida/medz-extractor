# GitHub Copilot Instructions — medz-extractor

You are an AI pair programmer working on the `medz-extractor` project.

## Project context

- `medz-extractor` is a deterministic, open-source preprocessing tool that converts official Algerian pharmaceutical nomenclature Excel reports into clean CSV datasets.
- Inputs are `.xlsx` files that contain:
  - An institutional header block (non-tabular text) above the real table header row.
  - A real table header row (column names).
  - Tabular data rows.
  - Optional footer notes block (e.g., `F=...`, `I=...`, `Nb:...`) after an empty row.
  - Occasional schema expansion (e.g., extra empty columns starting Nov 2025) that must be dropped.
- Outputs:
  - Exactly one CSV per expected sheet: `nomenclature.csv`, `non_renouveles.csv`, `retraits.csv`.
- The tool must run both locally and via GitHub Actions (CI).

## Key requirements (must follow)

1. Deterministic behavior

- Same input must always produce the same output.
- Do not introduce randomness, timestamps in data, system time, external service calls, network access, or any LLM usage from within the code.
- Do not rely on environment-specific behavior; keep parsing logic explicit and stable.

2. Scope: Excel → CSV only

- This project only extracts, cleans, and normalizes data from Excel to CSV.
- Do not add database access, ORM layers, web APIs, or UI logic.

3. Sheet validation

- The workbook must contain 3 expected sheets, detected via fuzzy matching:
  - Nomenclature
  - Non Renouvelés
  - Retraits
- Matching rules:
  - Case-insensitive.
  - Accent-insensitive.
  - Robust to minor spacing and punctuation differences.
- If any expected sheet is missing:
  - Fail fast with a clear, actionable error message.
  - Do not silently skip or guess an alternative sheet.

4. Structural parsing

- Remove the top institutional header block by detecting the real header row:
  - A header row is the first row with ≥ threshold non-empty cells and the next row also tabular.
  - Suggested thresholds:
    - Nomenclature sheet: at least 8 non-empty cells.
    - Other sheets: at least 6 non-empty cells.
- Extract tabular data starting immediately after the detected header row.
- Stop extraction before footer notes:
  - Stop if any cell in a row starts with `F=`, `I=`, or `Nb:` (whitespace tolerant).
  - Also stop when the table structure clearly collapses (e.g., a blank row followed by rows that are no longer tabular).
- Keep parsing logic in small, pure functions that can be unit tested.

5. Schema handling

- After extraction:
  - Drop columns that are entirely empty (all values blank or null).
- Preserve column order exactly as in the extracted header row.
- Avoid introducing dynamic schema changes between runs for the same input.

6. CSV output

- Encoding: UTF-8.
- Use a stable delimiter (configurable, but default must be consistent across all outputs).
- Preserve the column order from the detected header.
- Quote and escape fields correctly to preserve commas, semicolons, and other delimiters inside text.
- Do not write partial or inconsistent CSVs; fail clearly on write errors.

7. Fail fast

- Fail with a clear error in these cases:
  - Expected sheet missing.
  - Header row not found according to the structural rules.
  - Extracted data has 0 rows (after dropping header and footers).
  - CSV write fails for any reason.
- Prefer explicit, human-readable error messages over silent fallbacks.

## Coding standards

- Language: Python 3.14+.
- Prefer standard library where possible.
- Use `openpyxl` for reading `.xlsx` files.
- Keep functions small, pure, and testable, especially for parsing and detection logic.
- Avoid global state; pass explicit inputs and return explicit outputs.
- Add type hints for all new functions and public interfaces.
- Use `logging` from the standard library; do not use `print` except for CLI help output.
- Make errors actionable and human-readable.

## Repository conventions

- CLI entry point:
  - Use `src/medz_extractor/cli.py` (or equivalent) with a Typer-based CLI.
  - Support a command of the form: `process <input.xlsx> --out <output_dir>`.
- When running in the repository, keep outputs under `output/YYYY-MM/`.
- Normalize output file names exactly to:
  - `nomenclature.csv`
  - `non_renouveles.csv`
  - `retraits.csv`
- Use `pathlib.Path` for filesystem paths.

## Testing guidance

- Use `pytest` for all tests.
- Tests should cover at least:
  - Sheet name fuzzy matching (accents, case, spaces, minor differences).
  - Header detection on realistically formatted sheets.
  - Footer detection based on `F=`, `I=`, `Nb:` prefixes and structural collapse.
  - Dropping entirely empty columns from the extracted data.
  - Failure cases:
    - Missing expected sheet.
    - Header row not found.
    - Extracted data has zero rows.
- Prefer small, focused fixtures.
- If sample `.xlsx` files are included:
  - Keep them minimal.
  - Document their structure and purpose clearly.

## What “good PR” looks like

- Small, focused changes that are easy to review.
- Deterministic behavior preserved or improved.
- Tests added or updated for any parsing or structural changes, especially edge cases.
- Clear, actionable error messages.
- No new heavy dependencies unless there is a very strong justification and tests are provided.

## Avoid

- Any network access from the project code.
- Any LLM calls or AI inference usage inside the codebase.
- “Magic” heuristics without corresponding tests and clear documentation.
- Silent fallbacks or hidden behavior; prefer explicit failure.
- Writing CSVs with inconsistent schema or ordering across runs for the same input.
