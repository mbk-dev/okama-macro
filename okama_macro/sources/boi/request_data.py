"""Fetch Bank-of-Israel SDMX data through the shared _http layer.

boi's own retry adapter was dead code (mounted on http:// while the request is
https:// via the module-level requests.get), so the swap onto _http actually
gives this source working retry/back-off for the first time. The read_xml
parsing is unchanged (it runs on prod pandas 3.x today).
"""

import urllib.parse
from datetime import date
from io import StringIO

import pandas as pd

from okama_macro import _http
from okama_macro.sources.boi.settings import format_long, format_short

today = date.today()

BASE_URL = 'https://edge.boi.gov.il/FusionEdgeServer/sdmx/v2/data/dataflow/BOI.STATISTICS/PRI/1.0/'


def get_data(url: str = BASE_URL,
             series_code: str = 'RIB_BOI.D',
             date_start: str = '1900-1-1',
             date_end: str = today.strftime(format_long),
             freq: str = 'D') -> pd.Series:
    request_url = url + series_code
    date_parameter = urllib.parse.unquote('c%5BTIME_PERIOD%5D')
    params = {date_parameter: f'ge:{date_start}+le:{date_end}'}
    response = _http.get(request_url, params=params, label=f'boi {series_code}')
    resp = response.text

    df = pd.read_xml(StringIO(resp), xpath='//Obs')
    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
    if freq != 'Q':
        try:
            df['date'] = pd.to_datetime(df['date'], format=format_short)
        except ValueError:
            df['date'] = pd.to_datetime(df['date'], format=format_long)
            df.drop(columns=['RELEASE_STATUS'], inplace=True)
        df.set_index('date', inplace=True)
        df.index = df.index.to_period(freq=freq)
    else:
        df.set_index('date', inplace=True)
        df.sort_index(ascending=True, inplace=True)
    return df.squeeze()
