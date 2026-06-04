from System.Factor import Factor


class BuyActiveUpVolume(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__lag = self._getParameter("Lag")

    def calculate(self):
        orders = self._getLastTickData("Orders")
        if orders is None:
            self._addFactorValue(0)
            return

        price = self._getOrderData("Price", orders)
        volume = self._getOrderData("Volume", orders)
        bs = self._getOrderData("BSFlag", orders)

        bidP0s = self._getLastNTickData("BidPrice", self.__lag)
        bidP = min([x[0] for x in bidP0s])

        activeVolume = volume[(bs == 1) & (price > bidP)].sum()

        self._addFactorValue(activeVolume)
