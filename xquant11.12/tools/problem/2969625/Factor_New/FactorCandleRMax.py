# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/06
from System.Factor import Factor
import numpy as np


class FactorCandleRMax(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__rl = self._getParameter("RLag")

        self.__midPW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

    def calculate(self):
        midpw = self.__midPW.getFactorValueList()[-self.__lag:]
        n = len(midpw) // self.__rl
        if n == 0:
            factorValue = -(midpw[-1] / midpw[0] - 1) * 100
        else:
            midpc = [midpw[-1 - i * self.__rl] for i in range(n)]
            midpo = [midpw[-(i + 1) * self.__rl] for i in range(n)]
            cr = (np.divide(midpc, midpo) - 1) * 100
            factorValue = -np.nanmax(cr)

        self._addFactorValue(factorValue)
