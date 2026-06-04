# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 13:51:09 2017

@author: 006547 & 006566
updated: 2018/4/25
如要添加新标签子类（SubTag），注意需添加如下几处：
1) 实例化储存不同算法标签的类
2) def calculate
3) def SubTag（视情况而定）

updated: 2018/6/14 & 6/15 & 6/22
1） 把涉及时间的MaxMin类subTag的计算方法，都改为最后计算（原来是过程中逐步更新）
2） 新增了1minMaxMinLong和1minMaxMinShort两类标签，以1minMaxMinLong为例，它的returnRate有3个值，都是以卖1价开仓、
    买1价平仓计算的，这3个值分别是：[相对开仓点的最大涨幅、相对开仓点的最大跌幅、从开仓点到最大涨幅之间相对开仓点的最大
    跌幅]， 1minMaxMinShort则类似，以买1价开仓、卖1价平仓；
3)  新增了1minRR，它的returnRate有4个值，即1minMaxMinLong的第1个值、第3个值和1minMaxMinShort的第1个值和第3个值

updated: 2018/6/25 —— 1) 新增1minMM12s，2minMM12s
2) 为了给pickle文件节约空间，把1minMaxMinLong, 1minMaxMinShort, 2minMaxMinLong, 2minMaxMinShort,1min和2min的endSliceData注释了

updated: 2018/6/28 & 7/2
1) 新增1minLongAB -- 以Ask1的价格开仓，1min后Bid1价格平仓； 1minShortBA, 2minLongAB, 2minShortBA同理
2) 新增1minLongAVWAP -- 以Ask1的价格开仓，整个1min的VWap平仓；1minShortBVWAP, 2minLongAVWAP, 2minShortBVWAP同理
3) 修正了LongAVWP（以及ShortBVWP）等标签中计算收益率时除数为0的问题

updated: 2018/7/13: 新增6个标签，分别是1, 2和5分钟的Long与Short
updated: 2018/7/11 & 7/25  删除endSliceData; 修正逐笔成交的bug
updated: 2018/8/2 修正了self.__ask1PriceList的错误，为subTag新增了startMidPrice和endMidPrice两个属性
updated: 2018/9/30 仅保留1minLong 和 1minShort
updated: 2018/11/7 删除subTag类中的startSliceData
updated: 2018/11/9 对本模块大幅精简
"""
from System.BaseTag import BaseTag
from datetime import datetime
from numpy import mean


class Tag(BaseTag):
    def __init__(self, para, factorManagement, sliceData):
        BaseTag.__init__(self, para, factorManagement)
        # 获取Tag计算参数
        self.__paraEmaMidPriceLag = para["paraEmaMidPriceLag"]

        # 获取数据和其他因子值
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        self.__midPrice = self.getFactorData({"name": "midPrice", "className": "MidPrice",
                                              "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                              "indexFactorUnderlying": self.getIndexFactorUnderlying()})
        paraEmaMidPrice = {"name": "emaMidPrice", "className": "Ema",
                           "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                           "indexFactorUnderlying": self.getIndexFactorUnderlying(),
                           "paraLag": self.__paraEmaMidPriceLag,
                           "paraOriginalData": {"name": "midPrice", "className": "MidPrice",
                                                "indexTradingUnderlying": self.getIndexTradingUnderlying(),
                                                "indexFactorUnderlying": self.getIndexFactorUnderlying()}}
        self.__emaMidPrice = self.getFactorData(paraEmaMidPrice)

        # 实例化储存不同算法标签的类
        self.subTag = {}
        self.subTag.update({"1minLong": SubTag(self.__data, self.__midPrice, sliceData, "ask1", 1, 0)})
        self.subTag.update({"1minShort": SubTag(self.__data, self.__midPrice, sliceData, "bid1", 1, 0)})
        self.subTag.update({"2minLong": SubTag(self.__data, self.__midPrice, sliceData, "ask1", 1, 0)})
        self.subTag.update({"2minShort": SubTag(self.__data, self.__midPrice, sliceData, "bid1", 1, 0)})
        self.subTag.update({"5minLong": SubTag(self.__data, self.__midPrice, sliceData, "ask1", 1, 0)})
        self.subTag.update({"5minShort": SubTag(self.__data, self.__midPrice, sliceData, "bid1", 1, 0)})
        self.subTag.update({"10minLong": SubTag(self.__data, self.__midPrice, sliceData, "ask1", 1, 0)})
        self.subTag.update({"10minShort": SubTag(self.__data, self.__midPrice, sliceData, "bid1", 1, 0)})
        
        self.finished = False
        if sliceData.isLastSlice:
            self.finished = True
        # 需要用到的中间变量
        self.__bid1PriceList = []
        self.__ask1PriceList = []

    def calculate(self, sliceData):
        # 买1价和卖1价序列，是为了计算平仓价格而设立的，为了避免涨跌停的影响，若遇到0则改为中间价
        if self.__data.getLastContent().bidPrice[0] > 0:
            self.__bid1PriceList.append(self.__data.getLastContent().bidPrice[0])
        else:
            self.__bid1PriceList.append(self.__midPrice.getLastContent())
        if self.__data.getLastContent().askPrice[0] > 0:
            self.__ask1PriceList.append(self.__data.getLastContent().askPrice[0])
        else:
            self.__ask1PriceList.append(self.__midPrice.getLastContent())

        # 1minLong
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["1minLong"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["1minLong"].startTimeStamp)
            # 如时间超过66秒，或遇到最后一个tick的切片
            if timeElapsed >= 66 or sliceData.isLastSlice:
                self.subTag["1minLong"].endTimeStamp = sliceData.timeStamp
                if self.__bid1PriceList.__len__() >= 5:
                    self.subTag["1minLong"].endPrice = mean(self.__bid1PriceList[-5:])
                else:
                    self.subTag["1minLong"].endPrice = mean(self.__bid1PriceList)
                if self.subTag["1minLong"].startPrice > 0:
                    self.subTag["1minLong"].returnRate = self.subTag["1minLong"].endPrice / self.subTag[
                        "1minLong"].startPrice - 1
                else:
                    self.subTag["1minLong"].returnRate = 0
                self.subTag["1minLong"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["1minLong"].finished = True

        # 1minShort
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["1minShort"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["1minShort"].startTimeStamp)
            # 如时间超过66秒，或遇到最后一个tick的切片
            if timeElapsed >= 66 or sliceData.isLastSlice:
                self.subTag["1minShort"].endTimeStamp = sliceData.timeStamp
                if self.__ask1PriceList.__len__() >= 5:
                    self.subTag["1minShort"].endPrice = mean(self.__ask1PriceList[-5:])
                else:
                    self.subTag["1minShort"].endPrice = mean(self.__ask1PriceList)
                if self.subTag['1minShort'].startPrice > 0:
                    self.subTag["1minShort"].returnRate = self.subTag["1minShort"].endPrice / self.subTag[
                        "1minShort"].startPrice - 1
                else:
                    self.subTag["1minShort"].returnRate = 0
                self.subTag["1minShort"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["1minShort"].finished = True

        # 2minLong
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["2minLong"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["2minLong"].startTimeStamp)
            # 如时间超过126秒，或遇到最后一个tick的切片
            if timeElapsed >= 126 or sliceData.isLastSlice:
                self.subTag["2minLong"].endTimeStamp = sliceData.timeStamp
                if self.__bid1PriceList.__len__() >= 5:
                    self.subTag["2minLong"].endPrice = mean(self.__bid1PriceList[-5:])
                else:
                    self.subTag["2minLong"].endPrice = mean(self.__bid1PriceList)
                if self.subTag["2minLong"].startPrice > 0:
                    self.subTag["2minLong"].returnRate = self.subTag["2minLong"].endPrice / self.subTag[
                        "2minLong"].startPrice - 1
                else:
                    self.subTag["2minLong"].returnRate = 0
                self.subTag["2minLong"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["2minLong"].finished = True

        # 2minShort
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["2minShort"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["2minShort"].startTimeStamp)
            # 如时间超过126秒，或遇到最后一个tick的切片
            if timeElapsed >= 126 or sliceData.isLastSlice:
                self.subTag["2minShort"].endTimeStamp = sliceData.timeStamp
                if self.__ask1PriceList.__len__() >= 5:
                    self.subTag["2minShort"].endPrice = mean(self.__ask1PriceList[-5:])
                else:
                    self.subTag["2minShort"].endPrice = mean(self.__ask1PriceList)
                if self.subTag['2minShort'].startPrice > 0:
                    self.subTag["2minShort"].returnRate = self.subTag["2minShort"].endPrice / self.subTag[
                        "2minShort"].startPrice - 1
                else:
                    self.subTag["2minShort"].returnRate = 0
                self.subTag["2minShort"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["2minShort"].finished = True

        # 5minLong
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["5minLong"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["5minLong"].startTimeStamp)
            # 如时间超过306秒，或遇到最后一个tick的切片
            if timeElapsed >= 306 or sliceData.isLastSlice:
                self.subTag["5minLong"].endTimeStamp = sliceData.timeStamp
                if self.__bid1PriceList.__len__() >= 5:
                    self.subTag["5minLong"].endPrice = mean(self.__bid1PriceList[-5:])
                else:
                    self.subTag["5minLong"].endPrice = mean(self.__bid1PriceList)
                if self.subTag["5minLong"].startPrice > 0:
                    self.subTag["5minLong"].returnRate = self.subTag["5minLong"].endPrice / self.subTag[
                        "5minLong"].startPrice - 1
                else:
                    self.subTag["5minLong"].returnRate = 0
                self.subTag["5minLong"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["5minLong"].finished = True

        # 5minShort
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["5minShort"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["5minShort"].startTimeStamp)
            # 如时间超过306秒，或遇到最后一个tick的切片
            if timeElapsed >= 306 or sliceData.isLastSlice:
                self.subTag["5minShort"].endTimeStamp = sliceData.timeStamp
                if self.__ask1PriceList.__len__() >= 5:
                    self.subTag["5minShort"].endPrice = mean(self.__ask1PriceList[-5:])
                else:
                    self.subTag["5minShort"].endPrice = mean(self.__ask1PriceList)
                if self.subTag['5minShort'].startPrice > 0:
                    self.subTag["5minShort"].returnRate = self.subTag["5minShort"].endPrice / self.subTag[
                        "5minShort"].startPrice - 1
                else:
                    self.subTag["5minShort"].returnRate = 0
                self.subTag["5minShort"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["5minShort"].finished = True
        
        # 10minLong
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["10minLong"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["10minLong"].startTimeStamp)
            # 如时间超过606秒，或遇到最后一个tick的切片
            if timeElapsed >= 606 or sliceData.isLastSlice:
                self.subTag["10minLong"].endTimeStamp = sliceData.timeStamp
                if self.__bid1PriceList.__len__() >= 5:
                    self.subTag["10minLong"].endPrice = mean(self.__bid1PriceList[-5:])
                else:
                    self.subTag["10minLong"].endPrice = mean(self.__bid1PriceList)
                if self.subTag["10minLong"].startPrice > 0:
                    self.subTag["10minLong"].returnRate = self.subTag["10minLong"].endPrice / self.subTag[
                        "10minLong"].startPrice - 1
                else:
                    self.subTag["10minLong"].returnRate = 0
                self.subTag["10minLong"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["10minLong"].finished = True

        # 10minShort
        if len(self.__emaMidPrice.getContent()) > 0 and (not self.subTag["10minShort"].finished):
            timeElapsed = TimeElapsed(sliceData.timeStamp, self.subTag["10minShort"].startTimeStamp)
            # 如时间超过606秒，或遇到最后一个tick的切片
            if timeElapsed >= 606 or sliceData.isLastSlice:
                self.subTag["10minShort"].endTimeStamp = sliceData.timeStamp
                if self.__ask1PriceList.__len__() >= 5:
                    self.subTag["10minShort"].endPrice = mean(self.__ask1PriceList[-5:])
                else:
                    self.subTag["10minShort"].endPrice = mean(self.__ask1PriceList)
                if self.subTag['10minShort'].startPrice > 0:
                    self.subTag["10minShort"].returnRate = self.subTag["10minShort"].endPrice / self.subTag[
                        "10minShort"].startPrice - 1
                else:
                    self.subTag["10minShort"].returnRate = 0
                self.subTag["10minShort"].endMidPrice = self.__midPrice.getLastContent()
                self.subTag["10minShort"].finished = True
                
        # 所有子标签完成计算后Tag才算完成
        self.finished = True
        for key in self.subTag:
            if not self.subTag[key].finished:
                self.finished = False
                break


class SubTag:
    def __init__(self, data, midPrice, sliceData, bidOrAsk, position, adjust, resultType="scalar", seqLen=10):
        # resultType 如为"scalar"，则returnRate初值赋为0、endPrice赋为None；
        # resultType 如为"list"则returnRate初始化为长度为seq的list，内容全是0；endPrice, endTimeStamp 和 endSliceData初始化为[]
        if len(data.getContent()) > 0 and (not sliceData.isLastSlice):
            self.startTimeStamp = sliceData.timeStamp
            self.startMidPrice = midPrice.getLastContent()
            self.code = data.getLastContent().code
            if bidOrAsk == "ask":
                if data.getLastContent().askPrice[position - 1] != 0:
                    self.startPrice = data.getLastContent().askPrice[position - 1] + adjust
                else:
                    self.startPrice = midPrice.getLastContent()
            elif bidOrAsk == "bid":
                if data.getLastContent().bidPrice[position - 1] != 0:
                    self.startPrice = data.getLastContent().bidPrice[position - 1] + adjust
                else:
                    self.startPrice = midPrice.getLastContent()
            elif bidOrAsk == "mid":
                self.startPrice = midPrice.getLastContent() + adjust
            elif bidOrAsk == "ask1":
                self.startPrice = data.getLastContent().askPrice[position - 1] + adjust
            elif bidOrAsk == "bid1":
                self.startPrice = data.getLastContent().bidPrice[position - 1] + adjust
            if resultType == "scalar":
                self.endPrice = None
                self.endMidPrice = None
                self.returnRate = 0
                self.endTimeStamp = None
            elif resultType == "list":
                self.endPrice = []
                self.endMidPrice = []
                self.returnRate = [0] * seqLen
                self.endTimeStamp = []
            elif resultType == "scalar2":
                self.endPrice = None
                self.endMidPrice = None
                self.returnRate = None
                self.endTimeStamp = None
            elif resultType == "list2":
                self.endPrice = []
                self.endMidPrice = []
                self.returnRate = [None] * seqLen
                self.endTimeStamp = []
            self.finished = False
        elif len(data.getContent()) > 0 and sliceData.isLastSlice:  # 刚初始化就遇到最后一个切片
            self.startTimeStamp = sliceData.timeStamp
            self.endTimeStamp = sliceData.timeStamp
            self.startMidPrice = midPrice.getLastContent()
            self.code = data.getLastContent().code
            self.startPrice = midPrice.getLastContent()
            if resultType == "scalar" or resultType == "scalar2":
                self.returnRate = 0
                self.endPrice = midPrice.getLastContent()
                self.endMidPrice = midPrice.getLastContent()
                self.endTimeStamp = None
            elif resultType == "list":
                self.returnRate = [0] * seqLen
                self.endPrice = []
                self.endMidPrice = midPrice.getLastContent()
                self.endTimeStamp = []
            elif resultType == "list2":
                self.endPrice = []
                self.endMidPrice = midPrice.getLastContent()
                self.returnRate = [None] * seqLen
                self.endTimeStamp = []
            self.finished = True
        else:
            self.startTimeStamp = sliceData.timeStamp
            self.endTimeStamp = sliceData.timeStamp
            self.startMidPrice = midPrice.getLastContent()
            self.code = None
            self.startPrice = None
            if resultType == "scalar" or resultType == "scalar2":
                self.returnRate = 0
                self.endPrice = None
                self.endMidPrice = None
                self.endTimeStamp = None
            elif resultType == "list":
                self.returnRate = [0] * seqLen
                self.endPrice = []
                self.endMidPrice = []
                self.endTimeStamp = []
            elif resultType == "list2":
                self.endPrice = []
                self.endMidPrice = []
                self.returnRate = [None] * seqLen
                self.endTimeStamp = []
            self.finished = True


def TimeElapsed(time1, time2):  # 输入时间time1和time2 （都为timestamp），其中time2时间早于time1，返回两者之间的差（单位是秒）
    hour1 = datetime.fromtimestamp(time1).hour  # 目前的小时
    hour2 = datetime.fromtimestamp(time2).hour  # 起始时间的小时
    if (hour1 <= 11 and hour2 <= 11) or (hour1 >= 13 and hour2 >= 13):  # 如跨中午，则需另外计算
        timeElapsed = time1 - time2
    else:
        timeElapsed = time1 - time2 - 5400
    return timeElapsed