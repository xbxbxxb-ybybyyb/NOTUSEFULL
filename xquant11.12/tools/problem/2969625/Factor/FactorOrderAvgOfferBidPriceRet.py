from System.Factor import Factor


class FactorOrderAvgOfferBidPriceRet(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        AvgOfferPrice = self._getLastTickData("AvgOfferPrice")
        AvgBidPrice = self._getLastTickData("AvgBidPrice")
        if AvgBidPrice > 1e-4:
            factorValue = (AvgOfferPrice / AvgBidPrice - 1) * 1000
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)



