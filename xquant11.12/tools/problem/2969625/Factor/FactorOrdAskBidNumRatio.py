import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("NumRatioList", [])

    def calculate(self):
        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            askNum = (bsFlag == 2).sum()
            bidNum = (bsFlag == 1).sum()
            if bidNum != 0:
                numRatio = askNum / bidNum
            else:
                numRatio = None
        else:
            numRatio = None

        numRatioList = self.getIntermediate("NumRatioList")
        numRatioList.append(numRatio)

        filterNumRatioList = list(filter(lambda x: x is not None, numRatioList))

        factorValue = np.nanmean(filterNumRatioList[-self.__lag:])

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)




