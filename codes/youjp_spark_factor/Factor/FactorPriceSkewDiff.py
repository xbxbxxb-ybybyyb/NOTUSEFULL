#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPriceSkewDiff(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("BidPriceList", [])
        self._addIntermediate("AskPriceList", [])

    def calculate(self):
        bidPrice = self._getLastTickData("BidPrice")[0]
        askPrice = self._getLastTickData("AskPrice")[0]
        bidPriceList = self.getIntermediate("BidPriceList")
        askPriceList = self.getIntermediate("AskPriceList")
        bidPriceList.append(bidPrice)
        askPriceList.append(askPrice)

        bidPriceSlice = np.array(bidPriceList[-self.__lag:])
        askPriceSlice = np.array(askPriceList[-self.__lag:])
        if len(askPriceSlice) <= 1:
            factorValue = 0.
        else:
            factorValue = self.__compute_skew(bidPriceSlice) - self.__compute_skew(askPriceSlice)

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_skew(arr):
        if len(arr) <= 1:
            return np.nan
        else:
            arr_mean = np.nanmean(arr)
            arr_std = np.nanstd(arr)
            three = np.nanmean((arr - arr_mean)**3)
            skew = three / arr_std**3 if arr_std != 0 else 0
            return skew





