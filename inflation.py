import pandas as pd
from nbsc import request_data

today_year = pd.Timestamp.today().strftime('%Y')


def get_inflation_from_2001() -> pd.Series:
    """
    Request long term monthly inflation time series from 2001 to recent year.
    """
    s_2016 = request_data.load_nbs_web(series='A01030101', periods=f'2016-{today_year}', freq='month')
    s_2001 = request_data.load_nbs_web(series='A01030201', periods='2001-2015', freq='month')
    s = pd.concat([s_2016, s_2001], axis=0, join="outer", copy="false")
    s = (s - 100.) / 100
    s.index = s.index.to_period("M")
    return s.sort_index(ascending=False)


def get_recent_inflation(first_year: str = '2016') -> pd.Series:
    """
    Request monthly inflation time series (2016+).
    """
    s_2016 = request_data.load_nbs_web(series='A01030101', periods=f'{first_year}-{today_year}', freq='month')
    s_2016.index = s_2016.index.to_period("M")
    s_2016.sort_index(ascending=False, inplace=True)
    return (s_2016 - 100.) / 100


def get_annual_inflation() -> pd.Series:
    """
    Request annual inflation monthly time series (available from 1987 to 2015).

    Inflation is calculated from CPI ('A01010201' code - same month of last year=100).
    """
    s_old = request_data.load_nbs_web(series='A01010201', periods='1987-2015', freq='month')
    s_old.index = s_old.index.to_period("M")
    s_old.sort_index(ascending=False, inplace=True)
    s_old = s_old[s_old != 0]
    return (s_old - 100.) / 100


def calculate_monthly_from_annual():
    """
    Calculate monthly inflation (1987 - 2000) from annual and monthly data.
    """
    s_annual = get_annual_inflation()
    s_monthly = get_inflation_from_2001()
    new_index = pd.period_range('1987-01', '2000-12', freq='M').sort_values(ascending=False)
    for date in new_index:
        prod_monthly = (s_monthly.tail(11) + 1.).prod()
        s_monthly[date] = (s_annual.shift(11)[date] + 1.) / prod_monthly - 1.
    return s_monthly
