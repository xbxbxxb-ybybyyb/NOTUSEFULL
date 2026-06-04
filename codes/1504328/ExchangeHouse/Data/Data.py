# -*- coding: utf-8 -*-
# @Time    : 2018/4/14 10:11
# @Author  : 011673
# @File    : Data.py
from ExchangeHouse.Data.SingleStockData import SingleStockData
import datetime as dt


class Data:
    """
    返回多只股票的数据
    """

    def __init__(self, total_tick_data=None, total_transaction_data=None):
        """
        多股票数据集合存储，根据code调用特定股票的接口类signalStockData
        """
        self.__codeList = []
        self.__dataDic = {}
        self.__codeDate = {}
        self.__total_tick_data = total_tick_data
        self.__total_transaction_data = total_transaction_data

    def get_dic(self):
        return self.__dataDic

    def add_data(self, code, datetime, update_gap):
        update = False
        start = datetime - dt.timedelta(hours=datetime.hour, minutes=datetime.minute, seconds=datetime.second) - \
            dt.timedelta(days=update_gap[0])
        end = datetime - dt.timedelta(hours=datetime.hour, minutes=datetime.minute, seconds=datetime.second) + \
            dt.timedelta(days=(update_gap[1] + 1)) - dt.timedelta(seconds=1)
        if code not in self.__dataDic.keys():
            self.__dataDic.update({
                code: SingleStockData(code, start, end, self.__total_tick_data, self.__total_transaction_data)})
            self.__codeList.append(code)
            self.__codeDate[code] = [start, end]
            update = True
        else:
            if datetime < self.__codeDate[code][0] or datetime > self.__codeDate[code][1]:
                self.__dataDic.update({
                    code: SingleStockData(code, start, end, self.__total_tick_data, self.__total_transaction_data)})
                self.__codeDate[code] = [start, end]
                update = True
        return update

    def get_code_list(self):
        return self.__codeList

    def get_transaction_data_by_time_stamp_gap(self, code, start_time_stamp, end_time_stamp):
        return self.__dataDic[code].get_transaction_data_by_time_stamp_gap(self, start_time_stamp, end_time_stamp)

    def get_tick_data_by_time(self, code, time_stamp):
        return self.__dataDic[code].get_tick_data_by_time(time_stamp)

    def get_date(self, code):
        return self.__codeDate[code]
