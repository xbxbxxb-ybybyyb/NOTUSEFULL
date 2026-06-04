from System.Factor import Factor
import numpy as np

class FactorBidNumRatioM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__Lag = self._getParameter("Lag")
        self._addIntermediate("TotOrderNumList", [])
        self._addIntermediate("BidOrderNumList", [])

    def calculate(self):
        TotOrderNumList = self.getIntermediate("TotOrderNumList")
        BidOrderNumList = self.getIntermediate("BidOrderNumList")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            TotOrderNumList.append(len(bsFlag))
            BidOrderNumList.append(np.sum(bsFlag == 1))
        else:
            TotOrderNumList.append(0)
            BidOrderNumList.append(0)

        totNum = np.sum(TotOrderNumList[self.__Lag:])
        bidNum = np.sum(BidOrderNumList[self.__Lag:])

        if totNum < 1:
            factorValue = 0.5
        else:
            factorValue = bidNum / totNum

        self._addFactorValue(factorValue)
