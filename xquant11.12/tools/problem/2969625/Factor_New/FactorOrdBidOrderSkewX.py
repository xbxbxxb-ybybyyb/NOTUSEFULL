import numpy as np
from System.Factor import Factor


class FactorOrdBidOrderSkewX(Factor):
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
            qtyList.append([None])
        qtyArray = np.array([j for i in qtyList[-self.__lag:] for j in i if j is not None])

        if len(qtyArray) > 3 and len(qtyList) > 5:
            factorValue = self.__compute_skew(qtyArray)
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 4.5


        self._addFactorValue(factorValue)

    @staticmethod
    def __compute_skew(arr):
        if len(arr) < 2:
            return 0
        else:
            arr_mean = np.nanmean(arr)
            arr_std = np.nanstd(arr)
            three = np.nanmean((arr - arr_mean)**3)
            skew = three / arr_std**3 if arr_std >1e-6 else 0
            return skew




