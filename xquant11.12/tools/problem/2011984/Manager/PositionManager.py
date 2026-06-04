"""头寸管理器"""

from DataAPI.ExchangeHouse.ExchangeOrder import ExchangeOrder
import copy


class PositionManager:
    def __init__(self):
        self.__init_qty = None
        self.__buy_avail_qty = None
        self.__sell_avail_qty = None
        self.__net_position = 0
        self.__non_finished_order = None  # ExchangeOrder
        self.__finished_orders = None  # LIST of ExchangeOrders

    def init_position(self, quantity):
        self.__init_qty = quantity
        self.__buy_avail_qty = quantity
        self.__sell_avail_qty = quantity
        self.__net_position = 0
        self.__non_finished_order = None
        self.__finished_orders = []  # the value is a list

    def update_position(self, exchange_order):
        if isinstance(exchange_order, ExchangeOrder):
            d_volume = exchange_order.volume
            if self.__non_finished_order is not None:  # make sure they are the same order
                if self.__non_finished_order.orderNumber == exchange_order.orderNumber:
                    d_volume -= self.__non_finished_order.volume
                else:
                    print('There is no such order number in the nonFinishedOrder!')
                    return
            if exchange_order.BSFlag == 'B':
                self.__net_position += d_volume
                self.__buy_avail_qty -= d_volume
            elif exchange_order.BSFlag == 'S':
                self.__net_position -= d_volume
                self.__sell_avail_qty -= d_volume

            if exchange_order.order_state() in ['filled', 'cancelled', 'partially_cancelled']:
                self.__finished_orders.append(exchange_order)
                self.__non_finished_order = None
            else:  # ['new', 'partially_filled']  --> unfinished
                self.__non_finished_order = copy.deepcopy(exchange_order)
        else:
            raise Exception("The argument is not an instance of ExchangeOrder!")

    # -----------------------------------------------------------------------------
    def get_avail_qty(self):
        buy_avail_qty = self.__buy_avail_qty if self.__buy_avail_qty is not None else 0
        sell_avail_qty = self.__sell_avail_qty if self.__sell_avail_qty is not None else 0
        return min(buy_avail_qty, sell_avail_qty)

    def get_avail_qty_buy(self):
        return self.__buy_avail_qty if self.__buy_avail_qty is not None else 0

    def get_avail_qty_sell(self):
        return self.__sell_avail_qty if self.__sell_avail_qty is not None else 0

    def is_position_closed(self):
        return int(self.__net_position) == 0

    def is_position_positive(self):
        return self.__net_position > 0

    def is_position_negative(self):
        return self.__net_position < 0

    def get_net_position(self):
        """获取净头寸"""
        return int(self.__net_position)

    def get_non_finished_order(self):
        """获取未终结订单，如果没有该symbol，则返回None"""
        return self.__non_finished_order

    def get_finished_orders(self):
        """获取终结订单，返回值为一个list"""
        return self.__finished_orders

    def get_initial_qty(self):
        return self.__init_qty

    def has_non_finished(self):
        return self.__non_finished_order is not None
