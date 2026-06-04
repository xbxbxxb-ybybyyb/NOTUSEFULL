from System.Factor import Factor
import numpy as np


class INFMidPriceReturnsRank(Factor):
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

        n = np.nansum(~np.isnan(rtns_g))
        factorValue = [np.nansum(rtns_g < each) / n for each in rtns_g]

        self._addFactorValue(factorValue)
