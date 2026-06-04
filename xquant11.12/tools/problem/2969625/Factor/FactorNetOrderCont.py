import numpy as np
from System.Factor import Factor


class FactorNetOrderCont(Factor):
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

        netQtySign = np.sign(netQtyList[-self.lag:])
        if len(netQtySign) < 2:
            fv = 0
        else:
            fv = np.corrcoef(np.cumsum(netQtySign), np.arange(len(netQtySign)))[0, 1]
        if np.isnan(fv):
            fv = 0

        self._addFactorValue(fv)
