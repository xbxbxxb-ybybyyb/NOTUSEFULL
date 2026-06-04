import numpy as np
from L3FactorFrame.FactorBase import FactorBase
from L3FactorFrame.tools.regression import simpleRegression


class FacBuyPathTrend2(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)
        self.lag = config.get("lag", 2)*10
        self.price = [0]
        self.price_sign = []

    def calculate(self):

        base_price = self.getPrevTick("low_price")
        bid_price = self.getPrevTick("BidPrice")
        bid_volume = self.getPrevTick("BidVolume")

        volume_sum = bid_volume[:3].sum()
        amt_sum = (bid_volume*bid_price)[:3].sum()
        vwap = amt_sum/volume_sum if volume_sum>0 else base_price

        price_sign = 1 if vwap> self.price[-1] else -1 if vwap < self.price[-1] else 0
        self.price.append(vwap)
        self.price_sign.append(price_sign)

        if len(self.price_sign) < 5:
            value = 0
        else:
            y = np.array(self.price_sign[-self.lag:]).cumsum()
            X = np.arange(1, len(y)+1)
            value = simpleRegression(y, X)

        # print(value)
        self.addFactorValue(value)
