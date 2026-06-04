# -*- coding:utf-8 -*-

import os
from tquant.SmartFactor.HFBaseFactor import HFBaseFactor

class pxchange0(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'pxchange0'
    security_type = 'fund'
    security_pool = ['159958.SZ']
    depend_factor = []
    #custom_params = {"interval_seconds": 60, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        #interval_seconds = custom_params["interval_seconds"]
        #tick_interval_seconds = custom_params["tick_interval_seconds"]
        #n_tick = interval_seconds // tick_interval_seconds
        n_tick = 20
        #price_data = price_data["tick"]
        price_data["value"] = price_data['LastPx'].diff(n_tick) / price_data['LastPx'].shift(n_tick) * 1000
        res = price_data["value"]
        res.index = price_data["MDTime"]

        return res


if __name__ == "__main__":
    pxchange_ins = pxchange()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)

