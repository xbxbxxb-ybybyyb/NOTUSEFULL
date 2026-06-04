import numpy as np
from scipy.stats import skew
from System.Factor import Factor


class FactorOrdBidOrderSkew(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self._addIntermediate("QtyList", [])

    def calculate(self):
        qtyList = self.getIntermediate("QtyList")
        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            volume = self._getOrderData("Volume", orderData)
            qtyList.append(volume[bsFlag == 1].tolist())
        else:
            qtyList.append(None)

        filterQtyList = list(filter(lambda x: x is not None, qtyList))

        qtyArray = np.array([j for i in filterQtyList[-self.__lag:] for j in i])

        factorValue = skew(qtyArray)

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)




