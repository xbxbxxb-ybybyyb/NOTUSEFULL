from System.Factor import Factor
import numpy as np


class FactorPnlMaxERetRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__tickLag = self._getParameter("TickLag")
        self.__indexName = self._getParameter("IndexName")

        self._addIntermediate("ExcessReturnList", [])

    def calculate(self):
        excessRetList = self.getIntermediate("ExcessReturnList")
        price_array = self._getLastNTickData("LastPrice", self.__lag)
        index_price_array = self._getLastNIndexTickData(self.__indexName, "LastPrice", self.__ilag)
        excessRetList.append(self.get_ret(price_array) - self.get_ret(index_price_array))
        excess_ret_list = excessRetList[-self.__tickLag:]

        max_excess_ret_list = np.array([x if x > 0 else 0 for x in excess_ret_list])
        min_excess_ret_list = np.array([x if x < 0 else 0 for x in excess_ret_list])

        if len(min_excess_ret_list) != 0:
            factor_value = (np.nanmean(max_excess_ret_list) - np.nanmean(min_excess_ret_list)) * 1e2
        else:
            factor_value = 0

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)

    @staticmethod
    def get_ret(price_list):
        if len(price_list) == 0:
            return 0.
        else:
            return price_list[-1] / price_list[0] - 1
