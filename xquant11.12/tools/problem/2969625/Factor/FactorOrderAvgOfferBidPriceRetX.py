from System.Factor import Factor


class FactorOrderAvgOfferBidPriceRetX(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

    def calculate(self):
        AvgOfferPrice = self._getLastTickData("AvgOfferPrice")
        AvgBidPrice = self._getLastTickData("AvgBidPrice")
        maxPrice = self._getLastTickData("MaxPrice")
        minPrice = self._getLastTickData("MinPrice")
        
        AvgOfferPrice = AvgOfferPrice if AvgOfferPrice > 1e-4 else maxPrice
        AvgBidPrice = AvgBidPrice if AvgBidPrice > 1e-4 else minPrice

        factorValue = (AvgOfferPrice / AvgBidPrice - 1) * 10

        self._addFactorValue(factorValue)



