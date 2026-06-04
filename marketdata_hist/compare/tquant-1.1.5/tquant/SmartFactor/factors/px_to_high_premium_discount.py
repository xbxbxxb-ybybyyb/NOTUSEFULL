import os
import numpy as np
from tquant.SmartFactor.HFBaseFactor import HFBaseFactor


class px_to_high_premium_discount(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'px_to_high_premium_discount'
    security_type = 'fund'
    security_pool = ['159915.SZ']
    depend_factor = []
    custom_params = {"interval_seconds": 60, "tick_interval_seconds": 3}

    def calc(self, price_data, factor_data, custom_params):
        """
        实时相对日内最高价的折溢价率
        """
        df = price_data["tick"]
        res = np.log(
            df['LastPx'] / df['HighPx']) * 1000
        res.index = df["MDTime"]
        return res


if __name__ == "__main__":
    pxchange_ins = px_to_high_premium_discount()
    print(pxchange_ins.factor_name)
    res = pxchange_ins.run_hfre_factor_value("20201102", "20201103")
    print(res)