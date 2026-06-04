from System.Factor import Factor
import numpy as np


class FactorDistance2MAMulRet(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")
        self.__dLag = self._getParameter("DayLag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        daily_price_list = self._getLastNHistoricalDailyData("ClosePrice", self.__dLag - 1)
        last_price = self._getLastTickData("LastPrice")
        if last_price is None:
            factor_value = 0
        else:
            mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag1:]
            mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
            lag = min(self.__lag2, len(mid_price_list) - 1)
            ret = np.array(mid_price_list[lag:]) / np.array(mid_price_list[:-lag]) - 1
            ma20 = (np.nansum(daily_price_list) + last_price) / self.__dLag
            factor_value = last_price / ma20 * np.nanmean(ret)

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
