# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/27
from System.Factor import Factor
import numpy as np


class FactorOrderBidVToAllBV(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        bqty = self._getLastTickData("BidQty")
        order = self._getLastTickData("Orders")
        if order is not None:
            orderf = self._getOrderData("BSFlag", order)
            orderv = self._getOrderData("Volume", order)
            bv = np.nansum(orderv[orderf == 1])
        else:
            bv = 0.

        if bqty > 0.01:
            nv = bv / bqty * 100
        else:  # 跌停
            nv = 0.

        facv = self.getFactorValueList()
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
