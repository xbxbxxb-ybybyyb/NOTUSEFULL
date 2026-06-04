# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/27
from System.Factor import Factor
import numpy as np


class FactorOrderBidAmtQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__r = self._getParameter("R")

        self._addIntermediate("AggrBidOrderAmount", [])

    def calculate(self):
        aggrbm_list = self.getIntermediate("AggrBidOrderAmount")

        askp = self._getLastNTickData("AskPrice", 2)[0][0]
        bidp = self._getLastNTickData("BidPrice", 2)[0][0]
        order = self._getLastTickData("Orders")

        if order is not None:
            if askp < 0.01:  # 涨停
                incm = 0.
            else:
                if bidp < 0.01:
                    benchmp = self._getLastTickData("MinPrice")
                else:
                    benchmp = bidp * (1 - self.__r)

                orderp = self._getOrderData("Price", order)
                orderv = self._getOrderData("Volume", order)
                orderf = self._getOrderData("BSFlag", order)

                # 非市价单
                idxb = (orderp > benchmp) & (orderf == 1)
                incm_1 = np.nansum(orderp[idxb] * orderv[idxb])

                # 市价单
                idxb = (orderp < 0.01) & (orderf == 1)
                incm_2 = np.nansum(askp * orderv[idxb])

                incm = incm_1 + incm_2
        else:
            incm = 0.
        aggrbm_list.append(incm)

        if len(aggrbm_list) > 10:
            nv = np.nansum(np.array(aggrbm_list[-self.__lag:]) < incm) / len(aggrbm_list[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.35

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
