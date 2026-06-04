import numpy as np
from System.Factor import Factor


class FactorPriceLevelStable(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lookback = self._getParameter("LookBack")
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RetList", [])

    def calculate(self):
        price = self._getLastTickData("LastPrice")
        priceList = self._getLastNTickData("LastPrice", self.__lookback)
        volumeList = self._getLastNTickData("Volume", self.__lookback)

        zipList = sorted(list(zip(priceList, volumeList)))
        priceList, volumeList = [i[0] for i in zipList], [i[1] for i in zipList]
        priceMid = self.get_price_level(0.5, priceList, volumeList)

        ret = (price / priceMid - 1) * 1000

        retList = self.getIntermediate("RetList")
        retList.append(ret)
        retSlice = retList[-self.__lag:]

        if np.nanstd(retSlice) > 1e-5:
            factorValue = np.nanmean(retSlice) / np.nanstd(retSlice)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)

    @staticmethod
    def get_price_level(ratio, priceList, volumeList):
        i = 0
        target_volume = np.nansum(volumeList) * ratio
        cum_vol = 0
        while i < len(priceList) and cum_vol < target_volume:
            cum_vol += volumeList[i]
            i += 1
        return priceList[i - 1]

