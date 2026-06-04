import numpy as np
from System.Factor import Factor


class FactorOrdAskQtyCRTrendX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__window = self._getParameter("Window")

        self._addIntermediate("AskQtyList", [])
        self._addIntermediate("QtyList", [])
        self._addIntermediate("CRList", [])

    def calculate(self):

        askQtyList = self.getIntermediate("AskQtyList")
        qtyList = self.getIntermediate("QtyList")

        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            volume = self._getOrderData("Volume", orderData)
            price = self._getOrderData("Price", orderData)
            bsFlag = self._getOrderData("BSFlag", orderData)
            amount = volume * price
            askQtyList.append(amount[bsFlag == 2].tolist())
            qtyList.append(amount[(bsFlag == 1) | (bsFlag == 2)].tolist())
        else:
            askQtyList.append([None])
            qtyList.append([None])

        askQtyArray = np.array([j for i in askQtyList[-self.__lag:] for j in i if j is not None])
        qtyArray = np.array([j for i in qtyList[-self.__lag:] for j in i if j is not None])

        qtySquare = np.nansum(askQtyArray ** 2)
        totalSquare = np.nansum(qtyArray ** 2)

        cr = qtySquare / totalSquare if totalSquare > 1e-6 else 0.
        crList = self.getIntermediate("CRList")
        crList.append(cr)

        crSlice = np.array(crList[-self.__window:])

        if len(crSlice) < 5:
            factorValue = 0.
        else:
            factorValue = - np.corrcoef(crSlice, np.arange(len(crSlice)))[0, 1] * 100

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)





