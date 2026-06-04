from System.Factor import Factor
import numpy as np


class FactorPnlSkew(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__index_name = self._getParameter("IndexName")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )

    def calculate(self):
        mid_price = self.__midPrice.getFactorValueList()[-self.__lag:]
        ret_stock = mid_price[-1] / mid_price[0] - 1

        ret_group_skew = self._getLastINFTickData(self.__index_name, "MidPriceReturnsSkew_{}".format(self.__ilag))
        ret_group_skew = 0. if np.isnan(ret_group_skew) else ret_group_skew

        factorValue = ret_group_skew * ret_stock * 1e2

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

