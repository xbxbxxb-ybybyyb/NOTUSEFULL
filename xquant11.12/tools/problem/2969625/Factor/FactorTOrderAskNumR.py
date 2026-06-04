# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/26
from System.Factor import Factor
import numpy as np


class FactorTOrderAskNumR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__cutoffs = None

        self._addIntermediate("TailNum", [])

    def calculate(self):
        tailn_list = self.getIntermediate("TailNum")

        bidp = self._getLastNTickData("BidPrice", 2)[0][0]
        if bidp < 0.01:  # 跌停
            bidp = self._getLastTickData("MinPrice")

        order = self._getLastTickData("Orders")
        if order is not None:
            orderp = self._getOrderData("Price", order)
            orderv = self._getOrderData("Volume", order)
            orderf = self._getOrderData("BSFlag", order)

            # 非市价单
            idx = (orderp > 0.01) & (orderf == 2)
            am = orderp[idx] * orderv[idx]
            n_1 = np.nansum(am < self.__cutoffs)

            # 市价单
            idx = (orderp < 0.01) & (orderf == 2)
            am = bidp * orderv[idx]
            n_2 = np.nansum(am < self.__cutoffs)

            n = n_1 + n_2
        else:
            n = 0
        tailn_list.append(n)

        meanv = np.nanmean(tailn_list)
        if meanv > 0.01:
            nv = -np.clip(np.log(n / meanv), a_min=-5., a_max=5.)
        else:
            nv = 0.

        facv = self.getFactorValueList()[-5:]
        factorValue = self.__ema(nv, facv, 5)

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        mamount = self._getAllHistoricalMinuteData("Amount")
        mdnum = self._getAllHistoricalMinuteData("NumTrades")
        if len(mamount) > 0:
            self.__cutoffs = np.round(np.nanpercentile(mamount / mdnum, 30))
        else:  # 如果前一天没有分钟频数据
            self.__cutoffs = 4e4

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
