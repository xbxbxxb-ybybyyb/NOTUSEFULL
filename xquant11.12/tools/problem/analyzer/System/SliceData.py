# -*- coding: utf-8 -*-
"""
Created on Mon Aug  7 19:28:26 2017
Updated on 2018/7/10 新增 transactionData

@author: 006547 & 006566
"""


class SliceData:
    def __init__(self, code=0, timeStamp=0, time=0, bidPrice=0, askPrice=0, bidVolume=0, askVolume=0, lastPrice=0, volume=0, amount=0,
                 totalVolume=0, totalAmount=0, previousClosingPrice=0, transactionData=[], transactionTimeStamp=[],
                 maxPrice=0, minPrice=0, nextTimeStamp=0):
        self.code = code
        self.timeStamp = timeStamp
        self.time = time   # 当日日内的时间，例如103001000代表10:31:01
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.bidVolume = bidVolume
        self.askVolume = askVolume
        self.lastPrice = lastPrice
        self.volume = volume
        self.amount = amount
        self.totalVolume = totalVolume
        self.totalAmount = totalAmount
        self.previousClosingPrice = previousClosingPrice
        self.transactionData = transactionData
        self.transactionTimeStamp = transactionTimeStamp
        self.isLastSlice = False
        self.maxPrice = maxPrice
        self.minPrice = minPrice
        self.nextTimeStamp = nextTimeStamp
