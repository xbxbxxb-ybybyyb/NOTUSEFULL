import math
from System.Factor import Factor


class FactorTransPressureVolModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__MALag = self._getParameter("MALag")
        self.__eps = 1e-5

        self.__tradeVolumeWeighted = self._getFactor(
            {
                "ClassName": "TradeVolumeWeighted",
                "Parameters": {
                    "DecayNum": self.__decayNum,
                    "MALag": self.__MALag
                }
            }
        )

    def calculate(self):
        bidVolume, askVolume = self.__tradeVolumeWeighted.getLastFactorValue()

        if bidVolume < 0 or askVolume < 0:
            factorValue = 0
        else:
            factorValue = math.log(bidVolume + self.__eps) - math.log(askVolume + self.__eps)

        self._addFactorValue(factorValue)
