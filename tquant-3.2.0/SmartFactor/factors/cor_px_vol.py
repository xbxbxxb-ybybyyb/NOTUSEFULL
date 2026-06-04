import talib as ta
import pandas as pd
from SmartFactor.HFBaseFactor import HFBaseFactor


class cor_px_vol(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'cor_px_vol'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "sample_period": 3}

    def calc(self, price_data, factor_data, custom_params):
        """
        在 interval_seconds 内的量价相关性
        """
        n_tick = custom_params["interval_seconds"] // custom_params["sample_period"]
        df = price_data["tick"]

        res = ta.CORREL(df['LastPx'].values, df['TotalVolumeTrade'].diff(1).values, n_tick)
        res = pd.Series(res)
        res.index = df["MDTime"]
        return res


if __name__ == "__main__":
    pxchange_ins = cor_px_vol()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)