import math
import numpy as np
from System.Factor import Factor


class FactorMomentum_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__EMAMidPriceLag = self._getParameter("EMAMidPriceLag")
        self.__MAAmountLag = self._getParameter("MAAmountLag")
        self.__lag = self._getParameter("Lag")
        self.__eps = 1e-5

        self.__emaMidPrice = self._getFactor(
            {
                "ClassName": "EMA",
                "Parameters": {
                    "Lag": self.__EMAMidPriceLag,
                    "OriginalData": {
                        "ClassName": "MidPrice"
                    }
                }
            }
        )

    def calculate(self):
        emaPriceList = self.__emaMidPrice.getFactorValueList()
        historyAmountArray = self._getAllTickData("Amount")
        length = min(len(emaPriceList), self.__lag)

        # daily_price_list = self._getLastNHistoricalDailyData("ClosePrice", 20)
        # price = self._getLastNTickData('LastPrice', 100)
        # avg_price = np.nanmean(price)
        # ceiling_price = np.nanmax(daily_price_list)
        # floor_price = np.nanmin(daily_price_list)
        # price_ratio = (avg_price - floor_price) / (ceiling_price - floor_price) if (ceiling_price - floor_price) > 0.01 else 0
        ceiling = self._getLastTickData("HighPrice")
        floor = self._getLastTickData("LowPrice")
        lastPrice = self._getLastTickData("LastPrice")
        price_ratio = (lastPrice - floor) / (ceiling - floor) if (ceiling - floor) > 0.01 else 0

        isNotValid = (bool(sum([price < 0.01 for price in emaPriceList[-length:]]))
                      or (historyAmountArray[-length:] < 0).any())

        if isNotValid:
            factorValue = 0
        else:
            lastFactorSpeed = (emaPriceList[-1] / emaPriceList[-length] - 1) / (length / 20)
            # amount = math.log((np.nansum(historyAmountArray[-length:]) + self.__eps)
            #                   / (np.nansum(historyAmountArray[-self.__MAAmountLag:]) + self.__eps))
            factorValue = - lastFactorSpeed * price_ratio * 1000

        self._addFactorValue(factorValue)
