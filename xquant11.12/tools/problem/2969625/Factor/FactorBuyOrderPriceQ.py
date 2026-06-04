import numpy as np
from System.Factor import Factor


class FactorBuyOrderPriceQ(Factor):
    def calculate(self):

        minPrice = self._getLastTickData("MinPrice")
        maxPrice = self._getLastTickData("MaxPrice")

        askP = self._getLastTickData("AskPrice")
        bidP = self._getLastTickData("BidPrice")
        bidV = self._getLastTickData("BidVolume")

        buyPrice = bidP[0] if bidP[0] > 0 else minPrice
        sellPrice = askP[0] if askP[0] > 0 else maxPrice

        weightedBuyAmt = 0
        weightedBuyVolume = 0
        orders = self._getLastTickData("Orders")
        if orders is not None:
            orderType = self._getOrderData("OrderType", orders)
            orderBS = self._getOrderData("BSFlag", orders)
            price = self._getOrderData("Price", orders)
            volume = self._getOrderData("Volume", orders)
            for i in range(orderType.shape[0]):
                if orderType[i] == 2 and orderBS[i] == 1:
                    weight = np.power(2, (price[i] - buyPrice) / buyPrice * 200)
                    weightedBuyAmt += price[i] * volume[i] * weight
                    weightedBuyVolume += volume[i] * weight
        weightedBuyPrice = weightedBuyAmt / weightedBuyVolume if weightedBuyVolume > 0 else np.nan

        totalBidV = np.sum(bidV)
        fv = np.sum(bidV[bidP <= weightedBuyPrice]) / (2 - weightedBuyPrice / sellPrice) / totalBidV if totalBidV > 0 else 0

        if np.isnan(fv):
            fv = 0
        self._addFactorValue(fv)
