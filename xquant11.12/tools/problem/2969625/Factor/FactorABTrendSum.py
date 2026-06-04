from System.Factor import Factor
import numpy as np


class FactorABTrendSum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("ab_sum", [])

    def calculate(self):
        ask_price = self._getLastTickData("AskPrice")
        ask_price_adjust = self.__ask_vwap.getLastFactorValue()
        bid_price = self._getLastTickData("BidPrice")
        bid_price_adjust = self.__bid_vwap.getLastFactorValue()

        ab_sum = self.getIntermediate("ab_sum")
        if ask_price[0] == 0:
            ab_sum.append(bid_price_adjust / bid_price[0] - 1)
        elif bid_price[0] == 0:
            ab_sum.append(ask_price_adjust / ask_price[0] - 1)
        else:
            ab_sum.append(ask_price_adjust / ask_price[0] + bid_price_adjust / bid_price[0] - 2)
        ab_sum_slice = ab_sum[-self.__lag:]
        ab_sum_sorted = ab_sum_slice.copy()
        ab_sum_sorted.sort()
        if np.nanmax(ab_sum_slice) == np.nanmin(ab_sum_slice):
            factor_value = 0
        else:
            factor_value = np.corrcoef(ab_sum_slice, ab_sum_sorted)[0, 1]
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
