"""Fetch the Bank of England Bank-Rate table through the shared _http layer.

bankofengland.co.uk is served boe's original spoofed Chrome User-Agent (the
generic UA is unverified against it); _http merges the caller header (caller
wins), so the exact old UA is preserved across the swap, with retry/back-off
gained. The sort-before-pad / pad-from-previous / slice-after-pad logic below is
the boe#6 look-ahead fix and is left byte-identical.
"""

from io import StringIO

import pandas as pd

from okama_macro import _http

URL_BASE = 'https://www.bankofengland.co.uk/boeapps/database/Bank-Rate.asp#'

# The exact User-Agent standalone boe sent; the BoE site needs a browser UA, so
# it is preserved verbatim across the _http swap.
_CHROME_UA = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36'
)


def get_data_frame(
    freq: str = 'D',
    start_period: str = '1900-01-01',
    end_period: str | None = None,
) -> pd.Series:
    response = _http.get(URL_BASE, headers={'User-Agent': _CHROME_UA}, label='boe Bank-Rate')
    df = pd.read_html(StringIO(response.text))
    df = df[0]

    df.rename(columns={df.columns[0]: 'date'}, inplace=True)
    df['date'] = pd.to_datetime(df['date'], format='%d %b %y')
    df.set_index('date', inplace=True)
    # The Bank-Rate table is served newest-first. Sort ascending BEFORE slicing
    # and padding (boe#6 look-ahead fix): on a descending index reindex(pad)
    # fills each day from the NEXT (future) rate change instead of the previous.
    df.sort_index(inplace=True)
    df.index = df.index.to_period(freq=freq)
    # Pad over the FULL change-dates table first, then slice: slicing raw change
    # dates by start_period would drop the change still in effect at start_period.
    today = pd.Timestamp.today().to_period(freq)
    idx = pd.period_range(start=df.index[0], end=max(df.index[-1], today), freq=freq)
    df = df.reindex(idx, method='pad')
    df = df.loc[pd.Period(start_period, freq=freq):]
    if end_period is not None:
        df = df.loc[:pd.Period(end_period, freq=freq)]
    return df.squeeze(axis=1)
