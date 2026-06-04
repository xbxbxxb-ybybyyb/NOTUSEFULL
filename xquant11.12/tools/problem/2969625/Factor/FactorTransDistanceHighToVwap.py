from System.Factor import Factor
import numpy as np


class FactorTransDistanceHighToVwap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lltlag = self._getParameter("LltLag")
        self.__transVwap = self._getFactor(
            {
                "ClassName": "TransVwap",
                "Parameters": {
                    "Direction": "Both",
                }
            }
        )
        self.__transHighp = self._getFactor(
            {
                "ClassName": "TransHighPrice",
                "Parameters": {
                    "Direction": "Both",
                }
            }
        )
        self._addIntermediate("Llts", [])
        self._addIntermediate("Dists", [])

    def calculate(self):

        llts = self.getIntermediate("Llts")
        dists = self.getIntermediate("Dists")
        tvwap = self.__transVwap.getLastFactorValue()
        thighp = self.__transHighp.getLastFactorValue()

        filter_llts = list(filter(lambda x: x is not None, llts))
        if not np.isnan(tvwap):
            dist = (np.divide(tvwap, thighp) - 1) * 1e3
            dists.append(dist)
            filter_dists = list(filter(lambda x: x is not None, dists))
            if len(filter_llts) > 1:
                a = 2 / (1 + self.__lltlag)
                llt = (a - a * a / 4) * filter_dists[-1] + a * a / 2 * filter_dists[-2] - (a - 3 * a * a / 4) * \
                      filter_dists[-3] + 2 * (1 - a) * filter_llts[-1] - (1 - a) ** 2 * filter_llts[-2]
            else:
                llt = dist
            llts.append(llt)
            filter_llts.append(llt)
        else:
            dists.append(None)
            llts.append(None)

        if len(filter_llts) > 0:
            factorValue = filter_llts[-1]
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
