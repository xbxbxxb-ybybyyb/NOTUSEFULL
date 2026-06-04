import numpy as np
from System.Factor import Factor


class FactorOrderAvgBidPriceBounceZscore(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        avgPriceArray = self._getLastNTickData("AvgBidPrice", self.__lag)
        priceMin = np.minimum.accumulate(avgPriceArray)
        bounce = (avgPriceArray / priceMin - 1.) * 1000
        bounceStd = np.nanstd(bounce)
        if bounceStd > 1e-6:
            factorValue = (bounce[-1] - np.nanmean(bounce)) / bounceStd
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



