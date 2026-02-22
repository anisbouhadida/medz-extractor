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

    Creates parent directories automatically.  Uses
    ``csv.QUOTE_MINIMAL`` so that fields containing the delimiter,
    quotes, or newlines are properly escaped.

    Parameters:
        headers: Column header strings (first row of CSV).
        data_rows: List of data rows (each a list of strings).
        output_path: Destination file path (``pathlib.Path``).
        delimiter: Field delimiter (default ``","``).

    Returns:
        The *output_path* that was written, for easy chaining.

    Raises:
        ValueError: If *headers* or *data_rows* is empty.
        OSError: If the file cannot be created or written.
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
