"""Hong Kong Census & Statistics Department (C&SD) CPI client.

Fetches the Composite Consumer Price Index (all-items headline CPI for the whole
household sector) as a monthly index-level series. C&SD serves it as a plain CSV
on the open-data portal (data.gov.hk table 510-60001), so no API key or query
encoding is needed:

    https://www.censtatd.gov.hk/data/MDT_54_510-60001_CC_CM_1920_Raw_1dp_idx_n.csv

Columns: ``CCYY,MM,obs_value,sd_value``. ``obs_value`` is the index level on the
current 2019/10-2020/09 = 100 base; the earliest months (pre-1980-10) carry
``sd_value`` 9 (= not available) with a 0 level and are dropped. The series runs
from 1980-10 to the latest published month. Callers derive month-on-month
inflation by ``pct_change()`` on the index (base-invariant, so the base rebasings
C&SD applies over time do not affect the m/m fractions).
"""

import logging
from io import StringIO

import pandas as pd

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.censtatd')

# Composite CPI (CC), monthly, raw index level, 1 dp, not seasonally adjusted (n).
COMPOSITE_CPI_URL = (
    'https://www.censtatd.gov.hk/data/'
    'MDT_54_510-60001_CC_CM_1920_Raw_1dp_idx_n.csv'
)
API_TIMEOUT = 60  # seconds


def get_composite_cpi() -> pd.Series:
    """Return the HK Composite CPI index level as a monthly ``pd.Series``.

    The index is a first-of-month ``DatetimeIndex`` named ``date``; unavailable
    leading months (index level 0) are dropped and the series is sorted ascending.
    """
    info_logger.info('Loading HK Composite CPI via C&SD open-data CSV')
    response = _http.get(COMPOSITE_CPI_URL, timeout=API_TIMEOUT,
                         label='C&SD Composite CPI request')
    df = pd.read_csv(StringIO(response.text))
    # The CSV interleaves annual-average rows (MM blank) among the monthly rows;
    # keep only monthly rows with a published level (drop the not-yet-available
    # leading months whose level is 0).
    df = df[df['MM'].notna() & (df['obs_value'] > 0)]
    df['date'] = pd.to_datetime({
        'year': df['CCYY'].astype(int), 'month': df['MM'].astype(int), 'day': 1,
    })
    s = df.set_index('date')['obs_value'].astype(float)
    s.sort_index(inplace=True)
    s.name = 'HKD.INFL'
    return s
