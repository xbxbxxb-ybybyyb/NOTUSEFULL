from System.Factor import Factor
import numpy as np

class FactorPricePercentileAdjByVol_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")
        self.__mlag = self._getParameter("TickLag")

        self.__volRatio = self._getFactor(
            {
                "ClassName": "VolDailyRatio",
                "DailyLength": self.__dlag,
                "Parameters": {
                    "LagMin": self.__mlag,
                    "LagDay": self.__dlag
                }
            }
        )

    def calculate(self):
        vol_ratio = self.__volRatio.getLastFactorValue()
        last_price = self._getLastTickData("LastPrice")
        price_day_array = self._getLastNHistoricalDailyData("ClosePrice", self.__dlag)  # 需要考虑前交易日停牌，全为NaN的情况
        price_percentile = (last_price / np.mean(price_day_array) - 1) * 100
        factorValue = -price_percentile * vol_ratio
        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
