from importlib.metadata import version

from nbsc.inflation import (
    get_inflation_from_2001,
    get_recent_inflation,
    get_annual_inflation,
    calculate_monthly_from_annual,
)
from nbsc.request_data import load_nbs_web

# __version__ = version("nbsc")
