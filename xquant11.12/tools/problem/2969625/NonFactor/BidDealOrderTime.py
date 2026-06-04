from System.Factor import Factor
import numpy as np


class BidDealOrderTime(Factor):

    def calculate(self):

        early_orders = self._getEarlyData("Orders")
        orders = self._getAllTodayTickData("Orders")
        trans = self._getLastTickData("Transactions")

        if trans is not None and np.any([order is not None for order in orders]):

            transIndex = self._getTransactionData("BidOrder", trans)

            if early_orders is not None:
                earlyOrderTime = self._getOrderData("Timestamp", early_orders)
                earlyOrderIndex = self._getOrderData("OrderIndex", early_orders)
            else:
                earlyOrderTime = np.array([])
                earlyOrderIndex = np.array([])

            orderTime = np.hstack([self._getOrderData("Timestamp", order) for order in orders if order is not None])
            orderIndex = np.hstack([self._getOrderData("OrderIndex", order) for order in orders if order is not None])
            allOrderTime = np.hstack([earlyOrderTime, orderTime])
            allOrderIndex = np.hstack([earlyOrderIndex, orderIndex])

            factorValue = {each: allOrderTime[allOrderIndex == each][0] for each in transIndex if
                           len(allOrderTime[allOrderIndex == each]) > 0}
        else:
            factorValue = {}

        self._addFactorValue(factorValue)


