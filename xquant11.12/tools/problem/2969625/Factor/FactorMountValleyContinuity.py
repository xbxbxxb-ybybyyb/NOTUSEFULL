from System.Factor import Factor
import numpy as np


class FactorMountValleyContinuity(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__wd = self._getParameter("Window")
        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )
        self.__mvMidpW = self._getFactor(
            {
                "ClassName": "MountValleyMidpW",
                "Parameters": {
                    "Grade": 1,
                    "Window": self.__wd,
                }
            }
        )

    def calculate(self):

        tsp = self._getAllTodayTickData("Timestamp")
        midpw = self.__midPriceW.getFactorValueList()
        mvs = np.array(list(filter(lambda x: x is not None, self.__mvMidpW.getFactorValueList()))).reshape(-1, 2)
        mvloc, mvv = mvs[:, 0].astype(int), mvs[:, 1]

        if len(mvloc) > 0:

            dmvhrtns = np.diff(mvv) / mvv[:-1] * np.diff(np.abs(mvloc))
            dmvhrtns_up = list(dmvhrtns[dmvhrtns > 0])
            dmvhrtns_down = list(dmvhrtns[dmvhrtns < 0])

            sub_midp = midpw[np.abs(mvloc[-1]):]
            if mvloc[-1] < 0:
                itmp = np.argmax(sub_midp)
            else:
                itmp = np.argmin(sub_midp)
            if (itmp > len(sub_midp) - self.__wd) and (itmp < len(sub_midp) - 2):
                dist = len(sub_midp) - 1 - itmp
                mvrtns = midpw[-1] / sub_midp[itmp] - 1
            else:
                dist = len(tsp) - 1 - mvloc[-1]
                mvrtns = midpw[-1] / midpw[mvloc[-1]] - 1
            dmvrtns = dist * mvrtns

            if dmvrtns > 0:
                dmvhrtns_up = np.nanmean(dmvhrtns_up + [dmvrtns])
                factorValue = 1 - dmvrtns / dmvhrtns_up if not np.isnan(dmvhrtns_up) else 0
            elif dmvrtns < 0:
                dmvhrtns_down = np.nanmean(dmvhrtns_down + [dmvrtns])
                factorValue = dmvrtns / dmvhrtns_down if not np.isnan(dmvhrtns_down) else 0
            else:
                factorValue = 0
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

