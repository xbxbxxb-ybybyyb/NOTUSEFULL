# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/05/06
from System.Factor import Factor
import numpy as np


class FactorCandleHL(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

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
        dh = (midpw[-1] / np.nanmax(midpw) - 1) * 100
        dl = (midpw[-1] / np.nanmin(midpw) - 1) * 100
        if np.abs(dh) > np.abs(dl):
            factorValue = -dh
        elif np.abs(dl) > np.abs(dh):
            factorValue = -dl
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)
