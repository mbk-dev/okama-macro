"""Tests for DataFrame/Series shaping helpers (okama_macro/_frame.py)."""

import pandas as pd

from okama_macro import _frame


def _series():
    idx = pd.to_datetime(['2026-01-01', '2026-02-01', '2026-03-01'])
    return pd.Series([1.0, 2.0, 3.0], index=idx)


def test_clip_window_applies_inclusive_bounds():
    s = _frame.clip_window(_series(),
                           first_date=pd.Timestamp('2026-02-01'),
                           last_date=pd.Timestamp('2026-02-01'))
    assert s.tolist() == [2.0]


def test_clip_window_none_bounds_are_noop():
    s = _frame.clip_window(_series())
    assert len(s) == 3


def test_clip_window_accepts_datetimelike_strings():
    s = _frame.clip_window(_series(), first_date='2026-02-15')
    assert s.tolist() == [3.0]
