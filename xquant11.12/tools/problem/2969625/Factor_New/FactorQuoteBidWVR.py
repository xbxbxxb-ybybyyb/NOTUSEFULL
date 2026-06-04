# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/02
from System.Factor import Factor
import numpy as np


class FactorQuoteBidWVR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__r = self._getParameter("R")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidVolume", [])

    def calculate(self):
        bidv_list = self.getIntermediate("BidVolume")
        bidv = self._getLastTickData("BidVolume")
        bidp = self._getLastTickData("BidPrice")
        askp = self._getLastTickData("AskPrice")

        if askp[0] < 0.01:  # 涨停
            benchmp_b = self._getLastTickData("MaxPrice")
        elif bidp[0] < 0.01:
            benchmp_b = self._getLastTickData("MinPrice")
        else:
            benchmp_b = bidp[0] * (1 - self.__r)

        idx = bidp > benchmp_b
        w = np.arange(sum(idx), 0, -1)
        bv = np.nansum(bidv[idx] * w)
        bidv_list.append(bv)

        meanv = np.nanmean(bidv_list[-self.__lag:])
        facv = self.getFactorValueList()
        if (bv < 0.01) or (meanv < 0.01):
            if len(facv) > 0:
                nv = np.nanmin(facv[-self.__lag:])
            else:
                nv = 0.
        else:
            nv = np.clip(np.log(bv / meanv), a_min=-5., a_max=5.)
        factorValue = self.__ema(nv, facv, 5)

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
