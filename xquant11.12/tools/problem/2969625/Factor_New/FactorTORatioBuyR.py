import numpy as np
from System.Factor import Factor


class FactorTORatioBuyR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self._addIntermediate("resQtyList", [])
        self.lag1 = self._getParameter("Lag1")
        self.lag2 = self._getParameter("Lag2")

    def calculate(self):
        lastBidP2 = self._getLastNTickData("BidPrice", 2)[0][1]

        order = self._getLastTickData("Orders")
        transaction = self._getLastTickData("Transactions")

        buyOrder = 0
        if order is not None:
            orderBS = self._getOrderData("BSFlag", order)
            orderPrice = self._getOrderData("Price", order)
            orderQty = self._getOrderData("Volume", order)
            orderType = self._getOrderData("OrderType", order)
            for j in range(len(orderPrice)):
                if orderType[j] == 2 and orderBS[j] == 1:
                    if orderPrice[j] >= lastBidP2:
                        buyOrder += orderQty[j]

        sellTrans = 0
        if transaction is not None:
            transactionBS = self._getTransactionData("BSFlag", transaction)
            transactionPrice = self._getTransactionData("Price", transaction)
            transactionQty = self._getTransactionData("Volume", transaction)
            for j in range(len(transactionPrice)):
                if transactionBS[j] == 2:
                    sellTrans += transactionQty[j]

        resQtyList = self.getIntermediate("resQtyList")
        resQtyList.append(buyOrder - sellTrans)

        fv = self.zscore(resQtyList, self.lag1, self.lag2) * 100
        self._addFactorValue(fv)

    @staticmethod
    def zscore(l1, w1, w2):
        std1 = np.nanstd(l1[-w2:])
        if std1 == 0 or np.isnan(std1):
            return 0
        else:
            return (np.nanmean(l1[-w1:]) - np.nanmean(l1[-w2:])) / std1
