import datetime as dt
import numpy as np
from System.Factor import Factor


class TransactionDistribution(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__decayNum = self._getParameter("DecayNum")

    def calculate(self):
        if self.getLastFactorValue() is None:
            factorValue = [0, 0, 0]
        else:
            lastBidP0 = self._getLastNTickData("BidPrice", 2)[0][0]
            lastAskP0 = self._getLastNTickData("AskPrice", 2)[0][0]
            tickTimestamp = self._getLastTickData("Timestamp")
            transactionData = self._getLastTickData("Transactions")

            volumeBuy = 0
            volumeSell = 0
            volumeMid = 0
            if transactionData is None:
                factorValue = [0, 0, 0]
            else:
                transactionPrice = self._getTransactionData("Price", transactionData)
                transactionVolume = self._getTransactionData("Volume", transactionData)
                transactionTimestamp = self._getTransactionData("Timestamp", transactionData)

                for i in range(transactionData.shape[0]):
                    if transactionPrice[i] >= lastAskP0:
                        volumeBuy += self.cooling(transactionTimestamp[i], tickTimestamp, transactionVolume[i])
                    elif transactionPrice[i] <= lastBidP0:
                        volumeSell += self.cooling(transactionTimestamp[i], tickTimestamp, transactionVolume[i])
                    else:
                        volumeMid += self.cooling(transactionTimestamp[i], tickTimestamp, transactionVolume[i])
                totalVolume = volumeBuy + volumeSell + volumeMid

                if totalVolume == 0:
                    factorValue = [0, 0, 0]
                else:
                    factorValue = [volumeBuy / totalVolume, volumeMid / totalVolume, volumeSell / totalVolume]

        self._addFactorValue(factorValue)

    def cooling(self, transactionTimestamp, tickTimestamp, volume):
        transactionTime = dt.datetime.fromtimestamp(transactionTimestamp)
        tickTime = dt.datetime.fromtimestamp(tickTimestamp)
        morningEndTimestamp = dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day,
                                          11, 30, 00).timestamp()
        afternoonStartTimestamp = dt.datetime(tickTime.year, tickTime.month, tickTime.day, 13, 00, 00).timestamp()

        if transactionTimestamp <= morningEndTimestamp and tickTimestamp >= afternoonStartTimestamp:
            transactionTimestamp += (dt.datetime(transactionTime.year, transactionTime.month, transactionTime.day,
                                                 12, 59, 30).timestamp()
                                     - morningEndTimestamp)

        return np.power(0.5, (tickTimestamp - transactionTimestamp) / self.__decayNum) * volume
