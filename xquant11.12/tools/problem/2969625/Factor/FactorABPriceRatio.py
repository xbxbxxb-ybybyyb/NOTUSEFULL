from System.Factor import Factor
import numpy as np


class FactorABPriceRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

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
        ab_strength = self.getIntermediate("ab_strength")
        bid_price_adjust = self.__bid_vwap.getLastFactorValue()
        ask_price_adjust = self.__ask_vwap.getLastFactorValue()
        ab_strength.append(bid_price_adjust / ask_price_adjust if ask_price_adjust != 0 else 0)
        ab_strength_slice = ab_strength[-self.__lag:]
        factor_value = (np.nanmean(ab_strength_slice) - 1) * 1000
        if np.isnan(factor_value) or abs(factor_value) > 100:
            factor_value = 0

        self._addFactorValue(factor_value)
