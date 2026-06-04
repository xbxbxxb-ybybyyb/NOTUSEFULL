import numpy as np
from System.Factor import Factor


class FactorOrderOfferQtyAmp(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sLag = self._getParameter("sLag")

        self._addIntermediate("QtyList", [])

    def calculate(self):
        qtyList = self.getIntermediate("QtyList")
        qtyArray = self._getLastNTickData("OfferQty", 2)
        if len(qtyArray) < 2:
            qty = 0.
        else:
            qty = qtyArray[1] - qtyArray[0]
        qtyList.append(qty)

        if len(qtyList) < min(3, self.__sLag):
            factorValue = 0.
        else:
            factorValue = - self.amplify_zcore(qtyList, self.__sLag, self.__lag) * 100

        self._addFactorValue(factorValue)

    @staticmethod
    def amplify_zcore(valueList, sLag, lag):
        size = len(valueList)
        sLag = min(max(1, int(size * sLag / lag)), sLag)
        std = np.nanstd(valueList)
        if std < 1e-6 or np.isnan(std):
            return 0
        else:
            return (np.nanmean(valueList[-sLag:]) - np.nanmean(valueList[-lag:])) / std