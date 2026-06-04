from System.Factor import Factor
import numpy as np


class FactorBidMaxMin(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )

    def calculate(self):
        bid_price_list = self.__bid_vwap.getFactorValueList()[-self.__lag:][::-1]
        bid_price_max = np.nanmax(bid_price_list)
        bid_price_min = np.nanmin(bid_price_list)
        max_pos = np.argmax(bid_price_list)
        min_pos = np.argmin(bid_price_list)

        if max_pos > min_pos and bid_price_min > 1e-6:
            factor_value = (bid_price_max / bid_price_min - 1) * 1000
        elif max_pos < min_pos and bid_price_max > 1e-6:
            factor_value = (bid_price_min / bid_price_max - 1) * 1000
        else:
            factor_value = 0
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
