from System.Factor import Factor
import numpy as np


class FactorMdfABStrength(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag1 = self._getParameter("Lag1")
        self.__lag2 = self._getParameter("Lag2")
        self.__ask_vwap = self._getFactor(
            {
                "ClassName": "AskVwap"
            }
        )
        self.__bid_vwap = self._getFactor(
            {
                "ClassName": "BidVwap"
            }
        )
        self._addIntermediate("ab_strength", [])

    def calculate(self):
        # lag1 > lag2
        ab_strength = self.getIntermediate("ab_strength")
        ask_price = self.__ask_vwap.getLastFactorValue()
        bid_price = self.__bid_vwap.getLastFactorValue()
        ab_strength.append(bid_price / ask_price if ask_price != 0 else 0.)
        ab_strength_slice = ab_strength[-self.__lag1:]
        if np.nanmean(ab_strength_slice) > 1e-6:
            amt_pressure = np.nanmean(ab_strength_slice[-self.__lag2:]) / np.nanmean(ab_strength_slice)
            factor_value = (amt_pressure - 1) * 1000
        else:
            factor_value = 0.

        if np.isnan(factor_value):
            factor_value = 0.

        self._addFactorValue(factor_value)
