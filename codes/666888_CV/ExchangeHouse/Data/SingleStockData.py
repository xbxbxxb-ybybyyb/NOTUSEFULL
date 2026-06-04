# -*- coding: utf-8 -*-
# @Time    : 2018/4/14 10:11
# @Author  : 011673
# @File    : SingleStockData.py
import datetime as dt
import sys
import time
import copy
import numpy as np

import System.ReadDataFile as readData

sys.path.append("../")


class SingleStockData:
    """
    对于单个股票各种方式查询数据的外接接口
    """

    def __init__(self, stock_code, start_date_time, end_date_time, total_tick_data, total_transaction_data):
        self.__stockCode = stock_code
        self.__startDateTime = start_date_time
        self.__endDateTime = end_date_time
        # 全部tick数据
        if total_tick_data is None:
            self.__allData = self.get_data()
        else:
            self.__allData = self.get_data_from_total(total_tick_data)
        # 全部逐笔委托数据
        if total_transaction_data is None:
            self.__allTransactionData = self.get_transaction_data()
        else:
            self.__allTransactionData = self.get_transaction_data_from_total(total_transaction_data)
    #     self.hash_timestamp=self.get_hash_timestamp(self.__allData['TimeStamp'])
    #     pass
    #
    # def get_hash_timestamp(self,target_list):
    #     timestamp_list=[target_list[0]]
    #     number_list=[0]
    #     temp=0
    #     for i in range(0,len(target_list)):
    #
    #

    def return_all_data(self):
        return self.__allData

    def return_all_transaction_data(self):
        return self.__allTransactionData

    @staticmethod
    def get_position(data, tick_num):
        """
        返回盘口
        把数据转换成Tick模式。存储格式为list，形式和大智慧显示的一样
        :param data: self.__allData
        :param tick_num: 第几个tick
        :return: 盘口list
        """
        result_list = np.zeros([20, 2], float)
        # noinspection PyBroadException
        try:
            result_list[0, 0] = round(data['AskP10'][tick_num], 2)
            result_list[1, 0] = round(data['AskP9'][tick_num], 2)
            result_list[2, 0] = round(data['AskP8'][tick_num], 2)
            result_list[3, 0] = round(data['AskP7'][tick_num], 2)
            result_list[4, 0] = round(data['AskP6'][tick_num], 2)
            result_list[5, 0] = round(data['AskP5'][tick_num], 2)
            result_list[6, 0] = round(data['AskP4'][tick_num], 2)
            result_list[7, 0] = round(data['AskP3'][tick_num], 2)
            result_list[8, 0] = round(data['AskP2'][tick_num], 2)
            result_list[9, 0] = round(data['AskP1'][tick_num], 2)
            result_list[10, 0] = round(data['BidP1'][tick_num], 2)
            result_list[11, 0] = round(data['BidP2'][tick_num], 2)
            result_list[12, 0] = round(data['BidP3'][tick_num], 2)
            result_list[13, 0] = round(data['BidP4'][tick_num], 2)
            result_list[14, 0] = round(data['BidP5'][tick_num], 2)
            result_list[15, 0] = round(data['BidP6'][tick_num], 2)
            result_list[16, 0] = round(data['BidP7'][tick_num], 2)
            result_list[17, 0] = round(data['BidP8'][tick_num], 2)
            result_list[18, 0] = round(data['BidP9'][tick_num], 2)
            result_list[19, 0] = round(data['BidP10'][tick_num], 2)
            result_list[0, 1] = data['AskV10'][tick_num]
            result_list[1, 1] = data['AskV9'][tick_num]
            result_list[2, 1] = data['AskV8'][tick_num]
            result_list[3, 1] = data['AskV7'][tick_num]
            result_list[4, 1] = data['AskV6'][tick_num]
            result_list[5, 1] = data['AskV5'][tick_num]
            result_list[6, 1] = data['AskV4'][tick_num]
            result_list[7, 1] = data['AskV3'][tick_num]
            result_list[8, 1] = data['AskV2'][tick_num]
            result_list[9, 1] = data['AskV1'][tick_num]
            result_list[10, 1] = data['BidV1'][tick_num]
            result_list[11, 1] = data['BidV2'][tick_num]
            result_list[12, 1] = data['BidV3'][tick_num]
            result_list[13, 1] = data['BidV4'][tick_num]
            result_list[14, 1] = data['BidV5'][tick_num]
            result_list[15, 1] = data['BidV6'][tick_num]
            result_list[16, 1] = data['BidV7'][tick_num]
            result_list[17, 1] = data['BidV8'][tick_num]
            result_list[18, 1] = data['BidV9'][tick_num]
            result_list[19, 1] = data['BidV10'][tick_num]
        except:
            pass
        return result_list

    @staticmethod
    def tick_and_transaction_calculate(position, transaction_list, direction='Plus'):
        """
        :param position: 原始的盘口
        :param transaction_list: 逐笔成交
        :param direction: Plus表示经过逐笔成交后成为当前盘口。
        :return: 回溯之前的盘口，Minus表示盘口经过了以上的主笔成交，得到新的盘口 PS：假设这段时间没有挂单情况
        """
        position = np.array(position)
        # 没有成交盘口不变
        if not transaction_list:
            return position
        else:
            # 如果是回溯
            if direction == 'Plus':
                # 对于每一笔成交
                for TransNum in range(0, len(transaction_list))[::-1]:
                    # 对于成交价格在盘口上已经显示的，则还原到盘口原来的数量
                    if transaction_list[TransNum][1] in position[:, 0]:
                        temp = np.where(position[:, 0] == transaction_list[TransNum][1])
                        level = temp[0][0]
                        position[level, 1] = max((position[level, 1] - transaction_list[TransNum][3]), 0)
                    # 如果没有价格的，首先看他是否还在盘口价格显示的范围内，如果不在说明异常交易。报错
                    else:
                        in_20_level = False
                        for level in range(0, 19):
                            if position[level, 0] > transaction_list[TransNum][1] > position[level + 1, 0]:
                                in_20_level = True
                                break
                        if not in_20_level:
                            print('Beyond 10BA')
                        # 如果成交价格超越了现在的卖一或者买一档位，说明这个档位是新挂出来的单子，则把这个档位的单子全部去掉
                        # 如果是在买一卖一之间成交如果是主卖说明原来有买单，则还原他
                        else:
                            a = np.array([transaction_list[TransNum][1], transaction_list[TransNum][3]])
                            position = np.insert(position, level + 1, a, axis=0)
                            if level < 9:
                                position = np.delete(position, -1, axis=0)
                            elif level > 9:
                                position = np.delete(position, 0, axis=0)
                            else:
                                if transaction_list[TransNum][2] == 'B':
                                    position = np.delete(position, -1, axis=0)
                                else:
                                    position = np.delete(position, 0, axis=0)
                return position

            elif direction == 'Minus':
                try:
                    transaction_list_copy = copy.deepcopy(transaction_list)
                    for TransNum in range(0, len(transaction_list_copy)):
                        if position[9, 0] > transaction_list_copy[TransNum][1] > position[10, 0]:
                            pass
                        elif transaction_list_copy[TransNum][1] >= position[9, 0]:
                            for level in range(0, 10)[::-1]:
                                if transaction_list_copy[TransNum][1] >= position[level, 0]:
                                    volume_minus = min(transaction_list_copy[TransNum][3], position[level, 1])
                                    transaction_list_copy[TransNum][3] = max(
                                        (transaction_list_copy[TransNum][3] - volume_minus), 0)
                                    position[level, 1] = max((position[level, 1] - volume_minus), 0)
                                    if transaction_list_copy[TransNum][3] <= 0:
                                        break
                        elif transaction_list_copy[TransNum][1] <= position[10, 0]:
                            for level in range(10, 20):
                                if transaction_list_copy[TransNum][1] <= position[level, 0]:
                                    volume_minus = min(transaction_list_copy[TransNum][3], position[level, 1])
                                    transaction_list_copy[TransNum][3] = max(
                                        (transaction_list_copy[TransNum][3] - volume_minus), 0)
                                    position[level, 1] = max((position[level, 1] - volume_minus), 0)
                                    if transaction_list_copy[TransNum][3] <= 0:
                                        break
                    # 原理与Plus基本相同，可以参照Plus来看
                    #     if transaction_list[TransNum][1] in position[:, 0]:
                    #         temp = np.where(position[:, 0] == transaction_list[TransNum][1])
                    #         level = temp[0][0]
                    #         position[level, 1] = max((position[level, 1] - transaction_list[TransNum][3]), 0)
                    #     else:
                    #         # if transaction_list[TransNum][1] > maxBAPrice or transaction_list[TransNum][1] < minBAPrice:
                    #         #     print('Beyond 10BA')
                    #         in_20_level = False
                    #         for level in range(0, 19):
                    #             if position[level, 0] > transaction_list[TransNum][1] > position[level + 1, 0]:
                    #                 in_20_level = True
                    #                 break
                    #         if not in_20_level:
                    #             print('Beyond 10BA')
                    #         else:
                    #             position = np.insert(position, level + 1, np.array(
                    #                 [transaction_list[TransNum][1], transaction_list[TransNum][3]]), axis=0)
                    #             if level < 9:
                    #                 position = np.delete(position, 0, axis=0)
                    #                 position = position[1:][:]
                    #             elif level > 9:
                    #                 position = np.delete(position, -1, axis=0)
                    #                 position = position[:-2][:]
                    #             else:
                    #                 if transaction_list[TransNum][2] == 'B':
                    #                     position = np.delete(position, 0, axis=0)
                    #                 else:
                    #                     position = np.delete(position, -1, axis=0)
                    del transaction_list_copy
                except:
                    pass
                return position
            else:
                print('Wrong in tick_and_transaction_calculate')

    def return_position(self, datetime, timedelay):
        """
        根据时间返回推算的盘口
        :param datetime: 现在的时间
        :param timedelay: 现在时间到上一个更新tick时间的时间差
        :return: 现在推算的盘口
        """
        time_stamp = time.mktime(datetime.timetuple()) + datetime.microsecond / 1000000  # 时间转换为时间戳
        # 找到所有延迟时间中的成交
        transaction_list_delay = self.get_transaction_data_by_time_stamp_gap(time_stamp, time_stamp + timedelay)
        original_position = self.get_tick_data_by_time(time_stamp)['Position']  # 得到下单对应的切片Tick
        # 根据延迟的成交情况推测现在的盘口
        position = self.tick_and_transaction_calculate(original_position, transaction_list_delay, 'Minus')
        return position, original_position, transaction_list_delay

    @staticmethod
    def adjust_index(target_list,i,position,mod):
        if position == 'last':
            while target_list[i] == target_list[min((len(target_list) - 1), i + 1)]:
                i = min((i + 1), (len(target_list) - 1))
                if i == len(target_list) - 1:
                    break
            if mod == 'leftequal':
                return i
            else:
                return min(i + 1, len(target_list) - 1)
        else:
            while target_list[i] == target_list[max(0, i - 1)]:
                i = max(0, (i - 1))
                if i == 0:
                    break
            if mod == 'leftequal':
                return i
            else:
                return min(i + 1, len(target_list) - 1)

    def bi_find(self,value, target_list, mod):
        """
        利用2分法找寻输入的TimeStamp 在TimeStampList这个栏的位置
        :param time_stamp: 目标值
        :param time_stamp_list: 对象的栏
        :param mod: 'leftequal' 返回栏左边的值的位置  'rightequal':返回栏右边值的位置
        :return:返回mod中的位置
        # """
        # for i in range(0, len(target_list) - 1):
        #     if mod == 'leftequal' and (target_list[i] <= value < target_list[i + 1]):
        #         return i
        #     elif mod == 'rightequal' and (target_list[i] <= value < target_list[i + 1]):
        #         return i + 1
        # if value < target_list[0]:
        #     return -2
        # elif value > target_list[1]:
        #     return len(target_list) - 1
        # else:
        #     return -1
        # ##
        if value < target_list[0]:
            return -2
        elif value > target_list[-1]:
            return len(target_list) - 1
        low = 0
        high = len(target_list) - 1
        while low <= high:
            if (high - low == 1):
                if target_list[high] == value:
                    return self.adjust_index(target_list,high,'last',mod)
                elif target_list[low] == value:
                    return self.adjust_index(target_list, low, 'last',mod)
                else:
                    if mod == 'rightequal':
                        return high
                    else:
                        return low
            mid = int(low + (high - low) / 2)
            if value < target_list[mid]:
                high = mid
            elif value > target_list[mid]:
                low = mid
            else:
                if mod == 'leftequal':
                    return self.adjust_index(target_list, mid, 'last', mod)
                else:
                    temp = min((mid), (len(target_list) - 1))
                    return self.adjust_index(target_list, temp, 'last', mod)
        return -1

    def get_transaction_data_by_time_stamp_gap(self, start_time_stamp, end_time_stamp):
        """
        找到一定时间内的逐笔成交信息
        :param start_time_stamp:开始的时间戳
        :param end_time_stamp:结束的时间戳
        :return:返回一个list，每一条是一个主笔成交（列表存储），按顺序分布记录'TimeStamp'，'Price'，'BSFlag'，'Volume'，'Time'（数字形式的时间）
        """
        if start_time_stamp >= end_time_stamp:
            return []
        # 寻找开始时间后的第一笔逐笔成交位置
        start_index = self.bi_find(start_time_stamp, self.__allTransactionData['TimeStamp'], 'rightequal')
        # 找到时间结束的那笔逐笔成交位置
        end_index = self.bi_find(end_time_stamp, self.__allTransactionData['TimeStamp'], 'rightequal')
        if start_index >= end_index:
            return []
        result_list = []
        if start_index != 0:
            start_index = start_index + 1
        for index in range(start_index, end_index + 1):
            result_list.append([
                self.__allTransactionData['TimeStamp'][index], self.__allTransactionData['Price'][index],
                self.__allTransactionData['BSFlag'][index], self.__allTransactionData['Volume'][index],
                self.__allTransactionData['Time'][index]])
        return result_list

    def get_position_by_time(self, time_stamp):
        i = self.bi_find(time_stamp, self.__allData['TimeStamp'], 'leftequal')
        position_list = self.get_position(self.__allData, i)
        return position_list

    def get_tick_data_by_time(self, time_stamp):
        """
        得到这个时间能看到的tick数据
        :param time_stamp:时间
        :return:字典类型。Position里存储这个Tick（2*10的数组，和大智慧显示的格式一样），Transactiuon里存储这个Tick到下个Tick中的逐笔成交
        逐笔成交为1*4的字典，分别存储1 时间戳，2 成交价格， 3 买卖方向，4 成交量，5 具体时间
        """
        i = self.bi_find(time_stamp, self.__allData['TimeStamp'], 'leftequal')
        position_list = self.get_position(self.__allData, i)
        transaction_list = []
        if i == 0:
            last_time_stamp = None
        else:
            # noinspection PyBroadException
            try:
                transaction_list = self.get_transaction_data_by_time_stamp_gap(
                    self.__allData['TimeStamp'][i - 1], self.__allData['TimeStamp'][i])
            except:
                transaction_list = []
            last_time_stamp = self.__allData['TimeStamp'][i - 1]
        # noinspection PyBroadException
        try:
            date_time = dt.datetime.fromtimestamp(self.__allData['TimeStamp'][i])
        except:
            print()
            date_time = dt.datetime.fromtimestamp(self.__allData['TimeStamp'][i])
        result = {
            'Position': position_list, 'TransactionList': transaction_list,
            'TimeStamp': self.__allData['TimeStamp'][i],
            'Time': self.__allData['Time'][i], 'DateTime': date_time, 'lastTimeStamp': last_time_stamp}
        return result

    def tick_play(self):
        """
        按tick播放行情
        :return: 列表，时间顺序存放了信息信息为字典，其中包括'Position'：盘口，
        'TransactionList'：上个tick到这个tick的逐笔成交信息，'TimeStamp'：时间戳
        'DateTime'：时间（datetime格式），'accVolume'：总成交量，
        'accAmount'：总成交额， 'isFirstTick'：是否是当天第一个tick
        """
        result_list = []
        original_data = self.return_all_data()
        for tickNum in range(0, len(original_data['Date'])):
            position = self.get_position(original_data, tickNum)
            transaction_list = self.get_transaction_data_by_time_stamp_gap(
                original_data['TimeStamp'][tickNum - 1], original_data['TimeStamp'][tickNum])
            time_stamp = original_data['TimeStamp'][tickNum]
            date_time = dt.datetime.fromtimestamp(time_stamp)
            acc_volume = original_data['AccVolume'][tickNum]
            acc_amount = original_data['AccTurover'][tickNum]
            is_first_tick = False
            if tickNum == 0:
                is_first_tick = True
            else:
                if original_data['Date'][tickNum] != original_data['Date'][tickNum - 1]:
                    is_first_tick = True
            tempdic = {
                'Position': position, 'TransactionList': transaction_list, 'TimeStamp': time_stamp,
                'DateTime': date_time, 'accVolume': acc_volume, 'accAmount': acc_amount,
                'isFirstTick': is_first_tick}
            result_list.append(tempdic)
        return result_list

    def get_data(self):
        # noinspection PyBroadException
        try:
            data = readData.getData(self.__stockCode, self.__startDateTime, self.__endDateTime, timeMode=2)
            if data is None:
                return None
            if len(data) == 0:
                return data
            elif len(data) == 1:
                return data[0]
            else:
                result = data[0]
                for i in range(1, len(data)):
                    if type(data[i]) == dict:
                        for key in result.keys():
                            result[key].append(data[i][key])
                return result
        except:
            print('no_tick_data')
            return None

    def get_transaction_data(self):
        # noinspection PyBroadException
        try:
            data = readData.getTransactionData(self.__stockCode, self.__startDateTime, self.__endDateTime, 2)
            if data is None:
                return None
            if len(data) == 0:
                return data
            elif len(data) == 1:
                return data[0]
            else:
                result = data[0]
                for i in range(1, len(data)):
                    if type(data[i]) == dict:
                        for key in result.keys():
                            result[key].append(data[i][key])
                return result
        except:
            print('no_transaction_data')
            return None

    def get_data_from_total(self, total_tick):
        try:
            start_date = int(self.__startDateTime.strftime('%Y%m%d'))
            end = self.__endDateTime - dt.timedelta(seconds=1)
            end_date = int(end.strftime('%Y%m%d'))
            if total_tick.__len__() == 0:
                return None
            data = []
            for day in range(0, len(total_tick)):
                if (total_tick[day] is not None) or total_tick[day] is not None:
                    if start_date <= int(total_tick[day]['Date'][0]) <= end_date:
                        data.append(total_tick[day])
            if len(data) == 0:
                return None
            elif len(data) == 1:
                return data[0]
            else:
                result = data[0]
                for i in range(1, len(data)):
                    if type(data[i]) == dict:
                        for key in result.keys():
                            result[key].append(data[i][key])
                return result
        except Exception as f:
            print('No tick data')
            return None

    def get_transaction_data_from_total(self, total_transaction):
        try:
            start_date = int(self.__startDateTime.strftime('%Y%m%d'))
            end = self.__endDateTime - dt.timedelta(seconds=1)
            end_date = int(end.strftime('%Y%m%d'))
            if total_transaction.__len__() == 0:
                return None
            data = []
            for day in range(0, len(total_transaction)):
                if total_transaction[day] is not None:
                    if start_date <= int(total_transaction[day]['Date'][0]) <= end_date:
                        data.append(total_transaction[day])
            if data is None:
                return None
            if len(data) == 0:
                return None
            elif len(data) == 1:
                return data[0]
            else:
                result = data[0]
                for i in range(1, len(data)):
                    if type(data[i]) == dict:
                        for key in result.keys():
                            result[key].append(data[i][key])
                return result
        except:
            print('No transaction data')
            return None
