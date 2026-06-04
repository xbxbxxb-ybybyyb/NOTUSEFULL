from System.Factor import Factor
import numpy as np


class FactorPnlRankMulVol(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")
        self.__ilag = self._getParameter("IndexLag")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):

        rank = self._getLastINFTickData(self.__index_name, "MidPriceReturnsRank_{}".format(self.__ilag))
        rank = 0. if np.isnan(rank) else rank
        vol_list = self._getLastNTickData("Volume", self.__lag1)

        if np.nanmean(vol_list) != 0:
            vol_pct = np.nanmean(vol_list[-self.__lag2:]) / np.nanmean(vol_list)
        else:
            vol_pct = 1

        factorValue = rank * vol_pct

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
