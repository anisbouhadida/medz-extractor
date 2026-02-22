"""CSV writer.

Responsibilities:
- Write extracted, normalized data to UTF-8 CSV files.
- Create output directories as needed.
- Fail clearly on write errors.
"""

import csv
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

# Default CSV delimiter.
DEFAULT_DELIMITER: str = ","


def write_csv(
    headers: List[str],
    data_rows: List[List[str]],
    output_path: Path,
    delimiter: str = DEFAULT_DELIMITER,
) -> Path:
    """Write headers and data rows to a UTF-8 CSV file.

    Creates parent directories if they do not exist.

    Parameters:
        headers: Column header strings.
        data_rows: List of data rows (each a list of strings).
        output_path: Destination file path.
        delimiter: Field delimiter character.

    Returns:
        The *output_path* that was written.

    Raises:
        OSError: If the file cannot be written.
        ValueError: If headers or data_rows are empty.
    """
    if not headers:
        raise ValueError(
            "Cannot write CSV: headers list is empty."
        )
    if not data_rows:
        raise ValueError(
            "Cannot write CSV: data_rows list is empty."
        )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open(
            "w", encoding="utf-8", newline=""
        ) as fh:
            writer = csv.writer(
                fh,
                delimiter=delimiter,
                quoting=csv.QUOTE_MINIMAL,
            )
            writer.writerow(headers)
            writer.writerows(data_rows)
    except OSError as exc:
        raise OSError(
            f"Failed to write CSV to '{output_path}': {exc}"
        ) from exc

    logger.info(
        "Wrote %d data rows to '%s'.", len(data_rows), output_path
    )
    return output_path
