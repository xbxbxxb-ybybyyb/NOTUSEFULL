# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/07
from System.Factor import Factor
import numpy as np


class FactorQuoteAskPWToMidPW(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__g = self._getParameter("Grade")

        self.__midpW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

    def calculate(self):
        askp = self._getLastTickData("AskPrice")[:self.__g]
        askv = self._getLastTickData("AskVolume")[:self.__g]
        midpw = self.__midpW.getLastFactorValue()

        if np.nansum(askv) < 0.01:
            askpw = self._getLastTickData("MaxPrice")
        else:
            askpw = np.nansum(askp * askv) / np.nansum(askv)

        factorValue = (askpw / midpw - 1) * 100

        self._addFactorValue(factorValue)
