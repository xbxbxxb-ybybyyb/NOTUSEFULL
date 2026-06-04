# -*- coding: utf-8 -*-
"""
Created on 2018/7/11 18:48
@author: 013050
@revised by 006566 2018/7/25
"""

from System.Factor import Factor
import numpy as np
import datetime as dt

class TradeNumWeighted(Factor):
    def __init__(self, para, factorManagement):
        Factor.__init__(self, para, factorManagement)
        self.__paraDecayNum = para['paraDecayNum']
        self.__paraMALag = para['paraMALag']
        self.__data = self.getTradingUnderlyingData(self.getIndexTradingUnderlying()[0])
        factorManagement.registerFactor(self, para)

    def calculate(self):
        data = self.__data.getContent()[-self.__paraMALag - 1:]
        timestamp = self.__data.getContent()[-self.__paraMALag - 1:]
        tick_timestamp = self.__data.getLastTimeStamp()
        bid_num = 0.0
        ask_num = 0.0
        data_num = len(data)

        for i in range(data_num):
            transaction_data = data[i].transactionData
            transaction_timestamp = timestamp[i].transactionTimeStamp
            if len(transaction_data) > 0:
                for j in range(len(transaction_data)):
                    if transaction_data[j][2] == 1:
                        bid_num += self.cooling(transaction_timestamp[j], tick_timestamp)
                    elif transaction_data[j][2] == -1:
                        ask_num += self.cooling(transaction_timestamp[j], tick_timestamp)

        factor_value = [bid_num, ask_num]
        self.addData(factor_value, self.__data.getLastTimeStamp())

    def cooling(self, transaction_timestamp, tick_timestamp):  # 冷却函数
        transaction_time = dt.datetime.fromtimestamp(transaction_timestamp)
        tick_time = dt.datetime.fromtimestamp(tick_timestamp)
        morning_end_timestamp = dt.datetime(transaction_time.year, transaction_time.month, transaction_time.day, 11, 30, 00).timestamp()
        afternoon_start_timestamp = dt.datetime(tick_time.year, tick_time.month, tick_time.day, 13, 00, 00).timestamp()

        if transaction_timestamp <= morning_end_timestamp and tick_timestamp >= afternoon_start_timestamp:
            transaction_timestamp += (dt.datetime(transaction_time.year, transaction_time.month, transaction_time.day, 12, 59, 30).timestamp() - morning_end_timestamp)

        return np.power(0.5, ((tick_timestamp - transaction_timestamp) / self.__paraDecayNum))
