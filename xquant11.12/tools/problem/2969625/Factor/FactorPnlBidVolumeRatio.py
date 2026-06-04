from System.Factor import Factor
import numpy as np


class FactorPnlBidVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):
        factorValue = self._getLastINFTickData(self.__index_name, "BidDelegateVolumeRatio")

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
