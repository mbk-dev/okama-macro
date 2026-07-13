"""Fetch the chinamoney.com.cn LPR CSV through the shared _http layer.

The site is served the source's original spoofed Chrome User-Agent — the
generic okama UA is unverified against it, so the caller header (which _http
merges over its default, caller winning) preserves the exact old string.
"""

import json

from okama_macro import _http

URL = 'https://www.chinamoney.com.cn/ags/ms/cm-u-bk-currency/'

# The exact User-Agent the standalone cfets sent; a picky site is the usual
# reason for a hand-crafted UA, so it is preserved verbatim across the _http swap.
_CHROME_UA = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/89.0.4389.72 Safari/537.36'
)


def get_data_frame(code: str = 'LprChrtCSV',
                   start_date: str = '2013-10-01',
                   end_date: str | None = None) -> str:
    """Return the raw LPR CSV string from chinamoney.com.cn for ``code``."""
    params = {'startDate': start_date, 'endDate': end_date}
    response = _http.get(
        URL + code,
        params=params,
        headers={'user-agent': _CHROME_UA},
        label='cfets LPR',
    )
    return json.loads(response.text)['data']['csv']
