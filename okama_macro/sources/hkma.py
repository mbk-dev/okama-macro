"""Hong Kong Monetary Authority (HKMA) base-rate client.

Fetches the Discount Window Base Rate — the HKMA's official policy rate — as a
daily series from the HKMA open API (no key required):

    https://api.hkma.gov.hk/public/market-data-and-statistics/
        daily-monetary-statistics/daily-figures-interbank-liquidity

The ``disc_win_base_rate`` field runs daily from 2002-01-02. HKMA's ALB returns
502 for the ``choose`` / ``from`` / ``to`` / ``offset`` query parameters, so the
only reliable call is a single ``pagesize`` + ``sortby`` request; the full daily
history (~6.3k rows) comes back in one ~9 MB response. Date filtering is therefore
done client-side, and transient 502s are retried.
"""

import logging
import time

import pandas as pd

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.hkma')

BASE_URL = (
    'https://api.hkma.gov.hk/public/market-data-and-statistics/'
    'daily-monetary-statistics/daily-figures-interbank-liquidity'
)
_FIELD = 'disc_win_base_rate'
_MAX_PAGESIZE = 8000  # covers the full 2002-> daily history in one request
API_TIMEOUT = 120  # seconds — the full-history payload is large
_MAX_ATTEMPTS = 4  # HKMA's ALB 502s intermittently; retry transient failures
_RETRY_BACKOFF_SECONDS = 2.0


def _get_records(pagesize: int) -> list[dict]:
    """One HKMA request (latest ``pagesize`` daily rows), retried on failure.

    Transient 5xx retries happen inside ``_http.get``; this outer loop retries
    payload-level surprises (malformed JSON, ``success: false`` headers).
    """
    params = {'pagesize': pagesize, 'sortby': 'end_of_date', 'sortorder': 'desc'}
    for attempt in range(_MAX_ATTEMPTS):
        try:
            response = _http.get(BASE_URL, params=params, timeout=API_TIMEOUT,
                                 max_attempts=_MAX_ATTEMPTS,
                                 backoff=_RETRY_BACKOFF_SECONDS,
                                 label='HKMA API request')
            payload = response.json()
            if not payload['header']['success']:
                raise RuntimeError(f'HKMA API error: {payload["header"]["err_msg"]}')
            return payload['result']['records']
        except (ValueError, KeyError, RuntimeError) as error:
            if attempt < _MAX_ATTEMPTS - 1:
                info_logger.warning(
                    f'HKMA API attempt {attempt + 1}/{_MAX_ATTEMPTS} failed '
                    f'({type(error).__name__}); retrying'
                )
                time.sleep(_RETRY_BACKOFF_SECONDS * (attempt + 1))
                continue
            raise RuntimeError(f'HKMA API request failed: {error}') from None
    return []  # unreachable; the final attempt raises


def get_base_rate(
        first_date: pd.Timestamp | None = None,
        last_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return the HKMA Discount Window Base Rate as a daily one-column DataFrame.

    Index: a ``DatetimeIndex`` named ``DATE`` (ascending). Column:
    ``disc_win_base_rate`` (percent). ``first_date`` / ``last_date`` are applied
    client-side. Only enough of the latest history is requested to cover
    ``first_date`` (the whole series for a full backfill).
    """
    if first_date is not None:
        span_days = (pd.Timestamp.today() - pd.Timestamp(first_date)).days
        pagesize = min(max(int(span_days * 5 / 7) + 30, 30), _MAX_PAGESIZE)
    else:
        pagesize = _MAX_PAGESIZE
    info_logger.info(f'Loading HKMA base rate (pagesize={pagesize})')
    records = _get_records(pagesize)
    rows = [(r['end_of_date'], r[_FIELD]) for r in records if r.get(_FIELD) is not None]
    df = pd.DataFrame(rows, columns=['DATE', _FIELD])
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.set_index('DATE').sort_index()
    if first_date is not None:
        df = df[df.index >= pd.Timestamp(first_date)]
    if last_date is not None:
        df = df[df.index <= pd.Timestamp(last_date)]
    return df
