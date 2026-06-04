import numpy as np
from System.Factor import Factor


class FactorDistance2MaxStd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.window = self._getParameter("Window")

        self.midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

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
        fv = (priceList[-1] / priceList[np.argmax(transactionStdList[-self.window:])] - 1) * 1000

        self._addFactorValue(fv)
