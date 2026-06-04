import numpy as np
from System.Factor import Factor


class FactorOrderAvgOfferPriceBounceStdRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        avgPriceArray = self._getLastNTickData("AvgOfferPrice", self.__lag)
        priceLimit = np.minimum.accumulate(avgPriceArray)
        priceLimit[priceLimit == 0] = np.nan
        bounce = (avgPriceArray / priceLimit - 1.) * 1000
        mbb = np.nanmax(bounce)

        lastPriceArray = self._getLastNTickData("LastPrice", self.__lag + 1)
        lastPriceArray[lastPriceArray == 0] = np.nan
        if len(lastPriceArray) < 5:
            factorValue = 0
        else:
            ret = (lastPriceArray[1:] / lastPriceArray[:-1] - 1.) * 1000
            retStd = np.nanstd(ret)
            if retStd > 1e-6 and not np.isnan(mbb):
                factorValue = mbb / retStd
            else:
                lastFactorValue = self.getLastFactorValue()
                if lastFactorValue is not None:
                    factorValue = lastFactorValue
                else:
                    factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)



