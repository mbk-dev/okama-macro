"""MOSPI (India) Consumer Price Index client.

Fetches the headline General All-India Combined CPI as a monthly index-level
series from India's National Statistical Office open API. Callers derive
month-on-month inflation by ``pct_change()`` on the index, which is
base-invariant, so MOSPI's periodic rebasings do not affect the m/m fractions.

**Two bases, one continuous series.** In 2026 MOSPI rebased CPI from base 2012
to base 2024 and moved the live feed to a new endpoint with a new hierarchy:

* **base 2012** — ``getCPIIndex``: the historical series, frozen at 2025-12
  (``group_code=0`` General, ``state_code=99`` All-India, ``sector_code=3``
  Combined). Never updates again.
* **base 2024** — ``getCPIData``: the live series from 2026-01 onward, with
  renumbered codes (All-India is ``state_code=1``) and a division hierarchy
  (the headline index is ``division="CPI (General)"`` with ``group=None``,
  not ``group_code=0``). Queried one month at a time via ``year`` +
  ``month_code``; a month that returns no data is simply not published yet.

We keep base 2012 for months through its frozen tail (the anchor, 2025-12,
which base 2024 also carries) and splice the rescaled base-2024 series on top
for months past the anchor — so stored history is unchanged and only new months
are added. See okama-API#50.

Two MOSPI-specific quirks, both handled here:

* **TLS.** ``api.mospi.gov.in`` presents a chain that OpenSSL rejects
  ("self-signed certificate in certificate chain") and needs legacy server
  renegotiation. We mount an adapter with ``OP_LEGACY_SERVER_CONNECT`` and
  disable verification (``verify=False`` / ``CERT_NONE``) — the same workaround as
  MOSPI's own reference client (``nso-india/esankhyiki-mcp``, MIT). The adapter is
  provided by the shared ``_http.legacy_tls_session()`` helper.
* **No key.** The endpoint is keyless (the swagger's Bearer scheme is optional and
  the reference client sends none).

Foreign-source proxying is handled by ``_http.legacy_tls_session()``: the request
goes through the local HAProxy on the production server when ``PROXY_*`` env vars
are set, else direct (e.g. tests).
"""

import logging

import pandas as pd

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.mospi')

CPI_INDEX_URL = 'https://api.mospi.gov.in/api/cpi/getCPIIndex'  # base 2012 (frozen)
CPI_DATA_URL = 'https://api.mospi.gov.in/api/cpi/getCPIData'    # base 2024 (live)
API_TIMEOUT = 60  # seconds
_PAGE_SIZE = 500
# getCPIData caps limit at 100 and returns only the latest month unless
# constrained; we query one month at a time so a small page suffices.
_DATA_PAGE_SIZE = 100
# The India CPI publishes monthly with a ~1.5-month lag. A last month older
# than this many days means the feed stalled (e.g. base 2024 stopped and the
# spliced tail fell back to the frozen 2025-12 anchor) — fail the nightly
# update loudly instead of silently republishing a stale month. See okama-API#50.
_STALE_DAYS = 120
# Fallback anchor when base 2012 returns nothing: the last frozen 2012 month,
# which base 2024 also carries, so the splice can still rescale onto it.
_DEFAULT_ANCHOR = pd.Timestamp('2025-12-01')

# General All-India Combined index on the frozen 2012 base.
_GENERAL_PARAMS_2012 = {
    'base_year': '2012',
    'series': 'Current',
    'state_code': '99',   # All India (base-2012 numbering)
    'sector_code': '3',   # Combined (1 Rural, 2 Urban, 3 Combined)
    'group_code': '0',    # General
    'Format': 'JSON',
}

# General All-India Combined index on the live 2024 base.
_GENERAL_PARAMS_2024 = {
    'base_year': '2024',
    'series_code': 'Current',
    'state_code': '1',    # All India (base-2024 renumbering)
    'sector_code': '3',   # Combined
    'Format': 'JSON',
    'limit': str(_DATA_PAGE_SIZE),
    'page': '1',
}


def _fetch_base_2012(session) -> pd.Series:
    """The frozen base-2012 General All-India Combined index (2013-01 → 2025-12)."""
    records: list[dict] = []
    page = 1
    while True:
        params = {**_GENERAL_PARAMS_2012, 'limit': str(_PAGE_SIZE), 'page': str(page)}
        response = session.get(CPI_INDEX_URL, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json().get('data') or []
        if not data:
            break
        records.extend(data)
        page += 1
    records = [r for r in records if r.get('group') == 'General']
    if not records:
        return pd.Series(dtype='float64')
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(
        df['year'].astype(int).astype(str) + '-' + df['month'],
        format='%Y-%B',
    )
    s = df.set_index('date')['index'].astype(float)
    return s.sort_index()


def _fetch_base_2024(session, start: pd.Timestamp) -> pd.Series:
    """The live base-2024 General index, walked month-by-month from ``start``.

    Requests one month at a time (``year`` + ``month_code``) and stops at the
    first month the API has not published yet. The headline index is the
    ``division="CPI (General)"`` row with ``group=None``.
    """
    horizon = pd.Timestamp.today().normalize() + pd.DateOffset(months=1)
    dates: list[pd.Timestamp] = []
    values: list[float] = []
    cur = start
    while cur <= horizon:
        params = {**_GENERAL_PARAMS_2024,
                  'year': str(cur.year), 'month_code': str(cur.month)}
        response = session.get(CPI_DATA_URL, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json().get('data') or []
        row = next((r for r in data
                    if r.get('division') == 'CPI (General)' and r.get('group') is None),
                   None)
        if row is None:
            break
        dates.append(cur)
        values.append(float(row['index']))
        cur = cur + pd.DateOffset(months=1)
    if not dates:
        return pd.Series(dtype='float64')
    return pd.Series(values, index=pd.DatetimeIndex(dates), dtype='float64')


def _splice(old: pd.Series, new: pd.Series) -> pd.Series:
    """Splice the live ``new`` series onto the frozen ``old`` at their overlap.

    ``new`` is rescaled by ``old[anchor] / new[anchor]`` (anchor = latest common
    month) so the two index levels line up; ``old`` is kept through the anchor
    and rescaled ``new`` is appended past it. m/m across the boundary is then the
    base-2024 internal ratio, and ``old``'s stored history is untouched.
    """
    if new.empty:
        return old
    if old.empty:
        return new
    overlap = old.index.intersection(new.index)
    if overlap.empty:
        return old
    anchor = overlap.max()
    factor = old.loc[anchor] / new.loc[anchor]
    rescaled = new * factor
    combined = pd.concat([old[old.index <= anchor], rescaled[rescaled.index > anchor]])
    return combined.sort_index()


def get_general_cpi(session=None) -> pd.Series:
    """Return the India General CPI (Combined) index level as a monthly Series.

    The index is a first-of-month ``DatetimeIndex`` named ``date`` sorted
    ascending, with the CPI level as float, spliced across the base-2012 and
    base-2024 feeds (see the module docstring). Returns an empty Series when
    neither feed has data.
    """
    if session is None:
        session = _http.legacy_tls_session()
    info_logger.info('Loading India General CPI via MOSPI (base 2012 + base 2024)')
    base_2012 = _fetch_base_2012(session)
    anchor = base_2012.index[-1] if len(base_2012) else _DEFAULT_ANCHOR
    base_2024 = _fetch_base_2024(session, start=anchor)
    s = _splice(base_2012, base_2024)
    if s.empty:
        return pd.Series(dtype='float64', name='INR.INFL')
    s.name = 'INR.INFL'
    lag_days = (pd.Timestamp.today().normalize() - s.index[-1]).days
    if lag_days > _STALE_DAYS:
        raise RuntimeError(
            f'MOSPI CPI series is stale: last month {s.index[-1].date()} is '
            f'{lag_days} days old (limit {_STALE_DAYS}) - the base-2024 feed may '
            f'have moved again; see okama-API#50'
        )
    return s
