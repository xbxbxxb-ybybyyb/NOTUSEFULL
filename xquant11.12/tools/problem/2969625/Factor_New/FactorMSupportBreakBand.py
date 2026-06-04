from System.Factor import Factor
import numpy as np


class FactorMSupportBreakBand(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__sup_scale = self._getParameter("SupportScale")
        self.__brk_scale = self._getParameter("BreakScale")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice",
            }
        )
        self.__mean = None
        self.__std = None

    def calculate(self):
        openp = self._getAllTodayTickData("LastPrice")[0]
        expr = openp * (1 + self.__mean)
        support_up = openp * (1 + self.__mean + self.__std * self.__sup_scale)
        break_up = openp * (1 + self.__mean + self.__std * self.__brk_scale)
        support_down = openp * (1 + self.__mean - self.__std * self.__sup_scale)
        break_down = openp * (1 + self.__mean - self.__std * self.__brk_scale)

        midp = self.__midPrice.getLastFactorValue()

        if midp > break_up:
            factorValue = -(midp / break_up - 1) * 1e1
        elif midp > support_up:
            factorValue = -(midp / break_up - 1) * 1e1
        elif midp < break_down:
            factorValue = -(midp / break_down - 1) * 1e1
        elif midp < support_down:
            factorValue = -(midp / break_down - 1) * 1e1
        else:
            factorValue = -(midp / expr - 1) / 1e2

        self._addFactorValue(factorValue)

    def _onNewDay(self):
        closep = self._getLastNHistoricalDailyData("ClosePrice", self.__lag)
        openp = self._getLastNHistoricalDailyData("OpenPrice", self.__lag)
        drtns = closep / openp - 1
        drtns_mean = np.nanmean(drtns)
        drtns_std = np.nanstd(drtns)
        if np.isnan(drtns_mean):
            self.__mean = 0.
            self.__std = 0.1
        else:
            self.__mean = drtns_mean
            self.__std = drtns_std
