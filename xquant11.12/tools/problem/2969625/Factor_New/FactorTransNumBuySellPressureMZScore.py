from System.Factor import Factor
import numpy as np


class FactorTransNumBuySellPressureMZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__Lag = self._getParameter("Lag")
        self.__MALag = self._getParameter("MALag")
        self.__NumLag = self._getParameter("NumLag")
        self.__eps = 1e-5

        self.__tradeVolumeNumSum = self._getFactor(
            {
                "ClassName": "TradeNumWeightedM",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__MALag,
                    "NumLag": self.__NumLag,
                }
            }
        )
        self._addIntermediate("NumList", [])

    def calculate(self):
        bidNum, askNum = self.__tradeVolumeNumSum.getLastFactorValue()
        if bidNum + askNum > 0:
            value = (bidNum - askNum) / (bidNum + askNum)
        else:
            value = 0
        NumList = self.getIntermediate("NumList")
        NumList.append(value)

        if len(NumList) <= 10:
            factorValue = 0
        else:
            factorValue = (value - np.nanmean(NumList[-self.__Lag:])) / (np.nanstd(NumList[-self.__Lag:]) + self.__eps)

        self._addFactorValue(factorValue)
