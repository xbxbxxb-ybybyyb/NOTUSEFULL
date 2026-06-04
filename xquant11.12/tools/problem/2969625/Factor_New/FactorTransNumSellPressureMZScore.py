from System.Factor import Factor
import numpy as np

class FactorTransNumSellPressureMZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__Lag = self._getParameter("Lag")
        self.__MALag = self._getParameter("MALag")
        self.__NumLag = self._getParameter("NumLag")
        self.__eps = 1e-5

        self.__tradeNumSum = self._getFactor(
            {
                "ClassName": "TradeNumWeightedM",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__MALag,
                    "NumLag": self.__NumLag,
                }
            }
        )
        self._addIntermediate("askNumList", [])

    def calculate(self):
        bidNum, askNum = self.__tradeNumSum.getLastFactorValue()
        askNumList = self.getIntermediate("askNumList")
        askNumList.append(askNum)

        if len(askNumList) <= 10:
            factorValue = 0
        else:
            factorValue = -(askNum - np.nanmean(askNumList[-self.__Lag:])) / (np.nanstd(askNumList[-self.__Lag:]) + self.__eps)

        self._addFactorValue(factorValue)
