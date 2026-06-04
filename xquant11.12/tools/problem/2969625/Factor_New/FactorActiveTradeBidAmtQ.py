# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/24
from System.Factor import Factor
import numpy as np


class FactorActiveTradeBidAmtQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidAmount", [])

    def calculate(self):
        bamt_list = self.getIntermediate("BidAmount")

        trades = self._getLastTickData("Transactions")
        if trades is not None:
            bfs = self._getTransactionData("BSFlag", trades)
            tradem = self._getTransactionData("Amount", trades)
            bamt_list.append(np.nansum(tradem[bfs == 1]))
        else:
            bamt_list.append(0)

        if len(bamt_list) > 10:
            nv = np.nansum(np.array(bamt_list[-self.__lag:]) < bamt_list[-1]) / len(bamt_list[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.5

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
