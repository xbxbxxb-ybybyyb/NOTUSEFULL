# -*- coding: utf-8 -*-
# @Time    : 2018/4/14 10:11
# @Author  : 011673
# @File    : Order.py
import datetime as dt


class Order:
    """
    下单类
    """

    def __init__(self, code=None, order_number=None, order_price=0, ordervolume=0, direction='B',
                 order_time=dt.datetime(1970, 1, 1, 0, 0, 0)):
        """
        下单类
        :param order_price:价格
        :param ordervolume: 数量
        :param direction: 方向
        :param order_time: 下单时间（datetime格式）
        """
        # 下单号，作为下单的唯一标示
        self.orderNumber = order_number
        # 下单时间
        self.orderTime = order_time
        # 下单价格
        self.price = order_price
        # 下单量
        self.volume = ordervolume
        # 下单方向
        self.BSFlag = direction
        # 下单的code
        self.code = code
