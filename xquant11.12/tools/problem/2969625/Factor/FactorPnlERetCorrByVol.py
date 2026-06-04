from System.Factor import Factor
import numpy as np


class FactorPnlERetCorrByVol(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__ilag = self._getParameter("IndexLag")
        self.__lag2 = self._getParameter("Lag2")
        self.__indexName = self._getParameter("IndexName")

        self._addIntermediate("ReturnList", [])
        self._addIntermediate("IndexReturnList", [])

    def calculate(self):
        retList = self.getIntermediate("ReturnList")
        indexRetList = self.getIntermediate("IndexReturnList")
        price_array = self._getLastNTickData("LastPrice", self.__lag1)
        vol_array = self._getLastNTickData("Volume", self.__lag1)
        index_price_array = self._getLastNINFTickData(self.__indexName, "LastPrice", self.__ilag)
        index_vol_array = self._getLastNINFTickData(self.__indexName, "Volume", self.__ilag)
        retList.append(self.get_ret_and_vol(price_array, vol_array))
        indexRetList.append(self.get_ret_and_vol(index_price_array, index_vol_array))

        ret_vol = np.array(retList[-self.__lag2:])
        index_ret_vol = np.array(indexRetList[-self.__lag2:])

        if np.nansum(ret_vol[:, 1]) == 0 or np.nansum(index_ret_vol[:, 1]) == 0:
            factorValue = 0
        else:
            ret_by_vol_stock = np.nansum(ret_vol[:, 0] * ret_vol[:, 1]) / np.nansum(ret_vol[:, 1])
            ret_by_vol_index = np.nansum(index_ret_vol[:, 0] * index_ret_vol[:, 1]) / np.nansum(index_ret_vol[:, 1])
            factorValue = (ret_by_vol_stock - ret_by_vol_index) * 1000
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret_and_vol(price_list, vol_list):
        if (len(price_list) == 0) or (len(vol_list) == 0):
            return 0., 0.
        else:
            ret = price_list[-1] / price_list[0] - 1
            vol = np.nansum(vol_list)
        return ret, vol
