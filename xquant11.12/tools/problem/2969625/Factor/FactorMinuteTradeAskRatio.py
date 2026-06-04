import numpy as np
from System.Factor import Factor


class FactorMinuteTradeAskRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        askVolumeArray = self._getLastNTickData("AskVolume", self.__lag)
        askVolumeList = [np.nansum(askVolume) for askVolume in askVolumeArray]
        tickVolume = np.nansum(askVolumeList)

        volume = self._getLastMinuteData("Volume")

        if tickVolume > 1e-4:
            factorValue = volume / tickVolume
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

