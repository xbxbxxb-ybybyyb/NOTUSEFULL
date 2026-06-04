import math
import numpy as np
from System.Factor import Factor


class FactorOrderMomentum(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)

        self.__midPrice = self._getFactor(
            {
                "ClassName": "MidPrice"
            }
        )

    def calculate(self):
        orderBook = []
        orderAmountBuy = 0
        orderAmountSell = 0
        askVol = 0
        bidVol = 0

        if len(self.getFactorValueList()) > 0:
            askPriceLastTwo = self._getLastNTodayTickData("AskPrice", 2)
            bidPriceLastTwo = self._getLastNTodayTickData("BidPrice", 2)
            askVolumeLastTwo = self._getLastNTodayTickData("AskVolume", 2)
            bidVolumeLastTwo = self._getLastNTodayTickData("BidVolume", 2)

            askPriceLast = askPriceLastTwo[0]
            bidPriceLast = bidPriceLastTwo[0]
            askVolumeLast = askVolumeLastTwo[0]
            bidVolumeLast = bidVolumeLastTwo[0]
            askPriceNow = askPriceLastTwo[1]
            bidPriceNow = bidPriceLastTwo[1]
            askVolumeNow = askVolumeLastTwo[1]
            bidVolumeNow = bidVolumeLastTwo[1]

            # 还原卖盘委托
            askPriceNow = askPriceNow[askPriceNow != 0]
            askPriceLast = askPriceLast[askPriceLast != 0]
            askPriceAll = np.union1d(askPriceNow, askPriceLast)  # 相邻两个切片的共同委托价
            if askPriceNow.shape[0] > 0 and askPriceLast.shape[0] > 0:
                minPrice = min(askPriceNow[-1], askPriceLast[-1])
                askPriceAll = askPriceAll[askPriceAll <= minPrice]  # 如果未涨停，取两个卖盘最高价的较小值，比较不大于该值的委托

            if askPriceAll.shape[0] > 0:  # 涨停不进行比较
                askVolNow = np.zeros_like(askPriceAll)
                askVolLast = np.zeros_like(askPriceAll)

                # 计算各比较价格上的委托数量变化
                for i in range(askPriceAll.shape[0]):
                    if np.in1d(askPriceAll[i], askPriceNow):
                        askVolNow[i] = askVolumeNow[np.argwhere(askPriceNow == askPriceAll[i])]
                    if np.in1d(askPriceAll[i], askPriceLast):
                        askVolLast[i] = askVolumeLast[np.argwhere(askPriceLast == askPriceAll[i])]
                askVolChange = askVolNow - askVolLast
                askVol = np.sum(askVolNow[:3])

                if askVolChange[0] < 0:  # 分析主动买单部分
                    if np.intersect1d(askPriceAll, askPriceNow).shape[0] == 0:
                        orderBook.append([askPriceAll[-1], abs(sum(askVolChange)), "B"])
                    else:
                        startIdx = np.argwhere(askPriceAll == askPriceNow[0])[0, 0]
                        if askVolChange[startIdx] >= 0:
                            startIdx -= 1
                        orderBook.append([askPriceAll[startIdx], abs(sum(askVolChange[:startIdx + 1])), "B"])

            # 还原买盘委托
            bidPriceNow = bidPriceNow[bidPriceNow != 0]
            bidPriceLast = bidPriceLast[bidPriceLast != 0]
            bidPriceAll = np.union1d(bidPriceNow, bidPriceLast)[::-1]  # 逆序排列
            if bidPriceNow.shape[0] > 0 and bidPriceLast.shape[0] > 0:
                maxPrice = max(bidPriceNow[-1], bidPriceLast[-1])
                bidPriceAll = bidPriceAll[bidPriceAll >= maxPrice]

            if bidPriceAll.shape[0] > 0:  # 跌停不进行比较
                bidVolNow = np.zeros_like(bidPriceAll)
                bidVolLast = np.zeros_like(bidPriceAll)

                for i in range(bidPriceAll.shape[0]):
                    if np.in1d(bidPriceAll[i], bidPriceNow):
                        bidVolNow[i] = bidVolumeNow[np.argwhere(bidPriceNow == bidPriceAll[i])]
                    if np.in1d(bidPriceAll[i], bidPriceLast):
                        bidVolLast[i] = bidVolumeLast[np.argwhere(bidPriceLast == bidPriceAll[i])]
                bidVolChange = bidVolNow - bidVolLast
                bidVol = np.sum(bidVolNow[:3])

                if bidVolChange[0] < 0:  # 分析主动卖单部分
                    if np.intersect1d(bidPriceAll, bidPriceNow).shape[0] == 0:
                        orderBook.append([bidPriceAll[-1], abs(sum(bidVolChange)), "S"])
                    else:
                        startIdx = np.argwhere(bidPriceAll == bidPriceNow[0])[0, 0]
                        if bidVolChange[startIdx] >= 0:
                            startIdx = startIdx - 1
                        orderBook.append([bidPriceAll[startIdx], abs(sum(bidVolChange[:startIdx + 1])), "S"])

        # 利用还原出的当前切片的委托，计算买卖压
        midPrice = self.__midPrice.getLastFactorValue()
        for k in range(len(orderBook)):
            if orderBook[k][2] == "B":
                orderAmountBuy += ((orderBook[k][0] * orderBook[k][1])
                                   / (1 + math.exp(-1000 * (orderBook[k][0] / midPrice - 1))))
            if orderBook[k][2] == "S":
                orderAmountSell += ((orderBook[k][0] * orderBook[k][1])
                                    / (1 + math.exp(1000 * (orderBook[k][0] / midPrice - 1))))

        factorValue = orderAmountBuy - orderAmountSell

        if factorValue > 0:
            factorValue /= askVol + 1
        else:
            factorValue /= bidVol + 1

        self._addFactorValue(factorValue)
