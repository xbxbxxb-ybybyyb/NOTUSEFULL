from System.Factor import Factor
import numpy as np


class FactorVolumeToReturnsDoD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__vlag = self._getParameter("VolumeLag")
        self.__rfwd = self._getParameter("ReturnsForw")

        self.__hisVolumeList = None
        self.__hisReturnsList = None
        self._addIntermediate("PopCounter", [])
        self._addIntermediate("VolumeList", [])
        self._addIntermediate("ReturnsList", [])

    def calculate(self):

        tick_time = self._getAllTodayTickData("Time")
        volume_crt = self._getAllTodayTickData("Volume")
        lastp_crt = self._getAllTodayTickData("LastPrice")
        vol_list = self.getIntermediate("VolumeList")
        rtns_list = self.getIntermediate("ReturnsList")
        pop_counter = self.getIntermediate("PopCounter")

        # 历史数据
        if len(tick_time) == 1:
            volume_pre = self._getLastNHistoricalTickData("Volume", 1000)[:-self.__rfwd-1]
            volume_m_pre = np.array([volume_pre[i: -self.__vlag + i + 1] if i < self.__vlag - 1 else volume_pre[i:]
                                     for i in range(self.__vlag)])
            volume_mean_pre = np.nanmean(volume_m_pre, axis=0)
            lastp_pre = self._getLastNHistoricalTickData("LastPrice", 1000)[self.__vlag:]
            rtns_pre = lastp_pre[self.__rfwd:] / lastp_pre[:-self.__rfwd] - 1
            idx = (volume_mean_pre > 0) | np.isnan(volume_mean_pre)
            volume_mean_pre = volume_mean_pre[idx].tolist()
            rtns_pre = rtns_pre[idx].tolist()

            self.__hisVolumeList = volume_mean_pre
            self.__hisReturnsList = rtns_pre

        # 当天数据
        if len(tick_time) < self.__vlag + self.__rfwd:
            vol_list.append(None)
            rtns_list.append(None)
            pop_counter.append(0)
        else:
            temp_volume_mean = np.nanmean(volume_crt[-self.__vlag - self.__rfwd: -self.__rfwd])
            temp_rtns = lastp_crt[-1] / lastp_crt[-self.__rfwd] - 1
            if temp_volume_mean > 0:
                # 这个pop是历史遗留问题，事实上并不需要也没什么用
                nhis = 0 if self.__hisVolumeList is None else len(self.__hisReturnsList)
                nnow = len(list(filter(lambda x: x is not None, vol_list)))
                if nhis + nnow - pop_counter[-1] > 0:
                    pop_counter.append(pop_counter[-1] + 1)
                else:
                    pop_counter.append(pop_counter[-1])
                vol_list.append(temp_volume_mean)
                rtns_list.append(temp_rtns)
            else:
                vol_list.append(None)
                rtns_list.append(None)
                pop_counter.append(pop_counter[-1])

        # 拼接
        if self.__hisVolumeList is not None and self.__hisReturnsList is not None:
            vol_all = self.__hisVolumeList + list(filter(lambda x: x is not None, vol_list))
            rtns_all = self.__hisReturnsList + list(filter(lambda x: x is not None, rtns_list))
        else:
            vol_all = list(filter(lambda x: x is not None, vol_list))
            rtns_all = list(filter(lambda x: x is not None, rtns_list))
        # pop历史遗留问题
        for i in range(pop_counter[-1]):
            vol_all.pop(0)
            rtns_all.pop(0)

        # 计算
        eps = 1e-7
        if len(vol_all) > 0:
            temp_volume_s = np.array(vol_all)
            temp_rtns_s = np.array(rtns_all)
            volume_mean = np.nanmean(volume_crt[-self.__vlag:])
            vol_qtl = np.nansum(temp_volume_s < volume_mean + eps) / len(temp_volume_s)
            low_qtl = int(vol_qtl * 10) / 10
            up_qtl = np.nanmin([(int(vol_qtl * 10) + 1) / 10, 1])
            vol_lower_bound = np.nanpercentile(vol_all, low_qtl * 100)
            vol_upper_bound = np.nanpercentile(vol_all, up_qtl * 100)
            temp_rtns = temp_rtns_s[(temp_volume_s > vol_lower_bound - eps) & (temp_volume_s < vol_upper_bound + eps)]
            factorValue = np.nanmean(temp_rtns) * 1e2
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

