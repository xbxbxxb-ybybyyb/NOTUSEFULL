#-*- coding:utf-8 -*-
# author: 015629
# datetime:2021/10/26 13:20

class CounterManager(object):
    """"""
    def __init__(self, symbol):
        self.symbol = symbol

        self.max_bid = None
        self.min_ask = None
        self.max_long_return_rate = None

        self.open_long_times = 0
        self.open_short_times = 0
        self.tick_count_since_init_open_long = None
        self.tick_count_since_init_open_short = None

        self.is_repeat = False
        self.repeat_order_time = None

    def reset(self):
        self.max_bid = None
        self.min_ask = None
        self.max_long_return_rate = None

        self.open_long_times = 0
        self.open_short_times = 0
        self.tick_count_since_init_open_long = None
        self.tick_count_since_init_open_short = None

        self.is_repeat = False
        self.repeat_order_time = None