import math
from System.Factor import Factor


class FactorVolumeMagnificationModified(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__fastLag = self._getParameter("FastLag")
        self.__slowLag = self._getParameter("SlowLag")
        self.__eps = 1e-5

        self.__emaVolumeFast = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__fastLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )
        self.__emaVolumeSlow = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__slowLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )

    def calculate(self):
        fastVolume = self.__emaVolumeFast.getLastFactorValue()
        slowVolume = self.__emaVolumeSlow.getLastFactorValue()

        if fastVolume < 0 or slowVolume < 0:
            factorValue = 0
        else:
            factorValue = math.log((fastVolume + self.__eps) / (slowVolume + self.__eps))

        self._addFactorValue(factorValue)
