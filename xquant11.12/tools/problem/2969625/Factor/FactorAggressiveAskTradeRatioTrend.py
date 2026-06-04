import numpy as np
from System.Factor import Factor


class FactorAggressiveAskTradeRatioTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("ActiveRatioList", [])

    def calculate(self):
        bidP0 = self._getLastNTickData("BidPrice", 2)[0][0]
        transaction = self._getLastTickData("Transactions")
        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            price = self._getTransactionData("Price", transaction)
            volume = self._getTransactionData("Volume", transaction)
            amount = price * volume
            activeAmount = amount[(bsFlag == 2) & (price < bidP0 + 1e-4)].sum()
            totalAmount = amount[bsFlag == 2].sum()
            activeRatio = activeAmount / totalAmount if totalAmount > 1e-6 else 0.
        else:
            activeRatio = 0.

        activeRatioList = self.getIntermediate("ActiveRatioList")
        activeRatioList.append(activeRatio)

        activeRatioSlice = np.array(activeRatioList[-self.__lag:])
        if len(activeRatioSlice) > 1:
            factorValue = np.corrcoef(activeRatioSlice, np.arange(len(activeRatioSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)







