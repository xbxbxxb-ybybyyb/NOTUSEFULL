import numpy as np
from System.Factor import Factor


class FactortradeAskBidNumber(Factor):
    def __init__(self, para, factorManager):
        super().__init__(para, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__maLag = self._getParameter("MALag")

        self.__tradeNumWeighted = self._getFactor(
            {
                "ClassName": "TradeNumWeightedEasy",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__maLag
                }
            }
        )

    def calculate(self):
        bidNum, askNum = self.__tradeNumWeighted.getLastFactorValue()
        factorValueList = self.getFactorValueList()

        if len(factorValueList) == 0:  ## Java Code: return False
            value = 0.
        else:
            if bidNum <= 0 or askNum <= 0:
                value = 0.
            else:
                value = np.log(bidNum / askNum)

        self._addFactorValue(value)


