from System.Factor import Factor
import numpy as np


class FactorBidAggrNewOrderVolumeQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid1PriceAdj = self._getFactor(
            {
                "ClassName": "Bid1PriceTransAdjusted"
            }
        )

        self._addIntermediate("AggrNewOrderVolume", [])

    def calculate(self):

        anovs = self.getIntermediate("AggrNewOrderVolume")

        bid1p = self.__bid1PriceAdj.getFactorValueList()
        order = self._getLastTickData("Orders")

        if (len(bid1p) > 1) and order is not None:

            op = self._getOrderData("Price", order)
            ov = self._getOrderData("Volume", order)
            of = self._getOrderData("BSFlag", order)

            anovs.append(np.nansum(ov[(op > bid1p[-2] - 1e-4) & (of == 1)]))

        else:
            anovs.append(0.)

        factorValue = np.nansum(np.array(anovs) < np.nanmean(anovs[-self.__lag:])) / len(anovs)

        self._addFactorValue(factorValue)




