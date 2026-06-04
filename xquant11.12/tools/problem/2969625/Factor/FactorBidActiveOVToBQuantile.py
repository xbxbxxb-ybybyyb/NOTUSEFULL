from System.Factor import Factor
import numpy as np


class FactorBidActiveOVToBQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__bid1Price = self._getFactor(
            {
                "ClassName": "Bid1Price",
            }
        )
        self._addIntermediate("BidActiveVolume", [])

    def calculate(self):

        bavs = self.getIntermediate("BidActiveVolume")
        order = self._getLastTickData("Orders")
        last_bid1 = self.__bid1Price.getFactorValueList()[-2:][0]

        if order is not None:

            of = self._getOrderData("BSFlag", order)
            ov = self._getOrderData("Volume", order)
            op = self._getOrderData("Price", order)

            bavs.append(np.nansum(ov[(of == 1) & (op > last_bid1)]))
        else:
            bavs.append(None)

        filter_bavs = list(filter(lambda x: x is not None, bavs))
        if order is not None:
            factorValue = np.nansum(filter_bavs[-1] > np.array(filter_bavs)) / len(filter_bavs)
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
