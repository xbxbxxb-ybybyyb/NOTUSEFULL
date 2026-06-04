#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorRiseVolumeTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RiseRatioList", [])

    def calculate(self):
        riseRatioList = self.getIntermediate("RiseRatioList")
        if len(riseRatioList) == 0:
            riseRatio = 0.
        else:
            rise, mid, drop = self.__compute_rise_drop_volume()
            if rise + mid + drop != 0:
                riseRatio = rise / (rise + mid + drop)
            else:
                riseRatio = 0.

        riseRatioList.append(riseRatio)
        riseRatioSlice = np.array(riseRatioList[-self.__lag:])

        factorValue = np.corrcoef(riseRatioSlice, np.arange(len(riseRatioSlice)))[0, 1]
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def __compute_rise_drop_volume(self):
        rise, mid, drop = 0, 0, 0
        lastBidP0 = self._getLastNTickData("BidPrice", 2)[0][0]
        lastAskP0 = self._getLastNTickData("AskPrice", 2)[0][0]
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            Price = self._getTransactionData("Price", transaction)
            Volume = self._getTransactionData("Volume", transaction)
            for i in range(transaction.shape[0]):
                if Price[i] >= lastAskP0:
                    rise += Volume[i]
                elif Price[i] <= lastBidP0:
                    drop += Volume[i]
                else:
                    mid += Volume[i]
        return rise, mid, drop







