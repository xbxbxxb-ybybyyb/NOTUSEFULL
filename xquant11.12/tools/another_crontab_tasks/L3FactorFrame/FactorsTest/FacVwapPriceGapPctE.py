# 导入所需的包
import numpy as np
from L3FactorFrame.FactorBase import FactorBase


class FacVwapPriceGapPctE(FactorBase):
    def __init__(self, config, factorManager, marketDataManager):
        super().__init__(config, factorManager, marketDataManager)

    def calculate(self):
        asks_price = self.getPrevTick("AskPrice")
        asks_qty = self.getPrevTick("AskVolume")
        bids_price = self.getPrevTick("BidPrice")
        bids_qty = self.getPrevTick("BidVolume")

        midPrice = (asks_price[0] + bids_price[0]) / 2

        vwapAsk = np.sum(asks_price[:5]*asks_qty[:5])
        qtyAskSum = np.sum(asks_qty[:5])
        vwapBid = np.sum(bids_price[:5]*bids_qty[:5])
        qtyBidSum = np.sum(bids_qty[:5])
        value = 0.5

        if qtyAskSum > 0 and qtyBidSum > 0:
            vwapAsk /= qtyAskSum
            vwapBid /= qtyBidSum
            value = (vwapAsk - midPrice) / (vwapAsk - vwapBid)

        # print(self.__class__.__name__, value)
        self.addFactorValue(value)
