import numpy as np
from typing import List
from FactorBase import FactorBase


class FacBOVwapGap(FactorBase):
    def __init__(self, config, marketDataManager):
        super().__init__(config, marketDataManager)

        weightRatio = [0.0] * 10
        sum_weight = 0.0

        for i in range(10):
            tmp = pow(0.8, i)
            weightRatio[i] = tmp
            sum_weight += tmp

        for i in range(10):
            weightRatio[i] /= sum_weight

        self.weightRatio = np.array(weightRatio)

    def calculate(self):
        asks_price: List[float] = self.getPrevTick("AskPrice")
        asks_qty: List[float] = self.getPrevTick("AskVolume")
        bids_price: List[float] = self.getPrevTick("BidPrice")
        bids_qty: List[float] = self.getPrevTick("BidVolume")
        ask_avg_px = self.getPrevTick("avg_ask_price")
        bid_avg_px = self.getPrevTick("avg_bid_price")

        askVolSum = np.sum(asks_qty * self.weightRatio)
        bidVolSum = np.sum(bids_qty * self.weightRatio)
        askAmountSum = np.sum(askVolSum*asks_price)
        bidAmountSum = np.sum(bidVolSum*bids_price)

        askVwap = askAmountSum / askVolSum if askVolSum > 1e-4 else ask_avg_px
        bidVwap = bidAmountSum / bidVolSum if bidVolSum > 1e-4 else bid_avg_px

        priceDist = ask_avg_px - bid_avg_px

        value = 0.0 if priceDist <= 1e-4 else -(askVwap - bidVwap) / priceDist * 100

        # print(self.__class__.__name__, value)
        self.addFactorValue(value)
