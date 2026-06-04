from System.Factor import Factor
import numpy as np


class KLineHighLive(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__origData = self._getParameter("OriginalData")

    def calculate(self):
        data = self._getLastNTodayTickData(self.__origData, self.__lag)
        factorValue = np.nanmax(data)
        self._addFactorValue(factorValue)
