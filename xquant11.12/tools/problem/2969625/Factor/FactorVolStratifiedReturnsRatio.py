from System.Factor import Factor
import numpy as np


class FactorVolStratifiedReturnsRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )
        self._addIntermediate("ReturnsList", [])

    def calculate(self):

        rtns_list = self.getIntermediate("ReturnsList")
        tsp = self._getAllTodayTickData("Timestamp")
        midpw = self.__midPriceW.getFactorValueList()[-2:]
        volume = self._getLastNTodayTickData("Volume", self.__lag)

        epsilon = 1e-6
        if len(tsp) == 1:
            factorValue = 0.
            rtns_list.append(np.nan)
        else:
            rtns_list.append(midpw[-1] / midpw[0] - 1)
            rtns_s = np.array(rtns_list[-self.__lag:])
            volume = volume[-len(rtns_s):]
            if len(volume) < 2:
                factorValue = 0.
            else:
                vol_strong = np.nanpercentile(volume, 80)
                vol_weak = np.nanpercentile(volume, 20)
                rtns_strong = np.nanmean(rtns_s[volume >= vol_strong - epsilon])
                rtns_weak = np.nanmean(rtns_s[volume <= vol_weak + epsilon])
                factorValue = (rtns_strong - rtns_weak) * 1e3

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
