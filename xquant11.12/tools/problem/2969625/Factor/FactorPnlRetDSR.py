from System.Factor import Factor
import numpy as np


class FactorPnlRetDSR(Factor):
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

        excess_ret_array = np.array(ret_list) - np.array(index_ret_list)
        factorValue = np.nanmean(excess_ret_array) / np.nanstd(excess_ret_array) if np.nanstd(excess_ret_array) > 1e-6 else 0
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret(price_list):
        if len(price_list) == 0:
            return 0.
        else:
            return price_list[-1] / price_list[0] - 1
