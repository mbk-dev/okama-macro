"""Tests for the MOSPI (India) CPI data source client
(okama_macro/sources/mospi.py)."""

import pandas as pd
import pytest

from okama_macro.sources import mospi


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        pass


class FakeSession:
    """Returns queued pages in order and records the params of each call."""

    def __init__(self, pages: list[dict]):
        self._pages = list(pages)
        self.calls: list[dict] = []

    def get(self, url, params=None, timeout=None, **kwargs):
        self.calls.append(params or {})
        payload = self._pages.pop(0) if self._pages else {"data": []}
        return FakeResponse(payload)


def _row(year, month, group="General", index="100.0"):
    return {"baseyear": "2012", "year": year, "month": month, "state": "All India",
            "sector": "Combined", "group": group,
            "subgroup": f"{group}-Overall", "index": index,
            "inflation": None, "status": "F"}


# A fresh month within the staleness window (MOSPI publishes with a ~7-month lag).
_FRESH = (pd.Timestamp.today().normalize() - pd.DateOffset(months=7)).strftime("%B"), \
         (pd.Timestamp.today().normalize() - pd.DateOffset(months=7)).year


def _fresh_row():
    month_name, year = _FRESH
    return _row(year, month_name, index="198.0")


EMPTY_PAGE = {"data": [], "msg": "No Data Found", "statusCode": 200}
PAGE_1 = {
    "data": [
        _row(2013, "December", index="118.7"),
        _fresh_row(),
        _row(2025, "December", group="Housing", index="185.2"),
    ],
    "statusCode": 200,
}


def test_get_general_cpi_parses_paginates_and_filters():
    # Call order: base-2024 probe (empty = not yet populated), then 2012 pages.
    session = FakeSession([EMPTY_PAGE, PAGE_1, EMPTY_PAGE])

    s = mospi.get_general_cpi(session=session)

    # First call probes base 2024 (the #50 tripwire) with a minimal request.
    probe = session.calls[0]
    assert probe["base_year"] == "2024"
    assert probe["limit"] == "1"
    assert "group_code" not in probe  # 2012-style codes are invalid for base 2024
    # Then the General All-India Combined index on the current 2012 base.
    p = session.calls[1]
    assert p["base_year"] == "2012"
    assert p["series"] == "Current"
    assert p["state_code"] == "99"      # All India
    assert p["sector_code"] == "3"      # Combined
    assert p["group_code"] == "0"       # General
    assert p["Format"] == "JSON"
    # Paginated until an empty page came back.
    assert len(session.calls) == 3

    # Only the two General rows survive; Housing is dropped.
    assert len(s) == 2
    assert s.index[0] == pd.Timestamp("2013-12-01")
    assert s.iloc[0] == 118.7
    assert s.iloc[-1] == 198.0
    assert s.name == "INR.INFL"


def test_get_general_cpi_empty_first_page_returns_empty_series():
    session = FakeSession([EMPTY_PAGE, EMPTY_PAGE])

    s = mospi.get_general_cpi(session=session)

    assert isinstance(s, pd.Series)
    assert len(s) == 0


def test_get_general_cpi_raises_when_base_2024_is_populated():
    """#50 tripwire: once MOSPI loads base 2024, new months move there and the
    2012 series goes stale — fail the update loudly so the splice gets built."""
    probe_hit = {"data": [{"baseyear": "2024", "year": 2026, "month": "January"}],
                 "statusCode": 200}
    session = FakeSession([probe_hit])

    with pytest.raises(RuntimeError, match="base-2024"):
        mospi.get_general_cpi(session=session)


def test_get_general_cpi_raises_when_series_is_stale():
    """#50 tripwire: the publication lag is ~7 months; a last month older than
    the staleness limit means the feed stalled — fail loudly."""
    old = pd.Timestamp.today().normalize() - pd.DateOffset(days=400)
    stale_page = {"data": [_row(old.year, old.strftime("%B"), index="150.0")],
                  "statusCode": 200}
    session = FakeSession([EMPTY_PAGE, stale_page, EMPTY_PAGE])

    with pytest.raises(RuntimeError, match="stale"):
        mospi.get_general_cpi(session=session)
