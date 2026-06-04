import numpy as np
import math
from System.Factor import Factor


class FactorNetDriveForceRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")

        self.__driveForce = self._getFactor(
            {
                "ClassName": "OrderDriveForce",
                "Parameters": {
                    "Level": self.__level
                }
            }
        )
        self._addIntermediate("emaAskVolumeList", [])
        self._addIntermediate("emaBidVolumeList", [])

    def calculate(self):

        askVolume = self._getLastTickData("AskVolume")
        bidVolume = self._getLastTickData("BidVolume")

        askVolumeAve = self.__get_average_volume(askVolume)
        emaAskVolumeList = self.getIntermediate("emaAskVolumeList")
        emaAskVolumeAve = self._EMA_calculate(askVolumeAve, emaAskVolumeList, len(emaAskVolumeList))
        emaAskVolumeList.append(emaAskVolumeAve)

        bidVolumeAve = self.__get_average_volume(bidVolume)
        emaBidVolumeList = self.getIntermediate("emaBidVolumeList")
        emaBidVolumeAve = self._EMA_calculate(bidVolumeAve, emaBidVolumeList, len(emaBidVolumeList))
        emaBidVolumeList.append(emaBidVolumeAve)

        bidDriveForce, askDriveForce = self.__driveForce.getLastFactorValue()

        if emaAskVolumeAve != 0 and emaBidVolumeAve != 0:
            factorValue = bidDriveForce / emaBidVolumeAve - askDriveForce / emaAskVolumeAve
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    def __get_average_volume(self, volumeArray):

        if 0 in volumeArray:
            volumeArrayTemp = volumeArray[np.nonzero(volumeArray)]
            if len(volumeArrayTemp) == 0:
                volumeArrayAve = 0.
            else:
                volumeArrayAve = np.nanmean(volumeArrayTemp)
        else:
            volumeArrayAve = np.nanmean(volumeArray)
        if math.isnan(volumeArrayAve):
            volumeArrayAve = 0.

        return volumeArrayAve

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])