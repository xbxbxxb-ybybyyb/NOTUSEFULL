from System.Factor import Factor
import numpy as np


class FactorMdfShortStrength(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap",
            }
        )

    def calculate(self):
        ask_price = self._getLastTickData("AskPrice")[0]
        bid_price = self._getLastTickData("BidPrice")[0]
        mid_price = (ask_price + bid_price) / 2
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        short_strength = np.nanmean(bid_price_adjust) / mid_price - 1 if mid_price > 1e-6 else 0.
        factor_value = short_strength * 1000
        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
