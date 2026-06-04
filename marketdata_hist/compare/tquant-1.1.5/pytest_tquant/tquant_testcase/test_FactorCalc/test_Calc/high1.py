from tquant.SmartFactor.HFBaseFactor import HFBaseFactor
import numpy as np


class high1(HFBaseFactor):
    factor_type = "TICK"
    factor_name = 'high1'
    security_type = 'fund'
    security_pool = ["515520.SH", "159968.SZ", "511660.SH"]

    def calc(self, price_data, factor_data, custom_params):
        res = np.log(price_data['LastPx'] / price_data['PreClosePx']) * 1000
        res.index = price_data["MDTime"]
        return res



