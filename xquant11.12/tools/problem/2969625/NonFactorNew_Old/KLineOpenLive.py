from System.Factor import Factor


class KLineOpenLive(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__origData = self._getParameter("OriginalData")

    def calculate(self):
        data = self._getLastNTodayTickData(self.__origData, self.__lag)
        factorValue = data[0]
        self._addFactorValue(factorValue)
