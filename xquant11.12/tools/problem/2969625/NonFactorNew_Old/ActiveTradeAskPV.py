# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/18
from System.Factor import Factor


class ActiveTradeAskPV(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        trade = self._getLastTickData("Transactions")
        if trade is not None:
            tradef = self._getTransactionData("BSFlag", trade)
            tradep = self._getTransactionData("Price", trade)
            tradev = self._getTransactionData("Volume", trade)
            tradepv = dict()
            for i in range(len(trade)):
                if tradef[i] == 2:
                    tradepv[tradep[i]] = tradepv.get(tradep[i], 0.) + tradev[i]
            factorValue = tradepv
        else:
            factorValue = dict()

        self._addFactorValue(factorValue)
