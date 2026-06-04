from System.Factor import Factor
import numpy as np


class FactorReturnsMagnification(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__klag = self._getParameter("KLineLag")
        self.__knum = self._getParameter("KLineNumber")
        self.__lag = self.__klag * self.__knum
        self.__kLineHigh = self._getFactor(
            {
                "ClassName": "KLineHighLive",
                "Parameters": {
                    "Lag": self.__klag,
                    "OriginalData": "LastPrice",
                }
            }
        )
        self.__kLineLow = self._getFactor(
            {
                "ClassName": "KLineLowLive",
                "Parameters": {
                    "Lag": self.__klag,
                    "OriginalData": "LastPrice",
                }
            }
        )
        self.__midPriceW = self._getFactor(
            {
                "ClassName": "MidPriceWeighted",
                "Parameters": {
                    "Grade": 1,
                }
            }
        )

    def calculate(self):

        klph = np.array(self.__kLineHigh.getFactorValueList()[-self.__lag:][::-1])
        klpl = np.array(self.__kLineLow.getFactorValueList()[-self.__lag:][::-1])
        klph_sub = klph[range(0, len(klph), self.__klag)]
        klpl_sub = klpl[range(0, len(klpl), self.__klag)]
        rtns_amp = np.nansum(klph_sub - klpl_sub)
        midp = self.__midPriceW.getFactorValueList()[-self.__lag:]
        rtns = midp[-1] - midp[0]
        if np.abs(rtns_amp) > 1e-6:
            factorValue = rtns / rtns_amp
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
