"""Tests for the CSV writer module.

Covers:
- Output directory is created if missing.
- CSV is written with UTF-8 encoding.
- Fields containing the delimiter are correctly quoted/escaped.
- Write failure raises a clear error.
"""
