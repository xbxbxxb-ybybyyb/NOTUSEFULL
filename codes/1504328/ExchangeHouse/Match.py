# -*- coding: utf-8 -*-
# @Time    : 2018/4/14 10:11
# @Author  : 011673
# @File    : Match.py
import time
import datetime as dt
import numpy as np


class Match:
    """
    用来模拟撮合的模块
    输入的orderStatus是成交状态的类，需要提前阅读下其中各个参数的意义
    """

    def __init__(self, stock_code, data_class, use_l2p=False):
        self.__sh_delay = 0.3
        self.__stockCode = stock_code
        # 获取数据接口的字典
        self.__data = data_class
        self.__use_l2p = use_l2p

    def send_order_simulate(self, order_status, senddelay):
        """
        统计刚下单之后成交状态的变化情况（即下单之后吃盘口的情况）
        order_status：单子的状态
        sendDelay：下单的延迟
        :return:结束的成交状态
        """
        # 如果设置下单量为0
        b_s_flag = order_status.BSFlag
        if order_status.setVolume == 0:
            return order_status
        if order_status.volume != 0 or order_status.queue != 0:
            print('ordervolume/queue_set_error')
        # 时间转换为时间戳
        datetime = order_status.lastUpdateTime
        time_stamp = time.mktime(datetime.timetuple()) + datetime.microsecond / 1000000
        # 找到对应的盘口
        # noinspection PyBroadException
        try:
            if not self.__use_l2p and order_status.code[0] == "3":
                position = self.__data[self.__stockCode].get_tick_data_by_time(time_stamp + 3)['Position']
            else:
                position = self.__data[self.__stockCode].get_tick_data_by_time(time_stamp)['Position']
        except:
            order_status.accMount = order_status.setVolume * order_status.setPrice
            order_status.volume = order_status.setVolume
            return order_status
        # 因为你下单的时候有延迟，盘口已经不是当时的盘口了。所以模拟你单子进去时候的盘口Position
        # noinspection PyBroadException
        try:
            if not self.__use_l2p and order_status.code[0] == "3":
                old_time_stamp = self.__data[self.__stockCode].get_tick_data_by_time(time_stamp)['Timestamp']
                new_stamp = self.__data[self.__stockCode].get_tick_data_by_time(time_stamp + 3)['Timestamp']
                if new_stamp != old_time_stamp:
                    pass
                else:
                    transaction_list_delay = self.__data[self.__stockCode].get_transaction_data_by_time_stamp_gap(
                        time_stamp,
                        time_stamp + 3)
                    position = self.__data[self.__stockCode].tick_and_transaction_calculate(
                        position, transaction_list_delay, 'Minus')
            else:
                if order_status.code[-2:] == 'SZ':
                    transaction_list_delay = self.__data[self.__stockCode].get_transaction_data_by_time_stamp_gap(
                        time_stamp,
                        time_stamp + senddelay)
                    position = self.__data[self.__stockCode].tick_and_transaction_calculate(
                        position, transaction_list_delay, 'Minus')
                elif order_status.code[-2:] == 'SH':
                    # noinspection PyBroadException
                    try:
                        transaction_list_delay = self.__data[self.__stockCode].get_transaction_data_by_time_stamp_gap(
                            time_stamp + self.__sh_delay,
                            time_stamp + senddelay + self.__sh_delay)
                    except:
                        transaction_list_delay = []
                    position = self.__data[self.__stockCode].tick_and_transaction_calculate(
                        position, transaction_list_delay, 'Minus')
                else:
                    print('code_error')

            # 设定需要返回的订单状态,继承原来的状态
            result_order_state = order_status
            if b_s_flag == 'B':
                # 统计盘口中能吃的单子
                if result_order_state.setPrice >= position[9][0]:
                    for level in range(0, 10)[::-1]:
                        # 如果这一档盘口吃掉还没满就全部吃掉
                        if result_order_state.setPrice >= position[level][0] and result_order_state.volume \
                                + position[level][1] < result_order_state.setVolume:
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * min(
                                position[level][1], (result_order_state.setVolume - result_order_state.volume))
                            result_order_state.volume = result_order_state.volume + min(position[level][1], (
                                    result_order_state.setVolume - result_order_state.volume))
                        # 如果这一档盘口吃不掉就吃到饱就不吃了
                        elif ((result_order_state.setPrice >= position[level][0]) and (
                                result_order_state.volume + position[level][1] >= result_order_state.setVolume)):
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * (
                                    result_order_state.setVolume - result_order_state.volume)
                            result_order_state.volume = result_order_state.setVolume
                            break
                # 下单吃不到盘口，就统计下自己是否要排队，下在有的价格就排在人家后面
                else:
                    if result_order_state.setPrice in position[:, 0]:
                        index = np.where(position[:, 0] == result_order_state.setPrice)[0][0]
                        result_order_state.queue = position[index][1]

            # 和买入同理，只不过方向相反
            elif b_s_flag == 'S':
                # 统计盘口中能吃的单子
                if result_order_state.setPrice <= position[10][0]:
                    # 按价格遍历每一档
                    for level in range(10, 20):
                        # 如果这一档盘口吃掉还没满就全部吃掉
                        if result_order_state.setPrice <= position[level][0] and result_order_state.volume + \
                                position[level][1] < result_order_state.setVolume:
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * min(
                                position[level][1], (result_order_state.setVolume - result_order_state.volume))
                            result_order_state.volume = result_order_state.volume + min(position[level][1], (
                                    result_order_state.setVolume - result_order_state.volume))
                        # 如果这一档盘口吃不掉就吃到饱就不吃了
                        elif ((result_order_state.setPrice <= position[level][0]) and (
                                result_order_state.volume + position[level][1] >= result_order_state.setVolume)):
                            #
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * (
                                    result_order_state.setVolume - result_order_state.volume)
                            result_order_state.volume = result_order_state.setVolume
                            break
                else:
                    if result_order_state.setPrice in position[:, 0]:
                        index = np.where(position[:, 0] == result_order_state.setPrice)[0][0]
                        result_order_state.queue = position[index][1]
            else:
                print('BSFlag_set_error')
            result_order_state.lastUpdateTime = dt.datetime.fromtimestamp(time_stamp + senddelay)
            result_order_state.volume = min(result_order_state.volume, result_order_state.setVolume)
            return result_order_state
        except:
            # 设定需要返回的订单状态,继承原来的状态
            result_order_state = order_status
            if b_s_flag == 'B':
                # 统计盘口中能吃的单子
                if result_order_state.setPrice >= position[9][0]:
                    for level in range(0, 10)[::-1]:
                        # 如果这一档盘口吃掉还没满就全部吃掉
                        if result_order_state.setPrice >= position[level][0] and result_order_state.volume \
                                + position[level][1] * 0.5 < result_order_state.setVolume:
                            #
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * min(
                                position[level][1] * 0.5, (result_order_state.setVolume - result_order_state.volume))
                            result_order_state.volume = result_order_state.volume + min(position[level][1] * 0.5, (
                                    result_order_state.setVolume - result_order_state.volume))
                        # 如果这一档盘口吃不掉就吃到饱就不吃了
                        elif result_order_state.setPrice >= position[level][0] and result_order_state.volume \
                                + position[level][1] * 0.5 >= result_order_state.setVolume:
                            #
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * min(
                                position[level][1] * 0.5, (result_order_state.setVolume - result_order_state.volume))
                            result_order_state.volume = result_order_state.setVolume
                            break
                # 下单吃不到盘口，就统计下自己是否要排队，下在有的价格就排在人家后面
                else:
                    if result_order_state.setPrice in position[:, 0]:
                        index = np.where(position[:, 0] == result_order_state.setPrice)[0][0]
                        result_order_state.queue = position[index][1]
            # 和买入同理，只不过方向相反
            elif b_s_flag == 'S':
                # 统计盘口中能吃的单子
                if result_order_state.setPrice <= position[10][0]:
                    # 按价格遍历每一档
                    for level in range(10, 20):
                        # 如果这一档盘口吃掉还没满就全部吃掉
                        if result_order_state.setPrice <= position[level][0] and result_order_state.volume + \
                                position[level][1] * 0.5 < result_order_state.setVolume:
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * min(
                                position[level][1] * 0.5, (result_order_state.setVolume - result_order_state.volume))
                            result_order_state.volume = result_order_state.volume + min(position[level][1] * 0.5, (
                                    result_order_state.setVolume - result_order_state.volume))
                        # 如果这一档盘口吃不掉就吃到饱就不吃了
                        elif ((result_order_state.setPrice <= position[level][0]) and (
                                result_order_state.volume + position[level][1] * 0.5 >= result_order_state.setVolume)):
                            #
                            result_order_state.accMount = result_order_state.accMount + position[level][0] * min(
                                position[level][1] * 0.5, (result_order_state.setVolume - result_order_state.volume))
                            result_order_state.volume = result_order_state.setVolume
                            break
                else:
                    if result_order_state.setPrice in position[:, 0]:
                        index = np.where(position[:, 0] == result_order_state.setPrice)[0][0]
                        result_order_state.queue = position[index][1]
            else:
                print('BSFlag_set_error')
            result_order_state.lastUpdateTime = dt.datetime.fromtimestamp(time_stamp + senddelay)
            result_order_state.volume = min(result_order_state.volume, result_order_state.setVolume)
            return result_order_state

    def hold_or_back_order_simulate(self, order_status, back_delay, hold_time, send_delay):
        """
        统计挂单或者撤单的情况下成交状态的变化
        :param send_delay:
        :param order_status: 初始的成交状态
        :param back_delay: 撤单的延迟，如果是挂单情况就写0
        :param hold_time: 挂单或者撤单的时间，如果输入数字就表示挂多少秒哦，如果输入datetime时间就表示挂到制定的时间
        :return: 结束的成交状态
        """
        # 整体来说就是把接下来的逐笔成交当做委托，计算成交的状态
        if (self.__data[self.__stockCode].return_all_transaction_data() is None) and \
                (self.__data[self.__stockCode].return_all_data() is not None):
            #
            return order_status
        # noinspection PyBroadException
        try:
            a = self.__data[self.__stockCode].return_all_transaction_data()
        except:
            order_status.accMount = order_status.setVolume * order_status.setPrice
            order_status.volume = order_status.setVolume
            return order_status
        if a is None:
            order_status.accMount = order_status.setVolume * order_status.setPrice
            order_status.volume = order_status.setVolume
            return order_status

        start_time = order_status.lastUpdateTime
        start_time_stamp = time.mktime(start_time.timetuple()) + start_time.microsecond / 1000000
        # 判断挂单的截止时间戳
        if type(hold_time) == int or type(hold_time) == float:
            if not order_status.ishold:
                hold_time = max((hold_time - send_delay), 0)
            end_time_stamp = start_time_stamp + hold_time + back_delay
        else:
            end_time_stamp = time.mktime(hold_time.timetuple()) + hold_time.microsecond / 1000000 + back_delay
        if end_time_stamp < start_time_stamp:
            print('drive/back before lastUpdate')
            return order_status

        # 计算再挂期间的逐笔成交
        if not self.__use_l2p and order_status.code[0] == "3":
            transaction_list = self.__data[self.__stockCode].get_transaction_data_by_time_stamp_gap(
                start_time_stamp + 3, end_time_stamp + 3)
        else:
            if order_status.code[-2:] == 'SZ':
                transaction_list = self.__data[self.__stockCode].get_transaction_data_by_time_stamp_gap(
                    start_time_stamp, end_time_stamp)
            elif order_status.code[-2:] == 'SH':
                transaction_list = self.__data[self.__stockCode].get_transaction_data_by_time_stamp_gap(
                    start_time_stamp + self.__sh_delay, end_time_stamp + self.__sh_delay)
            else:
                transaction_list = []

        b_s_flag = order_status.BSFlag
        # 根据逐笔成交，每一笔逐笔成交。根据价格判断是否能成交到我的单子，如果买单，则逐笔成交中所有比我下单价格低或者相等的单子，先成交queue中的量
        # 即排队在我前面的人的单子，之后则成交我的单子，卖单完全相反
        if not transaction_list:
            pass
        else:
            if b_s_flag == 'B':
                for transactionNum in range(0, len(transaction_list)):
                    if order_status.volume < order_status.setVolume:
                        if transaction_list[transactionNum][1] <= order_status.setPrice:
                            if order_status.queue >= transaction_list[transactionNum][3]:
                                order_status.queue = order_status.queue - transaction_list[transactionNum][3]
                            elif 0 < order_status.queue < transaction_list[transactionNum][3]:
                                order_status.queue = 0
                                old_volume = order_status.volume
                                order_status.volume = order_status.volume + min(
                                    (transaction_list[transactionNum][3] - order_status.queue), order_status.setVolume)
                                order_status.accMount = order_status.accMount + (
                                        order_status.volume - old_volume) * order_status.setPrice
                            else:
                                old_volume = order_status.volume
                                order_status.volume = order_status.volume + min(
                                    (transaction_list[transactionNum][3] - -order_status.queue),
                                    (order_status.setVolume - order_status.volume))
                                order_status.accMount = order_status.accMount + (
                                        order_status.volume - old_volume) * order_status.setPrice

            elif b_s_flag == 'S':
                for transactionNum in range(0, len(transaction_list)):
                    if order_status.volume < order_status.setVolume:
                        if transaction_list[transactionNum][1] >= order_status.setPrice:
                            if order_status.queue >= transaction_list[transactionNum][3]:
                                order_status.queue = order_status.queue - transaction_list[transactionNum][3]
                            elif 0 < order_status.queue < transaction_list[transactionNum][3]:
                                order_status.queue = 0
                                old_volume = order_status.volume
                                order_status.volume = order_status.volume + min(
                                    (transaction_list[transactionNum][3] - order_status.queue), order_status.setVolume)
                                order_status.accMount = order_status.accMount + (
                                        order_status.volume - old_volume) * order_status.setPrice
                            else:
                                old_volume = order_status.volume
                                order_status.volume = order_status.volume + min(
                                    (transaction_list[transactionNum][3] - order_status.queue),
                                    (order_status.setVolume - order_status.volume))
                                order_status.accMount = order_status.accMount + (
                                        order_status.volume - old_volume) * order_status.setPrice
        order_status.lastUpdateTime = dt.datetime.fromtimestamp(end_time_stamp)
        order_status.ishold = True
        return order_status
