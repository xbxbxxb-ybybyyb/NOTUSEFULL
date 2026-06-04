#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorVolumeTopTailVwapRatioX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )

    def calculate(self):
        vwap = self.__vwapPrice.getLastFactorValue()

        volumeArray = self._getLastNTodayTickData("Volume", self.__window)
        amountArray = self._getLastNTodayTickData("Amount", self.__window)
        if len(volumeArray) < self.__window:
            hisVolumeArray = self._getAllHistoricalTickData("Volume")
            hisAmountArray = self._getAllHistoricalTickData("Amount")
            volumeArray = np.append(hisVolumeArray[-(self.__window - len(volumeArray)):], volumeArray)
            amountArray = np.append(hisAmountArray[-(self.__window - len(amountArray)):], amountArray)

        top = volumeArray > np.nanpercentile(volumeArray, 80)
        tail = volumeArray < np.nanpercentile(volumeArray, 20)
        topV = np.nansum(volumeArray[top])
        tailV = np.nansum(volumeArray[tail])
        vwapTop = np.nansum(amountArray[top]) / topV if topV > 1e-4 else vwap
        vwapTail = np.nansum(amountArray[tail]) / tailV if tailV > 1e-4 else vwap

        if vwapTop > 1e-4:
            factorValue = (vwapTail / vwapTop - 1. ) * 1000
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




