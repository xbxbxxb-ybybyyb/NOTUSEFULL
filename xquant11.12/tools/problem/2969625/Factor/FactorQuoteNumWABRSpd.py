# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/08
from System.Factor import Factor
import numpy as np


class FactorQuoteNumWABRSpd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__r = self._getParameter("R")
        self.__emalag = self._getParameter("EMALag")

    def calculate(self):
        bidn = self._getLastNTickData("BidNum", 2)
        askn = self._getLastNTickData("AskNum", 2)
        bidp = self._getLastNTickData("BidPrice", 2)
        askp = self._getLastNTickData("AskPrice", 2)

        if len(askp) > 1:
            if askp[0][0] < 0.01:  # 涨停
                benchmp_b = self._getLastTickData("MaxPrice")
                benchmp_s = self._getLastTickData("MaxPrice")
            elif bidp[0][0] < 0.01:
                benchmp_b = self._getLastTickData("MinPrice")
                benchmp_s = self._getLastTickData("MinPrice")
            else:
                benchmp_b = bidp[0][0] * (1 - self.__r)
                benchmp_s = askp[0][0] * (1 + self.__r)

            idx = bidp[0] > benchmp_b
            last_bn = np.nansum(bidn[0][idx] * np.arange(sum(idx), 0, -1))
            idx = askp[0] < benchmp_s
            last_an = np.nansum(askn[0][idx] * np.arange(sum(idx), 0, -1))

            idx = bidp[1] > benchmp_b
            crt_bn = np.nansum(bidn[1][idx] * np.arange(sum(idx), 0, -1))
            idx = askp[1] < benchmp_s
            crt_an = np.nansum(askn[1][idx] * np.arange(sum(idx), 0, -1))

            facv = self.getFactorValueList()[-self.__emalag:]
            if (last_bn > 0.01) and (last_an > 0.01) and (crt_bn > 0.01) and (crt_an > 0.01):
                last_abr = last_bn / last_an
                crt_abr = crt_bn / crt_an
                nv = np.clip(np.log(crt_abr / last_abr), a_max=5., a_min=-5.) * 100
            elif (last_bn > 0.01) and (last_an > 0.01) and (crt_bn > 0.01):  # 此刻涨停
                nv = np.nanmax(facv)
            elif (last_bn > 0.01) and (last_an > 0.01) and (crt_an > 0.01):  # 此刻跌停
                nv = np.nanmin(facv)
            elif (last_bn > 0.01) and (crt_bn > 0.01) and (crt_an > 0.01):  # 涨停开板
                nv = np.nanmin([np.nanmin(facv), 0.])
            elif (last_an > 0.01) and (crt_bn > 0.01) and (crt_an > 0.01):  # 跌停开板
                nv = np.nanmax([np.nanmax(facv), 0.])
            elif (last_bn > 0.01) and (crt_bn > 0.01):  # 涨停封板
                nv = facv[-1]
            elif (last_an > 0.01) and (crt_an > 0.01):  # 跌停封板
                nv = facv[-1]
            else:
                nv = 0.

            factorValue = self.__ema(nv, facv, self.__emalag)

        else:
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
