import math
from System.Factor import Factor


class FactorTransBuyVolumeDistance(Factor):
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
        fastBidVolume = self.__emaTradeVolumeFast.getLastFactorValue()[0]
        slowBidVolume = self.__emaTradeVolumeSlow.getLastFactorValue()[0]

        if fastBidVolume < 0 or slowBidVolume < 0:
            factorValue = 0
        else:
            factorValue = math.log(fastBidVolume + self.__eps) - math.log(slowBidVolume + self.__eps)

        self._addFactorValue(factorValue)
