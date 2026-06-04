from System.Factor import Factor
import numpy as np


class FactorBidAggrMildOrderVRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid1PriceAdj = self._getFactor(
            {
                "ClassName": "Bid1PriceTransAdjusted"
            }
        )

        self._addIntermediate("AggrNewOrderVolume", [])
        self._addIntermediate("MildNewOrderVolume", [])

    def calculate(self):

        anovs = self.getIntermediate("AggrNewOrderVolume")
        mnovs = self.getIntermediate("MildNewOrderVolume")

        bid1p = self.__bid1PriceAdj.getFactorValueList()
        order = self._getLastTickData("Orders")

        if (len(bid1p) > 1) and order is not None:

            op = self._getOrderData("Price", order)
            ov = self._getOrderData("Volume", order)
            of = self._getOrderData("BSFlag", order)

            anovs.append(np.nansum(ov[(op > bid1p[-2] - 1e-4) & (of == 1)]))
            mnovs.append(np.nansum(ov[(op > bid1p[-2] * (1 - 0.005)) & (of == 1)]))

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




