"""
头寸管理器
"""

from ExchangeHouse.ExchangeOrder import ExchangeOrder
import copy


class PositionManager:
    def __init__(self):
        self.__init_qty = {}  # key = symbol, value = quantity
        self.__buy_avail_qty = {}  # key = symbol, value = quantity
        self.__sell_avail_qty = {}  # key = symbol, value = quantity
        self.__net_position = {}  # key = symbol, value = quantity
        self.__non_finished_order = {}  # key = symbol, value = ExchangeOrder
        self.__finished_orders = {}  # key = symbol, value = LIST of ExchangeOrders, not used so far

    def __init_position_single(self, symbol, quantity):
        """初始化单个股票持仓，在相应字段的字典中，加入symbol"""
        self.__init_qty[symbol] = quantity
        self.__buy_avail_qty[symbol] = quantity
        self.__sell_avail_qty[symbol] = quantity
        self.__net_position[symbol] = 0
        self.__non_finished_order[symbol] = None
        self.__finished_orders[symbol] = []  # the value is a list

    def __init_position_list(self, symbol_list, quantity_list):
        """初始化股票持仓"""
        if len(symbol_list) == len(quantity_list):
            for i in range(len(symbol_list)):
                self.init_position(symbol_list[i], quantity_list[i])
        else:
            raise Exception("The dimensions of the two arguments did not match!")

    def init_position(self, symbol, quantity):
        if isinstance(symbol, list):
            self.__init_position_list(symbol, quantity)
        else:
            self.__init_position_single(symbol, quantity)

    def update_position(self, exchange_order):
        if isinstance(exchange_order, ExchangeOrder):
            status = exchange_order.order_state()  # new, filled, partially_filled, cancelled, partially_cancelled
            # 订单终结
            if status == 'cancelled' or status == 'filled' or status == 'partially_cancelled':
                self.__process_finished_order(exchange_order)
            else:
                self.__process_non_finished_order(exchange_order)
        else:
            raise Exception("The argument is not an instance of ExchangeOrder!")

    def is_position_closed(self, symbol):
        if symbol not in self.__net_position:
            return True
        if int(self.__net_position.get(symbol)) != 0:
            return False
        else:
            return True

    def is_position_positive(self, symbol):
        if symbol not in self.__net_position:
            return False
        if self.get_net_position(symbol) > 0:
            return True
        else:
            return False

    def is_position_negative(self, symbol):
        if symbol not in self.__net_position:
            return False
        if self.get_net_position(symbol) < 0:
            return True
        else:
            return False

    # -----------------------------------------------------------------------------
    # helper functions
    def __process_order(self, exchange_order):
        pre_volume = 0
        pre_order = self.__non_finished_order.get(exchange_order.code)
        if pre_order is not None:
            #  make sure they are the same order
            if pre_order.orderNumber == exchange_order.orderNumber:
                pre_volume = pre_order.volume
            else:
                print('There is no such order number in the nonFinishedOrder!')
                return
        d_volume = exchange_order.volume - pre_volume
        if exchange_order.BSFlag == 'B':
            self.__net_position[exchange_order.code] += d_volume
            self.__buy_avail_qty[exchange_order.code] -= d_volume
        elif exchange_order.BSFlag == 'S':
            self.__net_position[exchange_order.code] -= d_volume
            self.__sell_avail_qty[exchange_order.code] -= d_volume

    def __process_non_finished_order(self, exchange_order):
        self.__process_order(exchange_order)
        self.__non_finished_order[exchange_order.code] = copy.deepcopy(exchange_order)

    def __process_finished_order(self, exchange_order):
        self.__process_order(exchange_order)
        self.__finished_orders.get(exchange_order.code).append(exchange_order)
        self.__non_finished_order.pop(exchange_order.code, None)

    # -----------------------------------------------------------------------------
    # getters
    def get_buy_avail_qty(self, symbol):
        """
        获取买入可用额度
        :param symbol: 股票代码
        :return: 该股票代码的买入可用额度
        """
        if symbol not in self.__buy_avail_qty:
            return 0
        return self.__buy_avail_qty.get(symbol)

    def get_sell_avail_qty(self, symbol):
        """
        获取卖出可用额度
        :param symbol: 股票代码
        :return: 该股票代码的卖出可用额度
        """
        if symbol not in self.__sell_avail_qty:
            return 0
        return self.__sell_avail_qty.get(symbol)

    def get_net_position(self, symbol):
        """
        获取净头寸
        :param symbol: 股票代码
        :return: 该股票代码的净头寸
        """
        if symbol not in self.__net_position:
            return 0
        return int(self.__net_position.get(symbol))

    def get_non_finished_order(self, symbol):
        """
        获取未终结订单，如果没有该symbol，则返回None
        :param symbol: 股票代码
        :return: 该股票代码的未终结订单
        """
        return self.__non_finished_order.get(symbol)

    def get_finished_orders(self, symbol):
        """
        获取终结订单，返回值为一个list
        :param symbol: 股票代码
        :return: 该股票代码的终结订单，以list形式存储
        """
        return self.__finished_orders.get(symbol)

    def get_initial_qty(self, symbol):
        if symbol not in self.__init_qty:
            return 0
        return self.__init_qty.get(symbol)

    def has_non_finished(self, symbol):
        if symbol not in self.__non_finished_order or self.__non_finished_order.get(symbol) is None:
            return False
        else:
            return True

    # -----------------------------------------------------------------------------
    # setter
    def set_buy_avail_qty(self, quantity):
        self.__buy_avail_qty = quantity

    def set_sell_avail_qty(self, quantity):
        self.__sell_avail_qty = quantity
