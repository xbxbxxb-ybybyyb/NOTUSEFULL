from System.Factor import Factor
import numpy as np


class CancellationPriceST(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        orders = self._getLastNTodayTickData("Orders", self.__lag)
        cancell = self._getLastTickData("Cancellations")

        if cancell is not None and np.any([order is not None for order in orders]):
            cancellIndex = np.fmax(self._getCancellationData("BidOrder", cancell),
                                   self._getCancellationData("AskOrder", cancell))

            orderPrice = np.hstack([self._getOrderData("Price", order) for order in orders if order is not None])
            orderIndex = np.hstack([self._getOrderData("OrderIndex", order) for order in orders if order is not None])

            orderPriceDict = dict(zip(orderIndex, orderPrice))
            factorValue = {each: orderPriceDict[each] for each in cancellIndex if each in orderPriceDict}

        else:
            factorValue = {}

        self._addFactorValue(factorValue)


