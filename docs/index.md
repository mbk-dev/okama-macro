# okama-macro

![okama-macro — Macroeconomic data, normalized across borders](assets/okama-macro-hero.png)

`okama-macro` provides normalized CPI inflation and central-bank rate series for
Python. It combines source-specific clients behind one public API while keeping
raw clients available for source-native data.

## Installation

```bash
python -m pip install okama-macro
```

The package supports Python 3.11–3.14 and pandas 2.x–3.x.

## Quick start

```python
from okama_macro import get, list_series

keys = list_series()

deposit_rate = get(
    "EU_DFR.RATE",
    first_date="2024-01-01",
    last_date="2024-12-31",
)
```

`get()` returns a `pandas.Series` with decimal-fraction values, an ascending
`DatetimeIndex`, float dtype, and the requested registry key as its name.

!!! note "FRED API key"

    `USD.INFL` and `US_EFFR.RATE` require `FRED_API_KEY`.

## Public contract

- CPI series contain monthly month-over-month changes on first-of-month dates.
- Rate series normally contain source observations without implicit padding.
- `UK_BR.RATE` is the documented exception and is safely forward-filled from
  Bank of England change dates.
- `first_date` and `last_date` consistently clip the requested window.
- Unknown keys raise a clear `ValueError`.

## Explore

- See the [API reference](api.md) for the two public functions.
- Browse the
  [available series table](https://github.com/mbk-dev/okama-macro#available-series).
- Review the recorded source comparisons under **Data audits**.
- Read the
  [contribution guide](https://github.com/mbk-dev/okama-macro/blob/main/CONTRIBUTING.md)
  before proposing a source or parser change.
