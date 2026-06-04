import numpy as np
from System.Factor import Factor


class PassiveOrderNum(Factor):
    def calculate(self):

        lastBidP1 = self._getLastNTickData("BidPrice", 2)[0][0]
        if lastBidP1 < 1e-6:
            lastBidP1 = self._getLastTickData("MinPrice")
        lastAskP1 = self._getLastNTickData("AskPrice", 2)[0][0]
        if lastAskP1 < 1e-6:
            lastAskP1 = self._getLastTickData("MaxPrice")

        orders = self._getLastTickData("Orders")
        if orders is not None:
            bsFlag = self._getOrderData("BSFlag", orders)
            price = self._getOrderData("Price", orders)
            orderType = self._getOrderData("OrderType", orders)
            buyPassiveNum = np.nansum((price[bsFlag == 1] < (lastAskP1 + 1e-6)) & (orderType[bsFlag == 1] == 2))
            sellPassiveNum = np.nansum((price[bsFlag == 2] > (lastBidP1 - 1e-6)) & (orderType[bsFlag == 2] == 2))
        else:
            buyPassiveNum, sellPassiveNum = 0, 0

        self._addFactorValue([buyPassiveNum, sellPassiveNum])
