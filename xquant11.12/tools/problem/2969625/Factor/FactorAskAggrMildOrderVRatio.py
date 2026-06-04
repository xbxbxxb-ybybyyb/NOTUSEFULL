from System.Factor import Factor
import numpy as np


class FactorAskAggrMildOrderVRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__ask1PriceAdj = self._getFactor(
            {
                "ClassName": "Ask1PriceTransAdjusted"
            }
        )

        self._addIntermediate("AggrNewOrderVolume", [])
        self._addIntermediate("MildNewOrderVolume", [])

    def calculate(self):

        anovs = self.getIntermediate("AggrNewOrderVolume")
        mnovs = self.getIntermediate("MildNewOrderVolume")

        ask1p = self.__ask1PriceAdj.getFactorValueList()
        order = self._getLastTickData("Orders")

        if (len(ask1p) > 1) and order is not None:

            op = self._getOrderData("Price", order)
            ov = self._getOrderData("Volume", order)
            of = self._getOrderData("BSFlag", order)

            anovs.append(np.nansum(ov[(op < ask1p[-2] + 1e-4) & (of == 2)]))
            mnovs.append(np.nansum(ov[(op < ask1p[-2] * (1 + 0.005)) & (of == 2)]))

        else:
            anovs.append(0.)
            mnovs.append(0.)

        if np.nanmean(mnovs[-self.__lag:]) > 1e-4:
            factorValue = np.nanmean(anovs[-self.__lag:]) / np.nanmean(mnovs[-self.__lag:])
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




