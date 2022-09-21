import pandas as pd

from nbsc import request_data

today_year = pd.Timestamp.today().strftime("%Y")

def get_gdp() -> pd.Series:
    s = request_data.load_nbs_web(
        series="A020102", periods=f"1952-{today_year}", freq="year"
    )
    s.index = s.index.to_period("Y")
    return s.sort_index(ascending=False)

def get_gni() -> pd.Series:
    s = request_data.load_nbs_web(
        series="A020101", periods=f"1952-{today_year}", freq="year"
    )
    s.index = s.index.to_period("Y")
    return s.sort_index(ascending=False)

def get_per_cap_gdp() -> pd.Series:
    s = request_data.load_nbs_web(
        series="A020106", periods=f"1952-{today_year}", freq="year"
    )
    s.index = s.index.to_period("Y")
    return s.sort_index(ascending=False)
