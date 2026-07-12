"""Tests for the C&SD (Hong Kong) CPI data source client
(okama_macro/sources/censtatd.py)."""

import pandas as pd

from okama_macro import _http
from okama_macro.sources import censtatd


# CCYY,MM,obs_value,sd_value — leading months carry sd_value 9 (= not available)
# and obs_value 0, and must be dropped; real data starts 1980-10.
SAMPLE_CSV = (
    "CCYY,MM,obs_value,sd_value\n"
    "1974,10,0.0000000000,9\n"
    "1974,11,0.0000000000,9\n"
    "1980,10,19.4000000000,\n"
    "2025,,108.9000000000,\n"  # annual-average row (MM blank) — must be dropped
    "2026,4,110.4000000000,\n"
    "2026,5,110.5000000000,\n"
)


class FakeResponse:
    def __init__(self, text: str):
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:
        pass


def test_get_composite_cpi_parses_and_drops_unavailable(monkeypatch):
    captured = {}

    def fake_get(url, *args, **kwargs):
        captured["url"] = url
        return FakeResponse(SAMPLE_CSV)

    monkeypatch.setattr(_http.requests, "get", fake_get)

    s = censtatd.get_composite_cpi()

    # It hits the Composite CPI (CC) index-level CSV.
    assert "MDT_54_510-60001_CC_" in captured["url"]
    assert "idx" in captured["url"]
    # The three unavailable leading rows (obs_value 0 / sd_value 9) are dropped.
    assert len(s) == 3
    # Monthly first-of-month DatetimeIndex, ascending, index level as float.
    assert s.index[0] == pd.Timestamp("1980-10-01")
    assert s.index[-1] == pd.Timestamp("2026-05-01")
    assert s.iloc[0] == 19.4
    assert s.iloc[-1] == 110.5
