from System.Factor import Factor
import numpy as np


class FactorMdfBidDistanceMulRet(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwapAdj",
                "Parameters": {
                    "percentile": 0.005
                }

            }
        )
        self._addIntermediate("bid_distance", [])

    def calculate(self):
        bid_price0 = self._getLastTickData("BidPrice")[0]
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        bid_distance = self.getIntermediate("bid_distance")
        bidd = bid_price_adjust[-1] / bid_price0 - 1 if bid_price0 > 1e-6 else np.nan
        bid_distance.append(bidd)
        bid_distance_sub = bid_distance[-self.__lag:]
        bid_price_adjust_max = np.nanmax(bid_price_adjust)
        bid_price_adjust_min = np.nanmin(bid_price_adjust)
        if bid_price_adjust_max > 0 and bid_price0 > 1e-6:
            f1 = (bid_price_adjust_max / bid_price0 - 1) + (bid_price_adjust_min / bid_price0 - 1)
            factor_value = np.nanmax(bid_distance_sub) * f1 * 1e6
        else:
            lastv = self.getLastFactorValue()
            if lastv is not None:
                factor_value = lastv
            else:
                factor_value = 0

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
