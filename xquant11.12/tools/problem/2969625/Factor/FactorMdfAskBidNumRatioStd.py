from System.Factor import Factor
import numpy as np

'''
买入成交笔数/总成交笔数，表示上涨力量，其波动率考虑偏离一段时间的平均值
'''


class FactorMdfAskBidNumRatioStd(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__window = self._getParameter("Window")

        self._addIntermediate("BidNumRatioList", [])

    def calculate(self):
        bidNumRatioList = self.getIntermediate("BidNumRatioList")
        transaction = self._getLastTickData('Transactions')
        if transaction is None:
            value = 0
        else:
            value = self.__getRatio(transaction)
        bidNumRatioList.append(value)
        std_value = np.sort(bidNumRatioList[-self.__window:])[int(min(len(bidNumRatioList), self.__window) * 0.75)] - \
                    np.mean(bidNumRatioList[-5 * self.__window:])

        if np.isnan(std_value):
            std_value = 0

        self._addFactorValue(std_value)

    def __getRatio(self, transaction):
        BSFlag = self._getTransactionData("BSFlag", transaction)
        return (BSFlag == 1).sum() / len(BSFlag)
