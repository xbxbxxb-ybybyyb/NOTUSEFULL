# -*- coding: utf-8 -*-
"""

@author: 012807
"""


import numpy as np
import math

from System.Factor import Factor


class FactorOrderMomentum(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)
        self.__OrderBook = []  # 用于存放订单流
        self.__AccAmountBuy = []  # 存放买压
        self.__AccAmountSell = []  # 存放卖压

    def calculate(self):
        OrderBookTmp = []
        OrderAmountBuy = 0
        OrderAmountSell = 0
        askvol = 0
        bidvol = 0
        # factorValue = [0, 0]
        if len(self.__data.getContent()) > 1:
            dataNow = self.__data.getLastContent()  # 当前切片数据
            dataLast = self.__data.getContent()[-2]  # 上一个切片数据
            askPriceNow = np.array(dataNow.askPrice)
            bidPriceNow = np.array(dataNow.bidPrice)
            askVolumeNow = np.array(dataNow.askVolume)
            bidVolumeNow = np.array(dataNow.bidVolume)
            askPriceLast = np.array(dataLast.askPrice)
            bidPriceLast = np.array(dataLast.bidPrice)
            askVolumeLast = np.array(dataLast.askVolume)
            bidVolumeLast = np.array(dataLast.bidVolume)

            # 还原卖盘委托
            AskPriceNow = askPriceNow[askPriceNow != 0]
            AskPriceLast = askPriceLast[askPriceLast != 0]
            AskPriceAll = np.union1d(AskPriceNow, AskPriceLast)  # 相邻两个切片的共同委托价
            if len(AskPriceNow) > 0 and len(AskPriceLast) > 0:
                minprice = min(AskPriceNow[-1], AskPriceLast[-1])
                AskPriceAll = AskPriceAll[AskPriceAll <= minprice]  # 如果未涨停，取两个卖盘最高价的较小值，比较不大于该值的委托

            if len(AskPriceAll) > 0:  # 涨停不进行比较
                AskVolNow = np.zeros_like(AskPriceAll)
                AskVolLast = np.zeros_like(AskPriceAll)

                # 计算各比较价格上的委托数量变化
                for i in range(len(AskPriceAll)):
                    if np.in1d(AskPriceAll[i], askPriceNow):
                        AskVolNow[i] = askVolumeNow[np.argwhere(askPriceNow == AskPriceAll[i])]
                    if np.in1d(AskPriceAll[i], askPriceLast):
                        AskVolLast[i] = askVolumeLast[np.argwhere(askPriceLast == AskPriceAll[i])]
                AskVolChange = AskVolNow - AskVolLast
                if AskVolNow.shape[0]>=3:
                    askvol = AskVolNow[0] + AskVolNow[1] + AskVolNow[2]
                elif AskVolNow.shape[0]>0:
                    askvol = sum(AskVolNow)



                startid = -1  # 记录新卖一价所在位置
                if AskVolChange[0] < 0:  # 分析主动买单部分
                    if len(np.intersect1d(AskPriceAll, AskPriceNow)) == 0:
                        OrderBookTmp.append(
                            [self.__data.getLastTimeStamp(), AskPriceAll[-1], abs(sum(AskVolChange)), 'B'])
                        startid = len(AskVolChange)
                    else:
                        startid = np.argwhere(AskPriceAll == AskPriceNow[0])[0, 0]
                        if AskVolChange[startid] >= 0:
                            startid = startid - 1
                        OrderBookTmp.append([self.__data.getLastTimeStamp(), AskPriceAll[startid],
                                             abs(sum(AskVolChange[0:startid + 1])), 'B'])

                # for j in range(startid + 1, len(AskVolChange)):  # 分析主动买单上方部分
                #     if AskVolChange[j] > 0:
                #         OrderBookTmp.append([self.__data.getLastTimeStamp(), AskPriceAll[j], AskVolChange[j], 'S'])
                #     elif AskVolChange[j] < 0:
                #         OrderBookTmp.append([self.__data.getLastTimeStamp(), AskPriceAll[j], -AskVolChange[j], 'CS'])

            # 还原买盘委托
            BidPriceNow = bidPriceNow[bidPriceNow != 0]
            BidPriceLast = bidPriceLast[bidPriceLast != 0]
            BidPriceAll = np.union1d(BidPriceNow, BidPriceLast)[::-1]  # 逆序排列
            if len(BidPriceNow) > 0 and len(BidPriceLast) > 0:
                maxprice = max(BidPriceNow[-1], BidPriceLast[-1])
                BidPriceAll = BidPriceAll[BidPriceAll >= maxprice]

            if len(BidPriceAll) > 0:  # 跌停不进行比较
                BidVolNow = np.zeros_like(BidPriceAll)
                BidVolLast = np.zeros_like(BidPriceAll)

                for i in range(len(BidPriceAll)):
                    if np.in1d(BidPriceAll[i], bidPriceNow):
                        BidVolNow[i] = bidVolumeNow[np.argwhere(bidPriceNow == BidPriceAll[i])]
                    if np.in1d(BidPriceAll[i], bidPriceLast):
                        BidVolLast[i] = bidVolumeLast[np.argwhere(bidPriceLast == BidPriceAll[i])]
                BidVolChange = BidVolNow - BidVolLast
                if BidVolNow.shape[0] >= 3:
                    bidvol = BidVolNow[0] + BidVolNow[1] + BidVolNow[2]
                elif BidVolNow.shape[0] > 0:
                    bidvol = sum(BidVolNow)
                startid = -1  # 记录新买一价所在位置
                if BidVolChange[0] < 0:  # 分析主动卖单部分
                    if len(np.intersect1d(BidPriceAll, BidPriceNow)) == 0:
                        OrderBookTmp.append(
                            [self.__data.getLastTimeStamp(), BidPriceAll[-1], abs(sum(BidVolChange)), 'S'])
                        startid = len(BidVolChange)
                    else:
                        startid = np.argwhere(BidPriceAll == BidPriceNow[0])[0, 0]
                        if BidVolChange[startid] >= 0:
                            startid = startid - 1
                        OrderBookTmp.append([self.__data.getLastTimeStamp(), BidPriceAll[startid],
                                             abs(sum(BidVolChange[0:startid + 1])), 'S'])

                # for j in range(startid + 1, len(BidVolChange)):  # 分析主动卖单下方部分
                #     if BidVolChange[j] > 0:
                #         OrderBookTmp.append([self.__data.getLastTimeStamp(), BidPriceAll[j], BidVolChange[j], 'B'])
                #     elif BidVolChange[j] < 0:
                #         OrderBookTmp.append([self.__data.getLastTimeStamp(), BidPriceAll[j], -BidVolChange[j], 'CB'])

                # askvol = AskVolNow[0] + AskVolNow[1] + AskVolNow[2]
                # bidvol = BidVolNow[0] + BidVolNow[1] + BidVolNow[2]
        # 利用还原出的当前切片的委托，计算买卖压
        self.__OrderBook.append(OrderBookTmp)
        if len(OrderBookTmp)>0:
            for k in range(len(OrderBookTmp)):
                if OrderBookTmp[k][3] == 'B':
                    OrderAmountBuy += (OrderBookTmp[k][1] * OrderBookTmp[k][2]) / (
                        1 + math.exp(-1000 * (OrderBookTmp[k][1] / self.__midPrice.getLastContent() - 1)))
                if OrderBookTmp[k][3] == 'S':
                    OrderAmountSell += (OrderBookTmp[k][1] * OrderBookTmp[k][2]) / (
                        1 + math.exp(1000 * (OrderBookTmp[k][1] / self.__midPrice.getLastContent() - 1)))

        self.__AccAmountBuy.append(OrderAmountBuy)
        self.__AccAmountSell.append(OrderAmountSell)
        factorValue = OrderAmountBuy - OrderAmountSell

        if factorValue > 0:
            factorValue = factorValue / (askvol + 1)
        else:
            factorValue = factorValue / (bidvol + 1)
        self.addData(factorValue, self.__data.getLastTimeStamp())

    def getOrderBook(self):
        return self.__OrderBook

    def getAccAmountBuy(self):
        return self.__AccAmountBuy

    def getAccAmountSell(self):
        return self.__AccAmountSell
