from System.Factor import Factor
import numpy as np


class CancellationPrice(Factor):

    def calculate(self):

        early_orders = self._getEarlyData("Orders")
        orders = self._getAllTodayTickData("Orders")
        cancell = self._getLastTickData("Cancellations")

        if cancell is not None and np.any([order is not None for order in orders]):
            cancellIndex = np.fmax(self._getCancellationData("BidOrder", cancell),
                                   self._getCancellationData("AskOrder", cancell))

            if early_orders is not None:
                earlyOrderPrice = self._getOrderData("Price", early_orders)
                earlyOrderIndex = self._getOrderData("OrderIndex", early_orders)
            else:
                earlyOrderPrice, earlyOrderIndex = np.array([]), np.array([])

            orderPrice = np.hstack([self._getOrderData("Price", order) for order in orders if order is not None])
            orderIndex = np.hstack([self._getOrderData("OrderIndex", order) for order in orders if order is not None])
            allOrderPrice = np.hstack([earlyOrderPrice, orderPrice])
            allOrderIndex = np.hstack([earlyOrderIndex, orderIndex])

            factorValue = {each: allOrderPrice[allOrderIndex == each][0] for each in cancellIndex if
                           len(allOrderPrice[allOrderIndex == each]) > 0}
        else:
            factorValue = {}

        self._addFactorValue(factorValue)


