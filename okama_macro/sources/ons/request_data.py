"""Fetch ONS data through the shared _http layer.

ons's own retry adapter was dead code (mounted on http:// while the API is
https://), so the swap onto _http gives this source working retry/back-off.
"""

import json

from okama_macro import _http

URL_BASE = 'https://api.beta.ons.gov.uk/v1/datasets/'
URL_TIMESERIES = 'https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/'


def get_data(key: str):
    request_url = URL_BASE + key
    d = _connect_to_uk_api(request_url)
    url_ts = d['links']['latest_version']['href']
    csv_link = _connect_to_uk_api(url_ts)['downloads']['csv']['href']
    return _connect_to_uk_api(csv_link, request_type='csv')


def get_timeseries(cdid: str, dataset: str = 'mm23') -> dict:
    url = f'{URL_TIMESERIES}{cdid}/{dataset}/data'
    return _connect_to_uk_api(url)


def _connect_to_uk_api(url: str, request_type: str = 'json') -> dict | str:
    response = _http.get(url, label='ons')
    if request_type == 'json':
        return json.loads(response.text)
    return response.text
