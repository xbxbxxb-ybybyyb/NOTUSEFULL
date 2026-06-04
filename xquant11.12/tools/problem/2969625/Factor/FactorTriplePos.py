from System.Factor import Factor
import numpy as np


class FactorTriplePos(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndIndexLag")
        self.__wlag = self._getParameter("WideIndexLag")
        self.__tickLag = self._getParameter("TickLag")
        self.__wIndexName = self._getParameter("WideIndexName")
        self.__indIndexName = self._getParameter("IndIndexName")

        self._addIntermediate("ReturnStock", [])
        self._addIntermediate("ReturnIndustry", [])
        self._addIntermediate("ReturnIndex", [])

    def calculate(self):
        retStockList = self.getIntermediate("ReturnStock")
        retIndustryList = self.getIntermediate("ReturnIndustry")
        retIndexList = self.getIntermediate("ReturnIndex")

        price_array = self._getLastNTickData("LastPrice", self.__lag)
        index_price_array = self._getLastNIndexTickData(self.__wIndexName, "LastPrice", self.__wlag)
        industry_price_array = self._getLastNINFTickData(self.__indIndexName, "LastPrice", self.__ilag)

        retStockList.append(self.get_ret(price_array))
        retIndustryList.append(self.get_ret(industry_price_array))
        retIndexList.append(self.get_ret(index_price_array))

        ret_stock = retStockList[-self.__tickLag:]
        ret_industry = retIndustryList[-self.__tickLag:]
        ret_index = retIndexList[-self.__tickLag:]

        ret_stock_mean = np.nanmean(ret_stock)
        ret_industry_mean = np.nanmean(ret_industry)
        ret_index_mean = np.nanmean(ret_index)
        if 1 + ret_index_mean == 0:
            factor_value = 0.
        else:
            factor_value = (ret_stock_mean - ret_industry_mean) * (1 + ret_industry_mean) / (1 + ret_index_mean) * 1000

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)

    @staticmethod
    def get_ret(price_list):
        if len(price_list) == 0:
            return 0.
        else:
            return price_list[-1] / price_list[0] - 1
