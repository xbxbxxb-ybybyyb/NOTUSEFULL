# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/23
from System.Factor import Factor
import numpy as np


class FactorACTNetTailQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__cutoff = None

        self.__activeTradeBidIdxM = self._getFactor(
            {
                "ClassName": "ActiveTradeBidIdxM",
            }
        )

        self.__activeTradeAskIdxM = self._getFactor(
            {
                "ClassName": "ActiveTradeAskIdxM",
            }
        )

        self._addIntermediate("NetTailAmount", [])

    def calculate(self):

        net_tail_amount = self.getIntermediate("NetTailAmount")
        bid_amount = np.array(list(self.__activeTradeBidIdxM.getLastFactorValue().values()))
        ask_amount = np.array(list(self.__activeTradeAskIdxM.getLastFactorValue().values()))

        bid_tail_amount = bid_amount[bid_amount < self.__cutoff]
        ask_tail_amount = ask_amount[ask_amount < self.__cutoff]
        net_tail_amount.append(np.nansum(bid_tail_amount) - np.nansum(ask_tail_amount))

        if len(net_tail_amount) > 10:
            nv = sum(np.array(net_tail_amount[-self.__lag:]) < net_tail_amount[-1]) / len(net_tail_amount[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.5

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoff = np.round(np.nanpercentile(mamount / mdnum, 30))
        else:  # 如果前一天没有分钟频数据
            self.__cutoff = 4e4

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x