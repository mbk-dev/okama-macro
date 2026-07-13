"""Contract tests for the folded cfets consumed path (China LPR).

Locks the parse + HTTP contract per the boe#6 template: get_lpr_1y/5y return
m/m-cadence LPR FRACTIONS (÷100 already applied), observations only (no padding
injected), and — critically — the fetch preserves cfets's original spoofed
Chrome User-Agent when routed through the shared _http (the generic okama UA is
NOT sent on faith to chinamoney.com.cn). The network seam (_http.get) is mocked.
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from okama_macro.sources.cfets import lpr, request_data

# Two announcement rows; columns 0,6,7 are date, lpr1y, lpr5y (percent, as the
# chinamoney CSV publishes them — no header row). Newest first is how the site
# returns it; prepare_data must not depend on input order.
_RAW_CSV = (
    "2024-10-21,x,x,x,x,x,3.10,3.60\n"
    "2024-09-20,x,x,x,x,x,3.35,3.85\n"
)


@pytest.fixture
def _mock_http(monkeypatch):
    """Capture the headers _http.get is called with; return the fake CSV."""
    import json
    captured = {}

    def fake_get(url, *, params=None, headers=None, **kwargs):
        captured['url'] = url
        captured['headers'] = headers
        captured['params'] = params
        return SimpleNamespace(text=json.dumps({"data": {"csv": _RAW_CSV}}))

    monkeypatch.setattr(request_data._http, 'get', fake_get)
    return captured


def test_get_lpr_1y_returns_fractions_not_percent(_mock_http):
    s = lpr.get_lpr_1y(start_date=pd.Timestamp(2013, 10, 1))
    # 3.10% -> 0.0310, never the 3.10 percent value.
    assert (s.abs() < 1).all()
    assert 0.0310 in set(s.round(4).tolist())


def test_get_lpr_5y_returns_fractions(_mock_http):
    s = lpr.get_lpr_5y(start_date=pd.Timestamp(2013, 10, 1))
    assert (s.abs() < 1).all()
    assert 0.0360 in set(s.round(4).tolist())


def test_no_padding_only_observations(_mock_http):
    # Two announcement rows in, exactly two observations out — no daily fill.
    s = lpr.get_lpr_1y(start_date=pd.Timestamp(2013, 10, 1))
    assert len(s) == 2


def test_fetch_preserves_original_chrome_user_agent(_mock_http):
    lpr.get_lpr_1y(start_date=pd.Timestamp(2013, 10, 1))
    ua = _mock_http['headers']['user-agent']
    assert 'Chrome/89' in ua and 'Windows NT 10.0' in ua
