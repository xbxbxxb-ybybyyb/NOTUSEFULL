import numpy as np
from System.Factor import Factor


class PassiveOrderQty(Factor):
    def calculate(self):
        lastBidP1 = self._getLastNTickData("BidPrice", 2)[0][0]
        lastBidP3 = self._getLastNTickData("BidPrice", 2)[0][2]
        if lastBidP1 < 1e-6:
            lastBidP1 = self._getLastTickData("MinPrice")
        if lastBidP3 < 1e-6:
            lastBidP3 = self._getLastTickData("MinPrice")
        lastAskP1 = self._getLastNTickData("AskPrice", 2)[0][0]
        lastAskP3 = self._getLastNTickData("AskPrice", 2)[0][2]
        if lastAskP1 < 1e-6:
            lastAskP1 = self._getLastTickData("MaxPrice")
        if lastAskP3 < 1e-6:
            lastAskP3 = self._getLastTickData("MaxPrice")

        buyPassiveQty, sellPassiveQty = 0, 0
        orders = self._getLastTickData("Orders")
        if orders is not None:
            bsFlag = self._getOrderData("BSFlag", orders)
            price = self._getOrderData("Price", orders)
            orderType = self._getOrderData("OrderType", orders)
            volume = self._getOrderData("Volume", orders)
            buyPassiveMask = (price[bsFlag == 1] < (lastAskP1 - 1e-6)) & (price[bsFlag == 1] >= (lastBidP3 - 1e-6)) & (orderType[bsFlag == 1] == 2)
            sellPassiveMask = (price[bsFlag == 2] > (lastBidP1 + 1e-6)) & (price[bsFlag == 2] <= (lastAskP3 + 1e-6)) & (orderType[bsFlag == 2] == 2)
            if sum(buyPassiveMask) > 0:
                buyPassiveQty = np.mean(volume[bsFlag == 1][buyPassiveMask])
            if sum(sellPassiveMask) > 0:
                sellPassiveQty = np.mean(volume[bsFlag == 2][sellPassiveMask])

        self._addFactorValue([buyPassiveQty, sellPassiveQty])
