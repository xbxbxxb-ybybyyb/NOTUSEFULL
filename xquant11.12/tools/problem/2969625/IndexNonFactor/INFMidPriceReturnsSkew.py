from System.Factor import Factor
import numpy as np


class INFMidPriceReturnsSkew(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__index_name = self._getParameter("IndexName")

        self.__midPriceG = self._getFactor(
            {
                "ClassName": "MidPriceForStockGroup",
                "StockGroup": self.__index_name,
                "DataTypeCS": "Tick"
            }
        )

    def calculate(self):

        midp_g = self.__midPriceG.getFactorValueList()[-self.__lag:]
        rtns_g = np.divide(midp_g[-1], midp_g[0]) - 1

        factorValue = self.__compute_skew(rtns_g)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_skew(arr):
        if len(arr) <= 1:
            return np.nan
        else:
            arr_mean = np.nanmean(arr)
            arr_std = np.nanstd(arr)
            three = np.nanmean((arr - arr_mean) ** 3)
            skew = three / arr_std ** 3 if arr_std != 0 else 0
            return skew
