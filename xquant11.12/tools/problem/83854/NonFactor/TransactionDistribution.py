# -*- coding: utf-8 -*-
# @Time    : 2018/7/11 9:01
# @Author  : 011673
# @File    : TransactionDistribution.py
import numpy as np
import math
from System.Factor import Factor
import datetime as dt

class TransactionDistribution(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        if len(self.__data.getContent()) < 2:
            self.addData([0.0, 0, 0.0], self.__data.getLastTimeStamp())
        else:
            last_bid_0_price = self.__data.getContent()[-2].bidPrice[0]
            last_ask_0_price = self.__data.getContent()[-2].askPrice[0]
            transaction_list = self.__data.getContent()[-1].transactionData
            transaction_timestamp = self.__data.getContent()[-1].transactionTimeStamp
            tick_timestamp = self.__data.getLastTimeStamp()
            volume_buy = 0
            volume_sell = 0
            volume_mid = 0
            if len(transaction_list) == 0:
                self.addData([0.0, 0.0, 0.0], self.__data.getLastTimeStamp())
            else:
                for i in range(len(transaction_list)):
                    if transaction_list[i][3] >= last_ask_0_price:
                        volume_buy += self.cooling(transaction_timestamp[i], tick_timestamp, transaction_list[i][4])
                    elif transaction_list[i][3] <= last_bid_0_price:
                        volume_sell += self.cooling(transaction_timestamp[i], tick_timestamp, transaction_list[i][4])
                    else:
                        volume_mid += self.cooling(transaction_timestamp[i], tick_timestamp, transaction_list[i][4])
                total_vol = volume_mid + volume_buy + volume_sell
                if total_vol == 0:
                    self.addData([0.0, 0.0, 0.0], self.__data.getLastTimeStamp())
                else:
                    result = [volume_buy / total_vol, volume_mid / total_vol, volume_sell / total_vol]
                    self.addData(result, self.__data.getLastTimeStamp())

    def cooling(self, transaction_timestamp, tick_timestamp, volume): # 冷却函数
        transaction_time = dt.datetime.fromtimestamp(transaction_timestamp)
        tick_time = dt.datetime.fromtimestamp(tick_timestamp)
        morning_end_timestamp = dt.datetime(transaction_time.year, transaction_time.month, transaction_time.day, 11, 30, 00).timestamp()
        afternoon_start_timestamp = dt.datetime(tick_time.year, tick_time.month, tick_time.day, 13, 00, 00).timestamp()

        if transaction_timestamp <= morning_end_timestamp and tick_timestamp >= afternoon_start_timestamp:
            transaction_timestamp += (dt.datetime(transaction_time.year, transaction_time.month, transaction_time.day, 12, 59, 30).timestamp() - morning_end_timestamp)

        return np.power(0.5, (tick_timestamp - transaction_timestamp) / self.__paraDecayNum) * volume

