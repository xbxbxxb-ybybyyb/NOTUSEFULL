#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorVwapTwapRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

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
        vwapPrice = self.__vwapPrice.getLastFactorValue()
        twapPrice = self.__twapPrice.getLastFactorValue()

        factorValue = vwapPrice / twapPrice - 1.

        self._addFactorValue(factorValue)





