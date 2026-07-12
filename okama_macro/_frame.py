"""Shared DataFrame/Series shaping helpers."""

import pandas as pd


def clip_window(obj: pd.Series | pd.DataFrame,
                first_date: object = None,
                last_date: object = None) -> pd.Series | pd.DataFrame:
    """Clip a DatetimeIndex-ed object to the inclusive [first_date, last_date]."""
    if first_date is not None:
        obj = obj[obj.index >= pd.Timestamp(first_date)]
    if last_date is not None:
        obj = obj[obj.index <= pd.Timestamp(last_date)]
    return obj
