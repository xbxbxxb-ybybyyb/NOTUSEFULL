from System.Factor import Factor
import numpy as np


class FactorAskBidOrderNumberVolatility(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__slag = self._getParameter("SecondLag")

        self._addIntermediate("BidNum", [])
        self._addIntermediate("AskNum", [])

    def calculate(self):
        askNumList = self.getIntermediate("AskNum")
        bidNumList = self.getIntermediate("BidNum")
        transaction = self._getLastTickData("Transactions")

        if transaction is not None:
            askNumList.append(self.__get_ask_num(transaction))
            bidNumList.append(self.__get_bid_num(transaction))
        else:
            askNumList.append(None)
            bidNumList.append(None)

        askNumFilterList = list(filter(lambda x: x is not None, askNumList))
        bidNumFilterList = list(filter(lambda x: x is not None, bidNumList))

        bid_num = bidNumFilterList[-self.__slag // 3:]  # 买方成交
        ask_num = askNumFilterList[-self.__slag // 3:]  # 卖方成交
        if len(bid_num) >= 5:
            factorValue = np.nanstd(ask_num) - np.nanstd(bid_num)
        else:
            lastValue = self.getLastFactorValue()
            if lastValue is not None:
                factorValue = lastValue
            else:
                factorValue = 0

        if np.isnan(factorValue):
            factorValue = 0

        self._addFactorValue(factorValue)

    def __get_bid_num(self, transaction):
        BSFlag = self._getTransactionData("BSFlag", transaction)
        return (BSFlag == 1).sum()

    def __get_ask_num(self, transaction):
        BSFlag = self._getTransactionData("BSFlag", transaction)
        return (BSFlag == 2).sum()