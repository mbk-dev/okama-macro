"""Tests for the HKMA (Hong Kong Monetary Authority) base-rate client
(okama_macro/sources/hkma.py)."""

import pandas as pd

from okama_macro import _http
from okama_macro.sources import hkma


def _payload(records, ok=True):
    return {
        "header": {"success": ok, "err_code": "0000" if ok else "1002",
                   "err_msg": "" if ok else "bad"},
        "result": {"datasize": len(records), "records": records},
    }


RECORDS = [  # HKMA returns latest-first when sortorder=desc
    {"end_of_date": "2026-07-10", "disc_win_base_rate": 4},
    {"end_of_date": "2026-07-09", "disc_win_base_rate": 4},
    {"end_of_date": "2026-07-08", "disc_win_base_rate": None},  # missing -> dropped
    {"end_of_date": "2002-01-02", "disc_win_base_rate": 3.25},
]


class FakeResponse:
    def __init__(self, payload=None, *, status_code=200, text="{}"):
        self._payload = payload
        self.status_code = status_code
        self.text = text

    def raise_for_status(self):
        if self.status_code >= 400:
            raise _http.requests.HTTPError(f"{self.status_code}", response=self)

    def json(self):
        return self._payload


def test_get_base_rate_parses_sorts_and_drops_missing(monkeypatch):
    captured = {}

    def fake_get(url, params=None, timeout=None, headers=None, **kwargs):
        captured["params"] = params
        return FakeResponse(_payload(RECORDS))

    monkeypatch.setattr(_http.requests, "get", fake_get)

    df = hkma.get_base_rate()

    # Reads the disc_win_base_rate field, drops the None row, sorts ascending.
    assert list(df.columns) == ["disc_win_base_rate"]
    assert df.index[0] == pd.Timestamp("2002-01-02")
    assert df.index[-1] == pd.Timestamp("2026-07-10")
    assert df["disc_win_base_rate"].iloc[-1] == 4
    assert len(df) == 3  # the None row is dropped


def test_get_base_rate_filters_by_first_date(monkeypatch):
    monkeypatch.setattr(_http.requests, "get",
                        lambda *a, **k: FakeResponse(_payload(RECORDS)))

    df = hkma.get_base_rate(first_date=pd.Timestamp("2026-01-01"))

    # The 2002 row is filtered out client-side (HKMA's from/to filter 502s).
    assert df.index.min() >= pd.Timestamp("2026-01-01")
    assert len(df) == 2


def test_get_base_rate_retries_on_502(monkeypatch):
    calls = {"n": 0}

    def flaky_get(url, params=None, timeout=None, headers=None, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            # HKMA's ALB returns a 502 HTML page intermittently.
            return FakeResponse(status_code=502, text="<html>502</html>")
        return FakeResponse(_payload(RECORDS))

    monkeypatch.setattr(_http.requests, "get", flaky_get)
    monkeypatch.setattr(_http.time, "sleep", lambda *a: None)

    df = hkma.get_base_rate()

    assert calls["n"] == 2  # retried once, then succeeded
    assert not df.empty
