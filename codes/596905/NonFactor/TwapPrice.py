import numpy as np
from System.Factor import Factor


class TwapPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        lastPriceList = self._getAllTodayTickData("LastPrice")

        if len(lastPriceList) != 0:
            factorValue = np.nansum(lastPriceList) / len(lastPriceList)
        else:
            factorValue = self.__midPrice.getLastFactorValue()

        self._addFactorValue(factorValue)
