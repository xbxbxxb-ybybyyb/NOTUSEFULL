from System.Factor import Factor
import numpy as np


class FactorBidPerVal(Factor):
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

    def calculate(self):
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        ask_price_adjust = self.__ask_vwap.getFactorValueList()[-self.__lag:]
        bid_p10 = np.nanpercentile(bid_price_adjust, 10)
        factor_value = ask_price_adjust[0] / bid_p10 - 1 if bid_p10 > 1e-3 else 0
        factor_value *= 100
        self._addFactorValue(factor_value)
