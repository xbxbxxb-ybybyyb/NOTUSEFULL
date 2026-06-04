from System.Factor import Factor
import numpy as np

class FactorLongStrength_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwapZT"
            }
        )

    def calculate(self):
        bid_price = self._getLastTickData("BidPrice")[0]
        ask_price_adjust = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        long_strength = 1 - np.nanmean(ask_price_adjust) / bid_price if bid_price != 0 else 0
        factor_value = long_strength * 100
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
