from System.Factor import Factor


class EMA(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__lag = self._getParameter("Lag")
        self.__originalData = self._getFactor(self._getParameter("OriginalData"))

    def calculate(self):
        factorValueListLength = len(self.getFactorValueList())
        originalDataListLength = len(self.__originalData.getFactorValueList())

        lastOriginalData = self.__originalData.getLastFactorValue()
        lastEMAData = self.getLastFactorValue()

        if factorValueListLength == 0:
            factorValue = lastOriginalData
        else:
            if self.__lag is None or originalDataListLength <= self.__lag:
                length = factorValueListLength
            else:
                length = self.__lag

            if isinstance(lastOriginalData, list):
                factorValue = []
                for i in range(len(lastOriginalData)):
                    factorValue.append(lastEMAData[i] + 2 * (lastOriginalData[i] - lastEMAData[i]) / (length + 1))
            else:
                factorValue = lastEMAData + 2 * (lastOriginalData - lastEMAData) / (length + 1)

        self._addFactorValue(factorValue)
