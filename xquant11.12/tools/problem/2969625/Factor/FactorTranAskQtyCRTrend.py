import numpy as np
from System.Factor import Factor


class FactorTranAskQtyCRTrend(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__window = self._getParameter("Window")

        self._addIntermediate("AskQtyList", [])
        self._addIntermediate("QtyList", [])
        self._addIntermediate("CRList", [])

    def calculate(self):

        askQtyList = self.getIntermediate("AskQtyList")
        qtyList = self.getIntermediate("QtyList")

        transactionData = self._getLastTickData("Transactions")
        if transactionData is not None:
            volume = self._getTransactionData("Volume", transactionData)
            price = self._getTransactionData("Price", transactionData)
            bsFlag = self._getTransactionData("BSFlag", transactionData)
            amount = volume * price
            askQtyList.append(amount[bsFlag == 2].tolist())
            qtyList.append(amount[(bsFlag == 1) | (bsFlag == 2)].tolist())
        else:
            askQtyList.append(None)
            qtyList.append(None)

        filterAskQtyList = list(filter(lambda x: x is not None, askQtyList))
        filterQtyList = list(filter(lambda x: x is not None, qtyList))
        askQtyArray = np.array([j for i in filterAskQtyList[-self.__lag:] for j in i])
        qtyArray = np.array([j for i in filterQtyList[-self.__lag:] for j in i])

        qtySquare = np.nansum(askQtyArray ** 2)
        totalSquare = np.nansum(qtyArray ** 2)

        cr = qtySquare / totalSquare if totalSquare > 1e-6 else 0.
        crList = self.getIntermediate("CRList")
        crList.append(cr)

        crSlice = np.array(crList[-self.__window:])

        if len(crSlice) > 1 and (max(crSlice) - min(crSlice) > 1e-6):
            factorValue = np.corrcoef(crSlice, np.arange(len(crSlice)))[0, 1]
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





