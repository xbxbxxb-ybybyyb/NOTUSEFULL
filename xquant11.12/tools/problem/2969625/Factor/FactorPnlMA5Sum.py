from System.Factor import Factor
import numpy as np


class FactorPnlMA5Sum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")
        self.__dlag = self._getParameter("DayLag")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):
        # lag1 < lag2
        ma_ratio = self._getLastINFTickData(self.__index_name, "LastPriceRatioWeighted_{}".format(self.__dlag))
        ma_ratio = 0. if np.isnan(ma_ratio) else ma_ratio

        stock_vol = self._getLastNTickData("Volume", self.__lag2)
        lag1 = np.nanmin([self.__lag1, len(stock_vol) // 2])
        vol_ratio = np.nanmean(stock_vol[-lag1:]) / np.nanmean(stock_vol) if np.nanmean(stock_vol) != 0 else 1

        factorValue = ma_ratio * vol_ratio

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
