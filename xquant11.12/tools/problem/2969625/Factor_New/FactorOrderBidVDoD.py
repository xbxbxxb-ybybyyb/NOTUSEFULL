# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/26
from System.Factor import Factor
import numpy as np
import pandas as pd
import datetime as dt


class FactorOrderBidVDoD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__hisVolumePerM = None

    def calculate(self):
        order = self._getLastTickData("Orders")
        if order is not None:
            orderf = self._getOrderData("BSFlag", order)
            orderv = self._getOrderData("Volume", order)
            bv = np.nansum(orderv[orderf == 1])
        else:
            bv = 0.

        ctime = self._getLastTickData("Time") // 1e5 * 1e5
        if self.__hisVolumePerM is not None:
            mvolume = self.__hisVolumePerM.loc[ctime] / 20
            if mvolume < 0.1:  # 如果当前分钟为0，用全天均值代替
                mvolume = np.nanmean(self.__hisVolumePerM)
        else:
            mvolume = np.nanmean(self._getAllTodayTickData("Volume"))

        if (mvolume > 0.01) and (bv > 0.01):
            nv = np.clip(np.log(bv / mvolume), a_min=-5., a_max=5.)
        else:
            nv = 0.

        facv = self.getFactorValueList()
        factorValue = self.__ema(nv, facv, 5)

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x

    def _onNewDay(self):
        mvolume = self._getAllHistoricalMinuteData("Volume")
        mtime = self._getAllHistoricalMinuteData("Time")
        mdate = self._getAllHistoricalMinuteData("Date")

        if len(mvolume) > 0:
            valid_minutes = ([int((dt.datetime(1949, 10, 1, 9, 30) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)]
                             + [int((dt.datetime(1949, 10, 1, 13) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)])

            mean_volume_dict = {}
            for date in sorted(set(mdate)):
                idx = mdate == date
                mean_volume_dict[date] = pd.Series(mvolume[idx], index=mtime[idx])
            mean_volume = pd.DataFrame(mean_volume_dict).mean(axis=1).reindex(index=valid_minutes).fillna(0.)

            self.__hisVolumePerM = mean_volume
