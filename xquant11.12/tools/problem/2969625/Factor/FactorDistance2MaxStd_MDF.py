import numpy as np
from System.Factor import Factor


class FactorDistance2MaxStd_MDF(Factor):
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

        priceArr = np.array(self.midPrice.getFactorValueList())
        trStdArr = np.array(transactionStdList)
        filterPriceList = priceArr[trStdArr!=0].tolist()[-self.window:]
        filterTrStdList = trStdArr[trStdArr!=0].tolist()[-self.window:]

        if len(filterTrStdList)==0:
            fv = 0.
        else:
            fv = (priceArr[-1] / filterPriceList[np.argmax(filterTrStdList)] - 1) * 1000

        self._addFactorValue(fv)
