# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/03
from System.Factor import Factor
import numpy as np


class FactorQuoteAskWVR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__r = self._getParameter("R")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskVolume", [])

    def calculate(self):
        askv_list = self.getIntermediate("AskVolume")
        askv = self._getLastTickData("AskVolume")
        bidp = self._getLastTickData("BidPrice")
        askp = self._getLastTickData("AskPrice")

        if askp[0] < 0.01:  # 涨停
            benchmp_s = self._getLastTickData("MaxPrice")
        elif bidp[0] < 0.01:
            benchmp_s = self._getLastTickData("MinPrice")
        else:
            benchmp_s = askp[0] * (1 + self.__r)

        idx = askp < benchmp_s
        w = np.arange(sum(idx), 0, -1)
        av = np.nansum(askv[idx] * w)
        askv_list.append(av)

        meanv = np.nanmean(askv_list[-self.__lag:])
        facv = self.getFactorValueList()
        if (av < 0.01) or (meanv < 0.01):
            if len(facv) > 0:
                nv = np.nanmax(facv[-self.__lag:])
            else:
                nv = 0.
        else:
            nv = -np.clip(np.log(av / meanv), a_min=-5., a_max=5.)
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
