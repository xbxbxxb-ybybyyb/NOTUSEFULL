from System.Factor import Factor
import numpy as np
from scipy.stats import skew


class FactorCandleShadowRatioSkew(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__klag = self._getParameter("KLineLag")
        self.__lag = self._getParameter("Lag")
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
        self.__kLineOpen = self._getFactor(
            {
                "ClassName": "KLineOpenLive",
                "Parameters": {
                    "Lag": self.__klag,
                    "OriginalData": "LastPrice",
                }
            }
        )
        self._addIntermediate("CandleShadowList", [])

    def calculate(self):

        cs_list = self.getIntermediate("CandleShadowList")
        klph = self.__kLineHigh.getLastFactorValue()
        klpl = self.__kLineLow.getLastFactorValue()
        klpo = self.__kLineOpen.getLastFactorValue()
        klpc = self._getLastTickData("LastPrice")

        if klph - klpl > 0.0001:
            cs = (klpc - klpo) / (klph - klpl)
        else:
            cs = 0.
        cs_list.append(cs)

        factorValue = skew(cs_list[-self.__lag:])

        if np.isnan(factorValue):
            factorValue = 0.

        self._addFactorValue(factorValue)
