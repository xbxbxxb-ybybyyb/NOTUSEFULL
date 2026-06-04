from System.Factor import Factor
import numpy as np


class MountValleyMidpWM(Factor):
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

        if len(midpw) == 1:
            factorValue = (0, midpw[0])
        elif len(midpw) < self.__wd + 6:
            pclosep = self._getLastTickData("PreviousClose")
            if midpw[1] > pclosep:
                factorValue = (1, midpw[1])
            elif midpw[1] < pclosep:
                factorValue = (-1, midpw[1])
            else:
                factorValue = self.getLastFactorValue()
        else:
            i = len(midpw) - 1 - self.__wd
            flag = self.__decide_mount_valley(midpw, self.__wd, i)
            if flag != 0:
                factorValue = (i * flag, midpw[i])
            else:
                factorValue = self.getLastFactorValue()

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


