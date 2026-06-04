import math
import numpy as np
from System.Factor import Factor


class FactorDistanceToVwapPriceWeighted(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__MASlowLag = self._getParameter("MASlowLag")
        self.__MATinyLag = self._getParameter("MATinyLag")
        self.__MALongLag = self._getParameter("MALongLag")
        self.__MAShortLag = self._getParameter("MAShortLag")

        self.__emaMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__MATinyLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )
        self.__emaVolumeShort = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__MAShortLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )
        self.__emaVolumeLong = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__MALongLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )
        self.__emaVolumeTiny = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__MATinyLag,
                    "OriginalData": {
                        "ClassName": "Volume"
                    }
                }
            }
        )

    def calculate(self):
        historyVolume = self._getAllTickData("Volume")
        historyAmount = self._getAllTickData("Amount")

        shortMAVolume = np.nanmean(historyVolume[-self.__MAShortLag:])
        longMAVolume = np.nanmean(historyVolume[-self.__MALongLag:])
        slowMAVolume = np.nanmean(historyVolume[-self.__MASlowLag:])

        emaMidPrice = self.__emaMidPrice.getLastFactorValue()

        if emaMidPrice <= 0 or shortMAVolume <= 0 or longMAVolume <= 0 or slowMAVolume <= 0:
            factorValue = 0
        else:
            longEMAVolume = self.__emaVolumeLong.getLastFactorValue()
            shortEMAVolume = self.__emaVolumeLong.getLastFactorValue()
            tinyEMAVolume = self.__emaVolumeLong.getLastFactorValue()

            shortVwapPrice = np.nansum(historyAmount[-self.__MAShortLag:]) / np.nansum(historyVolume[-self.__MAShortLag:])
            longVwapPrice = np.nansum(historyAmount[-self.__MALongLag:]) / np.nansum(historyVolume[-self.__MALongLag:])

            if longVwapPrice <= 0 or shortVwapPrice <= 0 or shortEMAVolume <= 0 or tinyEMAVolume <= 0:
                factorValue = 0
            else:
                factorLong = (1000
                              * (1 - emaMidPrice / longVwapPrice)
                              * math.sqrt((longEMAVolume / tinyEMAVolume)
                                          / (longMAVolume / slowMAVolume)))
                factorShort = (1000
                               * (emaMidPrice / shortVwapPrice - 1)
                               * math.sqrt((tinyEMAVolume / shortEMAVolume)
                                           * (shortMAVolume / slowMAVolume)))
                factorValue = (factorLong + factorShort) / 2

        self._addFactorValue(factorValue)
