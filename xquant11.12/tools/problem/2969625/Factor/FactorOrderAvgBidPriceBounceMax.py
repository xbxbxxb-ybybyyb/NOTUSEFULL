import numpy as np
from System.Factor import Factor


class FactorOrderAvgBidPriceBounceMax(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        avgPriceArray = self._getLastNTickData("AvgBidPrice", self.__lag)
        priceLimit = np.minimum.accumulate(avgPriceArray)
        priceLimit[priceLimit == 0] = np.nan
        bounce = (avgPriceArray / priceLimit - 1.) * 1000

        if np.any(~np.isnan(bounce)):
            factorValue = np.nanmax(bounce)
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)



