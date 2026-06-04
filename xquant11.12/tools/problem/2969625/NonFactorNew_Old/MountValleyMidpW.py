from System.Factor import Factor
import numpy as np


class MountValleyMidpW(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__wd = self._getParameter("Window")
        self.__grade = self._getParameter("Grade")

        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": self.__grade
                }
            }
        )

    def calculate(self):

        midpw = self.__midPriceW.getFactorValueList()
        tsp = self._getAllTodayTickData("Timestamp")

        if len(tsp) == 2:
            flag = np.sign(midpw[0] - midpw[-1])
            if flag != 0:
                factorValue = (1 * flag, midpw[-1])
            else:
                factorValue = None
        elif len(tsp) > self.__wd:
            i = len(midpw) - 1 - self.__wd
            flag = self.__decide_mount_valley(midpw, self.__wd, i)
            if flag != 0:
                factorValue = (i * flag, midpw[i])
            else:
                factorValue = None
        else:
            factorValue = None

        self._addFactorValue(factorValue)

    @staticmethod
    def __decide_mount_valley(x, wd, i):
        ps = np.array(x[max(0, i - wd): i])
        ns = np.array(x[i + 1: i + wd])
        if np.all(x[i] > ps) and np.all(x[i] > ns):
            flag = 1
        elif np.all(x[i] < ps) and np.all(x[i] < ns):
            flag = -1
        else:
            flag = 0
        return flag


