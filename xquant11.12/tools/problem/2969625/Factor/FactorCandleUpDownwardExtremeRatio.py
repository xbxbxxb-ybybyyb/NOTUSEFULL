from System.Factor import Factor
import numpy as np


class FactorCandleUpDownwardExtremeRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__wd = self._getParameter("Window")
        self.__elag = self._getParameter("EMALag")

        self.__midPriceWeighted = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 2,
                }
            }
        )

    def calculate(self):

        midpw = self.__midPriceWeighted.getFactorValueList()[-self.__lag:][::-1]
        n = len(midpw) // self.__wd if len(midpw) % self.__wd == 0 else len(midpw) // self.__wd + 1
        midpw_itv = [midpw[i * self.__wd: (i + 1) * self.__wd] for i in range(n)]
        crtns = np.array([(each[0] / each[-1] - 1) for each in midpw_itv])
        crtns_up_max = np.nanmax(crtns[crtns > 0]) * 1e3 if len(crtns[crtns > 0]) > 0 else 0.0
        crtns_down_max = np.abs(np.nanmin(crtns[~(crtns > 0)])) * 1e3 if len(crtns[~(crtns > 0)]) > 0 else 0.0

        if crtns_up_max + crtns_down_max > 0:
            extreme_ratio = crtns_up_max / (crtns_up_max + crtns_down_max)
            factorValue = self.__ema(extreme_ratio, self.getFactorValueList(), self.__elag)
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0.

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)

    def __ema(self, value, ema_list, n):
        if len(ema_list) == 0:
            return value
        else:
            para = 2.0 / (min(len(ema_list), n) + 1)
            return ema_list[-1] + para * (value - ema_list[-1])
