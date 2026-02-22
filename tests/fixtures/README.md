# Test Fixtures

Real MIPH (*Ministère de l'Industrie Pharmaceutique*) Excel files
from different months/years.  These are the official nomenclature
reports placed here for regression testing.

## Fixture catalogue

| File | Period |
| --- | --- |
| `2024-08.xlsx` | August 2024 |
| `2024-12.xlsx` | December 2024 |
| `2025-10.xlsx` | October 2025 |
| `2025-12.xlsx` | December 2025 |

## Adding a new fixture

1. Place the `.xlsx` under `tests/fixtures/`.
2. Run `medz-extractor <file> --out tests/golden/<name>/` to generate golden CSVs.
3. Review the golden CSVs for correctness.
4. Commit both the fixture and the golden CSVs.
5. The parametrised regression test picks it up automatically.

## Golden CSV outputs

Expected outputs are committed in `tests/golden/`.  Each fixture
has a sub-directory named after the fixture stem (e.g. `2024-08/`)
containing the 3 expected CSV files:

- `nomenclature.csv`
- `non_renouveles.csv`
- `retraits.csv`
