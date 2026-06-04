from System.Factor import Factor
import numpy as np


class FactorPnlAskVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):
        factorValue = self._getLastINFTickData(self.__index_name, "AskDelegateVolumeRatio")

        if np.isnan(factorValue):  # 日频成交量为0/第一个Tick
            factorValue = 0

        self._addFactorValue(factorValue)
