import numpy as np


class Exchange:
    def __init__(self, market_data):
        """
        :param market_data: MarketData
        """
        # CONSTANTS
        self._TWO_TICKS_SPAN = 6
        self._GEM_QUOTE_DELAY = 3
        self._SH_TRANSACTION_DATA_DELAY = 0.3

        self._SZ_SEND_DELAY = 0.6
        self._SH_SEND_DELAY = 1
        self._BACK_DELAY = 0.4

        # NonConstants
        self._market_data = market_data
        self._order_number_accumulated = 0
        self._order_dict = {}

    def send(self, order):
        """
        下单
        :param order: Order
        :return: int
        """
        send_delay = self._get_send_delay(order.code)

        # 初始化订单号
        order.order_number = self._generate_order_number()

        # 更新market_data的_current_date
        self._market_data.update_current_date_for_tick_and_transaction_data(order.order_time)

        # 获取当前timestamp的盘口
        quote = self._get_quote(order.code, order.order_time + send_delay)

        # 更新订单队列位置
        queue = quote[quote[:, 0] == order.price, 1]
        order.queue = queue[0] if len(queue) == 1 else 0

        # 用盘口撮合
        self._match_using_quote(order, quote)

        # 检查是否处于对方盘口
        self._update_is_opposite_using_quote(order, quote)
        order.is_opposite_previous = order.is_opposite

        # 更新订单状态
        order.last_update_time = order.order_time + send_delay
        order.duration += send_delay
        order.update_order_status()

        self._order_dict[order.order_number] = order

        return order.order_number

    def drive(self, order_number, drive_time):
        """
        驱动
        :param order_number: int
        :param drive_time: float
        :return: Order
        """
        order = self._order_dict[order_number]

        if order.order_status == "filled":
            return order

        stock_code = order.code

        if order.is_first_drive is True:
            drive_time = max(drive_time - self._get_send_delay(stock_code), 0)
            order.is_first_drive = False

        start_timestamp = order.last_update_time
        end_timestamp = order.last_update_time + drive_time

        tick_timestamp_list = self._market_data.get_tick_timestamp_list(start_timestamp, end_timestamp, True)

        for tick_timestamp in tick_timestamp_list:
            # 先用逐笔撮合
            transaction_data = self._get_transaction_data(stock_code, start_timestamp, tick_timestamp)
            self._match_using_transaction_data(order, transaction_data)

            # 获取当前盘口
            quote = self._get_quote(stock_code, tick_timestamp)

            # 检查订单是否处于对方盘口
            self._update_is_opposite_using_quote(order, quote)

            # 再用盘口撮合
            if order.is_opposite_previous is False and order.is_opposite is True:
                self._match_using_quote(order, quote)

            order.is_opposite_previous = order.is_opposite

            start_timestamp = tick_timestamp

        # 若用最后一个盘口撮合完后，还有逐笔未撮合，则继续用逐笔撮合
        if start_timestamp != end_timestamp:
            transaction_data = self._get_transaction_data(stock_code, start_timestamp, end_timestamp)
            self._match_using_transaction_data(order, transaction_data)

        # 更新订单状态
        order.last_update_time = end_timestamp
        order.duration += drive_time
        order.update_order_status()

        return order

    def back(self, order_number):
        """
        撤单
        :param order_number: int
        :return: Order
        """
        back_delay = self._get_back_delay()
        order = self.drive(order_number, back_delay)

        order.is_back = True
        order.update_order_status()

        return order

    def get_order_status(self, order_number):
        """
        查询订单状态
        :param order_number: int
        :return: Order
        """
        return self._order_dict[order_number]

    def _generate_order_number(self):
        """
        :return: int
        """
        self._order_number_accumulated += 1
        return self._order_number_accumulated

    def _get_send_delay(self, stock_code):
        """
        :param stock_code: str
        :return: float
        """
        if stock_code[-2:] == "SH":
            return self._SH_SEND_DELAY
        else:
            return self._SZ_SEND_DELAY

    def _get_back_delay(self):
        """
        :return: float
        """
        return self._BACK_DELAY

    def _get_quote(self, stock_code, timestamp):
        """
        获取timestamp时刻的模拟盘口
        :param stock_code: str
        :param timestamp: float
        :return: np.ndarray
        """
        if stock_code[0] == "3":
            tick_timestamp = self._market_data.get_tick_timestamp(timestamp)
            tick_timestamp_list = self._market_data.get_tick_timestamp_list(
                tick_timestamp,
                tick_timestamp + self._TWO_TICKS_SPAN,
                False
            )

            if len(tick_timestamp_list) == 0:
                # 若(tick_timestamp, tick_timestamp + self._TWO_TICKS_SPAN)内没有tick，则取截至tick_timestamp最新的盘口作为当前盘口
                quote, _ = self._market_data.get_quote(tick_timestamp)

                transaction_data = self._get_transaction_data(
                    stock_code,
                    tick_timestamp - self._GEM_QUOTE_DELAY,
                    timestamp
                )

                return self._adjust_quote(quote, transaction_data)
            else:
                # 否则，取(tick_timestamp, tick_timestamp + self._TWO_TICKS_SPAN)内最新的盘口作为当前盘口
                quote, _ = self._market_data.get_quote(tick_timestamp_list[0])

                transaction_data = self._get_transaction_data(
                    stock_code,
                    tick_timestamp,
                    timestamp
                )

                return self._adjust_quote(quote, transaction_data)

        else:
            quote, quote_timestamp = self._market_data.get_quote(timestamp)
            if quote_timestamp == timestamp:
                return quote
            else:
                transaction_data = self._get_transaction_data(stock_code, quote_timestamp, timestamp)
                return self._adjust_quote(quote, transaction_data)

    def _get_transaction_data(self, stock_code, start_timestamp, end_timestamp):
        """
        获取[start_timestamp, end_timestamp)内的逐笔成交数据
        :param stock_code: str
        :param start_timestamp: float
        :param end_timestamp: float
        :return: np.ndarray
        """
        if stock_code[-2:] == "SH":
            return self._market_data.get_transaction_data(start_timestamp + self._SH_TRANSACTION_DATA_DELAY,
                                                          end_timestamp + self._SH_TRANSACTION_DATA_DELAY)
        else:
            return self._market_data.get_transaction_data(start_timestamp, end_timestamp)

    @staticmethod
    def _adjust_quote(quote, transaction_data):
        """
        盘口还原
        :param quote: np.ndarray
        :param transaction_data: np.ndarray
        :return: np.ndarray
        """
        quote = quote.copy()

        if len(transaction_data) == 0:
            return quote

        for i in range(20):
            quote[i, 1] -= transaction_data[transaction_data[:, 0] == quote[i, 0], 1].sum()

        quote[quote[:, 1] < 0, 1] = 0

        transaction_max_price = transaction_data[:, 0].max()
        transaction_min_price = transaction_data[:, 0].min()
        quote[np.logical_and(quote[:, 0] < transaction_max_price, quote[:, 0] > transaction_min_price), 1] = 0

        return quote

    @staticmethod
    def _update_is_opposite_using_quote(order, quote):
        """
        用盘口更新订单is_opposite属性
        :param order: Order
        :param quote: np.ndarray
        """
        if order.direction == "B":
            if order.price < quote[9, 0]:
                order.is_opposite = False
            else:
                order.is_opposite = True
        else:
            if order.price > quote[10, 0]:
                order.is_opposite = False
            else:
                order.is_opposite = True

    @staticmethod
    def _match_using_quote(order, quote):
        """
        用盘口撮合
        :param order: Order
        :param quote: np.ndarray
        """
        if order.direction == "B":
            if order.price > quote[10, 0]:
                # 若下单价大于买1，则更新队列位置至0
                order.queue = 0

            if order.price >= quote[9, 0]:
                for i in range(9, -1, -1):
                    if order.volume_executed == order.volume:
                        break

                    if order.price >= quote[i, 0]:
                        volume_to_be_executed = min(quote[i, 1], order.volume - order.volume_executed)
                        order.volume_executed += volume_to_be_executed
                        order.amount_executed += volume_to_be_executed * quote[i, 0]
        else:
            if order.price < quote[9, 0] or quote[9, 0] == 0:
                # 若下单价小于卖1，则更新队列位置至0
                order.queue = 0

            if order.price <= quote[10, 0]:
                for i in range(10, 20):
                    if order.volume_executed == order.volume:
                        break

                    if order.price <= quote[i, 0]:
                        volume_to_be_executed = min(quote[i, 1], order.volume - order.volume_executed)
                        order.volume_executed += volume_to_be_executed
                        order.amount_executed += volume_to_be_executed * quote[i, 0]

    @staticmethod
    def _match_using_transaction_data(order, transaction_data):
        """
        用逐笔数据撮合
        :param order: Order
        :param transaction_data: np.ndarray
        """
        # 统计transaction data中价格满足成交条件的量
        if order.direction == "B":
            volume_summation = transaction_data[transaction_data[:, 0] <= order.price, 1].sum()
        else:
            volume_summation = transaction_data[transaction_data[:, 0] >= order.price, 1].sum()

        # 更新队列信息，并根据队列位置成交
        queue_updated = order.queue - volume_summation
        if queue_updated >= 0:
            order.queue = queue_updated
        else:
            volume_to_be_executed = min(volume_summation - order.queue, order.volume - order.volume_executed)
            order.volume_executed += volume_to_be_executed
            order.amount_executed += volume_to_be_executed * order.price
            order.queue = 0
