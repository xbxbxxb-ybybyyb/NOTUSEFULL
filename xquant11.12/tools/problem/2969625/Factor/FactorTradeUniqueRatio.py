from System.Factor import Factor
import numpy as np


class FactorTradeUniqueRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__tradeNum = self._getFactor(
            {
                "ClassName": "TradeNum",
                "Parameters": {
                    "Lag": self.__lag,
                }
            }
        )

    def calculate(self):
        bid_unique, ask_unique = self.__tradeNum.getLastFactorValue()
        factor_value = bid_unique / (bid_unique + ask_unique) if bid_unique + ask_unique > 1e-4 else 0.5

        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
