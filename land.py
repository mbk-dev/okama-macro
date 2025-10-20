import pandas as pd

from nbsc import request_data

today_year = pd.Timestamp.today().strftime("%Y")



def get_land_space_purchased_accumulated(first_year: str = "2000", last_year: str = "2023") -> pd.Series:
    """
    Development and Sales of Real Estate, Land Space Purchased, Accumulated (10000 sq.m). Available data range: 2000-2023.
    """
    s = request_data.load_nbs_web( 
        series="A060301", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_land_space_growth_rate(first_year: str = "2000", last_year: str = "2022") -> pd.Series:
    """
    Development and Sales of Real Estate, Land Space Purchased, Accumulated Growth Rate (%). Available data range: 2000-2022.
    """
    s = request_data.load_nbs_web( 
        series="A060302", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_land_transaction_value_accumulated(first_year: str = "2004", last_year: str = "2022") -> pd.Series:
    """
    Development and Sales of Real Estate, Transaction Value of Land, Accumulated (100 million yuan). Available data range: 2004-2022.
    """
    s = request_data.load_nbs_web( 
        series="A060303", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_land_transaction_growth_rate(first_year: str = "2005", last_year: str = "2022") -> pd.Series:
    """
    Development and Sales of Real Estate, Transaction Value of Land, Accumulated Growth Rate (%). Available data range: 2005-2022.
    """
    s = request_data.load_nbs_web( 
        series="A060304", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 


def check_for_zero(s: pd.Series) -> pd.Series:
    """
    If the last CPI value is zero, skip it.

    NBSC shows zero value always for the last month statistics if the official data is not published yet.
    """
    if s[0] == 0:
        s = s[1:]
    return s
