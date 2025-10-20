import pandas as pd

from nbsc import request_data

today_year = pd.Timestamp.today().strftime("%Y")



def get_auto_retail_current(first_year: str = "2001") -> pd.Series:
    """
    Retail Sales of Enterprises above Designated Size, Automobile, Current Period (100 million yuan). Available data range: 2001+.
    """
    s = request_data.load_nbs_web( 
        series="A07040F01", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_auto_retail_accumulated(first_year: str = "2001") -> pd.Series:
    """
    Retail Sales of Enterprises above Designated Size, Automobile, Accumulated (100 million yuan). Available data range: 2001+.
    """
    s = request_data.load_nbs_web( 
        series="A07040F02", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_auto_retail_growth_rate(first_year: str = "2001") -> pd.Series:
    """
    Retail Sales of Enterprises above Designated Size, Automobile, Accumulated (The same period last year=100) (%). Available data range: 2001+.
    """
    s = request_data.load_nbs_web( 
        series="A07040F03", periods=f"{first_year}-{today_year}", freq="month"
    )    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_auto_retail_accumulated_growth_rate(first_year: str = "2001") -> pd.Series:
    """
    Retail Sales of Enterprises above Designated Size, Automobile, Accumulated Growth Rate (%). Available data range: 2001+.
    """
    s = request_data.load_nbs_web( 
        series="A07040F04", periods=f"{first_year}-{today_year}", freq="month"
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
