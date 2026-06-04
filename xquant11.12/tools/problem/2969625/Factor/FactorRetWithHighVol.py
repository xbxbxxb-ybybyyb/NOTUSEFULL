import numpy as np
from System.Factor import Factor


class FactorRetWithHighVol(Factor):
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
        
        res = sum(np.array(ret[-self.__window:])[np.array(ret_vol[-self.__window:]) > 1])

        if np.isnan(res) or np.isinf(res):
            res = 0

        self._addFactorValue(res)