import math
import datetime as dt
import numpy as np
from copy import deepcopy
from ModelSystem.SignalExecutorBase import SignalExecutorBase
from ModelSystem.Util.OrderSide import OrderSide
from ModelSystem.Util.SignalType import SignalType


class SignalExecutorAlphaVWAPEZ(SignalExecutorBase):
    def __init__(self, position_manager):
        SignalExecutorBase.__init__(self, position_manager)

        # CONSTANTS
        # TICK有效时间
        self._TICK_START_TIME_MORNING = dt.time(9, 30, 00)  # 早上开盘从该时刻起，才认为是正常的行情，开始接收早盘行情信号
        self._TICK_END_TIME_MORNING = dt.time(11, 29, 59)
        self._TICK_START_TIME_AFTERNOON = dt.time(13, 00, 00)  # 下午开盘从该时刻起，才认为是正常的行情，开始接收午盘行情信号
        self._TICK_END_TIME_AFTERNOON = dt.time(14, 56, 59)

        # 策略开始结束时间
        self._STRATEGY_START_TIME = dt.time(9, 30, 00)
        self._STRATEGY_END_TIME = dt.time(14, 56, 59)

        # 信号有效时间
        self._SIGNAL_START_TIME_MORNING = dt.time(9, 31, 15)
        self._SIGNAL_END_TIME_MORNING = dt.time(11, 29, 59)
        self._SIGNAL_START_TIME_AFTERNOON = dt.time(13, 1, 15)
        self._SIGNAL_END_TIME_AFTERNOON = dt.time(14, 56, 59)

        # 闭市区间开始时间
        self._MARKET_CLOSE_START_TIME_MORNING = dt.time(11, 29, 00)
        self._MARKET_CLOSE_END_TIME_MORNING = dt.time(11, 30, 00)
        self._MARKET_CLOSE_START_TIME_AFTERNOON = dt.time(14, 55, 00)
        self._MARKET_CLOSE_END_TIME_AFTERNOON = dt.time(14, 57, 00)

        # 区间结束时间长度
        self._INTERVAL_END_SECONDS = 30
        self._CLOSE_AT_EASE_SECONDS = 15

        # Price Multi
        self._PRICE_MULTI = 0.0002
        self._PRICE_LIMIT_MULTI = 0.001
        self._MARKET_CLOSE_PRICE_MULTI = 0.012

        # Invalid Signal Period Target Quantity Percentage
        self._INVALID_SIGNAL_PERIOD_QUANTITY_PCT = 0.1

        # NonConstants
        self._symbol = None

        self._long_aggressive_ratio = None
        self._short_aggressive_ratio = None
        self._long_passive_ratio = None
        self._short_passive_ratio = None

        self._time_table = None  # 建仓区间
        self._time_table_all = None
        self._target_qty_interval = None  # 当天建仓的区间数量
        self._target_qty_interval_all = None  # 区间建仓百分比 {date: target_qty_pct}
        self._side = None  # 建仓方向
        self._target_qty = 0
        self._curr_interval_index = 0
        self._cum_qty = 0

        self._volume_today = []  # 当天行情的volume
        self._previous_slice_data = None  # 上一个tick的tagInfo

        self._bid_predictions = []  # 存放当天的所有预测值 index 0
        self._ask_predictions = []  # 存放当天的所有预测值 index 1

        self._is_holo = False
        self._next_slice_data = None  # reserved for holo use

    def set_json_param_before_start(self, param):
        self._time_table_all = deepcopy(param["TimeTable"])
        self._time_table_all = {k: self._str_to_time(v) for k, v in self._time_table_all.items()}
        self._target_qty_interval_all = deepcopy(param['TargetQtyInterval'])

        if 'Holo' in param:
            value = (param['Holo'].lower() == 'true')
            self._is_holo = value

    def generateTriggerRatio(self, symbol, trigger_ratio_dict):
        self._symbol = symbol
        if trigger_ratio_dict:
            self._long_aggressive_ratio = trigger_ratio_dict['longAggressiveRatio']
            self._short_aggressive_ratio = trigger_ratio_dict['shortAggressiveRatio']
            self._long_passive_ratio = trigger_ratio_dict['longPassiveRatio']
            self._short_passive_ratio = trigger_ratio_dict['shortPassiveRatio']
        self._target_qty = self._positionMgr.getTargetQty(self._symbol)
        self._side = OrderSide.Buy.name if self._target_qty >= 0 else OrderSide.Sell.name

    def onOrderUpdated(self, order):
        self._cum_qty += order.volume_executed

    def onNewDay(self, date):
        self._volume_today = []
        self._bid_predictions = []
        self._ask_predictions = []
        self._previous_slice_data = None
        self._time_table = None
        self._target_qty_interval = None
        self._cum_qty = 0

    def onTimeEnd(self, predictions, slice_data, curr_dt):
        pass

    def onNewTick(self, predictions, slice_data, unfinished_order, **kwargs):
        self._generate_target_qty_interval(slice_data)
        self._update_index(slice_data)
        self._process_tick_data(slice_data)
        self._store_predictions(predictions)

        slice_data = self._get_next_slice_data(slice_data)

        if (not self._is_in_valid_tick_period(slice_data)
                or not self._is_in_strategy_period(slice_data)
                or self._is_tick_abnormal(slice_data)):
            pass

        elif self._is_reaching_price_limit(slice_data):
            self._process_tick_when_reaching_price_limit(slice_data, unfinished_order)

        elif self._is_price_limit_open(slice_data):
            self._process_tick_when_price_limit_open(slice_data)

        elif self._is_market_close(slice_data):
            self._process_tick_when_market_close(slice_data)

        elif not self._is_in_valid_signal_period(slice_data):
            self._process_tick_in_invalid_signal_period(slice_data, unfinished_order)

        elif predictions[0] is not None and predictions[1] is not None:
            self._process_tick_using_signals(predictions, slice_data, unfinished_order)

        self._previous_slice_data = slice_data

    def _is_in_valid_tick_period(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        return ((self._TICK_START_TIME_MORNING <= tick_time <= self._TICK_END_TIME_MORNING)
                or (self._TICK_START_TIME_AFTERNOON <= tick_time <= self._TICK_END_TIME_AFTERNOON))

    def _is_in_strategy_period(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        return self._STRATEGY_START_TIME <= tick_time <= self._STRATEGY_END_TIME

    @staticmethod
    def _is_tick_abnormal(slice_data):
        return slice_data.bidPrice[0] == 0 and slice_data.askPrice[0] == 0

    # 收盘处理
    def _is_market_close(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        return tick_time >= self._MARKET_CLOSE_START_TIME_AFTERNOON

    def _process_tick_when_market_close(self, slice_data):
        self._cancel_non_finished_order()
        self._open_when_market_close(slice_data)

    def _open_when_market_close(self, slice_data):
        if self._side == OrderSide.Buy.name:
            if slice_data.askPrice[0] == 0:
                price = min((slice_data.bidPrice[0] + 0.01) * (1 + self._MARKET_CLOSE_PRICE_MULTI), slice_data.maxPrice)
            else:
                price = min(slice_data.askPrice[0] * (1 + self._MARKET_CLOSE_PRICE_MULTI), slice_data.maxPrice)
        else:
            if slice_data.bidPrice[0] == 0:
                price = max((slice_data.askPrice[0] - 0.01) * (1 - self._MARKET_CLOSE_PRICE_MULTI), slice_data.minPrice)
            else:
                price = max(slice_data.bidPrice[0] * (1 - self._MARKET_CLOSE_PRICE_MULTI), slice_data.minPrice)

        quantity = self._target_qty_to_order()
        volume_limit = quantity / 6
        ema = self._ema_volume()
        quantity = min(math.ceil(max(ema * 4, volume_limit) / 100) * 100, quantity)

        if quantity >= 100:
            price = round(price, 2)
            self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.market_close)

    # 涨跌停板处理
    def _is_reaching_price_limit(self, slice_data):
        return (slice_data.bidPrice[0] >= (1 - self._PRICE_LIMIT_MULTI) * slice_data.maxPrice
                or (slice_data.askPrice[0] != 0
                    and slice_data.askPrice[0] <= (1 + self._PRICE_LIMIT_MULTI) * slice_data.minPrice))

    def _process_tick_when_reaching_price_limit(self, slice_data, unfinished_order):
        if unfinished_order is None:
            self._open_when_reaching_price_limit(slice_data)
        elif unfinished_order.signal_type.name == "price_limit":
            pass
        else:
            self._cancel_non_finished_order()
            self._open_when_reaching_price_limit(slice_data)

    def _open_when_reaching_price_limit(self, slice_data):
        if slice_data.bidPrice[0] >= (1 - self._PRICE_LIMIT_MULTI) * slice_data.maxPrice:
            price = slice_data.maxPrice

            if self._side == OrderSide.Buy.name:
                quantity = self._target_qty_to_order()
            else:
                quantity = int((abs(self._target_qty) - self._cum_qty) / 100) * 100

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.price_limit)
        else:
            price = slice_data.minPrice

            if self._side == OrderSide.Sell.name:
                quantity = self._target_qty_to_order()
            else:
                quantity = int((abs(self._target_qty) - self._cum_qty) / 100) * 100

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.price_limit)

    # 开板第一个TICK处理
    def _is_price_limit_open(self, slice_data):
        if not self._previous_slice_data:
            return False

        return (self._is_reaching_price_limit(self._previous_slice_data)
                and not self._is_reaching_price_limit(slice_data))

    def _process_tick_when_price_limit_open(self, slice_data):
        condition1 = (self._side == OrderSide.Buy.name
                      and self._previous_slice_data.bidPrice[0]
                      >= (1 - self._PRICE_LIMIT_MULTI) * self._previous_slice_data.maxPrice)
        condition2 = (self._side == OrderSide.Sell.name
                      and (self._previous_slice_data.askPrice[0] != 0
                           and self._previous_slice_data.askPrice[0]
                           <= (1 + self._PRICE_LIMIT_MULTI) * self._previous_slice_data.minPrice))
        if condition1 or condition2:
            self._cancel_non_finished_order()
            self._open_when_price_limit_open(slice_data)

    def _open_when_price_limit_open(self, slice_data):
        open_long_coef = 1 + self._PRICE_MULTI
        open_short_coef = 1 - self._PRICE_MULTI

        if self._side == OrderSide.Buy.name:
            if slice_data.askPrice[0] == 0:
                price = min(slice_data.bidPrice[0] + 0.01, slice_data.maxPrice)
            else:
                price = min(slice_data.askPrice[0] * open_long_coef, slice_data.maxPrice)

            quantity = min(math.ceil(self._ema_volume() / 100) * 100, self._target_qty_to_order())

            if quantity >= 100:
                price = round(price, 2)
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.price_limit_open)
        else:
            if slice_data.bidPrice[0] == 0:
                price = max(slice_data.askPrice[0] - 0.01, slice_data.minPrice)
            else:
                price = max(slice_data.bidPrice[0] * open_short_coef, slice_data.minPrice)

            quantity = min(math.ceil(self._ema_volume() / 100) * 100, self._target_qty_to_order())

            if quantity >= 100:
                price = round(price, 2)
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.price_limit_open)

    # 非有效信号时间处理
    def _is_in_valid_signal_period(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        return ((self._SIGNAL_START_TIME_MORNING <= tick_time <= self._SIGNAL_END_TIME_MORNING)
                or (self._SIGNAL_START_TIME_AFTERNOON <= tick_time <= self._SIGNAL_END_TIME_AFTERNOON))

    def _process_tick_in_invalid_signal_period(self, slice_data, unfinished_order):
        if self._side == OrderSide.Buy.name:
            if (unfinished_order is not None
                    and unfinished_order.signal_type.name == "invalid_signal"
                    and unfinished_order.price == slice_data.bidPrice[0]):
                pass
            else:
                self._open_in_invalid_signal_period(slice_data, unfinished_order)
        else:
            if (unfinished_order is not None
                    and unfinished_order.signal_type.name == "invalid_signal"
                    and unfinished_order.price == slice_data.askPrice[0]):
                pass
            else:
                self._open_in_invalid_signal_period(slice_data, unfinished_order)

    def _open_in_invalid_signal_period(self, slice_data, unfinished_order):
        if self._side == OrderSide.Buy.name:
            if slice_data.bidPrice[0] == 0:
                price = max(slice_data.askPrice[0] - 0.01, slice_data.minPrice)
            else:
                price = slice_data.bidPrice[0]
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.invalid_signal)
        else:
            if slice_data.askPrice[0] == 0:
                price = min(slice_data.bidPrice[0] + 0.01, slice_data.maxPrice)
            else:
                price = slice_data.askPrice[0]
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.invalid_signal)

    # 正常信号处理
    def _process_tick_using_signals(self, predictions, slice_data, unfinished_order):
        if self._side == OrderSide.Buy.name:
            if predictions[0] > self._long_aggressive_ratio:
                self._aggressive_open(slice_data, unfinished_order)
                return
            elif predictions[0] > self._long_passive_ratio:
                self._passive_open(slice_data, unfinished_order)
                return
        else:
            if predictions[1] < self._short_aggressive_ratio:
                self._aggressive_open(slice_data, unfinished_order)
                return
            elif predictions[1] < self._short_passive_ratio:
                self._passive_open(slice_data, unfinished_order)
                return

        if self._is_interval_end(slice_data):
            self._process_interval_end(slice_data, unfinished_order)
            return

    def _aggressive_open(self, slice_data, unfinished_order):
        open_long_coef = 1 + self._PRICE_MULTI
        open_short_coef = 1 - self._PRICE_MULTI

        if self._side == OrderSide.Buy.name:
            if slice_data.askPrice[0] == 0:
                price = min(slice_data.bidPrice[0] + 0.01, slice_data.maxPrice)
            else:
                price = min(slice_data.askPrice[0] * open_long_coef, slice_data.maxPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.aggressive)
        else:
            if slice_data.bidPrice[0] == 0:
                price = max(slice_data.askPrice[0] - 0.01, slice_data.minPrice)
            else:
                price = max(slice_data.bidPrice[0] * open_short_coef, slice_data.minPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.aggressive)

    def _passive_open(self, slice_data, unfinished_order):
        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        if self._side == OrderSide.Buy.name:
            if ask0 == 0:
                price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01), bid0 + 0.02, slice_data.maxPrice)
            elif bid0 == 0:
                price = ask0
            else:
                price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01),
                            bid0 + 0.02,
                            ask0,
                            slice_data.maxPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.passive)
        else:
            price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0, slice_data.minPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.passive)

    def _cal_dynamic_open_quantity(self, slice_data):
        quantity = 0
        ema = self._ema_volume()

        if self._side == OrderSide.Buy.name:
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())
        elif self._side == OrderSide.Sell.name:
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())

        return quantity

    # 区间结束处理
    def _is_interval_end(self, slice_data):
        slice_data_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        if self._MARKET_CLOSE_START_TIME_MORNING <= slice_data_time <= self._MARKET_CLOSE_END_TIME_MORNING:
            return True

        bm = self._add_seconds(self._time_table[self._curr_interval_index], -self._INTERVAL_END_SECONDS)
        return slice_data_time >= bm

    def _process_interval_end(self, slice_data, unfinished_order):
        time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        int_time = self._time_table[self._curr_interval_index]
        int_time = int_time if int_time != dt.time(13, 0, 0) else dt.time(11, 30, 0)
        is_close_at_ease = time < self._add_seconds(int_time, -self._CLOSE_AT_EASE_SECONDS)
        self._open_when_interval_end(slice_data, is_close_at_ease, unfinished_order)

    def _open_when_interval_end(self, slice_data, is_close_at_ease, unfinished_order):
        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        if self._side == OrderSide.Buy.name:
            if is_close_at_ease:
                if ask0 == 0:
                    price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01), bid0 + 0.02, slice_data.maxPrice)
                elif bid0 == 0:
                    price = ask0
                else:
                    price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01),
                                bid0 + 0.02,
                                ask0,
                                slice_data.maxPrice)
            else:
                if ask0 == 0:
                    price = min(bid0 + 0.01, slice_data.maxPrice)
                else:
                    price = ask0
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._target_qty_to_order()
            volume_limit = quantity / 6
            ema = self._ema_volume()
            quantity = min(math.ceil(max(ema * 4, volume_limit) / 100) * 100, quantity)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.interval_end)
        else:
            if is_close_at_ease:
                price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0, slice_data.minPrice)
            else:
                if bid0 == 0:
                    price = max(ask0 - 0.01, slice_data.minPrice)
                else:
                    price = bid0
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._target_qty_to_order()
            volume_limit = quantity / 6
            ema = self._ema_volume()
            quantity = min(math.ceil(max(ema * 4, volume_limit) / 100) * 100, quantity)

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.interval_end)

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #                                               Helper Functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def _generate_target_qty_interval(self, slice_data):
        if self._time_table is None and self._target_qty_interval is None:
            date_str = dt.datetime.fromtimestamp(slice_data.timeStamp).strftime('%Y%m%d')
            self._time_table = self._time_table_all[date_str]
            self._target_qty_interval = self._target_qty_interval_all[date_str]
            self._curr_interval_index = 0

    def _update_index(self, slice_data):
        time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        if time > self._time_table[self._curr_interval_index]:
            self._curr_interval_index += 1 if self._curr_interval_index < len(self._time_table) - 1 else 0

    def _process_tick_data(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        tick_datetime = dt.datetime.fromtimestamp(tick_timestamp)

        if (self._previous_slice_data is not None
                and dt.datetime.fromtimestamp(self._previous_slice_data.timeStamp).time() <= self._TICK_END_TIME_MORNING
                and tick_datetime.time() >= self._TICK_START_TIME_AFTERNOON):
            self._previous_slice_data = None
            self._bid_predictions = []
            self._ask_predictions = []
            self._volume_today = []

        if (self._TICK_START_TIME_MORNING <= tick_datetime.time() <= self._TICK_END_TIME_MORNING
                or self._TICK_START_TIME_AFTERNOON <= tick_datetime.time() <= self._TICK_END_TIME_AFTERNOON):
            self._volume_today.append(slice_data.volume)

    def _store_predictions(self, predictions):
        self._ask_predictions.append(predictions[1])
        self._bid_predictions.append(predictions[0])

    def _get_next_slice_data(self, slice_data):
        if self._is_holo:
            next_slice_data = self.next_slice_data_speed(slice_data)
            self._next_slice_data = next_slice_data
            return next_slice_data
        else:
            return slice_data

    def _target_qty_to_order(self):
        value = self._target_qty_interval[self._curr_interval_index] - self._cum_qty
        return int(value / 100) * 100

    def _cancel_non_finished_order(self):
        if self._positionMgr.hasNonFinished(self._symbol):
            order_number = self._positionMgr.getNonFinishedOrderNumber(self._symbol)
            self.cancelOrder(order_number)

    # ema成交量
    def _ema_volume(self):
        alpha = 0.9
        window = 40

        if self._volume_today is None or len(self._volume_today) == 0:
            return 100.0

        length = len(self._volume_today)
        start = max(0, length - window)
        ema = self._volume_today[start]
        for i in range(start + 1, length):
            ema = self._cal_ema(alpha, ema, self._volume_today[i])
        value = math.ceil(ema / 100) * 100.0

        return max(100.0, value)

    def _exponential_predict(self, predictions):
        if predictions.shape[0] == 0:
            return None

        if predictions.shape[0] == 1:
            return predictions[-1]

        alpha = 0.6
        s_single = self._exponential_smoothing(alpha, predictions)
        s_double = self._exponential_smoothing(alpha, s_single)

        a_double = 2 * s_single - s_double
        b_double = (alpha / (1 - alpha)) * (s_single - s_double)

        return a_double[-1] + b_double[-1]

    @staticmethod
    def _str_to_time(str_list):
        str_list = deepcopy(str_list)
        return list(map(lambda x: dt.time(int(x[:2]), int(x[3:5]), int(x[6:8])), str_list))

    @staticmethod
    def _add_seconds(time, sec):
        time = dt.datetime.combine(dt.datetime.today(), time)
        time += dt.timedelta(seconds=sec)
        return time.time()

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #                                      Helper Functions' Helper Functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    @staticmethod
    def _cal_vol_ratio(delta, prediction, base, times):
        return abs(prediction) * abs(delta) / (abs(base) + 0.1) / (times + 1)

    @staticmethod
    def _cal_ema(alpha, ema, value):
        return alpha * ema + (1 - alpha) * value

    @staticmethod
    def _exponential_smoothing(alpha, s):
        s2 = np.zeros(s.shape)
        s2[0] = s[0]
        for i in range(1, len(s2)):
            s2[i] = alpha * s[i] + (1 - alpha) * s2[i - 1]
        return s2
