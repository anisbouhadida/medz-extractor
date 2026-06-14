# Contributing

Thanks for considering a contribution to `medz-extractor`.

This is an open-source project maintained by a solo software engineer. Small,
focused improvements are easiest to review and merge.

## Project Scope

This repository owns one job:

```text
official Excel workbook -> normalized CSV files
```

Please keep these concerns out of this repository:

- web scraping or download automation,
- database loading,
- Spring Batch code,
- APIs or dashboards,
- data enrichment or deduplication.

Those can integrate with this project, but they should live elsewhere.

## Good Contributions

Useful contributions include:

- support for a new official workbook layout,
- tests for a real release that exposed a parsing edge case,
- clearer error messages,
- fixture or golden-output improvements,
- documentation improvements for Algerian developers,
- CI or tooling cleanup that keeps the project simple.

## Opening Issues

Use the GitHub issue templates when possible:

- **Bug report** for script crashes or unexpected failures.
- **Workbook parsing issue** for official Excel files that are not extracted
  correctly.
- **Feature or documentation request** for small improvements to the project,
  docs, tests, or contributor workflow.

Clear examples, command output, and release months help the maintainer respond
quickly.

## Development Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
```

Run tests:

```bash
.venv/bin/pytest
```

Run checks:

```bash
.venv/bin/ruff check scripts/ tests/
.venv/bin/ruff format --check scripts/ tests/
```

Run the script locally:

```bash
.venv/bin/python scripts/extract_medz.py input output
```

## Fixtures And Golden Files

Regression fixtures live in `tests/fixtures/`.

Golden CSV outputs live in `tests/golden/<YYYY-MM>/`.

When adding a fixture:

1. Add the workbook as `tests/fixtures/YYYY-MM.xlsx`.
2. Generate CSVs with the extractor.
3. Review the CSVs manually.
4. Commit the fixture and golden CSVs together.
5. Add or update tests if the fixture captures a new edge case.

Do not update golden files casually. A golden diff means the downstream CSV
contract may have changed.

## Pull Request Guidelines

- Keep PRs focused on one behavior or documentation improvement.
- Explain the real workbook/layout problem when changing parser logic.
- Add tests before or with parser behavior changes.
- Preserve the fixed CSV contract unless the breaking change is intentional and
  documented.
- Avoid adding runtime dependencies unless the benefit is clear and the project
  remains easy to run.

## Licensing

By contributing, you agree that your contribution will be licensed under the
same license as the project: GNU AGPLv3 or later.

This means contributions stay open source with the rest of the extractor. The
license allows commercial use, but modified distributed versions and modified
network-service versions must keep source code available under the same license.

## CI Expectations

Pull requests are expected to pass:

```bash
.venv/bin/ruff check scripts/ tests/
.venv/bin/ruff format --check scripts/ tests/
.venv/bin/pytest
```

The GitHub Actions CI runs the same checks on pull requests and pushes to
`main`.

## Release Process

Releases are maintainer-driven and tag-based.

Use a semantic version tag when the script, docs, or CSV contract should be
published for users:

```bash
git tag v1.2.3
git push origin v1.2.3
```

The release workflow reruns lint, format, and tests, then publishes a GitHub
Release containing a small script bundle and SHA-256 checksums.

Before tagging:

- confirm CI is green on `main`,
- review any CSV contract changes,
- update docs when user-facing behavior changed.

## Maintainer Notes

Because this is solo-maintained, review time may vary. Clear PR descriptions,
small diffs, and reproducible examples help a lot.
