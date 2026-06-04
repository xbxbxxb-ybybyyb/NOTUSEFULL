from System.Factor import Factor
import numpy as np


class FactorTransVolumeNumSellPressureMZScore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__Lag = self._getParameter("Lag")
        self.__MALag = self._getParameter("MALag")
        self.__NumLag = self._getParameter("NumLag")
        self.__eps = 1e-5

        self.__tradeVolumeNumSum = self._getFactor(
            {
                "ClassName": "TradeVolumeWeightedM",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__MALag,
                    "NumLag": self.__NumLag,
                }
            }
        )
        self._addIntermediate("askVolumeList", [])

    def calculate(self):
        bidVolume, askVolume = self.__tradeVolumeNumSum.getLastFactorValue()
        askVolumeList = self.getIntermediate("askVolumeList")
        askVolumeList.append(askVolume)

        if len(askVolumeList) <= 10:
            factorValue = 0
        else:
            factorValue = -(askVolume - np.nanmean(askVolumeList[-self.__Lag:])) / (np.nanstd(askVolumeList[-self.__Lag:]) + self.__eps)

        self._addFactorValue(factorValue)
