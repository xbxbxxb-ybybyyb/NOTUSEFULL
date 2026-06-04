from System.Factor import Factor
import numpy as np

class FactorBidNumKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__Lag = self._getParameter("Lag")
        self._addIntermediate("BidNumList", [])

    def calculate(self):
        bidNumList = self.getIntermediate("BidNumList")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            bidNumList.append(np.sum(bsFlag == 1))
        else:
            bidNumList.append(0)

        bidNums = bidNumList[-self.__Lag:]
        L = len(bidNums)

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            # orderAskVolDif = np.diff(orderAskVolume)
            factorValue = np.corrcoef(np.arange(len(bidNums)), bidNums)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)
