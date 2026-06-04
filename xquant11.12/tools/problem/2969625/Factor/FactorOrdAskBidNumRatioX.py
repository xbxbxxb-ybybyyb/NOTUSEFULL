import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNumRatioX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self._addIntermediate("NumRatioList", [])

    def calculate(self):
        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            askNum = (bsFlag == 2).sum()
            bidNum = (bsFlag == 1).sum()
            if bidNum > 0:
                numRatio = 1. - askNum / bidNum
            else:
                numRatio = 0.
        else:
            numRatio = 0.

        numRatioList = self.getIntermediate("NumRatioList")
        numRatioList.append(numRatio)

        factorValue = np.nanmean(numRatioList[-self.__window:])

        self._addFactorValue(factorValue)




