#-*- coding:utf-8 -*-
# author: 015629
# datetime:2020/8/7 13:23
import numpy as np
from System.Factor import Factor


class FactorPriceLowHighStdVolumeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("LastPriceList", [])
        self._addIntermediate("PriceStdList", [])

    def calculate(self):
        lastPrice = self._getLastTickData("LastPrice")
        volumeList = self._getAllTodayTickData("Volume")
        lastPriceList = self.getIntermediate("LastPriceList")

        if len(lastPriceList) == 0:
            hisLastPrice = self._getAllHistoricalTickData("LastPrice")
            lastPriceList.extend(hisLastPrice)

        lastPriceList.append(lastPrice)
        priceStdList = self.getIntermediate("PriceStdList")
        priceStdList.append(np.nanstd(lastPriceList[-self.__window:]))

        priceStdSlice = np.array(priceStdList[-self.__lag:])
        volumeSlice = np.array(volumeList[-self.__lag:])
        if len(priceStdSlice) < 10:
            factorValue = 0.
        else:
            volumeHigh = np.nansum(volumeSlice[priceStdSlice > np.nanpercentile(priceStdSlice, 90)])
            volumeLow = np.nansum(volumeSlice[priceStdSlice < np.nanpercentile(priceStdSlice, 10)])

            if volumeHigh != 0:
                factorValue = volumeLow / volumeHigh
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)




