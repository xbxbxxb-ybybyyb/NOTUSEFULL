#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
import pandas as pd
from System.Factor import Factor


class FactorPriceDiffSkew(Factor):
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
            weight = np.linspace(0, 1, priceDiffArray.shape[0])
            weight = weight / np.nansum(weight)
            mean = np.nansum(priceDiffArray * weight)
            std = np.nansum((priceDiffArray - mean)**2 * weight)
            three = np.nansum((priceDiffArray - mean)**3 * weight)
            factorValue = three / np.sqrt(std) ** 3 if std != 0 else 0

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





