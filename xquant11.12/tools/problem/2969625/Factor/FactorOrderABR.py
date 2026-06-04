# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/27
from System.Factor import Factor
import numpy as np


class FactorOrderABR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__emalag = self._getParameter("EMALag")
        self.__r = self._getParameter("R")

        self._addIntermediate("AggrBidOrderAmount", [])
        self._addIntermediate("AggrAskOrderAmount", [])

    def calculate(self):
        aggrbm_list = self.getIntermediate("AggrBidOrderAmount")
        aggram_list = self.getIntermediate("AggrAskOrderAmount")

        askp = self._getLastNTickData("AskPrice", 2)[0][0]
        bidp = self._getLastNTickData("BidPrice", 2)[0][0]
        order = self._getLastTickData("Orders")

        if order is not None:
            if askp < 0.01:  # 涨停
                benchmp_b = self._getLastTickData("MaxPrice")
                benchmp_s = self._getLastTickData("MaxPrice")
            elif bidp < 0.01:
                benchmp_b = self._getLastTickData("MinPrice")
                benchmp_s = self._getLastTickData("MinPrice")
            else:
                benchmp_b = bidp * (1 - self.__r)
                benchmp_s = askp * (1 + self.__r)

            orderp = self._getOrderData("Price", order)
            orderv = self._getOrderData("Volume", order)
            orderf = self._getOrderData("BSFlag", order)

            # 非市价单
            idxb = (orderp > benchmp_b) & (orderf == 1)
            idxs = (orderp < benchmp_s) & (orderf == 2) & (orderp > 0.01)
            incm_b_1 = np.nansum(orderp[idxb] * orderv[idxb])
            incm_s_1 = np.nansum(orderp[idxs] * orderv[idxs])

            # 市价单
            idxb = (orderp < 0.01) & (orderf == 1)
            idxs = (orderp < 0.01) & (orderf == 2)
            incm_b_2 = np.nansum(askp * orderv[idxb])
            incm_s_2 = np.nansum(bidp * orderv[idxs])

            incm_b = incm_b_1 + incm_b_2
            incm_s = incm_s_1 + incm_s_2

        else:
            incm_b = 0.
            incm_s = 0.
        aggrbm_list.append(incm_b)
        aggram_list.append(incm_s)

        if len(aggrbm_list) > 3:
            aggrbm = np.nanmean(aggrbm_list[-self.__lag:])
            aggram = np.nanmean(aggram_list[-self.__lag:])
            facv = self.getFactorValueList()
            if (aggrbm > 0.01) and (aggram > 0.01):
                nv = np.clip(np.log(aggrbm / aggram), a_min=-5., a_max=5.)
            elif aggrbm > 0.01:
                nv = np.nanmax(facv[-self.__emalag:])
            elif aggram > 0.01:
                nv = np.nanmin(facv[-self.__emalag:])
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
