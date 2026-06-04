from System.Factor import Factor
import numpy as np


class FactorMdf200AskAmtPerTrade(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "MdfAskAmtPerTrade",
                "Parameters": {
                    "Coef": 10,
                }
            }
        )

    def calculate(self):
        non_value = self.__askAmtPerTrade.getFactorValueList()
        ema_value = self.ema2(non_value, self.__window)
        fv = 0.
        amt_mean = self.ema2(self._getLastNTickData("Amount", self.__window), self.__window)
        if amt_mean > 1e-6:
            fv = ema_value / amt_mean

        self._addFactorValue(fv)

    def ema2(self, l, length):
        length = min(length, len(l))
        coef = 0.2
        coef_list = [(1 - coef) ** (length - 1)] + [coef * (1 - coef) ** (length - 1 - k) for k in range(1, length)]
        return sum([v * coef_list[i] for i, v in enumerate(l[-length:])])
