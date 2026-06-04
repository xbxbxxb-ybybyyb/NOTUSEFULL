import datetime as dt
import numpy as np
from System.Factor import Factor


class TradeVolumeWeightedM(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__MALag = self._getParameter("MALag")
        self.__NumLag = self._getParameter("NumLag")

    def calculate(self):
        transactionData = self._getLastNTodayTickData("Transactions", self.__MALag + 1)
        transactionData = [trans for trans in transactionData if trans is not None][-self.__NumLag:]
        tickTimestamp = self._getLastTickData("Timestamp")

        bidVolume = 0
        askVolume = 0
        for transaction in transactionData:
            if transaction is None:
                continue

            bsFlag = self._getTransactionData("BSFlag", transaction)
            transactionTimestamp = self._getTransactionData("Timestamp", transaction)
            transactionVolume = self._getTransactionData("Volume", transaction)
            for i in range(transaction.shape[0]):
                if bsFlag[i] == 1:
                    bidVolume += self.__cooling(transactionTimestamp[i], tickTimestamp, transactionVolume[i])
                elif bsFlag[i] == 2:
                    askVolume += self.__cooling(transactionTimestamp[i], tickTimestamp, transactionVolume[i])

        factorValue = [bidVolume, askVolume]
        self._addFactorValue(factorValue)

    def __cooling(self, transactionTimestamp, tickTimestamp, volume):
        transactionTime = dt.datetime.fromtimestamp(transactionTimestamp)
        tickTime = dt.datetime.fromtimestamp(tickTimestamp)
        morningEndTimestamp = (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day, 11, 30, 00)
                               .timestamp())
        afternoonStartTimestamp = dt.datetime(tickTime.year, tickTime.month, tickTime.day, 13, 00, 00).timestamp()

        if transactionTimestamp <= morningEndTimestamp and tickTimestamp >= afternoonStartTimestamp:
            transactionTimestamp += (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day,
                                                 12, 59, 30).timestamp()
                                     - morningEndTimestamp)

        return np.power(0.5, (tickTimestamp - transactionTimestamp) / self.__decayNum) * volume
