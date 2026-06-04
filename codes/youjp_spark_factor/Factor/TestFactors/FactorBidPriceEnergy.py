#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from Factor.PyEMD import EMD
from System.Factor import Factor


class FactorBidPriceEnergy(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window") # 100
        self.__lag = self._getParameter("Lag") # 20

        self._addIntermediate("bidPriceList", [])

    def calculate(self):
        bidPrice = self._getLastTickData("BidPrice")[0]
        bidPriceList = self.getIntermediate("bidPriceList")
        bidPriceList.append(bidPrice)

        if len(bidPriceList) < self.__lag:
            factorValue = 0
        else:
            bidPriceSlice = np.array(bidPriceList[-self.__window:])
            imfs = EMD().emd(bidPriceSlice, np.arange(bidPriceSlice.shape[0]))
            trend = np.nansum(imfs[imfs.shape[0] // 2:, :], axis=0)
            trendSlice = trend[-self.__lag:]
            if np.nanstd(trendSlice) != 0:
                factorValue = np.nanmean(trendSlice) / np.nanstd(trendSlice)
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])




