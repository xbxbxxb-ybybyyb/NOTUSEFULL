from System.Factor import Factor
import numpy as np
'''
100个tick的卖出成交额的非流动性指标*20个tick的卖出成交额，表示长期的下跌收益预测
'''


class Factor100IlliqAskAmt(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")
        self.__shortWindow = min(int(self.__window / 2), 20)

        self.__askAmtPerTrade = self._getFactor(
            {
                "ClassName": "AskAmtPerTrade"
            }
        )

    def calculate(self):
        price = self._getLastNTickData('LastPrice', self.__window + 1)
        if len(price) <= self.__window:
            pre_price = self._getLastTickData('PreviousClose')
            price = np.append(pre_price, price)
        pct = (price[1:] / price[:-1] - 1) * 100
        cum_pct = np.nansum(pct)

        askAmtPerTradeList = self.__askAmtPerTrade.getFactorValueList()
        long_amt = np.nansum(np.array(askAmtPerTradeList[-self.__window:]))
        if long_amt == 0:
            res = 0
        else:
            res = (cum_pct / long_amt) * np.nansum(np.array(askAmtPerTradeList[-self.__shortWindow:]))
        if np.isnan(res):
            res = 0

        self._addFactorValue(res)












