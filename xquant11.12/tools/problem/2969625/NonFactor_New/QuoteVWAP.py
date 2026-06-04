from System.Factor import Factor


class QuoteVWAP(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__firstLevels = self._getParameter("Level")

    def calculate(self):
        bidP = self._getLastTickData("BidPrice")
        bidV = self._getLastTickData("BidVolume")
        askP = self._getLastTickData("AskPrice")
        askV = self._getLastTickData("AskVolume")
        maxP = self._getLastTickData("MaxPrice")
        minP = self._getLastTickData("MinPrice")

        bidVSum = bidV[:self.__firstLevels].sum()
        bidVWAP = (bidP[:self.__firstLevels] * bidV[:self.__firstLevels]).sum() / bidVSum if bidVSum > 0 else minP

        askVSum = askV[:self.__firstLevels].sum()
        askVWAP = (askP[:self.__firstLevels] * askV[:self.__firstLevels]).sum() / askVSum if askVSum > 0 else maxP

        self._addFactorValue([bidVWAP, askVWAP])
