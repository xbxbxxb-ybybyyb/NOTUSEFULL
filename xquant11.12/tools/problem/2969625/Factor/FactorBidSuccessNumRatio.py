import numpy as np
from System.Factor import Factor


class FactorBidSuccessNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("SuccessRatioList", [])

    def calculate(self):
        numArray = self._getLastNTickData("AskNum", 2)[0]
        gdNum = np.nansum(numArray)
        transaction = self._getLastTickData("Transactions")

        if transaction is not None:
            bsFlag = self._getTransactionData("BSFlag", transaction)
            tradeNum = (bsFlag == 1).sum()
        else:
            tradeNum = 0.

        successRatio = tradeNum / gdNum if gdNum != 0 else 0
        successRatioList = self.getIntermediate("SuccessRatioList")
        successRatioList.append(successRatio)

        factorValue = np.nanmean(successRatioList[-self.__lag:])

        self._addFactorValue(factorValue)







