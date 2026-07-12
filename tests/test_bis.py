"""Tests for the BIS central-bank policy-rate client
(okama_macro/sources/bis.py, served via the DBnomics REST API)."""

import pandas as pd

from okama_macro import _http
from okama_macro.sources import bis


def _payload(periods, values):
    return {"series": {"docs": [{
        "period": periods,
        "value": values,
        "series_name": "Central bank policy rates - India - Daily - End of period",
    }]}}


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200

    def json(self):
        return self._payload

    def raise_for_status(self):
        pass


def test_get_policy_rate_parses_and_drops_missing(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None, headers=None, proxies=None, **kwargs):
        captured["url"] = url
        captured["params"] = params
        return FakeResponse(_payload(
            ["1946-01-01", "2025-07-03", "2025-07-04", "2025-07-07"],
            [3.0, None, "NA", 5.5],   # DBnomics marks gaps as null or "NA" -> dropped
        ))

    monkeypatch.setattr(_http.requests, "get", fake_get)

    df = bis.get_policy_rate("IN")

    # Hits the daily BIS policy-rate series for India with observations on.
    assert "BIS/WS_CBPOL/D.IN" in captured["url"]
    assert captured["params"]["observations"] == "1"
    # Daily DatetimeIndex ascending, percent floats, the None row dropped.
    assert list(df.columns) == ["policy_rate"]
    assert len(df) == 2
    assert df.index[0] == pd.Timestamp("1946-01-01")
    assert df.index[-1] == pd.Timestamp("2025-07-07")
    assert df["policy_rate"].iloc[-1] == 5.5


def test_get_policy_rate_filters_by_first_date(monkeypatch):
    monkeypatch.setattr(
        _http.requests, "get",
        lambda *a, **k: FakeResponse(_payload(
            ["2020-01-01", "2025-07-07"], [4.0, 5.5],
        )),
    )

    df = bis.get_policy_rate("IN", first_date=pd.Timestamp("2024-01-01"))

    assert len(df) == 1
    assert df.index[0] == pd.Timestamp("2025-07-07")
