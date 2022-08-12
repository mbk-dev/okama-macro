import pandas as pd
from nbsc import request_data

today_year = pd.Timestamp.today().strftime('%Y')
s_2016 = request_data.load_nbs_web(series='A01030101', periods=f'2016-{today_year}', freq='month')
s_2001 = request_data.load_nbs_web(series='A01030201', periods='2001-2015', freq='month')
s_old = request_data.load_nbs_web(series='A01010201', periods='1987-1990', freq='month')  # same month of last year=100
# s_old = s_old[s_old != 0]

