from System.Factor import Factor
import numpy as np


class FactorRetSRM(Factor):
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
            factor_value = 0
        else:
            lag = self.__lag2 if len(mid_price_list) > self.__lag2 + 5 else len(mid_price_list) - 5 if len(mid_price_list) > 6 else 1
            ret = (np.array(mid_price_list[lag:]) / np.array(mid_price_list[:-lag]) - 1) * 1e3
            if np.nanstd(ret) < 1e-3:
                factor_value = 0
            else:
                factor_value = -np.nanmean(ret) / np.nanstd(ret)

        self._addFactorValue(factor_value)
