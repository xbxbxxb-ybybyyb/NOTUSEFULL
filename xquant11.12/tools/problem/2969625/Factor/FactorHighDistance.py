from System.Factor import Factor
import numpy as np


class FactorHighDistance(Factor):
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
        mid_price_list = list(filter(lambda x: x is not None, mid_price_list))

        volume_array = self._getLastNTodayTickData("Volume", self.__lag)
        amount_array = self._getLastNTodayTickData("Amount", self.__lag)
        vwap_price = np.nansum(amount_array) / np.nansum(volume_array) if np.nansum(volume_array) != 0 else 0

        if len(mid_price_list) <= 1:
            factor_value = 0
        else:
            mid_price = mid_price_list[-1]
            high_price = max(mid_price_list)
            if vwap_price is None or mid_price is None:
                factor_value = 0
            elif vwap_price <= 0.01 or mid_price <= 0.01:
                if len(self.getFactorValueList()) == 0:
                    factor_value = 0
                else:
                    factor_value = self.getLastFactorValue()
            else:
                if high_price == vwap_price:
                    factor_value = 1
                else:
                    factor_value = (mid_price - vwap_price) / (high_price - vwap_price)

        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
