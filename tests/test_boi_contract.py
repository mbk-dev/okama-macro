"""Contract tests for the folded boi consumed path (ILS.INFL, ISR_IR.RATE).

Locks: get_inflation returns m/m FRACTIONS on a monthly index; get_ir returns
rate FRACTIONS (÷100) observations-only on a daily index; and the SDMX fetch
forwards date_start as a STRING into the ge:<date> query (a Timestamp would
leak 'ge:2020-01-01 00:00:00' and return empty — mock-invisible otherwise).
The _http.get seam is mocked; no network.
"""

from types import SimpleNamespace

import pytest

from okama_macro.sources.boi import infl, kr, request_data

# Minimal SDMX-style payload: two monthly CPI obs (index levels, 2020=100 base).
# Include dummy metadata columns to prevent squeeze() from converting to Series.
_CPI_XML = (
    '<Obs><TIME_PERIOD>2024-01</TIME_PERIOD><OBS_VALUE>100.0</OBS_VALUE><DUMMY>X</DUMMY></Obs>'
    '<Obs><TIME_PERIOD>2024-02</TIME_PERIOD><OBS_VALUE>100.5</OBS_VALUE><DUMMY>X</DUMMY></Obs>'
)
# Daily rate data needs RELEASE_STATUS column (dropped in format_long path).
_RATE_XML = (
    '<Obs><TIME_PERIOD>2024-01-01</TIME_PERIOD><OBS_VALUE>4.5</OBS_VALUE><RELEASE_STATUS>F</RELEASE_STATUS></Obs>'
    '<Obs><TIME_PERIOD>2024-01-02</TIME_PERIOD><OBS_VALUE>4.5</OBS_VALUE><RELEASE_STATUS>F</RELEASE_STATUS></Obs>'
)


def test_get_inflation_returns_mom_fractions(monkeypatch):
    captured = {}

    def fake_get(url, *, params=None, headers=None, **kwargs):
        captured['url'] = url
        captured['params'] = params
        return SimpleNamespace(text=f'<root>{_CPI_XML}</root>')

    monkeypatch.setattr(request_data._http, 'get', fake_get)
    s = infl.get_inflation(date_start='2024-01-01')
    # (100.5-100)/100 = 0.005 fraction, not an index level.
    assert (s.abs() < 1).all()
    assert s.iloc[-1] == pytest.approx(0.005, abs=1e-4)


def test_get_ir_returns_fractions_observations_only(monkeypatch):
    def fake_get(url, *, params=None, headers=None, **kwargs):
        return SimpleNamespace(text=f'<root>{_RATE_XML}</root>')

    monkeypatch.setattr(request_data._http, 'get', fake_get)
    s = kr.get_ir(date_start='2024-01-01')
    assert (s.abs() < 1).all()          # 4.5% -> 0.045
    assert s.iloc[0] == pytest.approx(0.045)
    assert len(s) == 2                  # two obs in, two out — no padding


def test_date_start_forwarded_as_string_not_timestamp(monkeypatch):
    captured = {}

    def fake_get(url, *, params=None, headers=None, **kwargs):
        captured['params'] = params
        return SimpleNamespace(text=f'<root>{_RATE_XML}</root>')

    monkeypatch.setattr(request_data._http, 'get', fake_get)
    kr.get_ir(date_start='2020-01-01')
    # The SDMX time filter must contain the plain date string, never a
    # '2020-01-01 00:00:00' Timestamp repr.
    time_param = next(iter(captured['params'].values()))
    assert 'ge:2020-01-01' in time_param
    assert '00:00:00' not in time_param
