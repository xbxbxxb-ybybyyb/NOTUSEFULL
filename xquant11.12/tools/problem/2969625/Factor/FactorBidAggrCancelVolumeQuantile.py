from System.Factor import Factor
import numpy as np


class FactorBidAggrCancelVolumeQuantile(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__slag = self._getParameter("SmoothLag")

        self.__cancellationPriceST = self._getFactor(
            {
                "ClassName": "CancellationPriceST",
                "Parameters": {
                    "Lag": 5
                }
            }
        )

        self.__cancelOrderTimeST = self._getFactor(
            {
                "ClassName": "CancelOrderTimeST",
                "Parameters": {
                    "Lag": 5
                }
            }
        )
        self.__bid1PriceAdj = self._getFactor(
            {
                "ClassName": "Bid1PriceTransAdjusted"
            }
        )

        self._addIntermediate("CancellationVolume", [])

    def calculate(self):

        cvs = self.getIntermediate("CancellationVolume")
        bidp = self.__bid1PriceAdj.getFactorValueList()
        cp = self.__cancellationPriceST.getLastFactorValue()
        cot = self.__cancelOrderTimeST.getLastFactorValue()
        cancel = self._getLastTickData("Cancellations")

        if (len(bidp) > 1) and cancel is not None:
            cf = self._getCancellationData("BSFlag", cancel)
            cv = self._getCancellationData("Volume", cancel)[cf == 1]
            crd = self._getCancellationData("BidOrder", cancel)[cf == 1]
            ct = self._getCancellationData("Timestamp", cancel)[cf == 1]

            cv = np.array([cv[i] for i, each in enumerate(crd) if each in cp])
            ct = np.array([ct[i] for i, each in enumerate(crd) if each in cp])
            cot = np.array([cot[each] for each in crd if each in cp])
            cp = np.array([cp[each] for each in crd if each in cp])
            rt = ct - cot  # 撤单时间-委托时间

            if (bidp[-2] > 1e-4) and np.any((cp > (bidp[-2] - 1e-4)) & (rt < 10)):
                cvs.append(np.nanmean(cv[(cp > (bidp[-2] - 1e-4)) & (rt < 10)]))
            else:
                cvs.append(0.)
        else:
            cvs.append(0.)

        qtl = np.nansum(np.array(cvs) < np.nanmean(cvs[-self.__lag:])) / len(cvs)

        factorValue = self.__ema(qtl, self.getFactorValueList(), self.__slag)

        self._addFactorValue(factorValue)

    def __ema(self, value, ema_list, n):
        if len(ema_list) == 0:
            return value
        else:
            para = 2.0 / (min(len(ema_list), n) + 1)
            return ema_list[-1] + para * (value - ema_list[-1])



