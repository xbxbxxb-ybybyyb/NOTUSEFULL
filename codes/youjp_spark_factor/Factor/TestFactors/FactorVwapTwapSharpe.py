#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorVwapTwapSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )
        self.__twapPrice = self._getFactor(
            {
                "ClassName": "TwapPrice"
            }
        )


    def calculate(self):
        vwapPriceList = self.__vwapPrice.getFactorValueList()
        twapPriceList = self.__twapPrice.getFactorValueList()
        priceDiff = np.array(vwapPriceList[-self.__window:]) - np.array(twapPriceList[-self.__window:])
        if np.nanstd(priceDiff) != 0:
            factorValue = np.nanmean(priceDiff) / np.nanstd(priceDiff)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)





