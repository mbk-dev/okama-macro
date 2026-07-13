"""Series registry: canonical okama series keys -> normalised ``pd.Series``.

Contract, uniform for every key: values are decimal fractions (m/m CPI
inflation ``0.0042``, rate ``0.0525``); CPI series are monthly on
first-of-month dates; rate series carry observations only — padding to a
daily frequency is the consumer's job (this removes the look-ahead-padding
bug class, see mbk-dev/boe#6); ascending ``DatetimeIndex``; float dtype;
``Series.name`` equals the key.
"""

from collections.abc import Callable

import pandas as pd

from okama_macro import _frame
from okama_macro.sources import (
    bis, boe, boi, censtatd, cfets, ecb, fred, hkma, mospi, nbsc, ons, rbi
)

Fetcher = Callable[[pd.Timestamp | None, pd.Timestamp | None], pd.Series]

_REGISTRY: dict[str, Fetcher] = {}


def _register(key: str) -> Callable[[Fetcher], Fetcher]:
    def decorator(fn: Fetcher) -> Fetcher:
        _REGISTRY[key] = fn
        return fn
    return decorator


def list_series() -> list[str]:
    """Return the sorted list of available series keys."""
    return sorted(_REGISTRY)


def get(
    key: str,
    first_date: pd.Timestamp | None = None,
    last_date: pd.Timestamp | None = None,
) -> pd.Series:
    """Return the normalised series for ``key`` (see the module docstring)."""
    try:
        fetch = _REGISTRY[key]
    except KeyError:
        msg = f'Unknown series key {key!r}; known: {list_series()}'
        raise ValueError(msg) from None
    s = fetch(first_date, last_date)
    s = s.astype(float)
    if not s.index.is_monotonic_increasing:
        s = s.sort_index()
    s.name = key
    return s


def _cpi_mom(levels: pd.Series,
             first_date: pd.Timestamp | None,
             last_date: pd.Timestamp | None) -> pd.Series:
    """Index levels -> m/m fractions (base-invariant), clipped to the window."""
    s = levels.pct_change().dropna()
    return _frame.clip_window(s, first_date, last_date)


@_register('USD.INFL')
def _usd_infl(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    # Fetch two extra months so pct_change has a prior level for first_date.
    ext = (
        None
        if first_date is None
        else pd.Timestamp(first_date) - pd.DateOffset(months=2)
    )
    df = fred.get_series('CPIAUCNS', first_date=ext, last_date=last_date)
    return _cpi_mom(df['CPIAUCNS'], first_date, last_date)


@_register('HKD.INFL')
def _hkd_infl(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _cpi_mom(censtatd.get_composite_cpi(), first_date, last_date)


@_register('INR.INFL')
def _inr_infl(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _cpi_mom(mospi.get_general_cpi(), first_date, last_date)


@_register('CNY.INFL')
def _cny_infl(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    """China m/m inflation fractions from the folded nbsc (NBS China).

    nbsc returns m/m fractions already (the NBS 'same-period=100' index turned
    into ``(x-100)/100``), so the registry passes them through — no pct_change.
    A two-years-back fetch keeps NBS's retroactive corrections re-pulled (#14).
    """
    first_year = str((pd.Timestamp.today().year) - 2)
    s = nbsc.get_recent_inflation(first_year)
    if isinstance(s.index, pd.PeriodIndex):
        s.index = s.index.to_timestamp()
    return _frame.clip_window(s, first_date, last_date)


@_register('GBP.INFL')
def _gbp_infl(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    """UK m/m inflation fractions from the folded ons (ONS CPIH, series l522).

    ons returns m/m fractions already (internal ``pct_change().round(4)`` off the
    CPIH index) on a first-of-month DatetimeIndex and takes no date args, so the
    registry passes them through and clips. The prod DB's pre-1988 GBP.INFL depth
    is a separate boe#6 backfill the nightly upsert leaves intact.
    """
    return _frame.clip_window(ons.get_inflation_cpih(), first_date, last_date)


@_register('US_EFFR.RATE')
def _us_effr(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    df = fred.get_series('DFF', first_date=first_date, last_date=last_date)
    return df['DFF'] / 100


@_register('HK_BR.RATE')
def _hk_br(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    df = hkma.get_base_rate(first_date=first_date, last_date=last_date)
    return df['disc_win_base_rate'] / 100


@_register('IND_RBI.RATE')
def _ind_rbi(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    """BIS ``WS_CBPOL/D.IN`` history + a same-day rbi.org.in scrape tail.

    BIS publishes with ~a year's lag, so today's rate is scraped and appended
    unless BIS already covers today or ``last_date`` excludes it. A failed
    scrape fails the whole key (no silent fallback).
    """
    df = bis.get_policy_rate('IN', first_date=first_date, last_date=last_date)
    s = df['policy_rate']
    today = pd.Timestamp.today().normalize()
    if (last_date is None or pd.Timestamp(last_date) >= today) and (
            s.empty or s.index[-1] < today):
        s.loc[today] = rbi.get_current_repo_rate()
    return s / 100


def _lpr(fetch: Callable[..., pd.Series],
         first_date: pd.Timestamp | None,
         last_date: pd.Timestamp | None) -> pd.Series:
    """China LPR fraction series from the folded cfets (observations-only).

    cfets returns m/m-cadence LPR fractions (÷100 already applied) on a daily
    PeriodIndex; convert to a DatetimeIndex and clip. ``get()`` sorts ascending
    and padding to a daily grid stays the consumer's job (rates contract).
    """
    kwargs = {} if first_date is None else {'start_date': pd.Timestamp(first_date)}
    s = fetch(**kwargs)
    if isinstance(s.index, pd.PeriodIndex):
        s.index = s.index.to_timestamp()
    return _frame.clip_window(s, first_date, last_date)


@_register('CHN_LPR1.RATE')
def _chn_lpr1(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _lpr(cfets.get_lpr_1y, first_date, last_date)


@_register('CHN_LPR5.RATE')
def _chn_lpr5(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _lpr(cfets.get_lpr_5y, first_date, last_date)


@_register('ILS.INFL')
def _ils_infl(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    """Israel m/m inflation fractions from the folded boi (Bank of Israel).

    boi returns m/m fractions already (internal ``pct_change().round(4)`` off the
    2020=100 CPI), so the registry passes them through — no pct_change. boi's
    date_start is a STRING interpolated into the SDMX query, so it is formatted.
    """
    kwargs = (
        {} if first_date is None
        else {'date_start': pd.Timestamp(first_date).strftime('%Y-%m-%d')}
    )
    s = boi.get_inflation(**kwargs)
    if isinstance(s.index, pd.PeriodIndex):
        s.index = s.index.to_timestamp()
    return _frame.clip_window(s, first_date, last_date)


@_register('ISR_IR.RATE')
def _isr_ir(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    """Bank of Israel policy rate fractions from the folded boi (observations-only).

    boi returns fractions already (internal ``/100``) on a daily PeriodIndex;
    convert to DatetimeIndex and clip. date_start is a STRING (SDMX query).
    """
    kwargs = (
        {} if first_date is None
        else {'date_start': pd.Timestamp(first_date).strftime('%Y-%m-%d')}
    )
    s = boi.get_ir(**kwargs)
    if isinstance(s.index, pd.PeriodIndex):
        s.index = s.index.to_timestamp()
    return _frame.clip_window(s, first_date, last_date)


def _ecb_rate(fetch: Callable[..., pd.Series],
              first_date: pd.Timestamp | None,
              last_date: pd.Timestamp | None) -> pd.Series:
    """ECB key-rate fraction series from the folded ecb (observations-only).

    ecb returns fractions (÷100 applied) on a daily PeriodIndex and takes a
    Timestamp start_date (it .strftime's it internally); convert the index to a
    DatetimeIndex and clip. ``get()`` sorts ascending; padding stays downstream.
    """
    kwargs = {} if first_date is None else {'start_date': pd.Timestamp(first_date)}
    s = fetch(**kwargs)
    if isinstance(s.index, pd.PeriodIndex):
        s.index = s.index.to_timestamp()
    return _frame.clip_window(s, first_date, last_date)


@_register('EU_MRO.RATE')
def _eu_mro(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _ecb_rate(ecb.get_refinancing_rate, first_date, last_date)


@_register('EU_MLR.RATE')
def _eu_mlr(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _ecb_rate(ecb.get_marginal_rate, first_date, last_date)


@_register('EU_DFR.RATE')
def _eu_dfr(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    return _ecb_rate(ecb.get_deposit_rate, first_date, last_date)


@_register('UK_BR.RATE')
def _uk_br(
    first_date: pd.Timestamp | None, last_date: pd.Timestamp | None
) -> pd.Series:
    """Bank of England bank rate fractions from the folded boe.

    Unlike the other rate keys, boe returns a **pre-padded** daily series (it
    reads the BoE change-dates table and forward-fills through today — the boe#6
    look-ahead fix; stripping that would change behavior), so this key is the
    documented exception to the observations-only contract. Fractions (÷100
    inside); Timestamp start_date (.strftime'd internally). The prod DB's pre-1975
    UK_BR depth is a separate BIS backfill the nightly upsert leaves intact.
    """
    kwargs = {} if first_date is None else {'start_date': pd.Timestamp(first_date)}
    s = boe.get_bank_rate(**kwargs)
    if isinstance(s.index, pd.PeriodIndex):
        s.index = s.index.to_timestamp()
    return _frame.clip_window(s, first_date, last_date)
