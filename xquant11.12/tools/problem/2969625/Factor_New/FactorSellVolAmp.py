import numpy as np
from System.Factor import Factor


class FactorSellVolAmp(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.sLag = self._getParameter("sLag")
        self.lag = self._getParameter("Lag")

        self._addIntermediate("QtyList", [])

    def calculate(self):
        qtyList = self.getIntermediate("QtyList")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            volume = self._getOrderData("Volume", orderData)
            qty = np.sum(volume[bsFlag == 2])
        else:
            qty = 0.

        qtyList.append(qty)

        if len(qtyList) < min(3, self.sLag):
            factorValue = 0.
        else:
            factorValue = - self.amplify_zcore(qtyList, self.sLag, self.lag) * 100

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
