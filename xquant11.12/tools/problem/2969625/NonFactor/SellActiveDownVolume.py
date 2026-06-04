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
        # askP = max([maxP if x[0] else x[0] for x in askP0s])  # TODO MARK: 本应对价格为0的进行过滤
        # activeVolume = volume[(bs == 2) & (price < askP)].sum()
        activeVolume = volume[bs == 2].sum()

        self._addFactorValue(activeVolume)
