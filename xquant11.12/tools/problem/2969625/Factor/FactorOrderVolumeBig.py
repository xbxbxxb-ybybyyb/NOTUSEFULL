import numpy as np
from System.Factor import Factor


class FactorOrderVolumeBig(Factor):
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
            askVN = askV / askN
            bidVN = bidV / bidN
            askVN[askN == 0] = 0
            bidVN[bidN == 0] = 0

            askP1 = askP[0] if askP[0] > 0 else self._getLastTickData("MaxPrice")
            bidP1 = bidP[0] if bidP[0] > 0 else self._getLastTickData("MinPrice")

            volumeSum = 0
            for i in range(orderP.shape[0]):  # 主动且低于对一价成交的大单
                if orderType[i] != 2:
                    continue
                price = orderP[i]
                volume = orderV[i]
                bs = orderBS[i]
                if bs == 1:
                    price = min(askP1, price)
                    weight = np.power(2, (price - bidP1) / bidP1 * 200)
                    quoteVolume = bidVN[bidP == price]
                    quoteVolume = quoteVolume[0] if quoteVolume.shape[0] > 0 else 0
                    volumeBig = 0 if volume < 2 * quoteVolume else volume
                    volumeSum += weight * volumeBig
                elif bs == 2:
                    price = max(bidP1, price)
                    weight = np.power(2, (askP1 - price) / askP1 * 200)
                    quoteVolume = askVN[askP == price]
                    quoteVolume = quoteVolume[0] if quoteVolume.shape[0] > 0 else 0
                    volumeBig = 0 if volume < 2 * quoteVolume else volume
                    volumeSum -= weight * volumeBig
            bsVolume.append(volumeSum)

        vm = np.mean(self._getLastNTickData("Volume", self.lag))
        fv = np.mean(bsVolume[-self.lag:]) / vm if vm > 1e-6 else 0

        self._addFactorValue(fv)
