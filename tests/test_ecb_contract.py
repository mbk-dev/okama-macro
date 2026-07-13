"""Contract tests for the folded ecb consumed path (EU_MRO/MLR/DFR.RATE).

Locks: the three kr getters return rate FRACTIONS (÷100 applied), observations
only (no padding), on an ascending index. The _http.get seam is mocked; no
network.
"""

from types import SimpleNamespace

import pandas as pd
import pytest

from okama_macro.sources.ecb import kr, request_data

# ECB csvdata: at minimum TIME_PERIOD + OBS_VALUE columns (percent, as published).
_CSV = (
    "KEY,FREQ,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
    "x,D,2024-06-06,4.25,A\n"
    "x,D,2024-09-12,3.65,A\n"
)


@pytest.fixture
def _mock_http(monkeypatch):
    def fake_get(url, *, params=None, headers=None, **kwargs):
        return SimpleNamespace(text=_CSV)
    monkeypatch.setattr(request_data._http, 'get', fake_get)


def test_refinancing_rate_returns_fractions(_mock_http):
    s = kr.get_refinancing_rate(start_date=pd.Timestamp(1900, 1, 1))
    # 4.25% -> 0.0425, never the 4.25 percent value.
    assert (s.abs() < 1).all()
    assert 0.0425 in set(s.round(4).tolist())


def test_deposit_rate_returns_fractions(_mock_http):
    s = kr.get_deposit_rate(start_date=pd.Timestamp(1900, 1, 1))
    assert (s.abs() < 1).all()


def test_marginal_rate_no_padding_only_observations(_mock_http):
    s = kr.get_marginal_rate(start_date=pd.Timestamp(1900, 1, 1))
    assert len(s) == 2   # two obs in, two out — no daily fill
