from System.Factor import Factor
import numpy as np


class MidPriceForStockGroup(Factor):
    def calculate(self):
        getP0 = np.vectorize(self.__get_P0)
        askP0Group = getP0(self._getLastTickDataForStockGroup("AskPrice"))[0, :]
        bidP0Group = getP0(self._getLastTickDataForStockGroup("BidPrice"))[0, :]
        lastMidPriceGroup = self.getLastFactorValue()

        factorValue = []
        for i in range(len(askP0Group)):
            askP0, bidP0 = askP0Group[i], bidP0Group[i]
            if askP0 == 0 or bidP0 == 0:
                if lastMidPriceGroup is not None:
                    lastMidPrice = lastMidPriceGroup[i]
                else:
                    lastMidPrice = None
                if lastMidPrice is None or lastMidPrice == 0:
                    factorValue.append(askP0 + bidP0)
                else:
                    factorValue.append(lastMidPrice)
            elif askP0 is None or bidP0 is None:
                factorValue.append(None)
            else:
                factorValue.append((askP0 + bidP0) / 2)

        factorValue = np.array(factorValue)
        self._addFactorValue(factorValue)

    @staticmethod
    def __get_P0(price_queue):
        if price_queue is not None:
            P0 = price_queue[0]
        else:
            P0 = None
        return P0
