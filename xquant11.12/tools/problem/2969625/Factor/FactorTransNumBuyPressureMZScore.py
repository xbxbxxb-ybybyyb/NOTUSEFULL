from System.Factor import Factor
import numpy as np

class FactorTransNumBuyPressureMZScore(Factor):
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
        self._addIntermediate("bidNumList", [])

    def calculate(self):
        bidNum, askNum = self.__tradeNumSum.getLastFactorValue()
        bidNumList = self.getIntermediate("bidNumList")
        bidNumList.append(bidNum)

        if len(bidNumList) <= 20:
            factorValue = 0
        else:
            factorValue = (bidNum - np.nanmean(bidNumList[-self.__Lag:])) / (np.nanstd(bidNumList[-self.__Lag:]) + self.__eps)

        self._addFactorValue(factorValue)
