"""okama-macro: consolidated macro-economic data-source clients for okama.

Public API: ``get(key, first_date=None, last_date=None)`` returns a normalised
``pd.Series`` (decimal fractions, ascending DatetimeIndex, observations only);
``list_series()`` lists the available keys. Per-source raw clients live in
``okama_macro.sources``.
"""

from okama_macro.registry import get, list_series

__all__ = ['get', 'list_series']
