from System.Factor import Factor
import numpy as np


class FactorPnlRetSum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__index_name = self._getParameter("IndexName")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        mid_price = self.__midPrice.getFactorValueList()[-self.__lag:]
        ret_stock = mid_price[-1] / mid_price[0] - 1

        lastp_group = self._getLastNINFTickData(self.__index_name, "LastPrice", self.__ilag)
        ret_group = lastp_group[-1] / lastp_group[0] - 1 if len(lastp_group) > 0 else 0.

        factorValue = (ret_group + ret_stock) * 10

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

