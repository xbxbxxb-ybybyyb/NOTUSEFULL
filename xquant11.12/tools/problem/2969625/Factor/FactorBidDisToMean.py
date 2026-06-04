from System.Factor import Factor
import numpy as np


class FactorBidDisToMean(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )

    def calculate(self):
        bid_price_list = self.__bid_vwap.getFactorValueList()[-self.__lag:]

        length = len(bid_price_list)
        adj_ratio = np.arange(length, 0, -1) / np.nansum(np.arange(length, 0, -1))
        bid_price_mean = np.nansum(bid_price_list * adj_ratio[:length])

        if bid_price_mean > 1e-6:
            factor_value = (bid_price_list[-1] / bid_price_mean - 1) * 1000
        else:
            factor_value = 0
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
