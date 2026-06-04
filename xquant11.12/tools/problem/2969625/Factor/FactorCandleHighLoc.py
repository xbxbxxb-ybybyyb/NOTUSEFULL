from System.Factor import Factor
import numpy as np


class FactorCandleHighLoc(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__klag_1 = self._getParameter("KLineLag1")
        self.__klag_2 = self._getParameter("KLineLag2")
        self.__klag_3 = self._getParameter("KLineLag3")
        self.__klag_4 = self._getParameter("KLineLag4")
        self.__kLineHigh_1 = self._getFactor(
            {
                "ClassName": "KLineHighLive",
                "Parameters": {
                    "Lag": self.__klag_1,
                    "OriginalData": "LastPrice",
                }
            }
        )
        self.__kLineHigh_2 = self._getFactor(
            {
                "ClassName": "KLineHighLive",
                "Parameters": {
                    "Lag": self.__klag_2,
                    "OriginalData": "LastPrice",
                }
            }
        )
        self.__kLineHigh_3 = self._getFactor(
            {
                "ClassName": "KLineHighLive",
                "Parameters": {
                    "Lag": self.__klag_3,
                    "OriginalData": "LastPrice",
                }
            }
        )
        self.__kLineHigh_4 = self._getFactor(
            {
                "ClassName": "KLineHighLive",
                "Parameters": {
                    "Lag": self.__klag_4,
                    "OriginalData": "LastPrice",
                }
            }
        )

    def calculate(self):

        klph_1 = self.__kLineHigh_1.getLastFactorValue()
        klph_2 = self.__kLineHigh_2.getLastFactorValue()
        klph_3 = self.__kLineHigh_3.getLastFactorValue()
        klph_4 = self.__kLineHigh_4.getLastFactorValue()

        if klph_4 > 0.01:
            factorValue = (klph_1 + klph_2 + klph_3) / klph_4 - 1.5
        else:
            factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
