# -*- coding: utf-8 -*-
# @Time    : 2018/4/14 10:11
# @Author  : 011673
# @File    : Exchange.py

from ExchangeHouse.ExchangeOrder import ExchangeOrder
from ExchangeHouse.Match import Match


class Exchange:
    """
    撮合机
    """

    def __init__(self, code, send_delay, back_delay, data_class, use_l2p=False):
        # 撮合类
        self.__match = Match(code, data_class, use_l2p)
        # 发送延迟
        self.__sendDelay = send_delay
        # 撤单延迟
        self.__backDelay = back_delay
        # 存储在挂订单的地方
        self.__orders = {}
        # 股票名称
        self.__code = code
        # 存储所有完成或者撤掉的订单的地方
        self.__record = {}

    def send(self, order):
        """
        发送订单进入撮合机
        :param order: 订单,输入为订单类
        :return:所有订单状态
        """
        # 获取订单号
        name = str(order.orderNumber)
        if name in self.__orders.keys():
            print('multi_order_number')
        # 根据下单信息建立新的订单信息类实例
        new_order_state = ExchangeOrder(order)
        # 发单撮合成交
        order_state = self.__match.send_order_simulate(new_order_state, self.__sendDelay)
        # 更新订单记录状态
        self.__orders.update({name: order_state})
        return self.__orders

    def drive(self, order_number, holdtime):
        """
        保持所有订单继续在撮合机
        :param order_number: 需要继续撮合的订单
        :param holdtime: 继续撮合的时间或者直到指定时间都继续撮合
        :return:订单列表
        """
        name = str(order_number)
        self.__match.hold_or_back_order_simulate(self.__orders[name], 0, holdtime, self.__sendDelay)
        return self.__orders

    def status(self, order_number, look_date_time=None):
        """
        查询现在订单状态
        :param order_number:
        :param look_date_time:如果设置为None，表示查询所有再挂委托
        :return:订单状态
        """
        # 查询现在的状态
        if look_date_time is None:
            # 如果不指定订单号就返回全部订单状态
            if order_number is None:
                return self.__orders
            else:
                return {str(order_number): self.__orders[str(order_number)]}
        # 查询制定时间的状态
        else:
            if order_number is None:
                # 查询全部订单的话，就先让所有订单更新到指定时刻，再查询
                for order_num in self.__orders.keys():
                    self.__orders[order_num] = self.__match.hold_or_back_order_simulate(self.__orders[order_num], 0,
                                                                                        look_date_time,
                                                                                        self.__sendDelay)
                return self.__orders
            else:
                # 查询特定的订单就只更新特定订单到指定时刻
                order_num = str(order_number)
                self.__orders[order_num] = self.__match.hold_or_back_order_simulate(self.__orders[order_num], 0,
                                                                                    look_date_time,
                                                                                    self.__sendDelay)
                return {order_num: self.__orders[order_num]}

    def back(self, order_number=None, back_date_time=None):
        """
        撤单
        :param order_number:
        :param back_date_time:如果为None为当前撤单，设定时间为指定时间撤单
        orderName是撤的哪一笔单子的ID
        :return:所有订单的状态
        """
        if order_number is None:
            return self.__orders
        else:
            # 获取订单号
            name = str(order_number)
            # noinspection PyBroadException
            try:
                if name not in self.__orders.keys():
                    print(name + '_order_not_in_list')
                else:
                    if self.__orders[name].isback:
                        pass
                    else:
                        # 如果不指定撤单事件则立刻执行撤单撮合，返回订单状态
                        if back_date_time is None:
                            # 执行撮合操作
                            self.__orders[name] = self.__match.hold_or_back_order_simulate(self.__orders[name],
                                                                                           self.__backDelay, 0,
                                                                                           self.__sendDelay)
                            # 更新订单状态中是否撤单为是
                            self.__orders[name].isback = True
                        else:
                            self.__orders[name] = self.__match.hold_or_back_order_simulate(self.__orders[name],
                                                                                           self.__backDelay,
                                                                                           back_date_time,
                                                                                           self.__sendDelay)
                            self.__orders[name].isback = True
            except:
                print('no_drive')
                self.__orders[name].isback = True
            return self.__orders
