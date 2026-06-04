from System.Factor import Factor


class FactorOrderAskBidNumRatio(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        askNumArray = self._getLastTickData("AskNum")
        bidNumArray = self._getLastTickData("BidNum")

        factorValue = askNumArray[0] / bidNumArray[0] if bidNumArray[0] != 0 else 0

        self._addFactorValue(factorValue)



