from System.Factor import Factor
import numpy as np


class FactorBidAggrCancelNumQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__slag = self._getParameter("SmoothLag")

        self.__cancellationPriceST = self._getFactor(
            {
                "ClassName": "CancellationPriceST",
                "Parameters": {
                    "Lag": 5,
                }
            }
        )

        self.__cancelOrderTimeST = self._getFactor(
            {
                "ClassName": "CancelOrderTimeST",
                "Parameters": {
                    "Lag": 5,
                }
            }
        )
        self.__bid1PriceAdj = self._getFactor(
            {
                "ClassName": "Bid1PriceTransAdjusted"
            }
        )

        self._addIntermediate("CancellationNum", [])

    def calculate(self):

        cns = self.getIntermediate("CancellationNum")
        cp = self.__cancellationPriceST.getLastFactorValue()
        cot = self.__cancelOrderTimeST.getLastFactorValue()
        bidp = self.__bid1PriceAdj.getFactorValueList()
        cancel = self._getLastTickData("Cancellations")

        if (len(bidp) > 1) and cancel is not None:
            cf = self._getCancellationData("BSFlag", cancel)
            crd = self._getCancellationData("BidOrder", cancel)[cf == 1]
            ct = self._getCancellationData("Timestamp", cancel)[cf == 1]

            ct = np.array([ct[i] for i, each in enumerate(crd) if each in cp])
            cot = np.array([cot[each] for each in crd if each in cp])
            cp = np.array([cp[each] for each in crd if each in cp])
            rt = ct - cot

            if (bidp[-2] > 1e-4) and np.any((cp > (bidp[-2] - 1e-4)) & (rt < 10)):
                cns.append(np.nansum((cp > (bidp[-2] - 1e-4)) & (rt < 10)))
            else:
                cns.append(0.)
        else:
            cns.append(0.)

        qtl = np.nansum(np.array(cns) < np.nanmean(cns[-self.__lag:])) / len(cns)

        factorValue = self.__ema(qtl, self.getFactorValueList(), self.__slag)

        self._addFactorValue(factorValue)

    def __ema(self, value, ema_list, n):
        if len(ema_list) == 0:
            return value
        else:
            para = 2.0 / (min(len(ema_list), n) + 1)
            return ema_list[-1] + para * (value - ema_list[-1])



