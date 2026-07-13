"""Tests for the series registry (okama_macro/registry.py) and the public API."""

import pandas as pd
import pytest

import okama_macro
from okama_macro import registry


def test_list_series_contains_the_phase1_keys():
    assert set(okama_macro.list_series()) == {
        'USD.INFL', 'HKD.INFL', 'INR.INFL', 'CNY.INFL',
        'US_EFFR.RATE', 'HK_BR.RATE', 'IND_RBI.RATE',
        'CHN_LPR1.RATE', 'CHN_LPR5.RATE',
    }


def test_get_unknown_key_raises_with_known_keys_listed():
    with pytest.raises(ValueError, match='USD.INFL'):
        okama_macro.get('NOPE.KEY')


def test_usd_infl_derives_mom_fractions_and_clips(monkeypatch):
    idx = pd.to_datetime(['2026-01-01', '2026-02-01', '2026-03-01'])
    levels = pd.DataFrame({'CPIAUCNS': [100.0, 101.0, 102.01]}, index=idx)
    captured = {}

    def fake_get_series(series_id, first_date=None, last_date=None):
        captured['series_id'], captured['first_date'] = series_id, first_date
        return levels

    monkeypatch.setattr(registry.fred, 'get_series', fake_get_series)

    s = okama_macro.get('USD.INFL', first_date=pd.Timestamp('2026-02-01'))

    assert captured['series_id'] == 'CPIAUCNS'
    # The fetch window is extended so pct_change has a prior level.
    assert captured['first_date'] < pd.Timestamp('2026-02-01')
    assert s.name == 'USD.INFL'
    assert s.index.tolist() == [pd.Timestamp('2026-02-01'), pd.Timestamp('2026-03-01')]
    assert s.iloc[0] == pytest.approx(0.01)


def test_hkd_infl_derives_mom_fractions(monkeypatch):
    idx = pd.to_datetime(['2026-04-01', '2026-05-01'])
    monkeypatch.setattr(registry.censtatd, 'get_composite_cpi',
                        lambda: pd.Series([110.4, 110.5], index=idx))

    s = okama_macro.get('HKD.INFL')

    assert s.name == 'HKD.INFL'
    assert len(s) == 1
    assert s.iloc[0] == pytest.approx(110.5 / 110.4 - 1)


def test_inr_infl_derives_mom_fractions(monkeypatch):
    idx = pd.to_datetime(['2025-11-01', '2025-12-01'])
    monkeypatch.setattr(registry.mospi, 'get_general_cpi',
                        lambda: pd.Series([197.0, 198.0], index=idx))

    s = okama_macro.get('INR.INFL')

    assert s.name == 'INR.INFL'
    assert s.iloc[-1] == pytest.approx(198.0 / 197.0 - 1)


def test_us_effr_scales_percent_to_fraction(monkeypatch):
    df = pd.DataFrame({'DFF': [4.33]}, index=pd.to_datetime(['2026-06-01']))
    monkeypatch.setattr(registry.fred, 'get_series', lambda *a, **k: df)

    s = okama_macro.get('US_EFFR.RATE')

    assert s.name == 'US_EFFR.RATE'
    assert s.iloc[0] == pytest.approx(0.0433)


def test_hk_br_scales_percent_to_fraction(monkeypatch):
    df = pd.DataFrame({'disc_win_base_rate': [4.0]},
                      index=pd.to_datetime(['2026-07-10']))
    monkeypatch.setattr(registry.hkma, 'get_base_rate', lambda **k: df)

    s = okama_macro.get('HK_BR.RATE')

    assert s.iloc[0] == pytest.approx(0.04)


def test_ind_rbi_appends_scrape_tail_when_bis_lags(monkeypatch):
    hist = pd.DataFrame({'policy_rate': [6.5]}, index=pd.to_datetime(['2025-07-01']))
    monkeypatch.setattr(registry.bis, 'get_policy_rate', lambda *a, **k: hist.copy())
    monkeypatch.setattr(registry.rbi, 'get_current_repo_rate', lambda: 5.25)

    s = okama_macro.get('IND_RBI.RATE')

    assert s.index[-1] == pd.Timestamp.today().normalize()
    assert s.iloc[-1] == pytest.approx(0.0525)
    assert s.iloc[0] == pytest.approx(0.065)


def test_ind_rbi_skips_scrape_when_bis_has_today(monkeypatch):
    today = pd.Timestamp.today().normalize()
    hist = pd.DataFrame({'policy_rate': [5.5]}, index=[today])
    monkeypatch.setattr(registry.bis, 'get_policy_rate', lambda *a, **k: hist.copy())
    monkeypatch.setattr(
        registry.rbi, 'get_current_repo_rate',
        lambda: (_ for _ in ()).throw(AssertionError('scrape must not be called')),
    )

    s = okama_macro.get('IND_RBI.RATE')

    assert len(s) == 1
    assert s.iloc[0] == pytest.approx(0.055)


def test_get_returns_float_ascending(monkeypatch):
    df = pd.DataFrame({'DFF': [4, 5]},
                      index=pd.to_datetime(['2026-06-02', '2026-06-01']))
    monkeypatch.setattr(registry.fred, 'get_series', lambda *a, **k: df)

    s = okama_macro.get('US_EFFR.RATE')

    assert s.index.is_monotonic_increasing
    assert s.dtype == 'float64'


def test_cny_infl_passes_through_fractions(monkeypatch):
    # nbsc returns m/m FRACTIONS on a monthly PeriodIndex already.
    idx = pd.period_range("2025-10", periods=3, freq="M")
    monkeypatch.setattr(
        registry.nbsc, "get_recent_inflation",
        lambda first_year="2016": pd.Series([0.004, -0.001, 0.002], index=idx)
    )

    s = okama_macro.get("CNY.INFL")

    assert s.name == "CNY.INFL"
    # No pct_change applied — the fraction is passed straight through.
    assert s.iloc[0] == pytest.approx(0.004)
    # PeriodIndex -> first-of-month DatetimeIndex.
    assert s.index[0] == pd.Timestamp("2025-10-01")
    assert s.index.is_monotonic_increasing
    assert s.dtype == "float64"


def test_cny_infl_in_list_series():
    assert "CNY.INFL" in okama_macro.list_series()


def test_chn_lpr1_passes_through_fractions(monkeypatch):
    # cfets returns fractions on a daily PeriodIndex, sorted DESCENDING.
    idx = pd.period_range('2024-09-20', periods=2, freq='D')[::-1]
    monkeypatch.setattr(registry.cfets, 'get_lpr_1y',
                        lambda start_date=None, end_date=None:
                        pd.Series([0.0335, 0.0310], index=idx))

    s = okama_macro.get('CHN_LPR1.RATE')

    assert s.name == 'CHN_LPR1.RATE'
    assert (s.abs() < 1).all()                       # fractions, not percent
    assert isinstance(s.index, pd.DatetimeIndex)     # PeriodIndex -> DatetimeIndex
    assert s.index.is_monotonic_increasing           # get() sorts ascending
    assert s.dtype == 'float64'


def test_chn_lpr5_routes_to_get_lpr_5y(monkeypatch):
    called = {}
    idx = pd.period_range('2024-10-21', periods=1, freq='D')
    def fake(start_date=None, end_date=None):
        called['hit'] = True
        return pd.Series([0.0360], index=idx)
    monkeypatch.setattr(registry.cfets, 'get_lpr_5y', fake)

    s = okama_macro.get('CHN_LPR5.RATE')

    assert called.get('hit') is True
    assert s.iloc[0] == pytest.approx(0.0360)


def test_chn_lpr_first_date_forwarded(monkeypatch):
    captured = {}
    idx = pd.period_range('2024-10-21', periods=1, freq='D')
    def fake(start_date=None, end_date=None):
        captured['start_date'] = start_date
        return pd.Series([0.0310], index=idx)
    monkeypatch.setattr(registry.cfets, 'get_lpr_1y', fake)

    okama_macro.get('CHN_LPR1.RATE', first_date=pd.Timestamp('2020-01-01'))

    assert captured['start_date'] == pd.Timestamp('2020-01-01')
