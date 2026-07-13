"""Contract tests for the folded boe consumed path (UK_BR.RATE).

Ported from mbk-dev/boe tests/test_request_data.py (the boe#6 look-ahead fix
template). The BoE Bank-Rate table is served newest-first; padding must fill each
day from the PREVIOUS change (forward-fill), not the next (the look-ahead bug).
Also locks that the fetch preserves boe's spoofed Chrome UA through _http.
"""

import pandas as pd
import pytest

from okama_macro.sources.boe import kr, request_data

SAMPLE_HTML = """
<table>
  <thead><tr><th>Date Changed</th><th>Rate</th></tr></thead>
  <tbody>
    <tr><td>16 Dec 21</td><td>0.25</td></tr>
    <tr><td>19 Mar 20</td><td>0.10</td></tr>
    <tr><td>05 Mar 09</td><td>0.50</td></tr>
  </tbody>
</table>
"""


class FakeResponse:
    text = SAMPLE_HTML
    status_code = 200


@pytest.fixture()
def fake_page(monkeypatch):
    captured = {}

    def fake_get(url, *, params=None, headers=None, **kwargs):
        captured['headers'] = headers
        return FakeResponse()

    monkeypatch.setattr(request_data._http, 'get', fake_get)
    return captured


def test_pads_forward_from_previous_change(fake_page):
    s = request_data.get_data_frame()
    assert s.index[0] == pd.Period("2009-03-05", freq="D")
    assert s.index[-1] == pd.Timestamp.today().to_period("D")
    assert s[pd.Period("2012-06-01", freq="D")] == 0.50
    assert s[pd.Period("2020-03-18", freq="D")] == 0.50
    assert s[pd.Period("2020-06-01", freq="D")] == 0.10
    assert s[pd.Period("2021-12-16", freq="D")] == 0.25
    assert s.iloc[-1] == 0.25


def test_recent_start_period_returns_the_standing_rate(fake_page):
    start = (pd.Timestamp.today() - pd.DateOffset(months=2)).strftime("%Y-%m-%d")
    s = request_data.get_data_frame(start_period=start)
    assert len(s) > 0
    assert s.index[0] == pd.Period(start, freq="D")
    assert (s == 0.25).all()


def test_start_period_keeps_the_rate_in_effect(fake_page):
    s = request_data.get_data_frame(start_period="2020-01-01")
    assert s.index[0] == pd.Period("2020-01-01", freq="D")
    assert s[pd.Period("2020-01-01", freq="D")] == 0.50
    assert s[pd.Period("2020-06-01", freq="D")] == 0.10


def test_get_bank_rate_returns_fractions(fake_page):
    s = kr.get_bank_rate()
    assert s.name == "bank_rate"
    assert s[pd.Period("2012-06-01", freq="D")] == pytest.approx(0.0050)


def test_fetch_preserves_chrome_user_agent(fake_page):
    request_data.get_data_frame()
    ua = fake_page['headers']['User-Agent']
    assert 'Chrome/54' in ua and 'X11; Linux' in ua
