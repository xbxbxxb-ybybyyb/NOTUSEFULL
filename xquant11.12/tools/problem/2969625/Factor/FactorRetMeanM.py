from System.Factor import Factor
import numpy as np


class FactorRetMeanM(Factor):
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
        if len(mid_price_list) < self.__lag2 + 20:
            factor_value = -1.0
        else:
            lag = min(self.__lag2, len(mid_price_list) - 1)
            ret = np.array(mid_price_list[lag:]) / np.array(mid_price_list[:-lag]) - 1
            ret_sorted = sorted(ret)[self.__lag2:-self.__lag2]
            if len(ret_sorted) < 20:
                factor_value = -1.0
            else:
                factor_value = -np.nanmean(ret_sorted) * 1000
        self._addFactorValue(factor_value)
