"""均线的涨跌幅"""

import numpy as np
from System.Factor import Factor


class MAPrice(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        mid_price_list = self.__midPrice.getFactorValueList()[-self.__lag:]
        ma_price = np.nanmean(mid_price_list)
        if np.isnan(ma_price):
            ma_price = 0

        self._addFactorValue(ma_price)
