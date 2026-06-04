import numpy as np
from System.Factor import Factor


class FactorOrderAvgOfferPriceBounceStdRatioX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        avgPriceArray = self._getLastNTickData("AvgOfferPrice", self.__lag)
        minPrice = self._getLastTickData("MinPrice")
        priceBase = np.minimum.accumulate(avgPriceArray)
        priceBase[priceBase < 1e-4] = minPrice
        bounce = (avgPriceArray / priceBase - 1.) * 1000
        mbb = np.nanmax(bounce)

        lastPriceArray = self._getLastNTickData("LastPrice", self.__lag + 1)
        if len(lastPriceArray) < 5:
            factorValue = 0.
        else:
            ret = (lastPriceArray[1:] / lastPriceArray[:-1] - 1.) * 1000
            retStd = np.nanstd(ret)
            if retStd > 1e-6:
                factorValue = mbb / retStd
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        self._addFactorValue(factorValue)



