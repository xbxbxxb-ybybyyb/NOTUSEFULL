#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPAskPriceRetSharpe(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")
        self.__lag = self._getParameter("Lag")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )
        self.__askPrice = self._getFactor(
            {
                "ClassName": "AskVwapNum",
                "Parameters": {
                    "n": self.__level
                }
            }
        )
        self._addIntermediate("ExcessReturnList", [])

    def calculate(self):
        excessReturnList = self.getIntermediate("ExcessReturnList")
        vwapPrice = self.__vwapPrice.getLastFactorValue()
        askPrice = self.__askPrice.getLastFactorValue()
        excessReturn  = (askPrice / vwapPrice - 1.) * 100
        excessReturnList.append(excessReturn)

        excessReturnSlice = np.array(excessReturnList[-self.__lag:])
        if len(excessReturnSlice) > 0 and np.nanstd(excessReturnSlice) > 1e-6:
            factorValue = np.nanmean(excessReturnSlice) / np.nanstd(excessReturnSlice)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)





