from System.Factor import Factor
import numpy as np


class FactorPVCoordRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__transVwap = self._getFactor(
            {
                "ClassName": "TransVwap",
                "SplitAdjusted": True,
                "Parameters": {
                    "Direction": "Both",
                }
            }
        )
        self.__hisLastP = None
        self.__hisVolume = None
        self._addIntermediate("transVwap", [])
        self._addIntermediate("Volume", [])

    def calculate(self):

        tvwap = self.getIntermediate("transVwap")
        vol = self.getIntermediate("Volume")
        tsp = self._getAllTodayTickData("Timestamp")
        if len(tsp) == 1:
            lastph = self._getLastNHistoricalTickData("LastPrice", self.__lag)  # 实盘不方便加载历史逐笔，遂暂用历史暂用LastPrice代替
            volh = self._getLastNHistoricalTickData("Volume", self.__lag)
            idx = ~np.isnan(lastph)
            lastph = list(np.array(lastph)[idx])
            volh = list(np.array(volh)[idx])
            self.__hisLastP = lastph
            self.__hisVolume = volh

        tvwapn = self.__transVwap.getLastFactorValue()
        voln = self._getLastTickData("Volume")
        if not np.isnan(tvwapn):
            tvwap.append(tvwapn)
            vol.append(voln)
        else:
            tvwap.append(None)
            vol.append(None)

        tvwap_all = self.__hisLastP + list(filter(lambda x: x is not None, tvwap))
        vol_all = self.__hisVolume + list(filter(lambda x: x is not None, vol))
        tvwap_sub = tvwap_all[-self.__lag - 1:]
        if len(tvwap_sub) >= 5:
            vol_sub = np.array(vol_all[-len(tvwap_sub) + 1:])
            trtns_sub = (np.divide(tvwap_sub[1:], tvwap_sub[:-1]) - 1) * 1e3
            factorValue = self.__corr_with(trtns_sub, vol_sub)
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    @staticmethod
    def __corr_with(x, y, axis=0):
        np.place(x, np.isinf(x), np.nan)
        np.place(y, np.isinf(y), np.nan)

        if axis == 1:  # 每一行的相关系数
            x = x.T
            y = y.T

        dx = x - np.nanmean(x, axis=0)
        dy = y - np.nanmean(y, axis=0)
        corr = np.nanmean(dx * dy, axis=0) / np.nanstd(x, axis=0) / np.nanstd(y, axis=0)

        return corr
