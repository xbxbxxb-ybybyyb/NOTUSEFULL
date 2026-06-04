from System.Factor import Factor
import numpy as np


class FactorBuyDistanceStd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("bid_distance", [])

    def calculate(self):
        bid_price = self._getLastTickData("BidPrice")
        bid_price_adjust = self.__bid_vwap.getLastFactorValue()
        bid_distance = self.getIntermediate("bid_distance")
        bidd = bid_price_adjust / bid_price[0] - 1 if bid_price[0] != 0 else np.nan
        bid_distance.append(bidd)
        bid_distance_sub = bid_distance[-self.__lag:]
        factor_value = np.nanstd(bid_distance_sub) * 1000
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
