from System.Factor import Factor
import numpy as np


class FactorBidBelow(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self._addIntermediate("ratio", [])

    def calculate(self):
        ratio_list = self.getIntermediate("ratio")
        avg_bid_price = self._getLastTickData("AvgBidPrice")
        bid_price = self._getLastTickData("BidPrice")
        bid_vol = self._getLastTickData("BidVolume")
        bid_price_mean = np.nansum(bid_price * bid_vol) / np.nansum(bid_vol) if np.nansum(bid_vol) != 0 else avg_bid_price
        ratio = (bid_price_mean - bid_price[0]) / (avg_bid_price - bid_price[0]) if avg_bid_price - bid_price[0] != 0 else 1
        ratio_list.append(ratio)
        if len(ratio_list) > 0:
            factor_value = np.nanmean(ratio_list[-self.__lag:])
        else:
            factor_value = 0
        self._addFactorValue(factor_value)
        print(factor_value)
