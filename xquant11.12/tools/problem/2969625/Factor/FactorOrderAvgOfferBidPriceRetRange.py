import numpy as np
from System.Factor import Factor


class FactorOrderAvgOfferBidPriceRetRange(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RetList", [])

    def calculate(self):
        AvgOfferPrice = self._getLastTickData("AvgOfferPrice")
        AvgBidPrice = self._getLastTickData("AvgBidPrice")
        if AvgBidPrice > 1e-4:
            ret = (AvgOfferPrice / AvgBidPrice - 1) * 1000
        else:
            ret = 0.

        retList = self.getIntermediate("RetList")
        retList.append(ret)
        retSlice = np.array(retList[-self.__lag:])
        factorValue = np.nanmax(retSlice) - np.nanmin(retSlice)

        self._addFactorValue(factorValue)



