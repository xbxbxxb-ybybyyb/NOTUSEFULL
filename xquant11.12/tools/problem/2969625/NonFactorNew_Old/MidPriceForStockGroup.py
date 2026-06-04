from System.Factor import Factor
import numpy as np


class MidPriceForStockGroup(Factor):
    def calculate(self):
        askP0Group = [self.__get_p0(each[0]) for each in self._getLastTickDataForStockGroup("AskPrice")]
        bidP0Group = [self.__get_p0(each[0]) for each in self._getLastTickDataForStockGroup("BidPrice")]
        lastMidPriceGroup = self.getLastFactorValue()

        factorValue = []
        for i in range(len(askP0Group)):
            askP0, bidP0 = askP0Group[i], bidP0Group[i]
            if askP0 == 0 or bidP0 == 0:
                factorValue.append(askP0 + bidP0)
            elif askP0 is None or bidP0 is None:
                if lastMidPriceGroup is not None:
                    lastMidPrice = lastMidPriceGroup[i]
                else:
                    lastMidPrice = np.nan
                factorValue.append(lastMidPrice)
            else:
                factorValue.append((askP0 + bidP0) / 2)

        self._addFactorValue(factorValue)

    @staticmethod
    def __get_p0(price_queue):
        if price_queue is not None:
            p0 = price_queue[0]
        else:
            p0 = None
        return p0
