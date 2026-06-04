from System.Factor import Factor
import numpy as np


class FactorVolumeReturnsMap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__rlag = self._getParameter("ReturnsLag")

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
            volume_pre = self._getLastNHistoricalTickData("Volume", 1000)
            volume_m_pre = np.array([volume_pre[i: -self.__lag + i + 1] if i < self.__lag - 1 else volume_pre[i:]
                                     for i in range(self.__lag)])
            volume_mean_pre = np.nanmean(volume_m_pre, axis=0)
            lastp_pre = self._getLastNHistoricalTickData("LastPrice", 1000 + self.__rlag)
            rtns_pre = lastp_pre[self.__rlag:] / lastp_pre[:-self.__rlag] - 1
            rtns_m_pre = np.array([rtns_pre[i: -self.__lag + i + 1] if i < self.__lag - 1 else rtns_pre[i:]
                                   for i in range(self.__lag)])
            rtns_mean_pre = np.nanmean(rtns_m_pre, axis=0)
            n = np.nanmin([len(rtns_mean_pre), len(volume_mean_pre)])
            if n != 0:  # 如果为False，前一天可能不交易，两个历史值为None，后续需要处理
                self.__hisVolumeList = volume_mean_pre[-n:].tolist()
                self.__hisReturnsList = rtns_mean_pre[-n:].tolist()

        # 当天数据
        if len(tick_time) < self.__lag + self.__rlag:
            vol_list.append(None)
            rtns_list.append(None)
            pop_counter.append(0)
        else:
            temp_volume_mean = np.nanmean(volume_crt[-self.__lag:])
            temp_rtns = lastp_crt[self.__rlag:] / lastp_crt[:-self.__rlag] - 1
            temp_rtns_mean = np.nanmean(temp_rtns[-self.__lag:])
            if temp_volume_mean > 0:
                # 这个pop是历史遗留问题，事实上并不需要也没什么用
                nhis = 0 if self.__hisVolumeList is None else len(self.__hisReturnsList)
                nnow = len(list(filter(lambda x: x is not None, vol_list)))
                if nhis + nnow - pop_counter[-1] > 0:
                    pop_counter.append(pop_counter[-1] + 1)
                else:
                    pop_counter.append(pop_counter[-1])
                vol_list.append(temp_volume_mean)
                rtns_list.append(temp_rtns_mean)
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

        # 因子计算
        flag = 0
        factorValue = 0
        eps = 1e-7

        if len(vol_all) > 0:
            temp_volume_s = np.array(vol_all)
            temp_rtns_s = np.array(rtns_all)
            if len(lastp_crt) > self.__rlag:
                temp_rtns = lastp_crt[self.__rlag:] / lastp_crt[:-self.__rlag] - 1
                temp_rtns = np.nanmean(temp_rtns[-self.__lag:])
                temp_volume = np.nanmean(volume_crt[-self.__lag:])
            else:
                temp_rtns = temp_rtns_s[-1]
                temp_volume = temp_volume_s[-1]

            rtns_qtl = sum(temp_rtns_s < temp_rtns + eps) / len(temp_rtns_s)
            low_qtl = int(rtns_qtl * 10) / 10
            up_qtl = np.nanmin([(int(rtns_qtl * 10) + 1) / 10, 1])
            rtns_lower_bound = np.nanpercentile(rtns_all, int(low_qtl * 100))
            rtns_upper_bound = np.nanpercentile(rtns_all, int(up_qtl * 100))
            temp_volume_pre = np.nanmean(temp_volume_s[(temp_rtns_s > rtns_lower_bound - eps) &
                                                       (temp_rtns_s < rtns_upper_bound + eps)])

            if temp_volume > 0:
                factorValue = - temp_rtns * temp_volume_pre / temp_volume
            else:
                flag = 1
        else:
            flag = 1

        if flag == 1:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

