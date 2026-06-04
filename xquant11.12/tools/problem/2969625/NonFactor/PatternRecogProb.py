# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/05
from System.Factor import Factor
import numpy as np
from copy import deepcopy


class PatternRecogProb(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("DayLag")
        self.__fwd = self._getParameter("PredictFwd")

        self.__hisPS = None

    def calculate(self):
        lastv = self.getLastFactorValue()
        last_ps = deepcopy(lastv) if lastv is not None else deepcopy(self.__hisPS)

        lastp = self._getLastNTickData("LastPrice", 200 + self.__fwd * 20)

        # 更新最新的
        if len(lastp) >= self.__fwd * 20 + 200:
            rtns = np.array([lastp[-1 - self.__fwd * 20] / lastp[-i * 20 - self.__fwd * 20] - 1 for i in [1, 2, 5, 10]])
            pat = self.__to_pattern(rtns > 0)
            rtns_fwd = lastp[-1] / lastp[-self.__fwd * 20] - 1
            stat = rtns_fwd > 0
            self.__update_pattern_status(last_ps, pat, stat)

        factorValue = last_ps

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mclosep = self._getAllHistoricalMinuteData("ClosePrice")

        rtns = []
        for i in [1, 2, 5, 10]:
            rtns.append(list(mclosep / np.hstack(([np.nan] * i, mclosep[:-i])) - 1))
        rtns = np.array(rtns)

        pfwd = np.hstack((mclosep[self.__fwd:], [np.nan] * self.__fwd)) / mclosep - 1

        idx = np.all(~np.isnan(rtns), axis=0) & (~np.isnan(pfwd))
        rtns = rtns[:, idx]
        pfwd = pfwd[idx]

        pattern = list(map(lambda i: self.__to_pattern(rtns[:, i] > 0), range(rtns.shape[1])))
        status = pfwd > 0
        # 形成字典
        pat_stat = dict.fromkeys(range(16), (0, 0))
        for i, pat in enumerate(pattern):
            self.__update_pattern_status(pat_stat, pat, status[i])
        self.__hisPS = pat_stat

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
