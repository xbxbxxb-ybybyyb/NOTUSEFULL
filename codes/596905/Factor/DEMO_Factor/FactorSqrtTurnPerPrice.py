from System.Factor import Factor
import numpy as np


class FactorSqrtTurnPerPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )
        self.__lag = self._getParameter("Lag")

    def calculate(self):
        free_float_shares = self._getLastNHistoricalDailyData("FreeFloatShares", 1)[0]
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag: ]
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))
        total_vol = np.nansum(self._getLastNTodayTickData("Volume", self.__lag))
        if len(mid_price_list) <= 1 or total_vol == 0 or mid_price_list[0] == 0:
            factor_value = 0
        else:
            sqrt_turn = np.sqrt(total_vol / free_float_shares)
            factor_value = (mid_price_list[-1] / mid_price_list[0] - 1) / sqrt_turn
        if np.isnan(factor_value):
            factor_value = 0
        self._addFactorValue(factor_value)
