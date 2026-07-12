"""Tests for the RBI current-rates crawler (okama_macro/sources/rbi.py)."""

import pytest

from okama_macro import _http
from okama_macro.sources import rbi


# Mirrors the CURRENT RATES block served on https://www.rbi.org.in/ (server-side
# HTML; th label + td ": value%" pairs, with &nbsp; and newlines sprinkled in).
SAMPLE_HTML = """
<html><body>
<!--  CURRENT RATES START-->
<table>
  <tr><th>Policy&nbsp;Repo Rate</th><td>: 5.25%</td></tr>
  <tr><th>Standing Deposit Facility Rate</th><td>: 5.00%</td></tr>
  <tr><th>Marginal Standing Facility Rate</th><td>: 5.50%</td></tr>
</table>
<!--  CURRENT RATES END-->
</body></html>
"""


class FakeResponse:
    def __init__(self, text):
        self.text = text
        self.status_code = 200

    def raise_for_status(self):
        pass


def test_get_current_repo_rate_parses_value(monkeypatch):
    captured = {}

    def fake_get(url, headers=None, timeout=None, **kwargs):
        captured["url"] = url
        return FakeResponse(SAMPLE_HTML)

    monkeypatch.setattr(_http.requests, "get", fake_get)

    rate = rbi.get_current_repo_rate()

    assert captured["url"].startswith("https://www.rbi.org.in")
    assert rate == 5.25


def test_get_current_repo_rate_raises_when_block_missing(monkeypatch):
    monkeypatch.setattr(
        _http.requests, "get",
        lambda *a, **k: FakeResponse("<html><body>redesigned</body></html>"),
    )

    with pytest.raises(ValueError, match="Policy Repo Rate"):
        rbi.get_current_repo_rate()
