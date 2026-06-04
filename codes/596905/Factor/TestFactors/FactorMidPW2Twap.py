#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorMidPW2Twap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")

        self.__twapPrice = self._getFactor(
            {
                "ClassName": "TwapPrice"
            }
        )

        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": self.__level,
                }
            }
        )

    def calculate(self):
        twapPrice = self.__twapPrice.getLastFactorValue()
        midPriceW = self.__midPriceW.getLastFactorValue()

        factorValue = midPriceW / twapPrice - 1.

        self._addFactorValue(factorValue)





