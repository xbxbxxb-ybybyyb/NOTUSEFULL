# 导入所需的包
import numpy as np
from FactorBase import FactorBase


class FacBOPriceGap(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)

    def calculate(self):
        ask_avg_px = self.getPrevTick("avg_ask_price")
        bid_avg_px = self.getPrevTick("avg_bid_price")
        ask_price = self.getPrevTick("AskPrice")
        bid_price = self.getPrevTick("BidPrice")

        priceDist = ask_avg_px - bid_avg_px

        if priceDist > 1e-4:
            value = -(ask_price[0] - bid_price[0]) / priceDist * 100
        else:
            value = 0.0

        # print(value)
        self.addFactorValue(value)
