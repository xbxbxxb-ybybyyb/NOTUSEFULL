#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorMaPriceBollingUp(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lltLag = self._getParameter("LLTLag")
        self.__window = self._getParameter("Window")

        self.__midPriceLLT = self._getFactor(
            {
                "ClassName": "LLTFilter",
                "Parameters": {
                    "Lag": self.__lltLag,
                    "FilterObj": "MidPrice"
                }
            }
        )
        self._addIntermediate("PriceMeanList", [])
        self._addIntermediate("PriceStdList", [])

    def calculate(self):
        midPriceList = self.__midPriceLLT.getFactorValueList()
        priceMean = np.nanmean(midPriceList[-self.__window:])
        priceStd = np.nanstd(midPriceList[-self.__window:]) if len(midPriceList) > 1 else 0.
        priceMeanList = self.getIntermediate("PriceMeanList")
        priceStdList = self.getIntermediate("PriceStdList")
        priceMeanList.append(priceMean)
        priceStdList.append(priceStd)

        bollingUp = np.array(midPriceList[-len(priceMeanList):]) - (np.array(priceMeanList) + np.array(priceStdList))
        factorValue = bollingUp[bollingUp > 1e-6].sum() / np.nansum(priceStdList) if (np.nansum(priceStdList) > 1e-6) else 0
        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





