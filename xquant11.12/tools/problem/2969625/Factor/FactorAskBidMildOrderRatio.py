from System.Factor import Factor
import numpy as np


class FactorAskBidMildOrderRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

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

        self._addIntermediate("BidMildOrderVolume", [])
        self._addIntermediate("AskMildOrderVolume", [])

    def calculate(self):

        bmovs = self.getIntermediate("BidMildOrderVolume")
        amovs = self.getIntermediate("AskMildOrderVolume")

        ask1p = self.__ask1PriceAdj.getFactorValueList()
        bid1p = self.__bid1PriceAdj.getFactorValueList()
        order = self._getLastTickData("Orders")

        if (len(bid1p) > 1) and order is not None:

            op = self._getOrderData("Price", order)
            ov = self._getOrderData("Volume", order)
            of = self._getOrderData("BSFlag", order)

            bmovs.append(np.nansum(ov[(op > bid1p[-2] * (1 - 0.005)) & (of == 1)]))
            amovs.append(np.nansum(ov[(op < ask1p[-2] * (1 + 0.005)) & (of == 2)]))

        else:
            bmovs.append(0.)
            amovs.append(0.)

        if (np.nanmean(bmovs[-self.__lag:]) > 1e-4) or (np.nanmean(amovs[-self.__lag:]) > 1e-4):

            factorValue = np.nanmean(bmovs[-self.__lag:]) / (np.nanmean(bmovs[-self.__lag:]) + np.nanmean(amovs[-self.__lag:]))
        else:
            lastFactorValue = self.getLastFactorValue()
            if lastFactorValue is not None:
                factorValue = lastFactorValue
            else:
                factorValue = 0.

        self._addFactorValue(factorValue)




