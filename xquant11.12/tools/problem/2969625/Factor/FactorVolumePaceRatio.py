from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorVolumePaceRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__mlag = self._getParameter("MinLag")
        self.__dlag = self._getParameter("DayLag")

        self.__hisTimePreList = None  # 存历史的time
        self.__hisVolPreList = None  # 存历史的量
        self._addIntermediate("TimestampCrtList", [])  # 存当天的timestamp
        self._addIntermediate("VolCrtList", [])  # 存当天的量

    def calculate(self):

        tick_time_crt = self._getAllTodayTickData("Time")
        timestamp = self._getLastTickData("Timestamp")
        dvol = np.nanmean(self._getLastNHistoricalDailyData("Volume", self.__dlag))  # 日均量
        # 时间处理
        date = int(self._getLastTickData("Date"))
        pm_start = dt.datetime.strptime("{} 13:00:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        pm_end = dt.datetime.strptime("{} 13:01:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        if (timestamp >= pm_start) and (timestamp < pm_end):
            delta = 60 + 60 * 90
        else:
            delta = 60

        if len(tick_time_crt) == 1:
            # 历史数据
            mvol = self._getAllHistoricalMinuteData("Volume")   # 需要考虑日K和分钟K线为NaN情况
            mtime = self._getAllHistoricalMinuteData("Time")
            tvol = mvol / 20
            self.__hisVolPreList = tvol.tolist()
            self.__hisTimePreList = mtime.tolist()

        # 当天数据
        tvol_crt = self._getLastNTickData("Volume", self.__mlag * 20)
        vol_crt_list = self.getIntermediate("VolCrtList")
        timestamp_crt_list = self.getIntermediate("TimestampCrtList")
        vol_crt_list.append(np.nanmean(tvol_crt))
        timestamp_crt_list.append(timestamp)

        min_crt = tick_time_crt[-1] // 1e5 * 1e5  # 当前分钟
        tvol_mean_pre = np.array(self.__hisVolPreList)[np.array(self.__hisTimePreList) == min_crt]  # 查找历史同期Time对应的量
        tvol_mean_crt = np.array(vol_crt_list)[np.array(timestamp_crt_list) > (timestamp - delta)]   # 当天1min内的量
        tvol_mean = np.append(tvol_mean_pre, tvol_mean_crt)  # 拼接

        if np.isnan(dvol) or dvol == 0:
            factorValue = 0.
        else:
            vol_pace_crt = tvol_mean[-1] / dvol
            vol_pace_pre = np.nanmean(tvol_mean[:-1]) / dvol
            factorValue = (vol_pace_crt - vol_pace_pre) * 1e3

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

