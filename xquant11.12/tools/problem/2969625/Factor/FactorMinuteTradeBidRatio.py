import numpy as np
from System.Factor import Factor


class FactorMinuteTradeBidRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        bidVolumeArray = self._getLastNTickData("BidVolume", self.__lag)
        bidVolumeList = [np.nansum(bidVolume) for bidVolume in bidVolumeArray]
        tickVolume = np.nansum(bidVolumeList)

        volume = self._getLastMinuteData("Volume")

        if tickVolume > 1e-4:
            factorValue = volume / tickVolume
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

