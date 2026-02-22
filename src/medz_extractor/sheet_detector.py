"""Sheet detection — fuzzy matching of expected sheet names.

Responsibilities:
- Locate the 3 required sheets (Nomenclature, Non Renouvelés, Retraits)
  using case-insensitive, accent-insensitive, whitespace-tolerant matching.
- Raise a clear error if any expected sheet is missing.
"""
