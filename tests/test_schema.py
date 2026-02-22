"""Tests for schema normalization module.

Covers:
- Entirely empty columns are dropped.
- Partially populated columns are kept.
- Column order is preserved.
- Schema expansion columns (all empty) are removed.
"""
