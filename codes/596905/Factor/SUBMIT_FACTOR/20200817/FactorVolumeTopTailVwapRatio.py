#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorVolumeTopTailVwapRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self.__vwapPrice = self._getFactor(
            {
                "ClassName": "AvePrice"
            }
        )
        self._addIntermediate("VolumeList", [])
        self._addIntermediate("AmountList", [])

    def calculate(self):
        vwap = self.__vwapPrice.getLastFactorValue()

        volume = self._getLastTickData("Volume")
        amount = self._getLastTickData("Amount")
        volumeList = self.getIntermediate("VolumeList")
        amountList = self.getIntermediate("AmountList")

        if len(volumeList) == 0:
            hisVolume = self._getAllHistoricalTickData("Volume")
            hisAmount = self._getAllHistoricalTickData("Amount")
            volumeList.extend(hisVolume)
            amountList.extend(hisAmount)

        amountList.append(amount)
        volumeList.append(volume)

        volumeSlice = np.array(volumeList[-self.__window:])
        amountSlice = np.array(amountList[-self.__window:])
        top = volumeSlice > np.nanpercentile(volumeSlice, 80)
        tail = volumeSlice < np.nanpercentile(volumeSlice, 20)
        vwapTop = np.nansum(amountSlice[top]) / np.nansum(volumeSlice[top]) if np.nansum(volumeSlice[top]) != 0 else vwap
        vwapTail = np.nansum(amountSlice[tail]) / np.nansum(volumeSlice[tail]) if np.nansum(volumeSlice[tail]) != 0 else vwap

        if vwapTop != 0:
            factorValue = vwapTail / vwapTop
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




