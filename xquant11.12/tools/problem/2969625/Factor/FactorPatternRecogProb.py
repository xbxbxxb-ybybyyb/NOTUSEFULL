from System.Factor import Factor
import numpy as np
from copy import deepcopy


class FactorPatternRecogProb(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")
        self.__pfwd = self._getParameter("PredictFwd")

        self._addIntermediate("PatternStatusList", [])

    def calculate(self):

        tick_time = self._getAllTodayTickData("Time")
        tlastp = self._getLastNTickData("LastPrice", 200 + self.__pfwd * 20)
        ps_list = self.getIntermediate("PatternStatusList")

        if len(tick_time) == 1:
            mclose = self._getAllHistoricalMinuteData("ClosePrice")
            # 状态和后续涨跌情况
            rtns = np.array([mclose[-self.__dlag * 240 - self.__pfwd: -self.__pfwd] /
                             mclose[-self.__dlag * 240 - i - self.__pfwd: - i - self.__pfwd] - 1
                             for i in [1, 2, 5, 10]])
            pattern = list(map(lambda i: self.__to_pattern(rtns[:, i] > 0), range(rtns.shape[1])))
            rtns_pfwd = mclose[-self.__dlag * 240:] / mclose[-self.__dlag * 240 - self.__pfwd: -self.__pfwd] - 1
            status = rtns_pfwd > 0
            # 形成字典
            pat_stat = dict.fromkeys(range(16), (0, 0))
            for i, pat in enumerate(pattern):
                self.__update_pattern_status(pat_stat, pat, status[i])
            # 存字典
            ps_list.append(pat_stat)

        elif len(tick_time) < self.__pfwd * 20 + 200:
            ps_list.append(None)
        else:
            # 更新最新的
            pat_stat = self.__fetch_pattern_status(ps_list)
            rtns = np.array([tlastp[-1 - self.__pfwd * 20] / tlastp[-i * 20 - self.__pfwd * 20] - 1 for i in [1, 2, 5, 10]])
            pat = self.__to_pattern(rtns > 0)
            rtns_pfwd = tlastp[-1] / tlastp[-self.__pfwd * 20] - 1
            stat = rtns_pfwd > 0
            self.__update_pattern_status(pat_stat, pat, stat)
            ps_list.append(pat_stat)

        pat_stat = self.__fetch_pattern_status(ps_list)
        stat = pat_stat[15]
        if stat[1] > 0:
            prob = stat[0] / stat[1]
        else:
            prob = 1 / 16.
        
        factorValue = prob

        if np.isnan(factorValue):
            factorValue = self.getLastFactorValue()

        if np.isnan(factorValue):
            factorValue = 1 / 16

        self._addFactorValue(factorValue)

    @staticmethod
    def __to_pattern(x):
        x_encode = ''.join(map(lambda i: str(int(i)), x))
        x_binary = int(x_encode, 2)
        return x_binary

    @staticmethod
    def __update_pattern_status(pat_stat, pat, stat):
        if stat > 0:
            pat_stat[pat] = (pat_stat[pat][0] + 1, pat_stat[pat][1] + 1)
        else:
            pat_stat[pat] = (pat_stat[pat][0], pat_stat[pat][1] + 1)

    @staticmethod
    def __fetch_pattern_status(pat_stat_list):
        pat_stat = dict()
        if len(pat_stat_list) > 0:
            for i in range(1, len(pat_stat_list) + 1):
                if pat_stat_list[-i] is not None:
                    pat_stat = deepcopy(pat_stat_list[-i])
                    break
        return pat_stat
