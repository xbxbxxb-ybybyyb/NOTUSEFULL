# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/11
from System.Factor import Factor
import numpy as np


class FactorQuoteVolumeWABRSpd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__r = self._getParameter("R")
        self.__emalag = self._getParameter("EMALag")

    def calculate(self):
        bidv = self._getLastNTickData("BidVolume", 2)
        askv = self._getLastNTickData("AskVolume", 2)
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
            last_bv = np.nansum(bidv[0][idx] * np.arange(sum(idx), 0, -1))
            idx = askp[0] < benchmp_s
            last_av = np.nansum(askv[0][idx] * np.arange(sum(idx), 0, -1))

            idx = bidp[1] > benchmp_b
            crt_bv = np.nansum(bidv[1][idx] * np.arange(sum(idx), 0, -1))
            idx = askp[1] < benchmp_s
            crt_av = np.nansum(askv[1][idx] * np.arange(sum(idx), 0, -1))

            facv = self.getFactorValueList()[-self.__emalag:]
            if (last_bv > 0.01) and (last_av > 0.01) and (crt_bv > 0.01) and (crt_av > 0.01):
                last_abr = last_bv / last_av
                crt_abr = crt_bv / crt_av
                nv = np.clip(np.log(crt_abr / last_abr), a_max=5., a_min=-5.) * 100
            elif (last_bv > 0.01) and (last_av > 0.01) and (crt_bv > 0.01):  # 此刻涨停
                nv = np.nanmax(facv)
            elif (last_bv > 0.01) and (last_av > 0.01) and (crt_av > 0.01):  # 此刻跌停
                nv = np.nanmin(facv)
            elif (last_bv > 0.01) and (crt_bv > 0.01) and (crt_av > 0.01):  # 涨停开板
                nv = np.nanmin([np.nanmin(facv), 0.])
            elif (last_av > 0.01) and (crt_bv > 0.01) and (crt_av > 0.01):  # 跌停开板
                nv = np.nanmax([np.nanmax(facv), 0.])
            elif (last_bv > 0.01) and (crt_bv > 0.01):  # 涨停封板
                nv = facv[-1]
            elif (last_av > 0.01) and (crt_av > 0.01):  # 跌停封板
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
