# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/15
from System.Factor import Factor
import numpy as np


class FactorActiveTradeBidPAmtR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidPAmt", [])

    def calculate(self):
        bpm_list = self.getIntermediate("BidPAmt")

        trades = self._getLastTickData("Transactions")
        if trades is not None:
            bfs = self._getTransactionData("BSFlag", trades)
            brs = self._getTransactionData("BidOrder", trades)
            bms = self._getTransactionData("Amount", trades)
            br_dict = dict()
            for i in range(len(bfs)):
                if bfs[i] == 1:
                    if brs[i] not in br_dict:
                        br_dict[brs[i]] = bms[i]
                    else:
                        br_dict[brs[i]] += bms[i]
            if br_dict:
                bpm = np.sum(list(br_dict.values())) / len(br_dict)
            else:
                bpm = 0.
        else:
            bpm = 0.
        bpm_list.append(bpm)

        bpmn = np.nanmean(bpm_list[-self.__lag:])
        if bpmn > 0.01:
            nv = bpm / bpmn
        else:
            nv = 1.

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
