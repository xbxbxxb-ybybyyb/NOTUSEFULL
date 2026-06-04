from System.Factor import Factor


class MidPriceHistorical(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")

    def calculate(self):

        existed_midP = self.getFactorValueList()

        if len(existed_midP) == 0:

            askP0_list = [each[0] for each in self._getLastNTickData("AskPrice", self.__lag)]
            bidP0_list = [each[0] for each in self._getLastNTickData("BidPrice", self.__lag)]

            for i in range(self.__lag):

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

