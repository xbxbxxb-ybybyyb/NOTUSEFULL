import numpy as np
from System.Factor import Factor


class FactorPriceToBidMaxRange(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("RetList", [])

    def calculate(self):
        bidNum = self._getLastTickData("BidNum")
        bidPrice = self._getLastTickData("BidPrice")
        lastPrice = self._getLastTickData("LastPrice")

        maxPrice = bidPrice[np.argmax(bidNum)]
        ret = (lastPrice / maxPrice - 1) * 1000 if maxPrice > 1e-6 else 0.
        retList = self.getIntermediate("RetList")
        retList.append(ret)
        retSlice = np.array(retList[-self.__lag:])
        factorValue = np.nanmax(retSlice) - np.nanmin(retSlice)

        self._addFactorValue(factorValue)



