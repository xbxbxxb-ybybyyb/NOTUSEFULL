import talib as ta
from SmartFactor.HFBaseFactor import HFBaseFactor
import pandas as pd


class roc(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'roc'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "sample_period": 3}

    def calc(self, price_data, factor_data, custom_params):
        df = price_data["tick"]
        n_tick = custom_params["interval_seconds"] // custom_params["sample_period"]
        res = ta.ROC(df['LastPx'].values, timeperiod=n_tick)
        res = pd.Series(res)
        res.index = df["MDTime"]
        return res


if __name__ == "__main__":
    pxchange_ins = roc()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)