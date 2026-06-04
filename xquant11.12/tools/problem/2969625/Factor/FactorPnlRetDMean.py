from System.Factor import Factor
import numpy as np


class FactorPnlRetDMean(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")
        self.__ilag = self._getParameter("IndexLag")
        self.__indexName = self._getParameter("IndexName")

        self._addIntermediate("ReturnList", [])
        self._addIntermediate("IndexReturnList", [])

    def calculate(self):
        retList = self.getIntermediate("ReturnList")
        indexRetList = self.getIntermediate("IndexReturnList")
        price_array = self._getLastNTickData("LastPrice", self.__lag1)
        index_price_array = self._getLastNINFTickData(self.__indexName, "LastPrice", self.__ilag)
        retList.append(self.get_ret(price_array))
        indexRetList.append(self.get_ret(index_price_array))

        ret_list = retList[-self.__lag2:]
        index_ret_list = indexRetList[-self.__lag2:]

        factorValue = (np.nanmean(ret_list) - np.nanmean(index_ret_list)) * 100
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret(price_list):
        if len(price_list) == 0:
            return 0.
        else:
            return price_list[-1] / price_list[0] - 1
