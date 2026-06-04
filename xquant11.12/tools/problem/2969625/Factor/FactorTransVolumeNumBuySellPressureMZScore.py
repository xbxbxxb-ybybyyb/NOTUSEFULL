from System.Factor import Factor
import numpy as np


class FactorTransVolumeNumBuySellPressureMZScore(Factor):
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
        self._addIntermediate("VolumeList", [])

    def calculate(self):
        bidVolume, askVolume = self.__tradeVolumeNumSum.getLastFactorValue()
        if bidVolume + askVolume > 0:
            value = (bidVolume - askVolume) / (bidVolume + askVolume)
        else:
            value = 0
        VolumeList = self.getIntermediate("VolumeList")
        VolumeList.append(value)

        if len(VolumeList) <= 10:
            factorValue = 0
        else:
            factorValue = (value - np.nanmean(VolumeList[-self.__Lag:])) / (np.nanstd(VolumeList[-self.__Lag:]) + self.__eps)

        self._addFactorValue(factorValue)
