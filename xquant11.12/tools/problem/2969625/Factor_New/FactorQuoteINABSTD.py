# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/08
from System.Factor import Factor
import numpy as np


class FactorQuoteINABSTD(Factor):

    def calculate(self):
        askN = self._getLastNTickData("AskNum", 2)
        bidN = self._getLastNTickData("BidNum", 2)
        askP = self._getLastNTickData("AskPrice", 2)
        bidP = self._getLastNTickData("BidPrice", 2)

        if len(askN) > 1:
            diff_b = self.__ndiff(bidP[-1], bidN[-1], bidP[0], bidN[0])
            diff_a = self.__ndiff(askP[-1], askN[-1], askP[0], askN[0])
            nv = (np.nanstd(diff_b) - np.nanstd(diff_a)) / 100
        else:
            nv = 0.

        facv = self.getFactorValueList()
        factorValue = self.__ema(nv, facv, 5)

        self._addFactorValue(factorValue)

    def __ndiff(self, this_p, this_v, last_p, last_v):
        p = np.union1d(this_p, last_p)
        this_d = dict(zip(this_p, this_v))
        last_d = dict(zip(last_p, last_v))
        this_v = [this_d.get(each, 0.) for each in p]
        last_v = [last_d.get(each, 0.) for each in p]
        v_diff = np.subtract(this_v, last_v)
        return v_diff

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
