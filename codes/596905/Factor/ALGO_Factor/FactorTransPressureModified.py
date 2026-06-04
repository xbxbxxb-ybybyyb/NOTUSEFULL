import math
from System.Factor import Factor


class FactorTransPressureModified(Factor):
    def __init__(self, para, factorManager):
        super().__init__(para, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__MALag = self._getParameter("MALag")
        self.__eps = 1e-5

        self.__tradeNumWeighted = self._getFactor(
            {
                "ClassName": "TradeNumWeighted",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__MALag
                }
            }
        )

    def calculate(self):
        bidNum, askNum = self.__tradeNumWeighted.getLastFactorValue()

        if bidNum < 0 or askNum < 0:
            factorValue = 0
        else:
            factorValue = math.log(bidNum + self.__eps) - math.log(askNum + self.__eps)

        self._addFactorValue(factorValue)
