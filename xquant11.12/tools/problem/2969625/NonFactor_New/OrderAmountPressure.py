import math
from System.Factor import Factor


class OrderAmountPressure(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__numOrderMax = self._getParameter("NumOrderMax")
        self.__numOrderMin = self._getParameter("NumOrderMin")
        self.__weightDecay = self._getParameter("WeightDecay")

        self.__aveOrderAmountWeighted = self._getFactor(
            {
                "ClassName": "AveOrderAmountWeightedM",
                "Parameters": {
                    "NumOrderMax": self.__numOrderMax,
                    "NumOrderMin": self.__numOrderMin,
                    "WeightDecay": self.__weightDecay
                }
            }
        )

    def calculate(self):
        aveAmountBid, aveAmountAsk = self.__aveOrderAmountWeighted.getLastFactorValue()

        if aveAmountBid == 0 and aveAmountAsk == 0:
            factorValue = 0
        else:
            factorValue = (aveAmountBid - aveAmountAsk) / (aveAmountBid + aveAmountAsk)

        self._addFactorValue(factorValue)
