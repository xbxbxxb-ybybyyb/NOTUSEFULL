from System.Factor import Factor
import numpy as np


class FactorSupportBreakBand(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__dlag = self._getParameter("DayLag")
        self.__sup_scale = self._getParameter("SupScale")
        self.__brk_scale = self._getParameter("BreakScale")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )

    def calculate(self):
        dopen_crt = self._getAllTodayTickData("LastPrice")

        dclose_pre = self._getLastNHistoricalDailyData("ClosePrice", self.__dlag)
        dopen_pre = self._getLastNHistoricalDailyData("OpenPrice", self.__dlag)
        dopen_crt = dopen_crt[0]
        drtns = dclose_pre / dopen_pre - 1
        drtns_mean = np.nanmean(drtns)
        drtns_std = np.nanstd(drtns)

        exp = dopen_crt * (1 + drtns_mean)
        support_up = dopen_crt * (1 + drtns_mean + drtns_std * self.__sup_scale)
        break_up = dopen_crt * (1 + drtns_mean + drtns_std * self.__brk_scale)
        support_down = dopen_crt * (1 + drtns_mean - drtns_std * self.__sup_scale)
        break_down = dopen_crt * (1 + drtns_mean - drtns_std * self.__brk_scale)

        mid_price = self.__midPrice.getLastFactorValue()

        if mid_price > break_up:
            factorValue = (mid_price / break_up - 1) * 1e1
        elif mid_price > support_up:
            factorValue = (support_up / mid_price - 1) * 1e1
        elif mid_price < break_down:
            factorValue = (mid_price / break_down - 1) * 1e1
        elif mid_price < support_down:
            factorValue = (support_down / mid_price - 1) * 1e1
        else:
            factorValue = (mid_price / exp - 1) / 1e2

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)
