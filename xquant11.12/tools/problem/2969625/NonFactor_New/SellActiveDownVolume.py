from System.Factor import Factor


class SellActiveDownVolume(Factor):
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

        askP0s = self._getLastNTickData("AskPrice", self.lag)
        maxP = self._getLastTickData("MaxPrice")
        askP0s = [x[0] if x[0] > 1e-4 else maxP for x in askP0s]
        askP = max(askP0s)

        activeVolume = volume[(bs == 2) & (price < askP)].sum()

        self._addFactorValue(activeVolume)
