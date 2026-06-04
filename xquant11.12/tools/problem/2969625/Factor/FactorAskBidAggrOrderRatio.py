from System.Factor import Factor
import numpy as np


class FactorAskBidAggrOrderRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slag = self._getParameter("SmoothLag")

        self.__ask1PriceAdj = self._getFactor(
            {
                "ClassName": "Ask1PriceTransAdjusted"
            }
        )

        self.__bid1PriceAdj = self._getFactor(
            {
                "ClassName": "Bid1PriceTransAdjusted"
            }
        )

        self._addIntermediate("BidAggrOrderVolume", [])
        self._addIntermediate("AskAggrOrderVolume", [])

    def calculate(self):

        baovs = self.getIntermediate("BidAggrOrderVolume")
        aaovs = self.getIntermediate("AskAggrOrderVolume")

        ask1p = self.__ask1PriceAdj.getFactorValueList()
        bid1p = self.__bid1PriceAdj.getFactorValueList()
        order = self._getLastTickData("Orders")

        if (len(bid1p) > 1) and order is not None:

            op = self._getOrderData("Price", order)
            ov = self._getOrderData("Volume", order)
            of = self._getOrderData("BSFlag", order)

            baovs.append(np.nansum(ov[(op > bid1p[-2] - 1e-4) & (of == 1)]))
            aaovs.append(np.nansum(ov[(op < ask1p[-2] + 1e-4) & (of == 2)]))

        else:
            baovs.append(0.)
            aaovs.append(0.)

        if (baovs[-1] > 1e-4) or (aaovs[-1] > 1e-4):
            r = baovs[-1] / (baovs[-1] + aaovs[-1])
        else:
            r = 0.

        factorValue = self.__ema(r, self.getFactorValueList(), self.__slag)

        self._addFactorValue(factorValue)

    def __ema(self, value, ema_list, n):
        if len(ema_list) == 0:
            return value
        else:
            para = 2.0 / (min(len(ema_list), n) + 1)
            return ema_list[-1] + para * (value - ema_list[-1])



