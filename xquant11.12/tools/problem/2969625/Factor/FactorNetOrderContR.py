import numpy as np
from System.Factor import Factor


class FactorNetOrderContR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.lag = self._getParameter("Lag")
        self._addIntermediate("netQtyList", [])

    def calculate(self):
        netQty = 0

        transactions = self._getLastTickData("Orders")
        if transactions is not None:
            netQty = np.sum(self._getOrderData("Volume", transactions)[self._getOrderData("BSFlag", transactions) == 1]) - \
                     np.sum(self._getOrderData("Volume", transactions)[self._getOrderData("BSFlag", transactions) == 2])

        netQtyList = self.getIntermediate("netQtyList")
        netQtyList.append(netQty)

        netQtySign = np.cumsum(np.sign(netQtyList[-self.lag:]))
        lag = np.arange(len(netQtySign))
        if len(netQtySign) < 2:
            fv = 0
        else:
            fv = (np.mean(netQtySign * lag) - np.mean(netQtySign) * np.mean(lag)) / np.var(lag)

        self._addFactorValue(fv)
