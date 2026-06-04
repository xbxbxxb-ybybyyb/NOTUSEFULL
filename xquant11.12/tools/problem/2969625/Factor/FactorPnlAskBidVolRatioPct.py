from System.Factor import Factor
import numpy as np


class FactorPnlAskBidVolRatioPct(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):

        avr = self._getLastINFTickData(self.__index_name, "TransAskVolumeRank")
        bvr = self._getLastINFTickData(self.__index_name, "TransBidVolumeRank")
        avr = 0 if np.isnan(avr) else avr
        bvr = 0 if np.isnan(bvr) else bvr
        factorValue = bvr - avr

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
