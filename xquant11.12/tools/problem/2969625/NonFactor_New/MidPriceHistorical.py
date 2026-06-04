from System.Factor import Factor


class MidPriceHistorical(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        existed_midP = self.getFactorValueList()

        if len(existed_midP) == 0:
            askP0_list = [each[0] for each in self._getLastNTickData("AskPrice", self.__lag) if each is not None]
            bidP0_list = [each[0] for each in self._getLastNTickData("BidPrice", self.__lag) if each is not None]
            if len(askP0_list) > 1:
                ask_gap = askP0_list[-1] - askP0_list[-2]
                askP0_list = [x + ask_gap for x in askP0_list[:-1]] + [askP0_list[-1]]
                bid_gap = bidP0_list[-1] - bidP0_list[-2]
                bidP0_list = [x + bid_gap for x in bidP0_list[:-1]] + [bidP0_list[-1]]

            for i in range(min(self.__lag, len(askP0_list))):

                askP0, bidP0 = askP0_list[i], bidP0_list[i]

                if askP0 == 0 or bidP0 == 0:
                    lastMidPrice = self.getLastFactorValue()
                    if lastMidPrice is None or lastMidPrice == 0:
                        factorValue = askP0 + bidP0
                    else:
                        factorValue = lastMidPrice
                else:
                    factorValue = (askP0 + bidP0) / 2

                self._addFactorValue(factorValue)

        else:

            askP0 = self._getLastTickData("AskPrice")[0]
            bidP0 = self._getLastTickData("BidPrice")[0]
            if askP0 == 0 or bidP0 == 0:
                lastMidPrice = self.getLastFactorValue()
                if lastMidPrice is None or lastMidPrice == 0:
                    factorValue = askP0 + bidP0
                else:
                    factorValue = lastMidPrice
            else:
                factorValue = (askP0 + bidP0) / 2

            self._addFactorValue(factorValue)

