import pandas as pd
from okama_macro.sources.ecb import request_data


# Between these dates the ECB allotted its main refinancing operations through
# VARIABLE-rate tenders, so the fixed rate (MRR_FR) has no observations at all
# and the policy rate of record is the minimum bid rate (MRR_MBR). Serving the
# last fixed rate across the gap froze EU_MRO at 4.25% for eight years
# (okama-API#53).
VARIABLE_TENDER_START = pd.Timestamp(2000, 6, 28)
VARIABLE_TENDER_END = pd.Timestamp(2008, 10, 14)


def _periods(start_date: pd.Timestamp, end_date: pd.Timestamp | None) -> tuple[str, str | None]:
    start_period = start_date.strftime("%Y-%m-%d")
    end_period = end_date.strftime("%Y-%m-%d") if end_date is not None else None
    return start_period, end_period


def get_min_bid_rate(start_date: pd.Timestamp = pd.Timestamp(1900, 1, 1),
                     end_date: pd.Timestamp = None) -> pd.Series:
    """
    Get the ECB minimum bid rate of the main refinancing operations.

    Published only for the variable-rate tender era (2000-06-28 … 2008-10-14);
    outside that window the series is empty.
    """
    start_period, end_period = _periods(start_date, end_date)
    s = request_data.get_data_frame("FM", "D.U2.EUR.4F.KR.MRR_MBR.LEV",
                                    start_period=start_period, end_period=end_period)
    s = s.rename("min_bid_rate")
    return s / 100


def get_refinancing_rate(start_date: pd.Timestamp = pd.Timestamp(1900, 1, 1),
                         end_date:pd.Timestamp = None) -> pd.Series:
    """
    Get ECB main refinancing operations key rate time series.

    The fixed rate (MRR_FR) outside the variable-rate tender era, spliced with
    the minimum bid rate (MRR_MBR) inside it — see VARIABLE_TENDER_START/END.
    """
    start_period, end_period = _periods(start_date, end_date)
    s = request_data.get_data_frame("FM", "D.U2.EUR.4F.KR.MRR_FR.LEV",
                                        start_period=start_period, end_period=end_period)
    if _overlaps_variable_tender(start_date, end_date):
        min_bid = get_min_bid_rate(start_date, end_date) * 100
        s = pd.concat([s, min_bid]).sort_index()
        # The two series do not overlap in ECB's data; if that ever changes the
        # fixed rate wins, being the published rate of record.
        s = s[~s.index.duplicated(keep="first")]
    s = s.rename("main_rate")
    return s / 100


def _overlaps_variable_tender(start_date: pd.Timestamp, end_date: pd.Timestamp | None) -> bool:
    """True if the requested window touches the variable-rate tender era."""
    if start_date > VARIABLE_TENDER_END:
        return False
    return end_date is None or end_date >= VARIABLE_TENDER_START


def get_deposit_rate(start_date: pd.Timestamp = pd.Timestamp(1900, 1, 1),
                         end_date:pd.Timestamp = None) -> pd.Series:
    """
    Get ECB key rate on the deposit facility monthly time series.

    On deposit facility rate banks can make overnight deposits with the Eurosystem.
    """
    start_period = start_date.strftime("%Y-%m-%d")
    if end_date != None:
        end_period = end_date.strftime("%Y-%m-%d")
    else:
        end_period = None
    s = request_data.get_data_frame("FM", "D.U2.EUR.4F.KR.DFR.LEV",
                                        start_period=start_period, end_period=end_period)
    s = s.rename("deposit_rate")
    return s / 100


def get_marginal_rate(start_date: pd.Timestamp = pd.Timestamp(1900, 1, 1),
                         end_date:pd.Timestamp = None) -> pd.Series:
    """
    Get ECB key rate on marginal lending facility monthly time seriesю

    On marginal lending facility rate ECB may offer overnight credit to banks from the Eurosystem.
    """

    start_period = start_date.strftime("%Y-%m-%d")
    if end_date != None:
        end_period = end_date.strftime("%Y-%m-%d")
    else:
        end_period = None
    s = request_data.get_data_frame(
        "FM",
        "D.U2.EUR.4F.KR.MLFR.LEV",
        start_period=start_period,
        end_period=end_period
    )
    s = s.rename("marginal_rate")
    return s / 100
