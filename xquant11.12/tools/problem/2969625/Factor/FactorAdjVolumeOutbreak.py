from System.Factor import Factor
import numpy as np
import datetime as dt


class FactorAdjVolumeOutbreak(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__vmlag = self._getParameter("VolumeMLag")
        self.__vdlag = self._getParameter("VolumeDLag")
        self.__mpthrd = self._getParameter("MidPriceThrd")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )
        self.__time_pre_list = None  # 存历史的time
        self.__vol_pre_list = None  # 存历史的量
        self._addIntermediate("TimestampCrtList", [])  # 存当天的timestamp
        self._addIntermediate("VolCrtList", [])  # 存当天的量

    def calculate(self):
        tick_time_crt = self._getAllTodayTickData("Time")
        tick_mid_price = self.__midPrice.getFactorValueList()[-len(tick_time_crt):]
        timestamp = self._getLastTickData("Timestamp")
        # 时间处理
        date = int(self._getLastTickData("Date"))
        pm_start = dt.datetime.strptime("{} 13:00:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        pm_end = dt.datetime.strptime("{} 13:01:00".format(date), "%Y%m%d %H:%M:%S").timestamp()
        if (timestamp >= pm_start) and (timestamp < pm_end):
            delta = 60 + 60 * 90
        else:
            delta = 60

        # 用分钟频处理历史的
        if len(tick_time_crt) == 1:
            mvol = self._getAllHistoricalMinuteData("Volume")
            mtime = self._getAllHistoricalMinuteData("Time")
            tvol = mvol / 20
            self.__vol_pre_list = tvol.tolist()
            self.__time_pre_list = mtime.tolist()

        # 当天数据
        tvol_crt = self._getLastNTickData("Volume", self.__vmlag * 20)
        vol_crt_list = self.getIntermediate("VolCrtList")
        timestamp_crt_list = self.getIntermediate("TimestampCrtList")
        vol_crt_list.append(np.nanmean(tvol_crt))
        timestamp_crt_list.append(timestamp)

        min_crt = tick_time_crt[-1] // 1e5 * 1e5  # 当前分钟
        tvol_mean_pre = np.array(self.__vol_pre_list)[np.array(self.__time_pre_list) == min_crt]  # 查找历史同期Time对应的量
        tvol_mean_crt = np.array(vol_crt_list)[np.array(timestamp_crt_list) > (timestamp - delta)]   # 当天1min内的量
        tvol_mean = np.append(tvol_mean_pre, tvol_mean_crt)  # 拼接
        tvol_crt = tvol_mean[-1]
        tvol_s = tvol_mean[:-1]

        if len(tvol_s) > 0:
            vol_qtl = np.nansum(tvol_s <= tvol_crt) / len(tvol_s)
            midprice_crt = tick_mid_price[-1]
            midprice_s = np.array(tick_mid_price[:-1])
            midprice_qtl = np.nansum(midprice_s <= midprice_crt) / len(midprice_s)

            if midprice_qtl < self.__mpthrd:
                factorValue = vol_qtl * midprice_qtl * 1e1
            elif midprice_qtl > 1 - self.__mpthrd:
                factorValue = - vol_qtl * midprice_qtl * 1e1
            else:
                factorValue = vol_qtl * midprice_qtl / 1e3
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
