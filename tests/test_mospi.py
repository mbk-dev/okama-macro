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
    """Routes by endpoint.

    ``getCPIIndex`` (base 2012) returns queued ``index_pages`` in order until an
    empty page. ``getCPIData`` (base 2024) returns the rows registered in
    ``data_by_month`` keyed by ``(year, month_code)`` — an unregistered month
    yields an empty ``data`` list (the "not yet published" signal).
    """

    def __init__(self, index_pages=None, data_by_month=None):
        self._index_pages = list(index_pages or [])
        self._data_by_month = data_by_month or {}
        self.calls: list[tuple[str, dict]] = []

    def get(self, url, params=None, timeout=None, **kwargs):
        params = params or {}
        self.calls.append((url, params))
        if url.endswith('getCPIData'):
            key = (int(params['year']), int(params['month_code']))
            return FakeResponse({'data': self._data_by_month.get(key, [])})
        payload = self._index_pages.pop(0) if self._index_pages else {'data': []}
        return FakeResponse(payload)


def _row2012(year, month, group='General', index='100.0'):
    return {'baseyear': '2012', 'year': year, 'month': month, 'state': 'All India',
            'sector': 'Combined', 'group': group,
            'subgroup': f'{group}-Overall', 'index': index,
            'inflation': None, 'status': 'F'}


def _row2024(division='CPI (General)', group=None, index='100.0'):
    return {'base_year': '2024', 'series': 'Current', 'state': 'All India',
            'sector': 'Combined', 'division': division, 'group': group,
            'class': None, 'sub_class': None, 'item': None, 'code': None,
            'index': index, 'inflation': None, 'imputation': None}


# ---------------------------------------------------------------------------
# _splice — pure function, no wall-clock coupling
# ---------------------------------------------------------------------------

def test_splice_keeps_old_through_anchor_and_appends_rescaled_new():
    old = pd.Series(
        [196.0, 198.0],
        index=pd.to_datetime(['2025-11-01', '2025-12-01']),
    )
    new = pd.Series(
        [104.10, 104.45, 104.57],
        index=pd.to_datetime(['2025-12-01', '2026-01-01', '2026-02-01']),
    )

    s = mospi._splice(old, new)

    # Old side is preserved byte-for-byte up to and including the anchor.
    assert s.loc['2025-11-01'] == 196.0
    assert s.loc['2025-12-01'] == 198.0
    # New months are rescaled onto the old level (factor = 198.0 / 104.10).
    factor = 198.0 / 104.10
    assert s.loc['2026-01-01'] == pytest.approx(104.45 * factor)
    assert s.loc['2026-02-01'] == pytest.approx(104.57 * factor)
    assert list(s.index) == list(pd.to_datetime(
        ['2025-11-01', '2025-12-01', '2026-01-01', '2026-02-01']))


def test_splice_boundary_mom_matches_base_2024_internal_ratio():
    # The whole point: the Jan-2026 m/m must be the base-2024 internal ratio,
    # not a spurious jump from the 198 -> 104 level change.
    old = pd.Series([198.0], index=pd.to_datetime(['2025-12-01']))
    new = pd.Series([104.10, 104.45],
                    index=pd.to_datetime(['2025-12-01', '2026-01-01']))

    s = mospi._splice(old, new)
    mom_jan = s.pct_change().loc['2026-01-01']

    assert mom_jan == pytest.approx(104.45 / 104.10 - 1)


def test_splice_returns_old_when_new_is_empty():
    old = pd.Series([198.0], index=pd.to_datetime(['2025-12-01']))
    empty = pd.Series(dtype='float64')

    s = mospi._splice(old, empty)

    assert list(s.index) == list(old.index)
    assert s.loc['2025-12-01'] == 198.0


# ---------------------------------------------------------------------------
# _fetch_base_2024 — getCPIData month walk
# ---------------------------------------------------------------------------

def test_fetch_base_2024_walks_months_from_start_and_stops_at_gap():
    start = pd.Timestamp('2025-12-01')
    data = {
        (2025, 12): [_row2024(index='104.10')],
        (2026, 1): [_row2024(index='104.45')],
        (2026, 2): [_row2024(index='104.57')],
        # 2026-03 unregistered -> empty -> walk stops here
    }
    session = FakeSession(data_by_month=data)

    s = mospi._fetch_base_2024(session, start=start)

    assert list(s.index) == list(pd.to_datetime(
        ['2025-12-01', '2026-01-01', '2026-02-01']))
    assert s.loc['2025-12-01'] == 104.10
    assert s.loc['2026-02-01'] == 104.57
    # Requests carry the base-2024 param shape (renumbered codes, new endpoint).
    url, p = session.calls[0]
    assert url.endswith('getCPIData')
    assert p['base_year'] == '2024'
    assert p['series_code'] == 'Current'
    assert p['state_code'] == '1'       # All India (renumbered from 99)
    assert p['sector_code'] == '3'      # Combined
    assert p['year'] == '2025' and p['month_code'] == '12'


def test_fetch_base_2024_keeps_only_general_division():
    start = pd.Timestamp('2026-01-01')
    data = {
        (2026, 1): [
            _row2024(division='Food and beverages', group=None, index='106.9'),
            _row2024(division='CPI (General)', group=None, index='104.45'),
            _row2024(division='CPI (General)', group='Food', index='999.0'),
        ],
    }
    session = FakeSession(data_by_month=data)

    s = mospi._fetch_base_2024(session, start=start)

    assert len(s) == 1
    assert s.loc['2026-01-01'] == 104.45


# ---------------------------------------------------------------------------
# get_general_cpi — orchestration (2012 pages + 2024 walk + splice)
# ---------------------------------------------------------------------------

def _recent_months(n):
    """The n most recent whole months ending last month (always fresh)."""
    last = pd.Timestamp.today().normalize().replace(day=1) - pd.DateOffset(months=1)
    return list(pd.date_range(end=last, periods=n, freq='MS'))


def test_get_general_cpi_splices_2012_history_with_live_2024():
    # base 2012: old history + the Dec-2025 anchor (frozen feed).
    anchor = pd.Timestamp('2025-12-01')
    page = {'data': [
        _row2012(2013, 'December', index='118.7'),
        _row2012(anchor.year, anchor.strftime('%B'), index='198.0'),
        _row2012(2025, 'December', group='Housing', index='185.2'),  # dropped
    ]}
    # base 2024: contiguous anchor -> recent, so the spliced tail is fresh.
    span = pd.date_range(start=anchor, end=_recent_months(1)[-1], freq='MS')
    data = {(d.year, d.month): [_row2024(index=f'{104.0 + i * 0.3:.2f}')]
            for i, d in enumerate(span)}
    session = FakeSession(index_pages=[page], data_by_month=data)

    s = mospi.get_general_cpi(session=session)

    assert s.name == 'INR.INFL'
    # 2012 history preserved on its own level.
    assert s.loc['2013-12-01'] == 118.7
    assert s.loc['2025-12-01'] == 198.0
    # The live 2024 tail is appended past the anchor and reaches a fresh month.
    assert s.index[-1] == span[-1]
    assert s.index[-1] > anchor


def test_get_general_cpi_raises_when_series_is_stale():
    # base 2024 never publishes past the anchor -> spliced tail stuck at Dec 2025.
    anchor = pd.Timestamp('2025-12-01')
    page = {'data': [_row2012(anchor.year, anchor.strftime('%B'), index='198.0')]}
    data = {(anchor.year, anchor.month): [_row2024(index='104.10')]}
    session = FakeSession(index_pages=[page], data_by_month=data)

    with pytest.raises(RuntimeError, match='stale'):
        mospi.get_general_cpi(session=session)
