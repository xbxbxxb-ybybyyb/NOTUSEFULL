from System.Factor import Factor
import numpy as np


class FactorMountValleyLinearPrediction(Factor):
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

            sub_midp = midpw[np.abs(mvloc[-1]):]
            if mvloc[-1] < 0:
                itmp = np.argmax(sub_midp)
            else:
                itmp = np.argmin(sub_midp)

            # 由于窗口期延迟未识别到的波峰/波谷
            if (itmp > len(sub_midp) - self.__wd) and (itmp < len(sub_midp) - 2):
                mvloc = np.append(mvloc, - np.sign(mvloc[-1]) * (itmp + np.abs(mvloc[-1])))
                mvv = np.append(mvv, sub_midp[itmp])

            if len(tsp) - 1 > np.abs(mvloc[-1]):
                # 最新值
                mvloc = np.append(mvloc, np.sign(midpw[-1] - mvloc[-1]) * (len(tsp) - 1))
                mvv = np.append(mvv, midpw[-1])

                mvvm = mvv[mvloc > 0]
                mvvv = mvv[mvloc < 0]

                if mvloc[-1] < 0:
                    if len(mvvv) < 2:
                        pv = mvvv[-1] - (mvvv[-1] - midpw[0])
                    else:
                        avg_chgv = np.nanmean(np.diff(mvvv))
                        pv = mvvv[-2] + avg_chgv
                else:
                    if len(mvvm) < 2:
                        pv = mvvm[-1] + (mvvm[-1] - midpw[0])
                    else:
                        avg_chgm = np.nanmean(np.diff(mvvm))
                        pv = mvvm[-2] + avg_chgm

                factorValue = (mvv[-1] / pv - 1) * 1e2
            else:
                factorValue = 0.
        else:
            factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

