# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/24
from System.Factor import Factor
import numpy as np


class FactorActiveTradeAskAmtQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskAmount", [])

    def calculate(self):
        aamt_list = self.getIntermediate("AskAmount")

        trades = self._getLastTickData("Transactions")
        if trades is not None:
            bfs = self._getTransactionData("BSFlag", trades)
            tradem = self._getTransactionData("Amount", trades)
            aamt_list.append(np.nansum(tradem[bfs == 2]))
        else:
            aamt_list.append(0)

        if len(aamt_list) > 10:
            nv = -np.nansum(np.array(aamt_list[-self.__lag:]) < aamt_list[-1]) / len(aamt_list[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = -0.5

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
