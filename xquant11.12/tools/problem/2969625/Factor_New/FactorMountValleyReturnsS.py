# ! /usr/bin/env python3
# ! -*- coding:utf-8 -*-
# @author: 015619
# @time: 2022/04/01
from System.Factor import Factor


class FactorMountValleyReturnsS(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__wd = self._getParameter("Window")

        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1
                }
            }
        )
        self.__mvMidpW = self._getFactor(
            {
                "ClassName": "MountValleyMidpWM",
                "Parameters": {
                    "Grade": 1,
                    "Window": self.__wd
                }
            }
        )

    def calculate(self):

        midpw = self.__midPriceW.getFactorValueList()
        mvs = self.__mvMidpW.getLastFactorValue()

        factorValue = -(midpw[-1] / mvs[1] - 1) * (len(midpw) - mvs[0]) * 1e2

        self._addFactorValue(factorValue)
