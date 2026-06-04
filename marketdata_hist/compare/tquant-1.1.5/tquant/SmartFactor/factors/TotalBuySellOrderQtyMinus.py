# -*- coding:utf-8 -*-
import os
import numpy as np
from tquant.SmartFactor.HFBaseFactor import HFBaseFactor
import time

class TotalBuySellOrderQtyMinus(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'TotalBuySellOrderQtyMinus'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        df = price_data["tick"]
        """
            净委买卖量差
            """
        res = df.apply(
            lambda x: np.sum(x['BuyOrderQtyQueue']) - np.sum(x['SellOrderQtyQueue']), axis=1)
        res.index = df["MDTime"]
        return res

if __name__ == "__main__":
    pxchange_ins = TotalBuySellOrderQtyMinus()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)

