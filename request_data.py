"""National Bureau of Statistics of China."""
import json

import pandas as pd

from datetime import datetime
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

requests.packages.urllib3.disable_warnings()

BASE_URL_ENG = "http://data.stats.gov.cn/english/easyquery.htm"
BASE_URL_CN = "http://data.stats.gov.cn/easyquery.htm"
default_timeout = 10  # seconds


def load_nbs_web(series: str, periods: str, freq: str):
    """
    Fetch & parse from the China National Bureau of Statistics web data API.

    Dataset for the NBS *level*, *series* and *period*.

    Data are identified by three dimensions, all given as strings:
    - *level*: either 'national' or 'regional'. If 'regional', the dataset has
      a coord 'region' which is the integer GB/T 2260 code for the region.
    - *series*: the indicator requested, e.g. 'A090302'.
    - *periods* a list of periods with one or more entries, in the forms
      indicated by the web interface, e.g.:
      - '1995': the single year 1995
      - '2003,2012': the years 2003 and 2012
      - '2020-2022': from 2020 to 2022 (full years)
      - 'LATEST10': the most recent 10 periods for which data is available
      - 'LAST5': any data available for the most recent 5 periods
    - *freq*: 'month' or 'year'
    """
    # Example query string (decoded):
    """
    http://data.stats.gov.cn/english/easyquery.htm?m=QueryData
      &dbcode=hgyd  # regional: fsnd / national: hgyd (monthly), hgnd (annual)
      &rowcode=zb  # regional: reg / national: zb
      &colcode=sj
      &wds=[{"wdcode":"zb","valuecode":"A090201"}]
      &dfwds=[{"wdcode":"sj","valuecode":"1995-2014"}]
      &k1=1472740901192
    """

    # Parameters for constructing the query string
    params = {
        # Method of easyquery.htm to call
        "m": "QueryData",
        # Periods are always one dimension of the returned data
        "colcode": "sj",
        # Timestamp
        "k1": int(datetime.now().timestamp() * 1000),
    }

    # Wrap series and periods in the form expected by the query string
    _series = {"wdcode": "zb", "valuecode": series}
    _periods = {"wdcode": "sj", "valuecode": periods}

    params["dbcode"] = "hgyd" if freq == "month" else "hgnd"
    params["rowcode"] = "zb"
    # Two dimensional data: leave this blank
    wds = []
    # Select both series and periods
    dfwds = [_series, _periods]

    # Convert the wds and dfwds parameters to stringified JSON
    seps = (",", ":")
    params["wds"] = json.dumps(wds, separators=seps)
    params["dfwds"] = json.dumps(dfwds, separators=seps)

    # Prepare the HTTP request
    session = requests.session()
    retry_strategy = Retry(
        total=3, backoff_factor=0.1, status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
  #  session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        r = session.get(
            BASE_URL_ENG, params=params, verify=False, timeout=default_timeout
        )
        r.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise requests.exceptions.HTTPError(
            f"HTTP error fetching data for {series}:",
            r.status_code,
            r.reason,
            BASE_URL_ENG,
        ) from err
    response = r.json()
    if response["returncode"] == 501:
        raise requests.exceptions.HTTPError(
            f"{series} is not found in the database.", 501
        )

    return get_monthly_series(response, freq)


def get_monthly_series(json_data: list, freq: str = "month") -> pd.Series:
    data_format = "%Y%m" if freq == "month" else "%Y"
    data = json_data["returndata"]["datanodes"]
    s = pd.Series(dtype="float")
    for row in data:
        value = row["data"]["data"]
        date = pd.to_datetime(row["wds"][1]["valuecode"], format=data_format)
        s[date] = value
    return s
