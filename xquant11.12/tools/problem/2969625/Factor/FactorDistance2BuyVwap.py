from System.Factor import Factor
import numpy as np


class FactorDistance2BuyVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("res_value", [])

    def calculate(self):
        bid_price_adjust = self.__bid_vwap.getLastFactorValue()
        bid_price_mean = np.nanmean(self._getLastTickData("BidPrice"))
        res_value = self.getIntermediate("res_value")
        if bid_price_mean != 0:
            res_value.append((bid_price_adjust / bid_price_mean - 1) * 1000)
        else:
            res_value.append(0.)

        factor_value = np.nanmean(res_value[-self.__lag:])

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
