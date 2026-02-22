"""Tests for parser module.

Covers:
- Header detection with institutional header block present.
- Header not found → failure.
- Footer detection via F=, I=, Nb: markers.
- Footer detection via structural collapse (blank row + non-tabular rows).
- Zero data rows after parsing → failure.
"""
