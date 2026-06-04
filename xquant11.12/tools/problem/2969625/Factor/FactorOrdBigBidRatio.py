import numpy as np
from System.Factor import Factor


class FactorOrdBigBidRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__window = self._getParameter("Window")

        self._addIntermediate("QtyList", [])
        self._addIntermediate("RatioList", [])

    def calculate(self):
        qtyList = self.getIntermediate("QtyList")
        orderData = self._getLastTickData("Orders")
        if orderData is not None:
            bsFlag = self._getOrderData("BSFlag", orderData)
            volume = self._getOrderData("Volume", orderData)
            price = self._getOrderData("Price", orderData)
            amount = price * volume
            qtyList.append(amount[bsFlag == 1].tolist())
        else:
            qtyList.append(None)

        filterQtyList = list(filter(lambda x: x is not None, qtyList))

        qtyArray = np.array([j for i in filterQtyList[-self.__lag:] for j in i])

        qty = np.nansum(qtyArray[qtyArray > np.nanpercentile(qtyArray, 50)])
        total = np.nansum(qtyArray)

        ratio = qty / total if total > 1e-6 else 0

        factorValueList = self.getFactorValueList()
        factorValue = self._EMA_calculate(ratio, factorValueList, self.__window)

        self._addFactorValue(factorValue)

    def _EMA_calculate(self, value, EMAList, n):
        size = EMAList.__len__()
        if size == 0:
            return value
        else:
            para = 2.0 / (min(size, n) + 1)
            return EMAList[-1] + para * (value - EMAList[-1])



