from System.Factor import Factor
import numpy as np


class FactorCBHighDistanceUA(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )
        self.__midPriceUA = self._getFactor(
            {
                "ClassName": "MidPriceUA",
            }
        )

    def calculate(self):

        midp = np.array(self.__midPrice.getFactorValueList())[-self.__lag:]
        midp_ua = np.array(self.__midPriceUA.getFactorValueList())[-self.__lag:]
        midp_ua = [each for each in midp_ua if each is not None]
        if len(midp_ua) > 0:
            factorValue = (np.nanargmax(midp) - np.nanargmax(midp_ua)) / 1e2
        else:
            factorValue = np.nanargmax(midp) / 1e2

        self._addFactorValue(factorValue)
