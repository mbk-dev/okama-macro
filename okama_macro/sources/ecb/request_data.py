"""Fetch ECB Statistical Data Warehouse series through the shared _http layer.

The ECB data-api is served the shared browser UA; _http adds retry/back-off and
fails loud on 4xx/5xx (the old code never called raise_for_status, so an error
page fell through to a cryptic read_csv failure).
"""

from io import StringIO

import pandas as pd

from okama_macro import _http

URL_BASE = 'https://data-api.ecb.europa.eu/service/data/'
URL_END = '/'


def get_data_frame(
    agency: str = 'FM',
    code: str = 'D.U2.EUR.4F.KR.MRR_FR.LEV',
    freq: str = 'D',
    detail: str = 'dataonly',
    format: str = 'csvdata',
    start_period: str = '1900-01-01',
    end_period: str | None = None,
) -> pd.Series:
    request_url = URL_BASE + agency + URL_END + code
    params = {
        'detail': detail,
        'format': format,
        'startPeriod': start_period,
        'endPeriod': end_period,
    }
    response = _http.get(request_url, params=params, label=f'ecb {code}')
    df = pd.read_csv(
        StringIO(response.text),
        usecols=['TIME_PERIOD', 'OBS_VALUE'],
        dtype={'OBS_VALUE': float},
        parse_dates=['TIME_PERIOD'],
    )
    df = df.rename(columns={df.columns[0]: 'date'})
    df = df.set_index('date')
    df.index = df.index.to_period(freq=freq)
    return df.squeeze()
