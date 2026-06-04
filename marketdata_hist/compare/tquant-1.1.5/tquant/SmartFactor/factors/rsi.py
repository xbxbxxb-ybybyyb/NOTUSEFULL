import os
import talib as ta
import pandas as pd
from tquant.SmartFactor.HFBaseFactor import HFBaseFactor

class rsi(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'rsi'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        df = price_data["tick"]
        n_tick = custom_params["interval_seconds"] // custom_params["tick_interval_seconds"]
        res = ta.RSI(df['LastPx'].values, timeperiod=n_tick)
        res = pd.Series(res)
        res.index = df["MDTime"]

        return res