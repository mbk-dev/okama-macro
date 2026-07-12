"""Contract tests for the folded nbsc consumed path (CNY.INFL).

Locks the parsing contract per the boe#6 template: the raw NBS series is the
"same-period=100" index, get_recent_inflation must return m/m FRACTIONS
(``(x-100)/100``), ascending, with NBS "not-yet-published" zeros handled (the
#14/#31 CNY -100% guard), monotonic index, correct units.
"""

import pandas as pd
import pytest

from okama_macro.sources.nbsc import inflation


@pytest.fixture
def _raw(monkeypatch):
    # Realistic raw NBS payload: a "same-period-last-... = 100" index Series on a
    # DatetimeIndex (load_nbs_web returns Timestamps, not PeriodIndex).
    # NEWEST (last) row is 0 = "not published yet".
    def fake_load(series, periods, freq):
        idx = pd.to_datetime([
            "2016-01-01", "2016-02-01", "2016-03-01", "2016-04-01", "2016-05-01"
        ])
        # 100.5 -> +0.5% m/m style values; LAST value is 0.0 = unpublished month.
        return pd.Series([100.5, 101.0, 100.8, 100.2, 0.0], index=idx)
    monkeypatch.setattr(inflation.request_data, "load_nbs_web", fake_load)


def test_returns_mom_fractions_not_index(_raw):
    s = inflation.get_recent_inflation("2016")
    # (100.5-100)/100 = 0.005 — fractions, not the 100.x index.
    assert s.iloc[0] == pytest.approx(0.005)
    assert (s.abs() < 1).all()  # fractions, never index-scale


def test_index_is_monotonic_ascending(_raw):
    s = inflation.get_recent_inflation("2016")
    assert s.index.is_monotonic_increasing


def test_not_published_zero_is_guarded(_raw):
    # NBS 0 => (0-100)/100 = -1.0 would zero the price level (#14/#31). The
    # library's check_for_zero must drop/neutralise it, so no -1.0 survives.
    s = inflation.get_recent_inflation("2016")
    assert (s > -0.99).all(), "an NBS not-published 0 leaked through as -100% m/m"
