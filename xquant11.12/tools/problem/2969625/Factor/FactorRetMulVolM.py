from System.Factor import Factor
import numpy as np


class FactorRetMulVolM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPriceHistorical",
                "TickLength": 1,
                'Parameters':
                    {
                        'Lag': max(self.__lag1, self.__lag2)
                    }
            }
        )

    def calculate(self):
        # lag1 > lag2
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag1:]
        if len(mid_price_list) < self.__lag2:
            factor_value = 0.0
        else:
            lag = min(self.__lag2, len(mid_price_list) - 1)
            ret = np.array(mid_price_list[lag:]) / np.array(mid_price_list[:-lag]) - 1
            ret_mean = np.nanmean(ret)

            vol_list = self._getLastNTickData("Volume", self.__lag1)
            if np.nanmean(vol_list) != 0:
                vol_pct = np.nanmean(vol_list[-self.__lag2:]) / np.nanmean(vol_list)
            else:
                vol_pct = 1

            factor_value = -ret_mean * vol_pct * 1000

        self._addFactorValue(factor_value)
