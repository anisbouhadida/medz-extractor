"""Schema normalization utilities.

Responsibilities:
- Drop columns that are entirely empty (all values blank or null).
- Preserve column order from the detected header row.
"""
