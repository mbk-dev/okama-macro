"""MOSPI (India) Consumer Price Index client.

Fetches the headline General All-India Combined CPI (base 2012) as a monthly
index-level series from India's National Statistical Office open API:

    https://api.mospi.gov.in/api/cpi/getCPIIndex

The query below pins the General index (``group_code=0``), All-India
(``state_code=99``), Combined sector (``sector_code=3``) on the current 2012
base. Callers derive month-on-month inflation by ``pct_change()`` on the index
(base-invariant, so MOSPI's periodic rebasings do not affect the m/m fractions).

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

Base-year note: as of 2026-07 the API's ``base_year=2012`` "Current" series runs
2013-01 → 2025-12 and ``base_year=2024`` is not yet populated. When MOSPI loads
base 2024, recent months will move there under a different (division/class) param
structure and this client will need to splice base 2012 with base 2024.
"""

import logging

import pandas as pd

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.mospi')

CPI_INDEX_URL = 'https://api.mospi.gov.in/api/cpi/getCPIIndex'
API_TIMEOUT = 60  # seconds
_PAGE_SIZE = 500
_HEADERS = {'User-Agent': 'Mozilla/5.0 (okama-data pipeline)'}
# The MOSPI API publishes with a ~7-month lag (observed 2026-07). A last month
# older than this many days means the 2012-base feed stalled (or moved to base
# 2024) — fail the nightly update loudly instead of silently stopping to
# advance. See okama-API#50.
_STALE_DAYS = 330

# General All-India Combined index on the current 2012 base.
_GENERAL_PARAMS = {
    'base_year': '2012',
    'series': 'Current',
    'state_code': '99',   # All India
    'sector_code': '3',   # Combined (1 Rural, 2 Urban, 3 Combined)
    'group_code': '0',    # General
    'Format': 'JSON',
}


def get_general_cpi(session=None) -> pd.Series:
    """Return the India General CPI (Combined) index level as a monthly Series.

    The index is a first-of-month ``DatetimeIndex`` named ``date`` sorted
    ascending, with the CPI level as float. Only General rows are kept. Costs one
    request per page until an empty page is returned. Returns an empty Series when
    the API has no data.
    """
    if session is None:
        session = _http.legacy_tls_session()
    info_logger.info('Loading India General CPI via MOSPI getCPIIndex API')
    # Tripwire (#50): once MOSPI populates base 2024, new months move there
    # (under division/class params, not group_code) and the 2012 series stops —
    # fail loudly so the base splice gets implemented. Minimal probe: 2012-style
    # group/sector codes are invalid for base 2024, so they are left out.
    probe_params = {'base_year': '2024', 'series': 'Current', 'Format': 'JSON',
                    'limit': '1', 'page': '1'}
    probe = session.get(CPI_INDEX_URL, params=probe_params, timeout=API_TIMEOUT)
    probe.raise_for_status()
    if probe.json().get('data'):
        raise RuntimeError(
            'MOSPI base-2024 CPI is now populated - the 2012-base series will '
            'stop updating; implement the base splice (okama-API#50)'
        )
    records: list[dict] = []
    page = 1
    while True:
        params = {**_GENERAL_PARAMS, 'limit': str(_PAGE_SIZE), 'page': str(page)}
        response = session.get(CPI_INDEX_URL, params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json().get('data') or []
        if not data:
            break
        records.extend(data)
        page += 1

    records = [r for r in records if r.get('group') == 'General']
    if not records:
        return pd.Series(dtype='float64', name='INR.INFL')
    df = pd.DataFrame(records)
    df['date'] = pd.to_datetime(
        df['year'].astype(int).astype(str) + '-' + df['month'],
        format='%Y-%B',
    )
    s = df.set_index('date')['index'].astype(float)
    s.sort_index(inplace=True)
    s.name = 'INR.INFL'
    lag_days = (pd.Timestamp.today().normalize() - s.index[-1]).days
    if lag_days > _STALE_DAYS:
        raise RuntimeError(
            f'MOSPI CPI series is stale: last month {s.index[-1].date()} is '
            f'{lag_days} days old (limit {_STALE_DAYS}) - see okama-API#50'
        )
    return s
