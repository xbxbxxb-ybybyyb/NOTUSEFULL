from System.Factor import Factor
import numpy as np


class FactorShortStrength_MDF(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwapZT"
            }
        )

    def calculate(self):
        import datetime as dt
        time = self._getLastTickData("Timestamp")
        time = dt.datetime.strftime(dt.datetime.fromtimestamp(time),'%H%M%S')
        if time == '133324':
            print('!')
        ask_price = self._getLastTickData("AskPrice")[0]
        bid_price_adjust = self.__bid_vwap.getFactorValueList()[-self.__lag:]
        short_strength = np.nanmean(bid_price_adjust) / ask_price - 1 if ask_price != 0 else 0.
        factor_value = short_strength * 100
        if np.isnan(factor_value):
            factor_value = 0

        self._addFactorValue(factor_value)
