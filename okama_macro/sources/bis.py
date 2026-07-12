"""BIS central-bank policy-rate client (served via the DBnomics REST API).

Fetches a country's policy rate from the BIS ``WS_CBPOL`` dataset (daily,
end-of-period) through DBnomics, which mirrors BIS reliably and needs no key:

    https://api.db.nomics.world/v22/series/BIS/WS_CBPOL/D.{code}?observations=1

For India (``IN``) this is the RBI policy repo rate from 1946. The same series
family backfilled Hong Kong's base rate (``M.HK``), so this client generalizes
that one-off into a reusable source.

**Publication lag:** BIS/DBnomics runs ~a year behind the actual policy rate
(e.g. last IN observation 2025-07 when the live rate had already been cut).
Callers that need a current value must combine this history with a same-day
source (see ``rates.get_ind_rbi_rate`` — rbi.org.in scrape tail).

Foreign-source proxying goes through the shared ``_http`` layer when ``PROXY_*``
env vars are set, else direct (e.g. tests).
"""

import logging

import pandas as pd

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.bis')

DBNOMICS_SERIES_URL = 'https://api.db.nomics.world/v22/series/BIS/WS_CBPOL/D.{code}'
API_TIMEOUT = 60  # seconds


def get_policy_rate(
        code: str = 'IN',
        first_date: pd.Timestamp | None = None,
        last_date: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Return a central bank's policy rate as a daily one-column DataFrame.

    Index: a ``DatetimeIndex`` (ascending). Column: ``policy_rate`` (percent).
    ``code`` is the BIS/ISO country code (``IN`` India). Unobserved days (null
    values) are dropped; ``first_date`` / ``last_date`` are applied client-side.
    """
    info_logger.info(f'Loading BIS policy rate for {code} via DBnomics')
    response = _http.get(
        DBNOMICS_SERIES_URL.format(code=code),
        params={'observations': '1'},
        timeout=API_TIMEOUT,
        use_proxy=True,
        label=f'BIS/DBnomics policy-rate request for {code}',
    )
    doc = response.json()['series']['docs'][0]
    df = pd.DataFrame({'DATE': doc['period'], 'policy_rate': doc['value']})
    # DBnomics marks unobserved days as null or the string "NA" -> both dropped.
    df['policy_rate'] = pd.to_numeric(df['policy_rate'], errors='coerce')
    df = df[df['policy_rate'].notna()]
    df['DATE'] = pd.to_datetime(df['DATE'])
    df = df.set_index('DATE').sort_index()
    if first_date is not None:
        df = df[df.index >= pd.Timestamp(first_date)]
    if last_date is not None:
        df = df[df.index <= pd.Timestamp(last_date)]
    return df
