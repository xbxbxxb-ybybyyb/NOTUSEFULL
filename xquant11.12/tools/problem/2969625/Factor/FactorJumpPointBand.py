from System.Factor import Factor
import numpy as np


class FactorJumpPointBand(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")
        self.__scale = self._getParameter("Scale")

        self.__band_up = None
        self.__band_down = None

    def calculate(self):

        tick_time = self._getAllTodayTickData("Time")
        dopen_crt = self._getAllTodayTickData("LastPrice")[0]  # 第一个TICK的LastPrice作为当天开盘价
        lastp = self._getLastTickData("LastPrice")

        if len(tick_time) == 1:
            # 取历史数据
            dclose_pre = self._getLastNHistoricalDailyData("ClosePrice", self.__dlag + 1)
            dopen_pre = self._getLastNHistoricalDailyData("OpenPrice", self.__dlag)
            mclose_pre = self._getLastNHistoricalMinuteData("ClosePrice", self.__dlag * 240)
            ddates = self._getLastNHistoricalDailyData("Date", self.__dlag)
            mdates = self._getLastNHistoricalMinuteData("Date", self.__dlag * 240)
            udates = sorted(set(mdates).intersection(set(ddates)))

            jump_rtns = dopen_pre / dclose_pre[:-1] - 1  # 个股隔夜收益率
            jump_rtns = jump_rtns[[each in udates for each in ddates]]
            dopen_pre = dopen_pre[[each in udates for each in ddates]]

            mclose_pre_max, mclose_pre_min = [], []
            for d in udates:
                idx = mdates == d
                mclose_pre_max.append(np.nanmax(mclose_pre[idx]))
                mclose_pre_min.append(np.nanmin(mclose_pre[idx]))
            mclose_pre_max = np.array(mclose_pre_max)  # 最高价
            mclose_pre_min = np.array(mclose_pre_min)  # 最低价

            high_bound = mclose_pre_max - dopen_pre
            low_bound = dopen_pre - mclose_pre_min
            np.place(high_bound, high_bound < 0, 0)
            np.place(low_bound, low_bound > 0, 0)
            np.place(jump_rtns, jump_rtns == 0, np.nan)
            high_bound_unit = high_bound / np.abs(jump_rtns)
            low_bound_unit = low_bound / np.abs(jump_rtns)

            jump_rtns_crt = dopen_crt / dclose_pre[-1] - 1
            if jump_rtns_crt > 0:
                high_bound_crt = np.nanmean(high_bound_unit[jump_rtns > 0]) * np.abs(jump_rtns_crt)
                low_bound_crt = np.nanmean(low_bound_unit[jump_rtns > 0]) * np.abs(jump_rtns_crt)
            else:
                high_bound_crt = np.nanmean(high_bound_unit[jump_rtns < 0]) * np.abs(jump_rtns_crt)
                low_bound_crt = np.nanmean(low_bound_unit[jump_rtns < 0]) * np.abs(jump_rtns_crt)
            # 适当调整
            if high_bound_crt == 0:
                high_bound_crt = low_bound_crt
            elif low_bound_crt == 0:
                low_bound_crt = high_bound_crt
            # 存储
            self.__band_up = high_bound_crt
            self.__band_down = low_bound_crt

        high_bound_crt, low_bound_crt = self.__band_up, self.__band_down

        if lastp > dopen_crt + high_bound_crt * self.__scale:
            factorValue = (lastp / (dopen_crt + high_bound_crt * self.__scale) - 1) * 1e2
        elif lastp < dopen_crt - low_bound_crt * self.__scale:
            factorValue = (lastp / (dopen_crt - low_bound_crt * self.__scale) - 1) * 1e2
        else:
            factorValue = lastp / dopen_crt / 1e2

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
