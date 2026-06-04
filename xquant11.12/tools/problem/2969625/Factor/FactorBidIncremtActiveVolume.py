from System.Factor import Factor
import numpy as np


class FactorBidIncremtActiveVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bidVolumeDeltaSelfSide = self._getFactor(
            {
                "ClassName": "BidVolumeDeltaSelfSide",
            }
        )
        self.__bidVolumeDeltaOtherSide = self._getFactor(
            {
                "ClassName": "BidVolumeDeltaOtherSide",
            }
        )
        self._addIntermediate("LLTs", [])

    def calculate(self):

        dvol = np.nanmean(self._getAllTodayTickData("Volume"))
        llts = self.getIntermediate("LLTs")
        bidvs = self.__bidVolumeDeltaSelfSide.getFactorValueList()[-3:]
        bidos = self.__bidVolumeDeltaOtherSide.getFactorValueList()[-3:]

        if dvol > 0:
            bidactv = np.add(bidvs, bidos)
            filter_llts = list(filter(lambda x: x is not None, llts))
            if len(filter_llts) < 2:
                llts.append(bidactv[-1])
            else:
                a = 2 / (1 + self.__lag)
                llt = (a - a * a / 4) * bidactv[-1] + a * a / 2 * bidactv[-2] - (a - 3 * a * a / 4) * bidactv[-3] + \
                      2 * (1 - a) * filter_llts[-1] - (1 - a) ** 2 * filter_llts[-2]
                llts.append(llt)
            factorValue = llts[-1] / dvol
        else:
            llts.append(None)
            factorValue = 0.

        self._addFactorValue(factorValue)
