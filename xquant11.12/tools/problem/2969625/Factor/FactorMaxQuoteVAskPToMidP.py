# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/20
from System.Factor import Factor
import numpy as np


class FactorMaxQuoteVAskPToMidP(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midpW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

    def calculate(self):
        av = self._getLastTickData("AskVolume")
        ap = self._getLastTickData("AskPrice")
        maxp = self._getLastTickData("MaxPrice")
        midpw = self.__midpW.getLastFactorValue()

        if np.all(av > 1e-6) and np.all(ap > 1e-6):
            mqvp = ap[np.argmax(av)]
        else:
            mqvp = maxp

        if midpw > 1e-4:
            factor_value = (mqvp / midpw - 1) * 1e2
        else:
            factor_value = 0.

        self._addFactorValue(factor_value)
