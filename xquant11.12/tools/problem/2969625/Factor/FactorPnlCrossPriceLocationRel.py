from System.Factor import Factor


class FactorPnlCrossPriceLocationRel(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__indexName = self._getParameter("IndexName")

    def calculate(self):
        price_ind = self._getAllTodayINFTickData(self.__indexName, 'LastPrice')
        price = self._getAllTodayTickData('LastPrice')

        if len(price_ind) > 0:
            ind_price = price_ind[-1] / price_ind[0]
            s_price = price[-1] / price[0]
            factorValue = (s_price - ind_price) * 1e2
        else:
            factorValue = 0

        self._addFactorValue(factorValue)


