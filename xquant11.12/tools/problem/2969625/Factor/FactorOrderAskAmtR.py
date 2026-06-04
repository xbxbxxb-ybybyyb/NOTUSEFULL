# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/27
from System.Factor import Factor
import numpy as np


class FactorOrderAskAmtR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__r = self._getParameter("R")

        self._addIntermediate("AggrAskOrderAmount", [])

    def calculate(self):
        aggram_list = self.getIntermediate("AggrAskOrderAmount")

        askp = self._getLastNTickData("AskPrice", 2)[0][0]
        bidp = self._getLastNTickData("BidPrice", 2)[0][0]
        order = self._getLastTickData("Orders")

        if order is not None:
            if bidp < 0.01:
                incm = 0.
            else:
                if askp < 0.01:
                    benchmp = self._getLastTickData("MaxPrice")
                else:
                    benchmp = askp * (1 + self.__r)

                orderp = self._getOrderData("Price", order)
                orderv = self._getOrderData("Volume", order)
                orderf = self._getOrderData("BSFlag", order)

                # 非市价单
                idxs = (orderp < benchmp) & (orderf == 2) & (orderp > 0.01)
                incm_1 = np.nansum(orderp[idxs] * orderv[idxs])

                # 市价单
                idxs = (orderp < 0.01) & (orderf == 2)
                incm_2 = np.nansum(bidp * orderv[idxs])

                incm = incm_1 + incm_2

        else:
            incm = 0.
        aggram_list.append(incm)

        if len(aggram_list) > 3:
            meanv = np.nanmean(aggram_list[-self.__lag:])
            facv = self.getFactorValueList()
            if (incm < 0.01) or (meanv < 0.01):  # 长时间无新增卖单
                nv = np.nanmax(facv[-self.__lag:])
            else:
                nv = -np.clip(np.log(incm / meanv), a_min=-5., a_max=5.)
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.6

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
