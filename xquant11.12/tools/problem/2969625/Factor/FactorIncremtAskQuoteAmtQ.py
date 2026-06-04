# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/26
from System.Factor import Factor
import numpy as np


class FactorIncremtAskQuoteAmtQ(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("IncremtAskQuoteAmount", [])

    def calculate(self):
        iaqm_list = self.getIntermediate("IncremtAskQuoteAmount")

        askp = self._getLastNTickData("AskPrice", 2)[0][0]
        bidp = self._getLastNTickData("BidPrice", 2)[0][0]
        order = self._getLastTickData("Orders")

        if order is not None:
            if bidp < 0.01:
                incm = 0.
            else:
                if askp < 0.01:
                    upp = self._getLastTickData("MaxPrice")
                    downp = upp * (1 - 0.005)
                else:
                    downp = bidp
                    upp = askp * (1 + 0.005)

                orderp = self._getOrderData("Price", order)
                orderv = self._getOrderData("Volume", order)
                orderf = self._getOrderData("BSFlag", order)
                idxs = (orderp > downp) & (orderp < upp + 0.001) & (orderf == 2)
                idxb_1 = (orderp > downp) & (orderf == 1)  # 非市价单
                idxb_2 = (orderp < 0.01) & (orderf == 1)  # 市价单
                incm = np.nansum(orderp[idxs] * orderv[idxs]) - np.nansum(orderp[idxb_1] * orderv[idxb_1]) - np.nansum(askp * orderv[idxb_2])
        else:
            incm = 0.
        iaqm_list.append(incm)

        if len(iaqm_list) > 10:
            nv = -np.nansum(np.array(iaqm_list[-self.__lag:]) < incm) / len(iaqm_list[-self.__lag:])
            facv = self.getFactorValueList()
            factorValue = self.__ema(nv, facv, 5)
        else:
            factorValue = -0.5

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
