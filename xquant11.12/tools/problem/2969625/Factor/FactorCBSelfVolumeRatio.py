from System.Factor import Factor
import numpy as np


class FactorCBSelfVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")
        self.__index_name = self._getConfig("IndexGroup")[0]

    def calculate(self):

        vol_all = self._getAllTodayTickData("Volume")
        vol = vol_all[-10 * 20:]
        vol_index = self._getLastNTodayIndexTickData(self.__index_name, "Volume", 10 * 12)
        dvol = self._getLastNHistoricalDailyData("Volume", self.__dlag)
        dvol_index = self._getLastNHistoricalIndexDailyData(self.__index_name, "Volume", self.__dlag)
        dvol_ratio_rlt = np.nanmean(dvol) / np.nanmean(dvol_index) if np.nanmean(dvol_index) != 0 else 1
        vol_ratio_rlt = np.nanmean(vol) / np.nanmean(vol_index) if np.nanmean(vol_index) != 0 else 1
        w = [1, 2, 5, 10]

        if len(vol_index) > 0:
            vol_crt_mean = np.nanmean(vol_all)
            if vol_crt_mean != 0:
                vol_ratio_abs = np.dot([np.nanmean(vol[-each * 20:]) / vol_crt_mean for each in w], w[::-1]) / np.nansum(w)
                if dvol_ratio_rlt != 0:
                    factorValue = vol_ratio_abs * vol_ratio_rlt / dvol_ratio_rlt
                else:  # 前面若干天完全没有交易
                    factorValue = vol_ratio_abs
            else:  # 当天完全没有交易
                factorValue = 0
        else:  # 第一个Tick可能取不出对应的指数
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
