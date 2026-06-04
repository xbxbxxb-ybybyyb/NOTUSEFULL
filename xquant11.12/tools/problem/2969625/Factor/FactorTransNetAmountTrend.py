#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorTransNetAmountTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NetAmountRatioList", [])

    def calculate(self):
        netAmountRatioList = self.getIntermediate("NetAmountRatioList")
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            price = self._getTransactionData("Price", transaction)
            volume = self._getTransactionData("Volume", transaction)
            amount = volume * price
            bidAmount = np.nansum(amount[bsFlag == 1])
            askAmount = np.nansum(amount[bsFlag == 2])
            totalVolume = bidAmount + askAmount
            netVolumeRatio = (bidAmount - askAmount) / totalVolume if totalVolume > 0 else 0.
            netAmountRatioList.append(netVolumeRatio)
        else:
            netAmountRatioList.append(None)
        filterNetAmountRatioList = list(filter(lambda x: x is not None, netAmountRatioList))

        netAmountArray = np.array(filterNetAmountRatioList[-self.__lag:])
        if len(netAmountArray) > 1:
            factorValue = np.corrcoef(netAmountArray, np.arange(len(netAmountArray)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)




