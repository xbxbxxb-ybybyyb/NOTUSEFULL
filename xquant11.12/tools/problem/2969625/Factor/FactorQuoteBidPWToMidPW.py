# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/08
from System.Factor import Factor
import numpy as np


class FactorQuoteBidPWToMidPW(Factor):
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
        bidp = self._getLastTickData("BidPrice")[:self.__g]
        bidv = self._getLastTickData("BidVolume")[:self.__g]
        midpw = self.__midpW.getLastFactorValue()

        if np.nansum(bidv) < 0.01:
            bidpw = self._getLastTickData("MinPrice")
        else:
            bidpw = np.nansum(bidp * bidv) / np.nansum(bidv)

        factorValue = (bidpw / midpw - 1) * 100

        self._addFactorValue(factorValue)
