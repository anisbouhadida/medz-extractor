# Nomenclature Preprocessing Script — PRD

## Overview

`medz-extractor` is an open-source preprocessing script for Algerian
pharmaceutical nomenclature data.

It converts official Excel workbooks into stable CSV files that can be loaded
by a downstream Spring Batch ETL application or reused by other developers.

The project is maintained by a solo software engineer and is designed to stay
small, readable, and easy to run from a shell script.

## Audience

Primary users:

- Algerian developers building health-data tools.
- Developers integrating official nomenclature releases into databases.
- Maintainers of the broader ETL system that downloads workbooks, runs this
  extractor, and loads CSVs through Spring Batch.

Secondary users:

- Open-source contributors who want to improve parsing reliability.
- Data engineers who need deterministic CSV outputs from official Excel files.

## Problem

Official nomenclature Excel files are not directly suitable for automated
loading because they may contain:

- institutional header blocks above the actual data table,
- footer notes and legends after the table,
- accented and inconsistent sheet names,
- embedded newlines in cells,
- extra empty columns introduced by layout changes.

Manual cleanup is slow and difficult to reproduce.

## Goals

- Process all `input/*.xlsx` files in one command.
- Require release filenames to follow `YYYY-MM.xlsx`.
- Produce one `output/YYYY-MM/` folder per workbook.
- Generate exactly three CSV files per workbook.
- Keep CSV formatting stable for Spring Batch ingestion.
- Archive current month CSVs before replacing them.
- Leave existing outputs untouched when replacement extraction fails.
- Keep the runtime interface simple enough for shell automation.
- Keep implementation transparent for open-source review.

## Non-Goals

- No file downloading or web scraping.
- No database access.
- No Spring Batch execution.
- No API, web UI, or dashboard.
- No dynamic delimiter selection.
- No dry-run mode.
- No installable Python package or console entry point.
- No enrichment, deduplication, or cross-release diffing.

## System Context

The broader system is expected to look like this:

```text
Downloader or manual download
        |
        v
input/YYYY-MM.xlsx
        |
        v
medz-extractor
        |
        v
output/YYYY-MM/*.csv
        |
        v
Spring Batch ETL
        |
        v
Database
```

Only the `medz-extractor` step is implemented in this repository.

## External Contract

For every valid workbook:

| Logical sheet | Output file |
| --- | --- |
| `Nomenclature` | `nomenclature.csv` |
| `Non Renouvelés` | `non_renouveles.csv` |
| `Retraits` | `retraits.csv` |

CSV contract:

- UTF-8 encoding
- comma delimiter
- header row first
- deterministic output for identical workbook content
- exactly three CSV files per valid workbook

## Archive Contract

When replacing outputs for `YYYY-MM`, existing `output/YYYY-MM/*.csv` files are
moved to:

```text
archive/YYYY-MM/YYYYMMDDTHHMMSSZ/
```

The archive directory is created beside the selected output directory. With the
standard command `python3 scripts/extract_medz.py input output`, this means
`archive/` is created in the repository root.

New CSVs are staged first. Existing outputs are archived only after staging
succeeds, so failed extractions do not remove current data.

## Success Criteria

A release is processed successfully when:

- every input workbook has a valid `YYYY-MM.xlsx` filename,
- every workbook contains the three expected logical sheets,
- every required sheet produces at least one data row,
- all three CSV files are written for every workbook,
- old outputs, when present, are archived before replacement,
- the script exits with code `0`.

Any violation fails the run with exit code `1` and a readable log message.

## Open-Source Maintenance Principles

- Prefer simple Python and standard-library code.
- Keep `openpyxl` as the only runtime dependency.
- Add tests for every new workbook layout edge case.
- Preserve the CSV contract unless a breaking change is explicitly documented.
- Keep non-extraction concerns out of this repository.
- License the project under GNU AGPLv3 or later so improvements remain open
  when redistributed or used as part of a network service.
