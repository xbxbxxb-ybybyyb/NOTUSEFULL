#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/11/11 14:54
# -*- coding: utf-8 -*-

class SliceData(object):
    def __init__(self, code=0, timeStamp=0, time=0, bidPrice=0, askPrice=0, bidVolume=0, askVolume=0,
                 volume=0, amount=0, totalVolume=0, totalAmount=0,
                 previousClosingPrice=0, lastPrice=0, maxPrice=0, minPrice=0,
                 nextTimeStamp=0
    ):
        self.code = code
        self.timeStamp = timeStamp
        self.time = time
        self.bidPrice = bidPrice
        self.askPrice = askPrice
        self.bidVolume = bidVolume
        self.askVolume = askVolume
        self.volume = volume
        self.amount = amount
        self.totalVolume = totalVolume
        self.totalAmount = totalAmount
        self.previousClosingPrice = previousClosingPrice
        self.maxPrice = maxPrice
        self.lastPrice = lastPrice
        self.minPrice = minPrice
        self.nextTimeStamp = nextTimeStamp
