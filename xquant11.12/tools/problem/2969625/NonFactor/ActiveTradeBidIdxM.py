# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/03/22
# @time: 2022/03/22
from System.Factor import Factor
import numpy as np


class ActiveTradeBidIdxM(Factor):
    def calculate(self):
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsflag = self._getTransactionData("BSFlag", transaction)
            bidr = self._getTransactionData("BidOrder", transaction)[bsflag == 1]
            amount = self._getTransactionData("Amount", transaction)[bsflag == 1]

            bid_order_dict = {}
            for i in range(len(bidr)):
                br = bidr[i]
                if br in bid_order_dict:
                    bid_order_dict[br] += amount[i]
                else:
                    bid_order_dict[br] = amount[i]

            factorValue = bid_order_dict
        else:
            factorValue = dict()

        self._addFactorValue(factorValue)
