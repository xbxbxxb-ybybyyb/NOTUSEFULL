from System.Factor import Factor


class BuyActiveUpVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.lag = self._getParameter("Lag")

    def calculate(self):
        orders = self._getLastTickData("Orders")
        if orders is None:
            self._addFactorValue(0)
            return

        price = self._getOrderData("Price", orders)
        volume = self._getOrderData("Volume", orders)
        bs = self._getOrderData("BSFlag", orders)

        bidP0s = self._getLastNTickData("BidPrice", self.lag)
        minP = self._getLastTickData("MinPrice")
        bidP0s = [x[0] if x[0] > 1e-4 else minP for x in bidP0s]
        bidP = min(bidP0s)

        activeVolume = volume[(bs == 1) & (price > bidP)].sum()

        self._addFactorValue(activeVolume)
