# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/22
from System.Factor import Factor
import numpy as np


class ActiveTradeAskIdxM(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsflag = self._getTransactionData("BSFlag", transaction)
            askr = self._getTransactionData("AskOrder", transaction)[bsflag == 2]
            amount = self._getTransactionData("Amount", transaction)[bsflag == 2]

            ask_order_dict = {}
            for i in range(len(askr)):
                ar = askr[i]
                if ar in ask_order_dict:
                    ask_order_dict[ar] += amount[i]
                else:
                    ask_order_dict[ar] = amount[i]

            factorValue = ask_order_dict

        else:
            factorValue = dict()

        self._addFactorValue(factorValue)
