#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from scipy.fftpack import fft
from System.Factor import Factor


class FactorPriceDiffAngle_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )

    def calculate(self):
        midPriceList = self.__midPrice.getFactorValueList()
        vwapPriceList = self.__vwapPrice.getFactorValueList()
        priceDiffArray = np.array(midPriceList) - np.array(vwapPriceList)

        if len(priceDiffArray) > 3:
            lookBack = self.__lag if self.__lag < len(priceDiffArray) else 3
            factorValue = np.nanmean(np.angle(fft(priceDiffArray))[-lookBack:])
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)





