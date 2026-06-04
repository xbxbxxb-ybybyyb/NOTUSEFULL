import math
from System.Factor import Factor


class FactorTransSellVolumeDistance(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MALag = self._getParameter("MALag")
        self.__MAFastLag = self._getParameter("MAFastLag")
        self.__MASlowLag = self._getParameter("MASlowLag")
        self.__decayNum = self._getParameter("DecayNum")
        self.__eps = 1e-5

        self.__emaTradeVolumeFast = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__MAFastLag,
                    "OriginalData": {
                        "ClassName": "TradeVolumeWeighted",
                        "Parameters": {
                            "MALag": self.__MALag,
                            "DecayNum": self.__decayNum
                        }
                    }
                }
            }
        )
        self.__emaTradeVolumeSlow = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__MASlowLag,
                    "OriginalData": {
                        "ClassName": "TradeVolumeWeighted",
                        "Parameters": {
                            "MALag": self.__MALag,
                            "DecayNum": self.__decayNum
                        }
                    }
                }
            }
        )

    def calculate(self):
        fastAskVolume = self.__emaTradeVolumeFast.getLastFactorValue()[1]
        slowAskVolume = self.__emaTradeVolumeSlow.getLastFactorValue()[1]

        if fastAskVolume < 0 or slowAskVolume < 0:
            factorValue = 0
        else:
            factorValue = math.log(fastAskVolume + self.__eps) - math.log(slowAskVolume + self.__eps)

        self._addFactorValue(factorValue)
