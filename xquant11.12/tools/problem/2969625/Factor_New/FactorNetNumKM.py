from System.Factor import Factor
import numpy as np


class FactorNetNumKM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__Lag = self._getParameter("Lag")
        self._addIntermediate("NetNumList", [])

    def calculate(self):
        netNumList = self.getIntermediate("NetNumList")
        ordersArray = self._getLastTickData("Orders")

        if ordersArray is not None:
            bsFlag = self._getOrderData("BSFlag", ordersArray)
            netNumList.append(np.sum(bsFlag == 1) - np.sum(bsFlag == 2))
        else:
            netNumList.append(0)

        netNums = netNumList[-self.__Lag:]
        L = len(netNums)

        if L < 5:
            if len(self.getFactorValueList()) == 0:
                factorValue = 0
            else:
                factorValue = self.getLastFactorValue()
        else:
            factorValue = np.corrcoef(np.arange(len(netNums)), netNums)[0][1]
            if np.isnan(factorValue):
                factorValue = 0

        self._addFactorValue(factorValue)