from System.Factor import Factor
import numpy as np


class FactorDistanceToVwapVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dmlag = self._getParameter("DistMinLag")
        self.__svlag = self._getParameter("VolumeShortLag")
        self.__lvlag = self._getParameter("VolumeLongLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "VWAPPrice",
                "Parameters": {
                    "Lag": self.__dmlag
                }
            }
        )

    def calculate(self):
        midPrice = self.__midPrice.getLastFactorValue()
        vwapPrice = self.__vwapPrice.getLastFactorValue()
        volume = self._getLastNTickData("Volume", self.__lvlag * 20)

        if vwapPrice <= 0.01 or midPrice <= 0.01:
            dist = 0
        else:
            dist = midPrice / vwapPrice - 1

        if np.nanmean(volume) == 0:
            volume_pct = 0
        else:
            volume_pct = np.nanmean(volume[-np.nanmin([self.__svlag * 20, len(volume) // 2]):]) / np.nanmean(volume)

        factorValue = - dist * volume_pct

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
