#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPriceDiffSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )

    def calculate(self):
        midPriceList = self.__midPrice.getFactorValueList()
        vwapPriceList = self.__vwapPrice.getFactorValueList()
        priceDiffArray = np.array(midPriceList[-self.__lag:]) - np.array(vwapPriceList[-self.__lag:])
        if len(priceDiffArray) <= 1:
            factorValue = 0.
        else:
            factorValue = np.nanmean(priceDiffArray) / np.nanstd(priceDiffArray) if np.nanstd(priceDiffArray) > 1e-6 else 0

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





