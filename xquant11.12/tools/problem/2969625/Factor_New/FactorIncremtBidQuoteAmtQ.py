# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/26
from System.Factor import Factor
import numpy as np


class FactorIncremtBidQuoteAmtQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("IncremtBidQuoteAmount", [])

    def calculate(self):
        ibqm_list = self.getIntermediate("IncremtBidQuoteAmount")

        askp = self._getLastNTickData("AskPrice", 2)[0][0]
        bidp = self._getLastNTickData("BidPrice", 2)[0][0]
        order = self._getLastTickData("Orders")

        if order is not None:
            if askp < 0.01:  # 涨停
                incm = 0.
            else:
                if bidp < 0.01:
                    downp = self._getLastTickData("MinPrice")
                    upp = downp * (1 + 0.005)
                else:
                    downp = bidp * (1 - 0.005)
                    upp = askp

                orderp = self._getOrderData("Price", order)
                orderv = self._getOrderData("Volume", order)
                orderf = self._getOrderData("BSFlag", order)
                idxb = (orderp < upp) & (orderp > downp - 0.001) & (orderf == 1)
                idxs = (orderp < upp) & (orderf == 2)  # 包含了市价单
                incm = np.nansum(orderp[idxb] * orderv[idxb]) - np.nansum(orderp[idxs] * orderv[idxs])
        else:
            incm = 0.
        ibqm_list.append(incm)

        if len(ibqm_list) > 10:
            nv = np.nansum(np.array(ibqm_list[-self.__lag:]) < incm) / len(ibqm_list[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = 0.5

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
