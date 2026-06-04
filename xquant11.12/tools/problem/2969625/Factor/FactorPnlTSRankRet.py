from System.Factor import Factor
import numpy as np


class FactorPnlTSRankRet(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__dlag = self._getParameter("DayLag")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):
        stock_price = self._getLastNTickData("LastPrice", self.__lag)
        ts_rank_g = self._getLastINFTickData(self.__index_name, "LastPriceTsRankMean_{}".format(self.__dlag))
        ts_rank_g = 0. if np.isnan(ts_rank_g) else ts_rank_g
        stock_ret = stock_price[-1] / stock_price[0] - 1
        factorValue = np.abs(stock_ret) * ts_rank_g * 1e2

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
