from System.Factor import Factor
import numpy as np


class FactorPnlERetWBV(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__tickLag = self._getParameter("TickLag")
        self.__indexName = self._getParameter("IndexName")

        self._addIntermediate("ExcessRetList", [])
        self._addIntermediate("VolumeList", [])

    def calculate(self):
        excessRetList = self.getIntermediate("ExcessRetList")
        volumeList = self.getIntermediate("VolumeList")
        price_array = self._getLastNTickData("LastPrice", self.__lag)
        vol_array = self._getLastNTickData("Volume", self.__lag)
        index_price_array = self._getLastNINFTickData(self.__indexName, "LastPrice", self.__ilag)

        excessRetList.append(self.get_ret(price_array) - self.get_ret(index_price_array))
        volumeList.append(np.nansum(vol_array))

        excess_ret_list = excessRetList[-self.__tickLag:]
        vol_list = volumeList[-self.__tickLag:]
        if np.nansum(vol_list) == 0:
            factorValue = 0.
        else:
            factorValue = np.nansum(np.array(excess_ret_list) * np.array(vol_list)) / np.nansum(vol_list) * 100
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret(price_list):
        if len(price_list) == 0:
            return 0.
        else:
            return price_list[-1] / price_list[0] - 1
