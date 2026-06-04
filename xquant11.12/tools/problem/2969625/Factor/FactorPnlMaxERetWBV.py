from System.Factor import Factor
import numpy as np


class FactorPnlMaxERetWBV(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__ilag = self._getParameter("IndexLag")
        self.__tickLag = self._getParameter("TickLag")
        self.__indexName = self._getParameter("IndexName")

        self._addIntermediate("ExcessReturnList", [])
        self._addIntermediate("VolumeList", [])

    def calculate(self):
        excessRetList = self.getIntermediate("ExcessReturnList")
        price_array = self._getLastNTickData("LastPrice", self.__lag)
        index_price_array = self._getLastNIndexTickData(self.__indexName, "LastPrice", self.__ilag)
        excessRetList.append(self.get_ret(price_array) - self.get_ret(index_price_array))

        volumeList = self.getIntermediate("VolumeList")
        vol_array = self._getLastNTickData("Volume", self.__lag)
        volumeList.append(np.nansum(vol_array))

        excess_ret_list = excessRetList[-self.__tickLag:]
        vol_list = volumeList[-self.__tickLag:]

        mean_excess_ret = np.nanmean(excess_ret_list)
        mean_vol = np.nanmean(vol_list)
        max_excess_ret_list = np.array([x if x > mean_excess_ret else 0 for x in excess_ret_list])
        max_vol_list = np.array([x if x > mean_vol else 0 for x in vol_list])
        if np.nansum(max_vol_list) == 0:
            factorValue = 0.
        else:
            factorValue = np.nansum(max_excess_ret_list * max_vol_list) / np.nansum(max_vol_list) * 100
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret(price_list):
        if price_list[0] is None or price_list[-1] is None or price_list[0] == 0:
            return 0
        else:
            return price_list[-1] / price_list[0] - 1
