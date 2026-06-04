# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/23
from System.Factor import Factor
import numpy as np


class FactorACTAskTailQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__cutoffs = None

        self.__activeTradeAskIdxM = self._getFactor(
            {
                "ClassName": "ActiveTradeAskIdxM",
            }
        )
        self._addIntermediate("TailAmount", [])

    def calculate(self):

        tail_amount = self.getIntermediate("TailAmount")
        ask_amount = np.array(list(self.__activeTradeAskIdxM.getLastFactorValue().values()))

        tail_amount.append(np.nansum(ask_amount[ask_amount < self.__cutoffs]))

        if len(tail_amount) > 10:
            nv = -np.nansum(tail_amount[-self.__lag:] < tail_amount[-1]) / len(tail_amount[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = -0.5

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoffs = np.round(np.nanpercentile(mamount / mdnum, 30))
        else:  # 如果前一天没有分钟频数据
            self.__cutoffs = 4e4

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
