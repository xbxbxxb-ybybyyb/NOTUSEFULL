from System.Factor import Factor
import numpy as np


class CancelOrderTime(Factor):

    def calculate(self):

        early_orders = self._getEarlyData("Orders")
        orders = self._getAllTodayTickData("Orders")
        cancel = self._getLastTickData("Cancellations")

        if cancel is not None and np.any([order is not None for order in orders]):
            cancelIndex = np.fmax(self._getCancellationData("BidOrder", cancel),
                                  self._getCancellationData("AskOrder", cancel))

            if early_orders is not None:
                earlyOrderTime = self._getOrderData("Timestamp", early_orders)
                earlyOrderIndex = self._getOrderData("OrderIndex", early_orders)
            else:
                earlyOrderTime, earlyOrderIndex = np.array([]), np.array([])

            orderTime = np.hstack([self._getOrderData("Timestamp", order) for order in orders if order is not None])
            orderIndex = np.hstack([self._getOrderData("OrderIndex", order) for order in orders if order is not None])
            allOrderTime = np.hstack([earlyOrderTime, orderTime])
            allOrderIndex = np.hstack([earlyOrderIndex, orderIndex])

            factorValue = {each: allOrderTime[allOrderIndex == each][0] for each in cancelIndex if
                           len(allOrderTime[allOrderIndex == each]) > 0}
        else:
            factorValue = {}

        self._addFactorValue(factorValue)


