import numpy as np
from System.Factor import Factor


class FactorOrderBidNumToNumTradesRange(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("TradeRatioList", [])

    def calculate(self):
        bidNumArray = self._getLastTickData("BidNum")
        bidNum = np.nansum(bidNumArray)
        numTrades = self._getLastTickData("NumTrades")
        tradeRatio = numTrades / bidNum if bidNum > 1e-4 else 0.

        tradeRatioList = self.getIntermediate("TradeRatioList")
        tradeRatioList.append(tradeRatio)

        tradeRatioSlice = np.array(tradeRatioList[-self.__lag:])
        factorValue = np.nanmax(tradeRatioSlice) - np.nanmin(tradeRatioSlice)

        self._addFactorValue(factorValue)



