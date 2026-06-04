import numpy as np
from System.Factor import Factor


class FactorOrderAvgOfferPriceBounceZscoreX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

    def calculate(self):
        avgPriceArray = self._getLastNTickData("AvgOfferPrice", self.__lag)
        maxPrice = self._getLastTickData("MaxPrice")
        if len(avgPriceArray) < min(5, self.__sLag):
            factorValue = 0.
        else:
            priceBase = np.maximum.accumulate(avgPriceArray)
            priceBase[priceBase < 1e-4] = maxPrice
            bounce = (avgPriceArray / priceBase - 1.) * 1000
            bounceStd = np.nanstd(bounce)
            if bounceStd > 1e-6:
                factorValue = (bounce[-1] - np.nanmean(bounce[-self.__sLag:])) / bounceStd
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)



