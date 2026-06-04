import math
import numpy as np
from System.Factor import Factor


class OrderDriveForce(Factor):
    def __init__(self, config, factorManager):
        super().__init__(config, factorManager)
        self.__level = self._getParameter("Level")

    def calculate(self):
        """
        lastSlice: 上一TICK数据
        currentSlice: 当前TICK数据
        midPrice: 当前TICK中间价
        """
        OrderBookTmp = []
        LastTimeStamp = 0
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

                startid = -1  # 记录新卖一价所在位置
                if AskVolChange[0] < 0:  # 分析主动买单部分
                    if len(np.intersect1d(AskPriceAll, AskPriceNow)) == 0:
                        OrderBookTmp.append(
                            [LastTimeStamp, AskPriceAll[-1], abs(sum(AskVolChange)), 'B'])
                        startid = len(AskVolChange)
                    else:
                        startid = np.argwhere(AskPriceAll == AskPriceNow[0])[0, 0]
                        if AskVolChange[startid] >= 0:
                            startid = startid - 1
                        OrderBookTmp.append([LastTimeStamp, AskPriceAll[startid],
                                             abs(sum(AskVolChange[0:startid + 1])), 'B'])

                for j in range(startid + 1, len(AskVolChange)):  # 分析主动买单上方部分
                    if AskVolChange[j] > 0:
                        OrderBookTmp.append([LastTimeStamp, AskPriceAll[j], AskVolChange[j], 'S'])
                    elif AskVolChange[j] < 0:
                        OrderBookTmp.append([LastTimeStamp, AskPriceAll[j], -AskVolChange[j], 'C'])

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

                startid = -1  # 记录新买一价所在位置
                if BidVolChange[0] < 0:  # 分析主动卖单部分
                    if len(np.intersect1d(BidPriceAll, BidPriceNow)) == 0:
                        OrderBookTmp.append(
                            [LastTimeStamp, BidPriceAll[-1], abs(sum(BidVolChange)), 'S'])
                        startid = len(BidVolChange)
                    else:
                        startid = np.argwhere(BidPriceAll == BidPriceNow[0])[0, 0]
                        if BidVolChange[startid] >= 0:
                            startid = startid - 1
                        OrderBookTmp.append([LastTimeStamp, BidPriceAll[startid],
                                             abs(sum(BidVolChange[0:startid + 1])), 'S'])

                for j in range(startid + 1, len(BidVolChange)):  # 分析主动卖单下方部分
                    if BidVolChange[j] > 0:
                        OrderBookTmp.append([LastTimeStamp, BidPriceAll[j], BidVolChange[j], 'B'])
                    elif BidVolChange[j] < 0:
                        OrderBookTmp.append([LastTimeStamp, BidPriceAll[j], -BidVolChange[j], 'C'])

            # 利用还原出的当前切片的委托，计算买卖压
            orderSide, orderPrice, orderVolume = [], [], []
            for k in range(len(OrderBookTmp)):
                orderSide.append(OrderBookTmp[k][3])
                orderPrice.append(OrderBookTmp[k][1])
                orderVolume.append(OrderBookTmp[k][2])

            bid_drive_force, ask_drive_force = self._compute_drive_force(bidPriceNow, askPriceNow,
                                                                      orderSide, orderPrice, orderVolume, self.__level)
        else:
            bid_drive_force, ask_drive_force = 0., 0.

        factorValue = [bid_drive_force, ask_drive_force]

        self._addFactorValue(factorValue)

    def _compute_drive_force(self, bidPrice, askPrice, orderSide, orderPrice, orderVolume, level):

        a_bid = 0
        b_bid = 0
        c_bid = 0
        a_ask = 0
        b_ask = 0
        c_ask = 0

        for i in range(len(orderPrice)):
            if orderSide[i] == 'B':
                if orderPrice[i] in bidPrice[:level]:
                    a_bid += orderVolume[i]
                elif orderPrice[i] in askPrice[:level]:
                    c_ask += orderVolume[i]

            elif orderSide[i] == 'S':
                if orderPrice[i] in bidPrice[:level]:
                    c_bid += orderVolume[i]
                elif orderPrice[i] in askPrice[:level]:
                    a_ask += orderVolume[i]

            elif orderSide[i] == 'C':
                if orderPrice[i] in bidPrice[:level]:
                    b_bid += orderVolume[i]
                elif orderPrice[i] in askPrice[:level]:
                    b_ask += orderVolume[i]

        if math.isnan(a_bid) or math.isinf(a_bid):
            a_bid = 0
        if math.isnan(b_bid) or math.isinf(b_bid):
            b_bid = 0
        if math.isnan(c_bid) or math.isinf(c_bid):
            c_bid = 0
        if math.isnan(a_ask) or math.isinf(a_ask):
            a_ask = 0
        if math.isnan(b_ask) or math.isinf(b_ask):
            b_ask = 0
        if math.isnan(c_ask) or math.isinf(c_ask):
            c_ask = 0

        bid_drive_force = a_bid - b_bid - c_bid
        ask_drive_force = a_ask - b_ask - c_ask

        return bid_drive_force, ask_drive_force