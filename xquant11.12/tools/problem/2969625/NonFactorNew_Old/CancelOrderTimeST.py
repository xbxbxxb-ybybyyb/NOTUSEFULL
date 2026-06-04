from System.Factor import Factor
import numpy as np


class CancelOrderTimeST(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        orders = self._getLastNTodayTickData("Orders", self.__lag)
        cancel = self._getLastTickData("Cancellations")

        if cancel is not None and np.any([order is not None for order in orders]):
            cancelIndex = np.fmax(self._getCancellationData("BidOrder", cancel),
                                  self._getCancellationData("AskOrder", cancel))

            orderTime = np.hstack([self._getOrderData("Timestamp", order) for order in orders if order is not None])
            orderIndex = np.hstack([self._getOrderData("OrderIndex", order) for order in orders if order is not None])

            orderTimeDict = dict(zip(orderIndex, orderTime))
            factorValue = {each: orderTimeDict[each] for each in cancelIndex if each in orderTimeDict}

        else:
            factorValue = {}

        self._addFactorValue(factorValue)


