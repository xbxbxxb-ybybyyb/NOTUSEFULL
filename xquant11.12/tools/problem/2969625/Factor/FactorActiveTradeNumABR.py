# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/14
from System.Factor import Factor
import numpy as np


class FactorActiveTradeNumABR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__emalag = self._getParameter("EMALag")

        self._addIntermediate("BidTradeNum", [])
        self._addIntermediate("AskTradeNum", [])

    def calculate(self):
        btn_list = self.getIntermediate("BidTradeNum")
        atn_list = self.getIntermediate("AskTradeNum")

        trades = self._getLastTickData("Transactions")
        if trades is not None:
            bfs = self._getTransactionData("BSFlag", trades)
            brs = self._getTransactionData("BidOrder", trades)
            ars = self._getTransactionData("AskOrder", trades)
            br_list = []
            ar_list = []
            for i in range(len(bfs)):
                if bfs[i] == 1:
                    if brs[i] not in br_list:
                        br_list.append(brs[i])
                else:
                    if ars[i] not in ar_list:
                        ar_list.append(ars[i])
            btn_list.append(len(br_list))
            atn_list.append(len(ar_list))
        else:
            btn_list.append(0)
            atn_list.append(0)

        if len(btn_list) < 3:
            factorValue = 0.
        else:
            btn = np.nansum(btn_list[-self.__lag:])
            atn = np.nansum(atn_list[-self.__lag:])

            facv = self.getFactorValueList()
            if (atn > 0.01) and (btn > 0.01):
                nv = np.clip(np.log(btn / atn), a_max=5., a_min=-5.)
            elif atn > 0.01:
                nv = np.nanmin(facv[-self.__emalag:])
            elif btn > 0.01:
                nv = np.nanmax(facv[-self.__emalag:])
            else:
                nv = 0.

            factorValue = self.__ema(nv, facv, self.__emalag)

        self._addFactorValue(factorValue)

    @staticmethod
    def __ema(x, xs, n):
        if len(xs) > 0:
            param = 2. / min(len(xs), n)
            ema_x = xs[-1] + param * (x - xs[-1])
        else:
            ema_x = x
        return ema_x
