import numpy as np
from System.Factor import Factor


class FactorDistance2MaxStdR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.window = self._getParameter("Window")

        self.midPrice = self._getFactor({"ClassName": "MidPrice"})

        self._addIntermediate("transactionStdList", [])

    def calculate(self):
        transactionStdList = self.getIntermediate("transactionStdList")

        transactions = self._getLastTickData("Transactions")
        if transactions is None:
            transactionStdList.append(0)
        else:
            transactionStd = np.std(self._getTransactionData("Price", transactions))
            if transactionStd > 1e-6:
                transactionStdList.append(transactionStd)
            else:
                transactionStdList.append(0)

        priceList = self.midPrice.getFactorValueList()[-self.window:]

        transactionStdList = transactionStdList[-self.window:]
        fv = (priceList[-1] / priceList[len(transactionStdList) - 1 - np.argmax(transactionStdList[::-1])] - 1) * 1000

        self._addFactorValue(-fv)
