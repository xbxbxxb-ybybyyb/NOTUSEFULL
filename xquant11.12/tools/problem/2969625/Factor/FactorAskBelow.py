from System.Factor import Factor
import numpy as np


class FactorAskBelow(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("ratio", [])

    def calculate(self):
        ratio_list = self.getIntermediate("ratio")
        avg_ask_price = self._getLastTickData("AvgOfferPrice")
        ask_price = self._getLastTickData("AskPrice")
        ask_vol = self._getLastTickData("AskVolume")
        ask_price_mean = np.nansum(ask_price * ask_vol) / np.nansum(ask_vol) if np.nansum(ask_vol) != 0 else avg_ask_price
        ratio = (ask_price_mean - ask_price[0]) / (avg_ask_price - ask_price[0]) if avg_ask_price - ask_price[0] != 0 else 1
        ratio_list.append(ratio)
        if len(ratio_list) > 0:
            factor_value = -np.nanmean(ratio_list[-self.__lag:])
        else:
            factor_value = 0
        self._addFactorValue(factor_value)
        print(factor_value)
