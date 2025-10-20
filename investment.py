import pandas as pd

from nbsc import request_data

today_year = pd.Timestamp.today().strftime("%Y")



def get_real_estate_investment_accumulated(first_year: str = "2000") -> pd.Series:
    """
    Investment of Real Estate , Accumulated (100 million yuan). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A060101", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_real_estate_investment_growth_rate(first_year: str = "2000") -> pd.Series:
    """
    Investment of Real Estate , Accumulated Growth Rate (%). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A060102", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_auxiliary_investment_accumulated(first_year: str = "2006", last_year: str = "2013") -> pd.Series:
    """
    Investment in Auxiliary Projects, Accumulated (100 million yuan). Available data range: 2006-2013.
    """
    s = request_data.load_nbs_web( 
        series="A060103", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_auxiliary_investment_growth_rate(first_year: str = "2007", last_year: str = "2014") -> pd.Series:
    """
    Investment in Auxiliary Projects, Accumulated Growth Rate (%). Available data range: 2007 - 2014.
    """
    s = request_data.load_nbs_web( 
        series="A060104", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_residential_total_investment_accumulated(first_year: str = "2000") -> pd.Series:
    """
    Total Investment in Residential Buildings in Real Estate Development, Accumulated (100 million yuan). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A060105", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_residential_total_investment_growth_rate(first_year: str = "2000") -> pd.Series:
    """
    Total Investment in Residential Buildings in Real Estate Development, Accumulated Growth Rate (%). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A060106", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_small_housing_investment_accumulated(first_year: str = "2007", last_year: str = "2023") -> pd.Series:
    """
    Investment in Residential Buildings, Housing Below 90 Square Meters, Accumulated (100 million yuan). Available data range: 2007-2023.
    """
    s = request_data.load_nbs_web( 
        series="A060107", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_small_housing_investment_growth_rate(first_year: str = "2008", last_year: str = "2023") -> pd.Series:
    """
    Investment in Residential Buildings, Housing Below 90 Square Meters, Accumulated Growth Rate (%). Available data range: 2008-2023.
    """
    s = request_data.load_nbs_web( 
        series="A060108", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_large_housing_investment_accumulated(first_year: str = "2008", last_year: str = "2023") -> pd.Series:
    """
    Investment in Residential Buildings, Housing Above 144 Square Meters, Accumulated (100 million yuan). Available data range: 2008-2023.
    """
    s = request_data.load_nbs_web( 
        series="A060109", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_large_housing_investment_growth_rate(first_year: str = "2009", last_year: str = "2023") -> pd.Series:
    """
    Investment in Residential Buildings, Housing Above 144 Square Meters, Accumulated Growth Rate (%). Available data range: 2009-2023.
    """
    s = request_data.load_nbs_web( 
        series="A06010A", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_villa_investment_accumulated(first_year: str = "2006", last_year: str = "2019") -> pd.Series:
    """
    Investment in Residential Buildings, Villas and High-grade Apartments, Accumulated (100 million yuan). Available data range: 2006-2019.
    """
    s = request_data.load_nbs_web( 
        series="A06010B", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_villa_investment_growth_rate(first_year: str = "2007", last_year: str = "2019") -> pd.Series:
    """
    Investment in Residential Buildings, Villas and High-grade Apartments, Accumulated Growth Rate (%). Available data range: 2007-2019.
    """
    s = request_data.load_nbs_web( 
        series="A06010C", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_office_investment_accumulated(first_year: str = "2000") -> pd.Series:
    """
    Investment in Office Buildings, Accumulated (100 million yuan). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010D", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_office_investment_growth_rate(first_year: str = "2000") -> pd.Series:
    """
    Investment in Office Buildings, Accumulated Growth Rate (%). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010E", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_business_housing_investment_accumulated(first_year: str = "2000") -> pd.Series:
    """
    Investment in Houses for Business Use, Accumulated (100 million yuan). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010F", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_business_housing_investment_growth_rate(first_year: str = "2000") -> pd.Series:
    """
    Investment in Houses for Business Use, Accumulated Growth Rate (%). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010G", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s    
    

def get_real_estate_other_investment_accumulated(first_year: str = "2000") -> pd.Series:
    """
    Investment of Real Estate,others, Accumulated (100 million yuan). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010H", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_real_estate_other_investment_growth_rate(first_year: str = "2000") -> pd.Series:
    """
    Investment in Office Buildings, Accumulated Growth Rate (%). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010I", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_real_estate_construction_investment_accumulated(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate, others, Accumulated Growth Rate (%). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010J", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_real_estate_construction_investment_growth_rate(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate, Construction, Accumulated Growth Rate (%). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010K", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
  
def get_real_estate_installation_investment_accumulated(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate,Installation, Accumulated (100 million yuan). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010L", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_real_estate_installation_investment_growth_rate(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate, Installation, Accumulated Growth Rate (%). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010M", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_real_estate_equipment_investment_accumulated(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate,Purchase of Equipment and Industrial Equipment, Accumulated (100 million yuan). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010N", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_real_estate_equipment_investment_accumulated_growth_rate(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate, Purchase of Equipment and Industrial Equipment, Accumulated Growth Rate (%). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010O", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s     
    

def get_real_estate_misc_investment_accumulated(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate,others, Accumulated (100 million yuan). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010P", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_real_estate_misc_investment_agrowth_rate(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate, others, Accumulated Growth Rate (%). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010Q", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_land_acquisition_investment_accumulated(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate,Land Acquisition Costs, Accumulated (100 million yuan). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010R", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_land_acquisition_investment_agrowth_rate(first_year: str = "2002") -> pd.Series:
    """
    Investment of Real Estate, Land Acquisition Costs, Accumulated Growth Rate (%). Available data range: 2002+.
    """
    s = request_data.load_nbs_web( 
        series="A06010S", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s          
    

def get_planned_real_estate_investment_accumulated(first_year: str = "2000") -> pd.Series:
    """
    Total Investment Planned for Real Estate Development, Accumulated (100 million yuan). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010T", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_planned_real_estate_growth_rate(first_year: str = "2000") -> pd.Series:
    """
    Total Investment Planned for Real Estate Development, Accumulated Growth Rate (%). Available data range: 2000+.
    """
    s = request_data.load_nbs_web( 
        series="A06010U", periods=f"{first_year}-{today_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s 
    
    
def get_new_fixed_assets_accumulated(first_year: str = "2000", last_year: str = "2023") -> pd.Series:
    """
    Newly Increased Fixed Assets of Real Estate Development, Accumulated (100 million yuan). Available data range: 2000-2023.
    """
    s = request_data.load_nbs_web( 
        series="A06010V", periods=f"{first_year}-{last_year}", freq="month"
    )    
    
    s = check_for_zero(s)    
    s.index = s.index.to_period("M")
    s.sort_index(ascending=False, inplace=True)
    return s  
    
    
def get_new_fixed_assets_growth_rate(first_year: str = "2000", last_year: str = "2023") -> pd.Series:
    """
    Newly Increased Fixed Assets of Real Estate Development, Accumulated Growth Rate (%). Available data range: 2000-2023.
    """
    s = request_data.load_nbs_web( 
        series="A06010W", periods=f"{first_year}-{last_year}", freq="month"
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
