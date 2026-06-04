# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/15
from System.Factor import Factor
import numpy as np


class FactorActiveTradeAmtABR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__emalag = self._getParameter("EMALag")

        self._addIntermediate("BidTradeAmount", [])
        self._addIntermediate("AskTradeAmount", [])

    def calculate(self):
        bta_list = self.getIntermediate("BidTradeAmount")
        ata_list = self.getIntermediate("AskTradeAmount")

        trades = self._getLastTickData("Transactions")
        if trades is not None:
            bfs = self._getTransactionData("BSFlag", trades)
            amts = self._getTransactionData("Amount", trades)
            bta_list.append(np.nansum(amts[bfs == 1]))
            ata_list.append(np.nansum(amts[bfs == 2]))
        else:
            bta_list.append(0)
            ata_list.append(0)

        if len(bta_list) < 3:
            factorValue = 0.
        else:
            bta = np.nansum(bta_list[-self.__lag:])
            ata = np.nansum(ata_list[-self.__lag:])

            facv = self.getFactorValueList()
            if (ata > 0.01) and (bta > 0.01):
                nv = np.clip(np.log(bta / ata), a_max=5., a_min=-5.)
            elif ata > 0.01:
                nv = np.nanmin(facv[-self.__emalag:])
            elif bta > 0.01:
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
