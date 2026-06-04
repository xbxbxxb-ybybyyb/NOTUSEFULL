import numpy as np
from System.Factor import Factor


class FactorRetWithHighVolM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__relWindow = self._getParameter("RelWindow")

        self._addIntermediate("ReturnList", [])
        self._addIntermediate("VolumeRatioList", [])
        
    def calculate(self):
        ret = self.getIntermediate("ReturnList")
        ret_vol = self.getIntermediate("VolumeRatioList")
        vol = self._getLastNTickData('Volume', self.__relWindow)
        price = self._getLastNTickData('LastPrice', 2)
        
        ret_vol.append(np.nanmean(vol[-5:]) / np.nanmean(vol) if np.nanmean(vol) != 0 else 1)
        ret.append((price[-1] / price[0] - 1) * 100)
        if len(np.array(ret[-self.__window:])[np.array(ret_vol[-self.__window:]) > 1]) == 0:
            res = 0
        else:
            res = sum(np.array(ret[-self.__window:])[np.array(ret_vol[-self.__window:]) > 1])

        res = res * (-1)
        self._addFactorValue(res)