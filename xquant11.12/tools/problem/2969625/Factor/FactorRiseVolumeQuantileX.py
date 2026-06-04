#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorRiseVolumeQuantileX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("SmoothLag")

        self._addIntermediate("RiseRatioList", [])

    def calculate(self):
        riseRatioList = self.getIntermediate("RiseRatioList")
        if len(riseRatioList) == 0:
            riseRatio = 0.
        else:
            rise, mid, drop = self.__compute_rise_drop_volume()
            if rise + mid + drop > 1e-6:
                riseRatio = rise / (rise + mid + drop)
            else:
                riseRatio = 0.

        riseRatioList.append(riseRatio)
        riseRatioSlice = np.array(riseRatioList[-self.__lag:])

        if len(riseRatioSlice) < 5:
            factorValue = 0.
        else:
            factorValue = np.sum(riseRatioSlice < riseRatioSlice[-1]) / len(riseRatioSlice) - 0.5

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(factorValue, factorValueList, self.__sLag)

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

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])







