import numpy as np
from System.Factor import Factor


class FactorTranBigBidQtyRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("QtyList", [])

    def calculate(self):

        qtyList = self.getIntermediate("QtyList")
        transactionData = self._getLastTickData("Transactions")
        if transactionData is not None:
            bsFlag = self._getTransactionData("BSFlag", transactionData)
            amount = self._getTransactionData("Amount", transactionData)
            qtyList.append(amount[bsFlag == 1].tolist())
        else:
            qtyList.append(None)

        filterQtyList = list(filter(lambda x: x is not None, qtyList))

        qtyArray = np.array([j for i in filterQtyList[-self.__lag:] for j in i])

        qty = np.nansum(qtyArray[qtyArray > (np.nanpercentile(qtyArray, 70) + 1e-6)])
        total = np.nansum(qtyArray)

        factorValue = qty / total if total > 1e-6 else 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





