from System.Factor import Factor


class FactorBOPriceGap(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        AvgOfferPrice = self._getLastTickData("AvgOfferPrice")
        AskP0 = self._getLastTickData("AskPrice")[0]
        AvgBidPrice = self._getLastTickData("AvgBidPrice")
        BidP0 = self._getLastTickData("BidPrice")[0]
        priceDist = AvgOfferPrice - AvgBidPrice
        if priceDist > 1e-4:
            factorValue = - (AskP0 - BidP0) / priceDist * 100
        else:
            factorValue = 0.

        self._addFactorValue(factorValue)



