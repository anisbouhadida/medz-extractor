"""Structural parser for nomenclature sheets.

Responsibilities:
- Detect the real header row (skip institutional header block).
- Extract tabular data rows.
- Stop extraction at footer markers (F=, I=, Nb:) or structural collapse.
"""
