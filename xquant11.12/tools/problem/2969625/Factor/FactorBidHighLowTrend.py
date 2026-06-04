from System.Factor import Factor
import numpy as np


class FactorBidHighLowTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("high_to_low", [])

    def calculate(self):
        bid_price_list = self.__bid_vwap.getFactorValueList()[-self.__lag:]

        bid_high = np.nanmax(bid_price_list)
        bid_low = np.nanmin(bid_price_list)
        high_to_low = bid_high / bid_low - 1 if bid_low > 1e-6 else 0

        high_to_low_list = self.getIntermediate("high_to_low")
        high_to_low_list.append(high_to_low)
        factor_value = np.nanmean(high_to_low_list[-self.__lag:]) * 1000

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
