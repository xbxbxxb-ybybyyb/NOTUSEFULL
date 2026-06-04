"""ExchangeHouse ————update @ 2021.11.9"""

import copy as cp
import pandas as pd
from DataAPI.ExchangeHouse.Exchange import Exchange


class ExchangeHouse:
    """
    模拟交易所，由数台不同股票的撮合机构成
    整个程序的维护全局字典order的技巧是：所有撮合机操作之后都是返回以订单号为key，最新订单状态为values的字典，而exchange中的order也是以同样类型的字典（只是包含了各个撮合机的信息）
    利用字典中update函数的特性，就可以实现从深拷贝到更新订单状态等一系列对order中所有订单状态的维护
    """

    def __init__(self, data_class, is_holo, delay=None, update_gap=None):
        self.__DataClass = data_class
        # index是股票代码 columms是撮合机exchange 发送延迟sendDelay 撤单延迟backDelay
        self.__exchangeData = pd.DataFrame(index=[], columns=['exchange', 'sendDelay', 'backDelay'])
        # 所有订单状态的字典
        self.__orders = {}
        # 产生订单号
        self.__orderNumberProduction = 0
        if update_gap is None:
            update_gap = [0, 0]
        self.__update_gap = update_gap
        self.__is_holo = is_holo
        self.__send_delay, self.__back_delay = delay

    def send(self, order=None):
        """
        发送单子来
        :param order:发送来的订单，没有订单号
        :return: 订单号
        """
        # 分配全局唯一的订单号
        # noinspection PyBroadException
        try:
            self.__DataClass.add_data(order.code, order.orderTime, self.__update_gap)
            if order is None:
                return None
            else:
                order_number = self.get_order_number()
                order.orderNumber = order_number
                # 如果没有对应的撮合机就创建一个
                if order.code not in self.__exchangeData.index:
                    exchange = Exchange(order.code, self.__send_delay, self.__back_delay, self.__DataClass.get_dic(), self.__is_holo)
                    tempdataframe = pd.DataFrame([[
                        exchange, self.__send_delay, self.__back_delay]], index=[order.code],
                        columns=['exchange', 'sendDelay', 'backDelay'])
                    self.__exchangeData = self.__exchangeData.append(tempdataframe)
                # 对这个撮合机发出送单指令
                exchange_order_dic = self.__exchangeData['exchange'][order.code].send(order)
                # 更新所有订单状态
                self.__orders.update(exchange_order_dic)
                return int(order_number)
        except:
            print(f'{order.code} cannot_send')
            return None

    def drive(self, order_number, holdtime):
        # noinspection PyBroadException
        try:
            order_name = str(order_number)
            # 查询订单，如果没有就不继续挂单并打印结果
            if order_name not in self.__orders.keys():
                print('no_order_to_drive' + order_name)
                return None
            # 如果查询的到订单，检查是否已经撤单或者是否是已成状态，如果不是，
            # 对这个订单所属的撮合机发出继续挂单指令，更新订单状态
            if self.__orders[order_name].isback:
                print(order_name + 'already_back')
                return self.__orders[order_name]
            if self.__orders[order_name].order_state() == 'filled':
                # print(order_name + 'is_filled')
                return self.__orders[order_name]
            code = self.__orders[order_name].code
            exchange_order_dic = self.__exchangeData['exchange'][code].drive(order_number, holdtime)
            self.__orders.update(exchange_order_dic)
            return self.__orders[order_name]
        except:
            print(str(order_number) + 'cannot_drive')
            return None

    def status(self, order_number=None, look_datetime=None):
        # 查询订单状态
        # noinspection PyBroadException
        try:
            if order_number is None:
                if look_datetime is None:
                    return self.__orders
                else:
                    # 对所有订单查询也就是对所有撮合机都执行全部查询，再把每个撮合机的状态更新进来
                    for code, rows in self.__exchangeData.iterrows():
                        exchange_order_dic = rows['exchange'].status(order_number, look_datetime)
                        self.__orders.update(exchange_order_dic)
                    return self.__orders[str(order_number)]
            # 查询个别订单
            else:
                order_name = str(order_number)
                code = self.__orders[order_name].code
                exchange_order_dic = self.__exchangeData['exchange'][code].status(order_number, look_datetime)
                self.__orders.update(exchange_order_dic)
                return self.__orders[str(order_number)]
        except:
            print(str(order_number) + 'cannot_get_status')
            return None

    # def statusToday(self, datetime):
    # '''
    # 现在没有用，在多日Porgram里应用
    # :param datetime:
    # :return:
    # '''
    # statues = cp.deepcopy(self.status())
    # for number in statues.keys():
    # if statues[number].lastUpdateTime < datetime:
    # del statues[number]
    # return statues

    def get_status(self, order_number=None, look_datetime=None):
        # 由于当前订单状态
        return cp.deepcopy(self.status(order_number, look_datetime))

    def back(self, order_number=None, back_date_time=None):
        """
        撤单，返回撤单后的订单状态
        :param back_date_time: 指定时间撤单或者过多少秒撤单
        :param order_number: 订单号 None表示撤全
        :return: 撤单之后的订单状态
        """
        if order_number is None:
            # 撤全
            for order_number in self.__orders.keys():
                code = self.__orders[str(order_number)].code
                exchange_order_dic = self.__exchangeData['exchange'][code].back(order_number, back_date_time)
                self.__orders.update(exchange_order_dic)
            return cp.deepcopy(self.__orders)
        else:
            code = self.__orders[str(order_number)].code
            exchange_order_dic = self.__exchangeData['exchange'][code].back(order_number, back_date_time)
            self.__orders.update(exchange_order_dic)
            return cp.deepcopy(self.__orders[str(order_number)])

    def get_record(self):
        # 返回完成撮合的订单，也就是成交记录
        record_dic = {}
        for orderName in self.__orders.keys():
            if self.__orders[orderName].isback is True or self.__orders[orderName].order_state == 'filled':
                record_dic.update({orderName: self.__orders[orderName]})
        return record_dic

    def get_order_number(self):
        # 累加产生订单号
        self.__orderNumberProduction += 1
        return self.__orderNumberProduction
