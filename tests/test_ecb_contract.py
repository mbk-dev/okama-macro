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


# --------------------------------------------------------------------------- #
# Variable-rate tender window (2000-06-28 … 2008-10-14): the ECB ran the main
# refinancing operations as variable-rate tenders, so MRR_FR has NO observations
# there and the policy rate is the minimum bid rate MRR_MBR (okama-API#53).
# --------------------------------------------------------------------------- #
_FR_CSV = (
    "KEY,FREQ,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
    "x,D,2000-06-27,4.25,A\n"       # last fixed-rate tender before the switch
    "x,D,2008-10-15,3.75,A\n"       # fixed-rate tender resumes
)
_MBR_CSV = (
    "KEY,FREQ,TIME_PERIOD,OBS_VALUE,OBS_STATUS\n"
    "x,D,2000-06-28,4.25,A\n"
    "x,D,2001-05-11,4.50,A\n"
    "x,D,2003-06-06,2.00,A\n"
    "x,D,2008-10-14,4.25,A\n"
)


@pytest.fixture
def _mock_http_by_code(monkeypatch):
    """Serve MRR_FR and MRR_MBR separately; record which codes were requested."""
    requested = []

    def fake_get(url, *, params=None, headers=None, **kwargs):
        requested.append(url)
        text = _MBR_CSV if 'MRR_MBR' in url else _FR_CSV
        return SimpleNamespace(text=text)

    monkeypatch.setattr(request_data._http, 'get', fake_get)
    return requested


def test_refinancing_rate_splices_the_minimum_bid_rate(_mock_http_by_code):
    s = kr.get_refinancing_rate(start_date=pd.Timestamp(1900, 1, 1))

    values = s.round(4).to_dict()
    assert values[pd.Period('2001-05-11', freq='D')] == 0.045   # from MRR_MBR
    assert values[pd.Period('2003-06-06', freq='D')] == 0.02    # from MRR_MBR
    assert values[pd.Period('2000-06-27', freq='D')] == 0.0425  # from MRR_FR
    assert values[pd.Period('2008-10-15', freq='D')] == 0.0375  # from MRR_FR
    assert s.index.is_monotonic_increasing
    assert s.index.is_unique


def test_refinancing_rate_skips_min_bid_request_after_the_window(_mock_http_by_code):
    """A refresh starts at the last stored date — do not fetch a dead series."""
    kr.get_refinancing_rate(start_date=pd.Timestamp(2020, 1, 1))

    assert not any('MRR_MBR' in url for url in _mock_http_by_code)


def test_min_bid_rate_is_available_on_its_own(_mock_http_by_code):
    s = kr.get_min_bid_rate(start_date=pd.Timestamp(1900, 1, 1))

    assert (s.abs() < 1).all()          # fractions, like every other rate getter
    assert len(s) == 4                  # observations only, no padding


def test_get_data_frame_survives_an_empty_body(monkeypatch):
    """ECB answers 200 with an EMPTY body outside a series' range (not a 404)."""
    monkeypatch.setattr(
        request_data._http, 'get',
        lambda url, **kwargs: SimpleNamespace(text=''),
    )

    s = request_data.get_data_frame('FM', 'D.U2.EUR.4F.KR.MRR_MBR.LEV', 'D',
                                    start_period='2026-01-01')

    assert isinstance(s, pd.Series)
    assert s.empty
