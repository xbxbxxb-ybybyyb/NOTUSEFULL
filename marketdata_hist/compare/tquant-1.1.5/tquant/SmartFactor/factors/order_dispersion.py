import os
from tquant.SmartFactor.HFBaseFactor import HFBaseFactor
import numpy as np


class order_dispersion(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'order_dispersion'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        def get_order_dispersion(arrLike):
            vol_bid = arrLike["BuyOrderQtyQueue"]
            vol_ask = arrLike["SellOrderQtyQueue"]
            price_bid = arrLike['BuyPriceQueue']
            price_ask = arrLike['SellPriceQueue']
            ds1 = (np.sum(np.diff(price_bid, n=1) * vol_bid[0:-1]) + 1e-10) / ((np.sum(vol_bid[0:-1])) + 1e-10)
            ds2 = (np.sum(np.diff(price_ask, n=1) * vol_ask[0:-1]) + 1e-10) / ((np.sum(vol_ask[0:-1])) + 1e-10)
            return (ds1 + ds2) / 2

        df = price_data["tick"]
        res = df.apply(get_order_dispersion, axis=1)
        res.index = df["MDTime"]
        return res


if __name__ == "__main__":
    pxchange_ins = order_dispersion()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)