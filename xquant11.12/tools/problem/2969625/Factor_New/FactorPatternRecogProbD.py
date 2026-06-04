# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/05
from System.Factor import Factor


class FactorPatternRecogProbD(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("DayLag")
        self.__fwd = self._getParameter("PredictFwd")

        self.__patternRecogProb = self._getFactor(
            {
                "ClassName": "PatternRecogProb",
                "MinuteLength": self.__lag,
                "TickLength": 1,
                "SplitAdjusted": True,
                "Parameters": {
                    "DayLag": self.__lag,
                    "PredictFwd": self.__fwd,
                }
            }
        )

    def calculate(self):
        # 全跌的概率
        stat = self.__patternRecogProb.getLastFactorValue()[0]
        if stat[1] > 0:
            factorValue = - stat[0] / stat[1]
        else:
            factorValue = - 1 / 16.

        self._addFactorValue(factorValue)

