from System.Factor import Factor
import numpy as np


class FactorBidDistance(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("BidDistanceList", [])

    def calculate(self):
        bidDistanceList = self.getIntermediate("BidDistanceList")
        bid_price = self._getLastTickData("BidPrice")
        bid_price_adjust = self.__bid_vwap.getLastFactorValue()
        bidd = bid_price_adjust / bid_price[0] - 1 if bid_price[0] != 0 else np.nan
        bidDistanceList.append(bidd)
        factor_value = np.nanmean(bidDistanceList[-self.__lag:]) * 1000
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
