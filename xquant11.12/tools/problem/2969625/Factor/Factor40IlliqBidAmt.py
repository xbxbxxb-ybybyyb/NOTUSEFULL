from System.Factor import Factor
import numpy as np
'''
40个tick的买入成交额的非流动性指标*20个tick的买入成交额，表示短期的上涨收益预测
'''


class Factor40IlliqBidAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__shortWindow = min(int(self.__window / 2), 20)

        self.__bidAmtPerTrade = self._getFactor(
            {
                "ClassName": "BidAmtPerTrade"
            }
        )

    def calculate(self):
        price = self._getLastNTickData('LastPrice',self.__window + 1)
        if len(price) <= self.__window:
            pre_price = self._getLastTickData('PreviousClose')
            price = np.append(pre_price, price)
        pct = (price[1:] / price[:-1] - 1) * 100
        cum_pct = np.nansum(pct)

        bidAmtPerTradeList = self.__bidAmtPerTrade.getFactorValueList()
        long_amt = np.nansum(np.array(bidAmtPerTradeList[-self.__window:]))
        if long_amt == 0:
            res = 0
        else:
            res = (cum_pct / long_amt) * np.nansum(np.array(bidAmtPerTradeList[-self.__shortWindow:]))
        if np.isnan(res):
            res = 0

        self._addFactorValue(res)











