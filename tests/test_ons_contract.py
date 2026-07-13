"""Contract tests for the folded ons consumed path (GBP.INFL / CPIH).

Locks: get_inflation_cpih returns m/m FRACTIONS (pct_change of the CPIH index)
on a monthly first-of-month DatetimeIndex, ascending. The _http.get seam is
mocked; no network.
"""

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from okama_macro.sources.ons import infl, request_data

_L522 = json.dumps({
    "months": [
        {"date": "2023 Nov", "value": "131.0"},
        {"date": "2023 Dec", "value": "131.5"},
        {"date": "2024 Jan", "value": "131.9"},
    ]
})


@pytest.fixture
def _mock_http(monkeypatch):
    def fake_get(url, *, params=None, headers=None, **kwargs):
        return SimpleNamespace(text=_L522)
    monkeypatch.setattr(request_data._http, 'get', fake_get)


def test_get_inflation_cpih_returns_mom_fractions(_mock_http):
    s = infl.get_inflation_cpih()
    # (131.5-131.0)/131.0 = 0.0038 fraction, not an index level.
    assert (s.abs() < 1).all()
    assert s.iloc[0] == pytest.approx(0.0038, abs=1e-4)


def test_get_inflation_cpih_index_is_first_of_month_ascending(_mock_http):
    s = infl.get_inflation_cpih()
    assert isinstance(s.index, pd.DatetimeIndex)
    assert s.index.is_monotonic_increasing
    assert s.index[0] == pd.Timestamp('2023-12-01')  # first pct_change month


def test_get_cpih_parses_index_levels(_mock_http):
    s = infl.get_cpih()
    assert s.iloc[0] == pytest.approx(131.0)   # index level, ascending
    assert s.index[0] == pd.Timestamp('2023-11-01')
