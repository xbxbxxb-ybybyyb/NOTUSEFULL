from System.Factor import Factor
import numpy as np


class FactorPnlRelativeVolumeSum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__smlag = self._getParameter("ShortMinLag")
        self.__lmlag = self._getParameter("LongMinLag")
        self.__tnum = self._getParameter("TicksPerMin")
        self.__itnum = self._getParameter("ITicksPerMin")
        self.__index_name = self._getParameter("IndexName")

    def calculate(self):

        vol = self._getLastNTickData("Volume", self.__lmlag * self.__tnum)
        vol_g = self._getLastNINFTickData(self.__index_name, "Volume", self.__lmlag * self.__itnum)

        lag = np.nanmin([self.__smlag * self.__tnum, len(vol) // 3])
        vol_pct = np.nanmean(vol[-lag:]) / np.nanmean(vol) if np.nanmean(vol) != 0 else 1
        lag_g = np.nanmin([self.__smlag * self.__itnum, len(vol_g) // 3])
        vol_pct_g = np.nanmean(vol_g[-lag_g:]) / np.nanmean(vol_g) if np.nanmean(vol_g) != 0 and len(vol_g) > 0 else 1

        factorValue = vol_pct + vol_pct_g

        if np.isnan(factorValue):
            factorValue = 2

        self._addFactorValue(factorValue)
