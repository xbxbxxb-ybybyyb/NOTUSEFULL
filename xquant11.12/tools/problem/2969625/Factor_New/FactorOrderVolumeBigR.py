import numpy as np
from System.Factor import Factor


class FactorOrderVolumeBigR(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.lag = self._getParameter("Lag")
        self._addIntermediate("bsVolume", [])

    def calculate(self):
        bsVolume = self.getIntermediate("bsVolume")
        orders = self._getLastTickData("Orders")
        if orders is None:
            bsVolume.append(0)
        else:
            orderP = self._getOrderData("Price", orders)
            orderV = self._getOrderData("Volume", orders)
            orderBS = self._getOrderData("BSFlag", orders)
            orderType = self._getOrderData("OrderType", orders)

            askP = self._getLastTickData("AskPrice")
            bidP = self._getLastTickData("BidPrice")
            askV = self._getLastTickData("AskVolume")
            bidV = self._getLastTickData("BidVolume")
            askN = self._getLastTickData("AskNum")
            bidN = self._getLastTickData("BidNum")
            askVN = np.sum(askV[:5]) / np.sum(askN[:5])
            bidVN = np.sum(bidV[:5]) / np.sum(bidN[:5])

            askP1 = askP[0] if askP[0] > 0 else self._getLastTickData("MaxPrice")
            bidP1 = bidP[0] if bidP[0] > 0 else self._getLastTickData("MinPrice")

            volumeSum = 0
            for i in range(orderP.shape[0]):
                if orderType[i] != 2:
                    continue
                price = orderP[i]
                volume = orderV[i]
                bs = orderBS[i]
                if bs == 1:
                    weight = np.power(2, (price - bidP1) / bidP1 * 10)
                    volumeBig = 0 if volume < 2 * bidVN else volume
                    volumeSum += weight * volumeBig / askVN if askVN > 0 else bidVN
                elif bs == 2:
                    weight = np.power(2, (askP1 - price) / askP1 * 10)
                    volumeBig = 0 if volume < 2 * askVN else volume
                    volumeSum -= weight * volumeBig / bidVN if bidVN > 0 else askVN
            bsVolume.append(volumeSum)

        factorValue = self.zscore(bsVolume, 5, 60)

        self._addFactorValue(factorValue)

    @staticmethod
    def zscore(l1, w1, w2):
        std1 = np.nanstd(l1[-w2:])
        if std1 == 0 or np.isnan(std1):
            return 0
        else:
            return (np.nanmean(l1[-w1:]) - np.nanmean(l1[-w2:])) / std1
