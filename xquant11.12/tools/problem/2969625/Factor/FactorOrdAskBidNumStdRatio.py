import numpy as np
from System.Factor import Factor


class FactorOrdAskBidNumStdRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("AskNumList", [])
        self._addIntermediate("BidNumList", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNumList")
        bidNumList = self.getIntermediate("BidNumList")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            askNumList.append((bsFlag == 2).sum())
            bidNumList.append((bsFlag == 1).sum())
        else:
            askNumList.append(None)
            bidNumList.append(None)

        filterAskNumList = list(filter(lambda x: x is not None, askNumList))
        filterBidNumList = list(filter(lambda x: x is not None, bidNumList))
        askNumSlice = np.array(filterAskNumList[-self.__lag:])
        bidNumSlice = np.array(filterBidNumList[-self.__lag:])

        bidNumStd = np.nanstd(bidNumSlice)
        if bidNumStd > 1e-6:
            factorValue = np.nanstd(askNumSlice) / bidNumStd
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




