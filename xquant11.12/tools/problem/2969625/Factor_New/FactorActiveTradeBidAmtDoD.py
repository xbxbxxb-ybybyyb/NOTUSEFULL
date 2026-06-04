# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/26
from System.Factor import Factor
import numpy as np
import pandas as pd
import datetime as dt


class FactorActiveTradeBidAmtDoD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__hisAmtPerM = None

    def calculate(self):
        trades = self._getLastTickData("Transactions")
        if trades is not None:
            bfs = self._getTransactionData("BSFlag", trades)
            tradem = self._getTransactionData("Amount", trades)
            bm = np.nansum(tradem[bfs == 1])
        else:
            bm = 0.

        ctime = self._getLastTickData("Time") // 1e5 * 1e5
        if self.__hisAmtPerM is not None:
            mamt = self.__hisAmtPerM.loc[ctime] / 20
            if mamt < 0.1:  # 如果当前分钟为0，用全天均值代替
                mamt = np.nanmean(self.__hisAmtPerM)
        else:
            mamt = np.nanmean(self._getAllTodayTickData("Amount"))

        facv = self.getFactorValueList()
        if (mamt > 0.01) and (bm > 0.01):
            nv = bm / mamt
        else:
            nv = 0.
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
        mamount = self._getAllHistoricalMinuteData("Amount")
        mtime = self._getAllHistoricalMinuteData("Time")
        mdate = self._getAllHistoricalMinuteData("Date")

        if len(mamount) > 0:
            valid_minutes = ([int((dt.datetime(1949, 10, 1, 9, 30) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)]
                             + [int((dt.datetime(1949, 10, 1, 13) + dt.timedelta(minutes=i)).strftime("%H%M%S") + "000") for i in range(120)])

            mean_amount_dict = {}
            for date in sorted(set(mdate)):
                idx = mdate == date
                mean_amount_dict[date] = pd.Series(mamount[idx], index=mtime[idx])
            mean_amount = pd.DataFrame(mean_amount_dict).mean(axis=1).reindex(index=valid_minutes).fillna(0.)

            self.__hisAmtPerM = mean_amount
