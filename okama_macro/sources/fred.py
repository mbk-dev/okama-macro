"""FRED (Federal Reserve Economic Data) time series client.

Uses the official FRED API (https://fred.stlouisfed.org/docs/api/fred/).
Requires the FRED_API_KEY environment variable; the key is a free
32-character string issued at https://fredaccount.stlouisfed.org/apikeys.
"""

import datetime
import logging
import os

import pandas as pd

from okama_macro import _http

info_logger = logging.getLogger('okama_macro.fred')

FRED_API_URL = 'https://api.stlouisfed.org/fred/series/observations'
API_TIMEOUT = 60  # seconds
_MAX_ATTEMPTS = 3  # total tries on a transient 5xx before giving up


def get_series(
        series_id: str,
        first_date: datetime.datetime | None = None,
        last_date: datetime.datetime | None = None,
) -> pd.DataFrame:
    """
    Load a FRED series as a one-column DataFrame.

    The frame shape: a DatetimeIndex named 'DATE' and a single float column
    named after the series id.
    """
    api_key = os.getenv('FRED_API_KEY')
    if not api_key:
        raise RuntimeError(
            'FRED_API_KEY environment variable is not set (required for the FRED API)'
        )
    info_logger.info(f'Loading {series_id} via FRED API')
    params = {
        'series_id': series_id,
        'api_key': api_key,
        'file_type': 'json',
    }
    if first_date:
        params['observation_start'] = first_date.strftime('%Y-%m-%d')
    if last_date:
        params['observation_end'] = last_date.strftime('%Y-%m-%d')
    response = _http.get(
        FRED_API_URL, params=params, timeout=API_TIMEOUT,
        max_attempts=_MAX_ATTEMPTS, redact=(api_key,),
        label=f'FRED API request for {series_id}',
    )
    payload = response.json()
    observations = payload['observations']
    if payload['count'] > len(observations):
        raise RuntimeError(
            f'FRED API returned {len(observations)} of {payload["count"]} observations'
            f' for {series_id}: pagination required'
        )
    records = [
        (obs['date'], float(obs['value']))
        for obs in observations
        if obs['value'] != '.'  # '.' marks missing values
    ]
    df = pd.DataFrame(records, columns=['DATE', series_id])
    df['DATE'] = pd.to_datetime(df['DATE'])
    return df.set_index('DATE')
