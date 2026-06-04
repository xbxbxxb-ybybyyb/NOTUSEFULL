import os
from tquant.SmartFactor.HFBaseFactor import HFBaseFactor


class weighted_buysell_px_spread_delta(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'weighted_buysell_px_spread_delta'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        """
        在 interval_seconds 内, 委托买卖加权平价价格价差spread的变化
        """
        n_tick = custom_params["interval_seconds"] // custom_params["tick_interval_seconds"]
        df = price_data["tick"]
        res =  df['WeightedBuySellPxGap'].diff(n_tick)
        res.index = df["MDTime"]
        return res


if __name__ == "__main__":
    pxchange_ins = weighted_buysell_px_spread_delta()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)