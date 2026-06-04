import numpy as np
from System.Factor import Factor


class FactorOrderAskNumToNumTradesRange(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("TradeRatioList", [])

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        askNum = np.nansum(askNumArray)
        numTrades = self._getLastTickData("NumTrades")
        tradeRatio = numTrades / askNum if askNum > 1e-4 else 0.

        tradeRatioList = self.getIntermediate("TradeRatioList")
        tradeRatioList.append(tradeRatio)

        tradeRatioSlice = np.array(tradeRatioList[-self.__lag:])
        factorValue = np.nanmax(tradeRatioSlice) - np.nanmin(tradeRatioSlice)

        self._addFactorValue(factorValue)



