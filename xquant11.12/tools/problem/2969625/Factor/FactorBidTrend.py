from System.Factor import Factor
import numpy as np


class FactorBidTrend(Factor):
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
        bid_distance_list = self.getIntermediate("bid_distance")
        bidd = bid_price_adjust / bid_price[0] - 1 if bid_price[0] != 0 else np.nan
        bid_distance_list.append(bidd)
        bid_distance_slice = bid_distance_list[-self.__lag:]
        bid_distance_list_sorted = bid_distance_slice.copy()
        bid_distance_list_sorted.sort()
        if np.nanmax(bid_distance_slice) == np.nanmin(bid_distance_slice):
            factor_value = 0
        else:
            factor_value = np.corrcoef(bid_distance_slice, bid_distance_list_sorted)[0, 1]
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
