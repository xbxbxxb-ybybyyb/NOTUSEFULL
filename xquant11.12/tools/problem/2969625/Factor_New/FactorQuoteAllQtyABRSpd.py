# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/13
from System.Factor import Factor
import numpy as np


class FactorQuoteAllQtyABRSpd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__emalag = self._getParameter("EMALag")

        self._addIntermediate("ABQtyRatio", [])

    def calculate(self):
        abqr_list = self.getIntermediate("ABQtyRatio")
        bidq = self._getLastTickData("BidQty")
        askq = self._getLastTickData("OfferQty")

        if (bidq > 0.01) and (askq > 0.01):
            abr = bidq / askq
        elif bidq > 0.01:
            if len(abqr_list) > 0:  # 此刻涨停
                abr = np.nanmax(abqr_list[-self.__emalag:])
            else:
                abr = 1.  # 开盘涨停
        else:
            if len(abqr_list) > 0:  # 此刻跌停
                abr = np.nanmin(abqr_list[-self.__emalag:])
            else:
                abr = 1.  # 开盘跌停
        abqr_list.append(abr)

        facv = self.getFactorValueList()[-self.__emalag:]
        if len(abqr_list) > 2:
            nv = np.clip(np.log(abqr_list[-1] / abqr_list[-2]), a_max=5., a_min=-5.) * 1e3
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
