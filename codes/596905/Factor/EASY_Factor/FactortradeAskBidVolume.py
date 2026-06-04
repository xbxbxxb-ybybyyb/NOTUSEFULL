import numpy as np
from System.Factor import Factor


class FactortradeAskBidVolume(Factor):
    def __init__(self, para, factorManager):
        super().__init__(para, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__maLag = self._getParameter("MALag")

        self.__tradeVolumeWeighted = self._getFactor(
            {
                "ClassName": "TradeVolumeWeightedEasy",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__maLag
                }
            }
        )

    def calculate(self):
        bidVolume, askVolume = self.__tradeVolumeWeighted.getLastFactorValue()
        factorValueList = self.getFactorValueList()

        if len(factorValueList) == 0:
            value = 0.
        else:
            if bidVolume <= 0 or askVolume <= 0:
                value = 0.
            else:
                value = np.log(bidVolume / askVolume)

        self._addFactorValue(value)


