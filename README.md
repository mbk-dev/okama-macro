# okama-macro

[![PyPI](https://img.shields.io/pypi/v/okama-macro.svg)](https://pypi.org/project/okama-macro/)
[![Python](https://img.shields.io/pypi/pyversions/okama-macro.svg)](https://pypi.org/project/okama-macro/)
[![CI](https://github.com/mbk-dev/okama-macro/actions/workflows/ci.yml/badge.svg)](https://github.com/mbk-dev/okama-macro/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/okama-macro.svg)](https://pypi.org/project/okama-macro/)

![okama-macro — Macroeconomic data, normalized across borders](https://raw.githubusercontent.com/mbk-dev/okama-macro/main/docs/assets/okama-macro-hero.png)

Normalized CPI inflation and central-bank rate series for Python, built for the
[okama](https://github.com/mbk-dev/okama) project and available as a standalone
package.

`okama-macro` consolidates official macroeconomic data clients behind one
installable package, a shared HTTP/DataFrame layer, and a consistent public API.

## Highlights

- **One API** — discover series with `list_series()` and fetch them with `get()`.
- **Consistent output** — every public series uses decimal fractions, an
  ascending `DatetimeIndex`, float values, and a stable series name.
- **Broad coverage** — CPI and policy-rate series across the United States,
  Hong Kong, India, China, the United Kingdom, Israel, and the euro area.
- **Raw-source access** — use the underlying clients when source-native units
  and shapes are required.
- **Source-aware transport** — shared retries, proxy support, secret redaction,
  and compatibility handling for sources with specialized TLS or User-Agent
  requirements.

## Installation

```bash
python -m pip install okama-macro
```

Requires **Python ≥ 3.11**. Runs on both **pandas 2.x and 3.x**.

## Quick start

```python
from okama_macro import get, list_series

# Discover the supported public keys.
keys = list_series()

# Fetch a normalized rate series for a date window.
deposit_rate = get(
    "EU_DFR.RATE",
    first_date="2024-01-01",
    last_date="2024-12-31",
)

# Monthly m/m inflation as a decimal fraction:
us_inflation = get("USD.INFL", first_date="2024-01-01")
```

Each `get()` call returns a `pandas.Series`. For example, a 3.62% rate is
represented as `0.0362`, not `3.62`.

> `USD.INFL` and `US_EFFR.RATE` require a
> [FRED API key](https://fred.stlouisfed.org/docs/api/api_key.html) in the
> `FRED_API_KEY` environment variable.

## Data contract

Every series returned by `get()` obeys the same contract, so callers never
special-case a source:

- **Decimal fractions** — m/m inflation `0.0042`, a rate `0.0525` (never percent,
  never an index level).
- **CPI series** are monthly, stamped on the **first of the month**, derived from
  the source's index via `pct_change()` (base-invariant).
- **Rate series** normally carry **observations only — no padding**. Forward-fill
  to a daily grid on the consumer side if you need one. `UK_BR.RATE` is the
  documented exception: the Bank of England source publishes change dates, and
  the client safely forward-fills them into a daily series.
- **Ascending `DatetimeIndex`**, `float` dtype, and `Series.name == key`.

`get()` raises `ValueError` for an unknown key (listing the known ones);
`list_series()` returns the available keys, sorted.

## Available series

| Key | Series | Country | Source module |
|-----|--------|---------|---------------|
| `USD.INFL` | US CPI, m/m | United States | `fred` (FRED `CPIAUCNS`) |
| `US_EFFR.RATE` | US Federal Funds rate | United States | `fred` (FRED `DFF`) |
| `HKD.INFL` | Hong Kong Composite CPI, m/m | Hong Kong | `censtatd` (HK C&SD) |
| `HK_BR.RATE` | HKMA Discount Window Base Rate | Hong Kong | `hkma` |
| `INR.INFL` | India General CPI, m/m | India | `mospi` (MOSPI) |
| `IND_RBI.RATE` | RBI policy repo rate | India | `bis` (history) + `rbi` (same-day tail) |
| `CNY.INFL` | China CPI, m/m | China | `nbsc` (NBS China) |
| `CHN_LPR1.RATE` | China one-year Loan Prime Rate | China | `cfets` |
| `CHN_LPR5.RATE` | China five-year Loan Prime Rate | China | `cfets` |
| `GBP.INFL` | UK CPIH, m/m | United Kingdom | `ons` (UK ONS) |
| `UK_BR.RATE` | Bank of England Bank Rate | United Kingdom | `boe` |
| `ILS.INFL` | Israel CPI, m/m | Israel | `boi` (Bank of Israel) |
| `ISR_IR.RATE` | Bank of Israel policy rate | Israel | `boi` |
| `EU_MRO.RATE` | ECB main refinancing operations rate | Euro area | `ecb` |
| `EU_MLR.RATE` | ECB marginal lending facility rate | Euro area | `ecb` |
| `EU_DFR.RATE` | ECB deposit facility rate | Euro area | `ecb` |

## Raw source clients

Each source also exposes its raw client under `okama_macro.sources.*`, returning
data **as the agency publishes it** (CPI index levels, rates in percent) — use
these only if you need the unnormalised series; prefer `get()` otherwise.

```python
from okama_macro.sources import (
    bis, boe, boi, censtatd, cfets, ecb, fred, hkma, mospi, nbsc, ons, rbi
)

hkma.get_base_rate()          # percent, daily
censtatd.get_composite_cpi()  # CPI index level, monthly
```

## Configuration (environment)

| Variable | Needed for | Notes |
|----------|-----------|-------|
| `FRED_API_KEY` | `USD.INFL`, `US_EFFR.RATE` | Free key from FRED; kept out of logs. |
| `PROXY_HOST`, `PROXY_PORT` | `bis`, `mospi`, `rbi` | Optional outbound HTTP proxy. |
| `PROXY_USER`, `PROXY_PASS` | — | Optional proxy credentials. |

## Data quality

Material parser changes and newly consumed series are checked against independent
sources when a comparable mirror exists. The recorded audits describe the
comparison method, coverage, and known limitations:

- [China CPI](https://github.com/mbk-dev/okama-macro/blob/main/docs/audits/nbsc-cny-infl.md)
- [China Loan Prime Rates](https://github.com/mbk-dev/okama-macro/blob/main/docs/audits/cfets-chn-lpr.md)
- [ECB key rates](https://github.com/mbk-dev/okama-macro/blob/main/docs/audits/ecb-eu-rates.md)
- [Israel CPI and policy rate](https://github.com/mbk-dev/okama-macro/blob/main/docs/audits/boi-ils-isr.md)
- [UK CPIH](https://github.com/mbk-dev/okama-macro/blob/main/docs/audits/ons-gbp-infl.md)
- [UK Bank Rate](https://github.com/mbk-dev/okama-macro/blob/main/docs/audits/boe-uk-br.md)

## Architecture

```
okama_macro/
├── __init__.py        # public API: get(), list_series()
├── registry.py        # key -> normalised Series (the contract)
├── _http.py           # shared Session: retry/back-off, proxy, browser UA,
│                       #   legacy-TLS, secret redaction
├── _frame.py          # DataFrame/Series shaping helpers
└── sources/           # one client per source (bis, boe, boi, censtatd, cfets,
                        #   ecb, fred, hkma, mospi, nbsc, ons, rbi)
```

Two layers: thin **sources** (data as published, on the shared `_http`) and a
**registry** that normalises each key to the contract above.

The package replaces separate per-source clients and duplicated modules that
previously lived across the okama ecosystem. The rationale and migration history
are tracked in [mbk-dev/okama-API#41](https://github.com/mbk-dev/okama-API/issues/41).

## Contributing

Set up a local development checkout with Poetry:

```bash
git clone https://github.com/mbk-dev/okama-macro.git
cd okama-macro
poetry install
poetry run pytest -q
poetry run ruff check .
poetry build
```

CI runs the suite and lint on Python 3.11, 3.12, 3.13 and 3.14. Keep executable
changes covered by tests and do not commit `poetry.lock`; the full development
conventions are documented in
[`AGENTS.md`](https://github.com/mbk-dev/okama-macro/blob/main/AGENTS.md).

## License

`okama-macro` is distributed under the
[MIT License](https://spdx.org/licenses/MIT.html).
