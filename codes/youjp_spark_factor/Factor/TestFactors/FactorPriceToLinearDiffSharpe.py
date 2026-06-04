#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPriceToLinearDiffSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        priceList = self.__midPrice.getFactorValueList()
        if len(priceList) < 5:
            factorValue = 0.
        else:
            priceSlice = np.array(priceList[-self.__lag:])
            startPrice = priceSlice[0]
            endPrice = priceSlice[-1]
            linearPriceSlice = startPrice + (endPrice - startPrice) * np.linspace(0, 1, priceSlice.shape[0])
            factorValue = np.nanmean(linearPriceSlice) / np.nanstd(linearPriceSlice) if np.nanstd(linearPriceSlice) != 0 else 0

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





