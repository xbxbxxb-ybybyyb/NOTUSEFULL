from System.Factor import Factor
import numpy as np


class FactorLongStrength(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )

    def calculate(self):
        bid_price = self._getLastTickData("BidPrice")[0]
        ask_price_adjust = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        long_strength = np.nanmean(ask_price_adjust) / bid_price - 1 if bid_price != 0 else 0
        factor_value = long_strength * 100

        self._addFactorValue(factor_value)
