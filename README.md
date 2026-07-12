# okama-macro

Macro-economic data-source clients (CPI, central-bank policy rates) for the
[okama](https://github.com/mbk-dev/okama) project. Consolidates the former
per-source micro-repos and okama-API in-repo clients (mbk-dev/okama-API#41,
ADR 0001).

## Install

```
pip install "okama-macro @ git+https://github.com/mbk-dev/okama-macro.git"
```

Python >= 3.11; works on pandas 2.x and 3.x.

## Unified API

```python
import okama_macro

okama_macro.list_series()
# ['HKD.INFL', 'HK_BR.RATE', 'IND_RBI.RATE', 'INR.INFL', 'USD.INFL', 'US_EFFR.RATE']

s = okama_macro.get('US_EFFR.RATE', first_date='2020-01-01')
```

Contract, uniform for every key:

- values are **decimal fractions** (m/m inflation `0.0042`, rate `0.0525`);
- CPI series are monthly on first-of-month dates (derived from index levels
  via `pct_change()`, base-invariant);
- rate series carry **observations only — no padding** (pad on the consumer
  side if you need a daily grid);
- ascending `DatetimeIndex`, float dtype, `Series.name` equals the key.

Raw per-source clients (data as published: index levels, percent) live in
`okama_macro.sources.{fred,censtatd,hkma,bis,mospi,rbi}`.

## Environment

- `FRED_API_KEY` — required for the FRED-backed keys (`USD.INFL`, `US_EFFR.RATE`).
- `PROXY_HOST`/`PROXY_PORT`(/`PROXY_USER`/`PROXY_PASS`) — optional outbound
  proxy used by the sources that need one (`bis`, `mospi`, `rbi`).
