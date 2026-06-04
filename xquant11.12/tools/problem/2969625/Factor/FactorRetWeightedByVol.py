from System.Factor import Factor
import numpy as np


class FactorRetWeightedByVol(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

        self._addIntermediate("ReturnList", [])
        self._addIntermediate("VolumeList", [])

    def calculate(self):
        retList = self.getIntermediate("ReturnList")
        volumeList = self.getIntermediate("VolumeList")
        price_array = self._getLastNTickData("LastPrice", self.__lag1)
        vol_array = self._getLastNTickData("Volume", self.__lag1)
        retList.append(self.get_ret(price_array))
        volumeList.append(np.nansum(vol_array))

        ret_list = retList[-self.__lag2:]
        vol_list = volumeList[-self.__lag2:]

        if np.nansum(vol_list) > 0:
            factorValue = np.nansum(np.array(ret_list) * np.array(vol_list)) / np.nansum(vol_list)
        else:
            factorValue = 0
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def get_ret(price_list):
        if price_list[0] is None or price_list[-1] is None or price_list[0] == 0:
            return 0
        else:
            return price_list[-1] / price_list[0] - 1
