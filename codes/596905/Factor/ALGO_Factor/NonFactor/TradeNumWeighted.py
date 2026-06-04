import datetime as dt
import numpy as np
from System.Factor import Factor


class TradeNumWeighted(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")
        self.__MALag = self._getParameter("MALag")

    def calculate(self):
        transactionData = self._getLastNTodayTickData("Transactions", self.__MALag + 1)
        tickTimestamp = self._getLastTickData("Timestamp")

        bidNum = 0
        askNum = 0
        for transaction in transactionData:
            if transaction is None:
                continue

            bsFlag = self._getTransactionData("BSFlag", transaction)
            transactionTimestamp = self._getTransactionData("Timestamp", transaction)
            for i in range(transaction.shape[0]):
                if bsFlag[i] == 1:
                    bidNum += self.__cooling(transactionTimestamp[i], tickTimestamp)
                elif bsFlag[i] == 2:
                    askNum += self.__cooling(transactionTimestamp[i], tickTimestamp)

        factorValue = [bidNum, askNum]
        self._addFactorValue(factorValue)

    def __cooling(self, transactionTimestamp, tickTimestamp):
        transactionTime = dt.datetime.fromtimestamp(transactionTimestamp)
        tickTime = dt.datetime.fromtimestamp(tickTimestamp)
        morningEndTimestamp = (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day, 11, 30, 00)
                               .timestamp())
        afternoonStartTimestamp = dt.datetime(tickTime.year, tickTime.month, tickTime.day, 13, 00, 00).timestamp()

        if transactionTimestamp <= morningEndTimestamp and tickTimestamp >= afternoonStartTimestamp:
            transactionTimestamp += (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day,
                                                 12, 59, 30).timestamp()
                                     - morningEndTimestamp)

        return np.power(0.5, (tickTimestamp - transactionTimestamp) / self.__decayNum)
