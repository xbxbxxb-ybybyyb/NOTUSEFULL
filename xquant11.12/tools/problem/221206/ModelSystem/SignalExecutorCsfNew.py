import math
import datetime as dt
import numpy as np
from copy import deepcopy
from ModelSystem.SignalExecutorBase import SignalExecutorBase
from ModelSystem.Util.OrderSide import OrderSide
from ModelSystem.Util.SignalType import SignalType


class SignalExecutorCsfNew(SignalExecutorBase):
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

        # 闭市区间开始时间
        self._MARKET_CLOSE_START_TIME_MORNING = dt.time(11, 29, 00)
        self._MARKET_CLOSE_END_TIME_MORNING = dt.time(11, 30, 00)
        self._MARKET_CLOSE_START_TIME_AFTERNOON = dt.time(14, 55, 00)

        # 区间结束时间长度
        self._INTERVAL_END_SECONDS = 15
        self._CLOSE_AT_EASE_SECONDS = 15

        # Price Multi
        self._AGGRESSIVE_PRICE_MULTI = 0.0002
        self._PRICE_MULTI = 0.0004
        self._PRICE_LIMIT_MULTI = 0.001

        # NonConstants
        self._symbol = None

        self._long_aggressive_ratio = None
        self._short_aggressive_ratio = None
        self._long_passive_ratio = None
        self._short_passive_ratio = None

        self._time_table = None  # 建仓区间
        self._time_table_all = None
        self._target_qty_interval = None  # 当天建仓的区间数量
        self._target_qty_interval_org = None  # 当天建仓的区间数量
        self._target_qty_interval_all = None  # 区间建仓百分比 {date: target_qty_pct}
        self._side = None  # 建仓方向
        self._cur_direction = None  # 建仓方向
        self._target_qty = 0
        self._curr_interval_index = 0
        self._cum_qty = 0
        self._cum_amt = 0

        self._volume_today = []  # 当天行情的volume
        self._previous_slice_data = None  # 上一个tick的tagInfo

        self._is_holo = False
        self._next_slice_data = None  # reserved for holo use

        self._total_market_close_volume = 0.0
        self._total_open_market_close_volume = 0.0
        self._market_close_limit_ratio = 0.3
        self._limit_ratio = 0.03
        self._ask0 = []  # 当天行情的ask0
        self._bid0 = []  # 当天行情的bid0
        self._direction = 0
        self._vwap_lag = 100
        self._low_swing_long_lag = 200
        self._low_swing_short_lag = 20
        self._price_lag = 5
        self._vwap_bias_ema = []
        self._vwap_bias_llt = []
        self._last_price = []
        self._target_qty_interval_percent = None
        self._today_volume = []
        self._trigger_sta = {0: {"aggressive_count": 0, "passive_count": 0}}

    def set_json_param_before_start(self, param):
        self._time_table_all = deepcopy(param["Timetable"])
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
        self._cum_amt += order.amount_executed
        order_time = dt.datetime.fromtimestamp(order.order_time).time()

        if (self._MARKET_CLOSE_START_TIME_MORNING <= order_time <= self._MARKET_CLOSE_END_TIME_MORNING) or (
                order_time >= self._MARKET_CLOSE_START_TIME_AFTERNOON):
            self._total_open_market_close_volume += order.volume_executed

    def onNewDay(self, date):
        self._volume_today = []
        self._previous_slice_data = None
        self._time_table = None
        self._target_qty_interval = None
        self._target_qty_interval_org = None
        self._cur_direction = None
        self._cum_qty = 0
        self._cum_amt = 0
        self._total_open_market_close_volume = 0
        self._total_market_close_volume = 0
        self._ask0 = []
        self._bid0 = []
        self._vwap_bias_ema = []
        self._vwap_bias_llt = []
        self._last_price = []
        self._direction = 0
        self._today_volume = []
        self._trigger_sta = {0: {"aggressive_count": 0, "passive_count": 0}}

    def onTimeEnd(self, predictions, slice_data, curr_dt):
        pass

    def _update_vwap_bias(self, slice_data):
        if len(self._ask0) == 0 or len(self._bid0) == 0:
            return
        vwap = slice_data.totalAmount / slice_data.totalVolume
        if self._side == OrderSide.Buy.name:
            self._vwap_bias_ema.append(1000 * (vwap / self._ask0[-1] - 1))
        else:
            self._vwap_bias_ema.append(1000 * (self._bid0[-1] / vwap - 1))
        if len(self._vwap_bias_ema) <= 2:
            self._vwap_bias_llt.append(self._vwap_bias_ema[-1])
        else:
            self._vwap_bias_llt.append(self._llt_step(self._vwap_bias_ema, self._vwap_bias_llt, 0.07))

    def onNewTick(self, predictions, slice_data, unfinished_order, **kwargs):
        self._generate_target_qty_interval(slice_data)
        self._update_index(slice_data)
        self._process_tick_data(slice_data)

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

        elif predictions[0] is not None and predictions[1] is not None:
            self._process_tick_using_signals(predictions, slice_data, unfinished_order)

        self._previous_slice_data = slice_data

    def _is_low_swing(self, slice_data):
        if len(self._last_price) < (self._low_swing_long_lag + self._low_swing_short_lag):
            return False
        long_delta_p = max(self._last_price[-self._low_swing_long_lag:]) - min(
            self._last_price[-self._low_swing_long_lag:])
        short_delta_p = max(self._last_price[-self._low_swing_short_lag:]) - min(
            self._last_price[-self._low_swing_short_lag:])

        if long_delta_p < 0.03:
            return True
        elif long_delta_p < 0.04 and short_delta_p < 0.02:
            return True
        else:
            return False

    def _is_vwap_bias(self, slice_data):
        if len(self._volume_today) < self._vwap_lag:
            return False

        if self._vwap_bias_llt[-1] - min(self._vwap_bias_llt[-1200:]) < 10 or self._vwap_bias_llt[-1] - min(
                self._vwap_bias_llt[-60:]) < 2:
            return False

        peak_indexs = self._detect_peaks(self._vwap_bias_llt,
                                         distance=1,
                                         leftNeighborDistanceThresholdPairs=[[(1200, 10)], [(60, 2)]],
                                         edge="both",
                                         keepEqualHeight=True,
                                         valley=False)

        valley_indexs = self._detect_peaks(self._vwap_bias_llt,
                                           distance=1,
                                           leftNeighborDistanceThresholdPairs=[[(1200, 10)], [(60, 2)]],
                                           edge="both",
                                           keepEqualHeight=True,
                                           valley=True)
        if len(peak_indexs) == 0:
            return False
        elif len(self._vwap_bias_ema) - peak_indexs[-1] > 5:
            return False
        elif len(valley_indexs) == 0:
            if self._side == OrderSide.Buy.name:
                if self._ask0[-1] < round((self._ask0[peak_indexs[-1]] + self._ask0[0]) / 2) - 0.01:
                    return True
                else:
                    return False
            else:
                if self._bid0[-1] > round((self._bid0[peak_indexs[-1]] + self._bid0[0]) / 2) + 0.01:
                    return True
                else:
                    return False
        elif peak_indexs[-1] < valley_indexs[-1]:
            return False
        else:
            return True

    def _process_vwap_bias(self, slice_data, unfinished_order):
        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        if self._side == OrderSide.Buy.name:
            if ask0 == 0:
                price = min(bid0 + 0.02, slice_data.maxPrice)
            else:
                price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01),
                            bid0 + 0.02,
                            ask0)

            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_vwap_bias_open_quantity(slice_data)
            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.vwap_bias,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            if bid0 == 0:
                price = max(ask0 - 0.02, slice_data.minPrice)
            else:
                price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0)

            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_vwap_bias_open_quantity(slice_data)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.vwap_bias,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _is_in_valid_tick_period(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        return ((self._TICK_START_TIME_MORNING <= tick_time <= self._TICK_END_TIME_MORNING)
                or (self._TICK_START_TIME_AFTERNOON <= tick_time <= self._TICK_END_TIME_AFTERNOON))

    def _is_in_strategy_period(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()

        return self._STRATEGY_START_TIME <= tick_time <= self._STRATEGY_END_TIME

    # @staticmethod
    def _is_tick_abnormal(self, slice_data):
        return ((slice_data.bidPrice[0] == 0 and slice_data.askPrice[0] != slice_data.minPrice)
                or (slice_data.askPrice[0] == 0 and slice_data.bidPrice[0] != slice_data.maxPrice))

    # 收盘处理
    def _is_market_close(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        if self._MARKET_CLOSE_START_TIME_MORNING <= tick_time <= self._MARKET_CLOSE_END_TIME_MORNING:
            if (self._target_qty_interval_org[self._curr_interval_index] / slice_data.totalVolume > self._limit_ratio
                    or self._cum_qty / self._target_qty_interval_org[self._curr_interval_index] < 0.75):
                return True
        return tick_time >= self._MARKET_CLOSE_START_TIME_AFTERNOON

    def _process_tick_when_market_close(self, slice_data):
        self._cancel_non_finished_order()
        self._open_when_market_close(slice_data)

    def _open_when_market_close(self, slice_data):
        if self._side == OrderSide.Buy.name:
            if slice_data.askPrice[0] == 0:
                price = min((slice_data.bidPrice[0] + 0.01), slice_data.maxPrice)
            else:
                price = slice_data.askPrice[0]

            quote_volume = slice_data.askVolume[0]
        else:
            if slice_data.bidPrice[0] == 0:
                price = max((slice_data.askPrice[0] - 0.01), slice_data.minPrice)
            else:
                price = slice_data.bidPrice[0]

            quote_volume = slice_data.bidVolume[0]

        quantity = self._cal_market_close_open_quantity(slice_data)

        if quantity >= 100:
            price = round(price, 2)
            self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.market_close,
                            market_vwap=self._calculate_market_realized_vwap(slice_data),
                            strategy_vwap=self._calculate_strategy_realized_vwap(),
                            ema_volume=self._ema_volume(),
                            quote_volume=quote_volume)

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

                quote_volume = slice_data.askVolume[0]
            else:
                quantity = int((abs(self._target_qty) - self._cum_qty) / 100) * 100

                quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.price_limit,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            price = slice_data.minPrice

            if self._side == OrderSide.Sell.name:
                quantity = self._target_qty_to_order()

                quote_volume = slice_data.bidVolume[0]
            else:
                quantity = int((abs(self._target_qty) - self._cum_qty) / 100) * 100

                quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.price_limit,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

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
        open_long_coef = 1 + self._AGGRESSIVE_PRICE_MULTI
        open_short_coef = 1 - self._AGGRESSIVE_PRICE_MULTI

        if self._side == OrderSide.Buy.name:
            if slice_data.askPrice[0] == 0:
                price = min(slice_data.bidPrice[0] + 0.01, slice_data.maxPrice)
            else:
                price = min(slice_data.askPrice[0] * open_long_coef, slice_data.maxPrice)

            quantity = min(math.ceil(self._ema_volume() / 100) * 100, self._target_qty_to_order())

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                price = round(price, 2)
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.price_limit_open,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            if slice_data.bidPrice[0] == 0:
                price = max(slice_data.askPrice[0] - 0.01, slice_data.minPrice)
            else:
                price = max(slice_data.bidPrice[0] * open_short_coef, slice_data.minPrice)

            quantity = min(math.ceil(self._ema_volume() / 100) * 100, self._target_qty_to_order())

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                price = round(price, 2)
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.price_limit_open,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    # 正常信号处理
    def _process_tick_using_signals(self, predictions, slice_data, unfinished_order):
        if self._side == OrderSide.Buy.name:
            if self._cur_direction is None:
                if predictions[0] > self._long_aggressive_ratio:
                    self._aggressive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["aggressive_count"] += 1
                    self._cur_direction = SignalType.up
                    return
                elif predictions[1] < self._short_aggressive_ratio:
                    self._cur_direction = SignalType.down
            elif self._cur_direction.value == SignalType.up.value:
                if predictions[0] > self._long_aggressive_ratio:
                    self._aggressive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["aggressive_count"] += 1
                    return
                elif predictions[1] < self._short_aggressive_ratio:
                    self._cur_direction = SignalType.down
                elif predictions[1] < self._short_passive_ratio:
                    self._cur_direction = None  # self._cur_direction == None
            elif self._cur_direction.value == SignalType.down.value:
                if predictions[0] > self._long_aggressive_ratio:
                    self._aggressive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["aggressive_count"] += 1
                    self._cur_direction = SignalType.up
                    return
                elif predictions[0] > self._long_passive_ratio:
                    self._passive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["passive_count"] += 1
                    return

            if predictions[0] > self._long_passive_ratio:
                if self._is_vwap_bias(slice_data):
                    self._process_vwap_bias(slice_data, unfinished_order)
                    return
        else:
            if self._cur_direction is None:
                if predictions[1] < self._short_aggressive_ratio:
                    self._aggressive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["aggressive_count"] += 1
                    self._cur_direction = SignalType.down
                    return
                elif predictions[0] > self._long_aggressive_ratio:
                    self._cur_direction = SignalType.up
            elif self._cur_direction.value == SignalType.down.value:
                if predictions[1] < self._short_aggressive_ratio:
                    self._aggressive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["aggressive_count"] += 1
                    return
                elif predictions[0] > self._long_aggressive_ratio:
                    self._cur_direction = SignalType.up
                elif predictions[0] > self._long_passive_ratio:
                    self._cur_direction = None
            elif self._cur_direction.value == SignalType.up.value:
                if predictions[1] < self._short_aggressive_ratio:
                    self._aggressive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["aggressive_count"] += 1
                    self._cur_direction = SignalType.down
                    return
                elif predictions[1] < self._short_passive_ratio:
                    self._passive_open(slice_data, unfinished_order)
                    self._trigger_sta[self._curr_interval_index]["passive_count"] += 1
                    return

            if predictions[1] < self._short_passive_ratio:
                if self._is_vwap_bias(slice_data):
                    self._process_vwap_bias(slice_data, unfinished_order)
                    return

        if self._is_interval_end(slice_data):
            self._process_interval_end(slice_data, unfinished_order)
        elif not self._is_low_swing(slice_data):
            self._cancel_non_finished_order()
        elif self._is_low_swing_open(slice_data):
            self._low_swing_open(slice_data, unfinished_order)

    def _is_low_swing_open(self, slice_data):
        if self._curr_interval_index <= 1:
            return False
        aggressive_trigger = self._trigger_sta[self._curr_interval_index - 1]["aggressive_count"] + \
                             self._trigger_sta[self._curr_interval_index]["aggressive_count"]
        passive_trigger = self._trigger_sta[self._curr_interval_index - 1]["passive_count"] + \
                          self._trigger_sta[self._curr_interval_index]["passive_count"]
        if self._target_qty_interval_org[self._curr_interval_index - 1] == 0:
            finished_rate = 1.0
        else:
            finished_rate = self._cum_qty / self._target_qty_interval_org[self._curr_interval_index - 1]
        if (aggressive_trigger == 0 and passive_trigger < 2 and finished_rate < 0.95) and self._is_low_swing(
                slice_data):
            return True

        return False

    def _aggressive_open(self, slice_data, unfinished_order):
        open_long_coef = 1 + self._AGGRESSIVE_PRICE_MULTI
        open_short_coef = 1 - self._AGGRESSIVE_PRICE_MULTI

        if self._side == OrderSide.Buy.name:
            if slice_data.askPrice[0] == 0:
                price = min(slice_data.bidPrice[0] + 0.01, slice_data.maxPrice)
            else:
                price = min(slice_data.askPrice[0] * open_long_coef, slice_data.maxPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_aggressive_open_quantity(slice_data)

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.aggressive,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            if slice_data.bidPrice[0] == 0:
                price = max(slice_data.askPrice[0] - 0.01, slice_data.minPrice)
            else:
                price = max(slice_data.bidPrice[0] * open_short_coef, slice_data.minPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_aggressive_open_quantity(slice_data)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.aggressive,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _passive_open(self, slice_data, unfinished_order):
        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        if self._side == OrderSide.Buy.name:
            if ask0 == 0:
                price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01), bid0 + 0.02, slice_data.maxPrice)
            elif bid0 == 0:
                price = ask0
            elif self._is_low_swing(slice_data):
                price = min(max(min(ask0 - 0.01, bid0 + 0.01), bid0), slice_data.maxPrice)
            else:
                price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01),
                            bid0 + 0.02,
                            ask0,
                            slice_data.maxPrice)

            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_passive_open_quantity(slice_data)

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.passive,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            if self._is_low_swing(slice_data):
                price = max(min(max(ask0 - 0.01, bid0 + 0.01), ask0), slice_data.minPrice)
            else:
                price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0, slice_data.minPrice)

            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_passive_open_quantity(slice_data)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.passive,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _low_swing_open(self, slice_data, unfinished_order):
        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        if self._side == OrderSide.Buy.name:
            if ask0 == 0:
                price = min(max(bid0 * (1 + self._PRICE_MULTI), bid0 + 0.01), bid0 + 0.02, slice_data.maxPrice)
            elif bid0 == 0:
                price = ask0
            else:
                price = min(max(min(ask0 - 0.01, bid0 + 0.01), bid0), slice_data.maxPrice)

            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_low_swing_open_quantity(slice_data)

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.low_swing,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:

            price = max(min(max(ask0 - 0.01, bid0 + 0.01), ask0), slice_data.minPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_low_swing_open_quantity(slice_data)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp, SignalType.low_swing,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _cal_aggressive_open_quantity(self, slice_data):
        quantity = 0
        ema = self._ema_volume()

        if self._side == OrderSide.Buy.name:
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order_excess_agressive())
        elif self._side == OrderSide.Sell.name:
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order_excess_agressive())

        return quantity

    def _cal_passive_open_quantity(self, slice_data):
        quantity = 0
        ema = self._ema_volume()

        if self._side == OrderSide.Buy.name:
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())
        elif self._side == OrderSide.Sell.name:
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())

        return quantity

    def _cal_low_swing_open_quantity(self, slice_data):
        quantity = 0
        ema = self._ema_volume()

        if self._side == OrderSide.Buy.name:
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 2), 4)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())
        elif self._side == OrderSide.Sell.name:
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 2), 4)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())

        return quantity

    def _cal_vwap_bias_open_quantity(self, slice_data):
        quantity = 0
        ema = self._ema_volume()

        if self._side == OrderSide.Buy.name:
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.3), 1.0)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order_excess_vwap_bias())
        elif self._side == OrderSide.Sell.name:
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.3), 1.0)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order_excess_vwap_bias())

        return quantity

    def _cal_interval_end_open_quantity(self, slice_data):
        quantity = 0
        ema = self._ema_volume()

        if self._side == OrderSide.Buy.name:
            k2 = 0.8 * slice_data.askVolume[0] / ema
            k = min(max(k2, 0.3), 1.0)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())
        elif self._side == OrderSide.Sell.name:
            k2 = 0.8 * slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.3), 1.0)

            quantity = min(math.ceil(ema * k / 100) * 100, self._target_qty_to_order())

        return quantity

    def _cal_market_close_open_quantity(self, slice_data):
        quantity = self._cal_interval_end_open_quantity(slice_data)
        limit_volume = self._market_close_limit_ratio * self._total_market_close_volume - self._total_open_market_close_volume
        if limit_volume < 0:
            limit_volume = 0
        if self._side == OrderSide.Buy.name:
            max_ask_volume = 0.3 * slice_data.askVolume[0]
            quantity = min(math.ceil(limit_volume / 100) * 100, math.ceil(max_ask_volume / 100) * 100, quantity)
        elif self._side == OrderSide.Sell.name:
            max_bid_volume = 0.3 * slice_data.bidVolume[0]
            quantity = min(math.ceil(limit_volume / 100) * 100, math.ceil(max_bid_volume / 100) * 100, quantity)

        return quantity

    # 区间结束处理
    def _is_interval_end(self, slice_data):
        slice_data_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        bm = self._add_seconds(self._time_table[self._curr_interval_index], -self._INTERVAL_END_SECONDS)
        if self._curr_interval_index == 0:
            remain_val = 1.0
        elif self._target_qty_interval_org[self._curr_interval_index] == 0:
            remain_val = 1.0
        else:
            remain_val = self._cum_qty / self._target_qty_interval_org[self._curr_interval_index]

        return ((slice_data_time >= bm
                 and ((remain_val < 0.5)
                      or (remain_val < 0.9
                          and (self._target_qty_interval_org[self._curr_interval_index] / slice_data.totalVolume
                               > self._limit_ratio)))))

        # return (slice_data_time >= bm and remain_val < 0.9 and self._target_qty_interval_org[
            # self._curr_interval_index] / slice_data.totalVolume > self._limit_ratio)

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
            quantity = self._cal_interval_end_open_quantity(slice_data)
            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.interval_end,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
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
            quantity = self._cal_interval_end_open_quantity(slice_data)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.interval_end,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #                                               Helper Functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def _generate_target_qty_interval(self, slice_data):
        if self._time_table is None and self._target_qty_interval is None:
            date_str = dt.datetime.fromtimestamp(slice_data.timeStamp).strftime('%Y%m%d')
            self._time_table = self._time_table_all[date_str]
            self._target_qty_interval = deepcopy(self._target_qty_interval_all[date_str])
            self._target_qty_interval_org = deepcopy(self._target_qty_interval_all[date_str])
            self._target_qty_interval_percent = [1.0 * quantity / self._target_qty_interval[-1] for quantity in
                                                 self._target_qty_interval]
            for index in range(1, len(self._target_qty_interval_percent)):
                self._target_qty_interval_percent[index] = self._target_qty_interval_percent[index] - \
                                                           self._target_qty_interval_percent[index - 1]
            self._curr_interval_index = 0

    def _update_index(self, slice_data):
        time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        if time > self._time_table[self._curr_interval_index]:
            self._curr_interval_index += 1 if self._curr_interval_index < len(self._time_table) - 1 else 0
            self._recalcu_target_qty_to_order()
            self._trigger_sta.update({self._curr_interval_index: {"aggressive_count": 0, "passive_count": 0}})

    def _process_tick_data(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        tick_datetime = dt.datetime.fromtimestamp(tick_timestamp)

        if (self._previous_slice_data is not None
                and (dt.datetime.fromtimestamp(self._previous_slice_data.timeStamp).time()
                     < self._TICK_START_TIME_AFTERNOON)
                and tick_datetime.time() >= self._TICK_START_TIME_AFTERNOON):
            self._previous_slice_data = None
            self._volume_today = []
            self._total_open_market_close_volume = 0
            self._total_market_close_volume = 0

        if (self._TICK_START_TIME_MORNING <= tick_datetime.time() <= self._TICK_END_TIME_MORNING
                or self._TICK_START_TIME_AFTERNOON <= tick_datetime.time() <= self._TICK_END_TIME_AFTERNOON):
            self._volume_today.append(slice_data.volume)
            self._last_price.append(slice_data.lastPrice)
            if slice_data.askPrice[0] == 0 and slice_data.bidPrice[0] == 0:
                if len(self._ask0) > 0:
                    self._ask0.append(self._ask0[-1])
                    self._bid0.append(self._bid0[-1])
                else:
                    return
            else:
                if slice_data.askPrice[0] == 0:
                    self._ask0.append(slice_data.bidPrice[0])
                    self._bid0.append(slice_data.bidPrice[0])
                elif slice_data.bidPrice[0] == 0:
                    self._ask0.append(slice_data.askPrice[0])
                    self._bid0.append(slice_data.askPrice[0])
                else:
                    self._ask0.append(slice_data.askPrice[0])
                    self._bid0.append(slice_data.bidPrice[0])
            self._update_vwap_bias(slice_data)

        if (self._MARKET_CLOSE_START_TIME_MORNING <= tick_datetime.time() <= self._MARKET_CLOSE_END_TIME_MORNING) or (
                tick_datetime.time() >= self._MARKET_CLOSE_START_TIME_AFTERNOON):
            self._total_market_close_volume += slice_data.volume

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

    def _recalcu_target_qty_to_order(self):
        if self._curr_interval_index == 0:
            return
        value = self._target_qty_to_order()
        if value < 0:
            remain_val = self._target_qty_interval[-1] - self._cum_qty
            if self._curr_interval_index < len(self._target_qty_interval) - 2:
                total_weight = sum(self._target_qty_interval_percent[self._curr_interval_index + 1:])

                if total_weight == 0:
                    return

                self._target_qty_interval[self._curr_interval_index - 1] = self._cum_qty
                for index in range(self._curr_interval_index, len(self._target_qty_interval) - 1):
                    self._target_qty_interval[index] = remain_val * self._target_qty_interval_percent[
                        index] / total_weight + self._target_qty_interval[index - 1]

    def _target_qty_to_order_excess_vwap_bias(self):
        excess_index = min(self._curr_interval_index + int(max(self._vwap_bias_ema[-1] / 10, 0) + 1),
                           len(self._target_qty_interval) - 1)
        value = self._target_qty_interval[excess_index] - self._cum_qty
        return int(value / 100) * 100

    def _target_qty_to_order_excess_agressive(self):
        excess_index = min(self._curr_interval_index + 1, len(self._target_qty_interval) - 1)
        value = self._target_qty_interval[excess_index] - self._cum_qty
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

    @staticmethod
    def _str_to_time(str_list):
        str_list = deepcopy(str_list)
        return list(map(lambda x: dt.time(int(x[:2]), int(x[3:5]), int(x[6:8])), str_list))

    @staticmethod
    def _add_seconds(time, sec):
        time = dt.datetime.combine(dt.datetime.today(), time)
        time += dt.timedelta(seconds=sec)
        return time.time()

    @staticmethod
    def _calculate_market_realized_vwap(slice_data):
        if slice_data.totalVolume == 0:
            return 0
        else:
            return slice_data.totalAmount / slice_data.totalVolume

    def _calculate_strategy_realized_vwap(self):
        if self._cum_qty == 0:
            return 0
        else:
            return self._cum_amt / self._cum_qty

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    #                                      Helper Functions' Helper Functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    @staticmethod
    def _cal_ema(alpha, ema, value):
        return alpha * ema + (1 - alpha) * value

    @staticmethod
    def _llt_step(data_list, last_llt, alpha):
        alpha_squared = alpha ** 2

        llt = ((alpha - alpha_squared / 4) * data_list[-1] + alpha_squared / 2 * data_list[-2]
               - (alpha - alpha_squared * 3 / 4) * data_list[-3] + 2 * (1 - alpha) * last_llt[-1]
               - (1 - alpha) ** 2 * last_llt[-2])

        return llt

    @staticmethod
    def _detect_peaks(x,
                      distance=1,
                      leftNeighborDistanceThresholdPairs=None,
                      rightNeighborDistanceThresholdPairs=None,
                      edge="falling",
                      height=None,
                      threshold=0,
                      valley=False,
                      keepEqualHeight=True,
                      show=False,
                      ax=None,
                      mec="orchid"):
        x = np.atleast_1d(x).astype("float64")

        if x.size < 3:
            return np.array([], dtype=int)

        if valley:
            x = -x
            if height is not None:
                height = -height

        # find indices of all peaks
        dx = x[1:] - x[:-1]
        # handle NaN"s
        indnan = np.where(np.isnan(x))[0]
        if indnan.size:
            x[indnan] = np.inf
            dx[np.where(np.isnan(dx))[0]] = np.inf

        ine, ire, ife = np.array([[], [], []], dtype=int)
        if not edge:
            ine = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) > 0))[0]
        else:
            if edge.lower() in ["rising", "both"]:
                ire = np.where((np.hstack((dx, 0)) <= 0) & (np.hstack((0, dx)) > 0))[0]
            if edge.lower() in ["falling", "both"]:
                ife = np.where((np.hstack((dx, 0)) < 0) & (np.hstack((0, dx)) >= 0))[0]
        ind = np.unique(np.hstack((ine, ire, ife)))

        # handle NaN"s
        if ind.size and indnan.size:
            # NaN"s and values close to NaN"s cannot be peaks
            ind = ind[np.in1d(ind, np.unique(np.hstack((indnan, indnan - 1, indnan + 1))), invert=True)]
        # first and last values of x cannot be peaks
        if ind.size and ind[0] == 0:
            ind = ind[1:]
        if ind.size and ind[-1] == x.size - 1:
            ind = ind[:-1]

        # remove peaks < minimum peak height
        if ind.size and height is not None:
            ind = ind[x[ind] >= height]
        # remove peaks - neighbors < threshold
        if ind.size and threshold > 0:
            dx = np.min(np.vstack([x[ind] - x[ind - 1], x[ind] - x[ind + 1]]), axis=0)
            ind = np.delete(ind, np.where((dx != 0) & (dx < threshold))[0])
        # detect small peaks closer than minimum peak distance
        if ind.size:
            ind = ind[np.argsort(x[ind])][::-1]  # sort ind by peak height
            idel = np.zeros(ind.size, dtype=bool)
            for i in range(ind.size):
                if not idel[i]:
                    # keep peaks with the same height if keepEqualHeight is True
                    if distance > 1:
                        idel = (idel
                                | (ind >= ind[i] - distance)
                                & (ind <= ind[i] + distance)
                                & (x[ind[i]] > x[ind] if keepEqualHeight
                                   else np.hstack((x[ind[i]] >= x[ind[:i]], [False], x[ind[i]] >= x[ind[i + 1:]]))))

                    if not (leftNeighborDistanceThresholdPairs or rightNeighborDistanceThresholdPairs):
                        idel[i] = 0  # Keep current peak
                    else:
                        isCurrPeakValid = True

                        if leftNeighborDistanceThresholdPairs:
                            for pairList in leftNeighborDistanceThresholdPairs:
                                if isinstance(pairList, tuple):
                                    leftNeighborDistance, leftNeighborThreshold = pairList
                                    if (x[ind[i]] - x[max(0, ind[i] - leftNeighborDistance):ind[i]].min()
                                            < leftNeighborThreshold):
                                        idel[i] = 1
                                        isCurrPeakValid = False
                                        break
                                else:
                                    for pair in pairList:
                                        leftNeighborDistance, leftNeighborThreshold = pair
                                        if (x[ind[i]] - x[max(0, ind[i] - leftNeighborDistance):ind[i]].min()
                                                < leftNeighborThreshold):
                                            idel[i] = 1
                                            isCurrPeakValid = False
                                        else:
                                            isCurrPeakValid = True
                                            break
                                    if not isCurrPeakValid:
                                        break
                        if not isCurrPeakValid:
                            continue

                        if rightNeighborDistanceThresholdPairs:
                            for pairList in rightNeighborDistanceThresholdPairs:
                                if isinstance(pairList, tuple):
                                    rightNeighborDistance, rightNeighborThreshold = pairList
                                    if (x[ind[i]] - x[ind[i] + 1:ind[i] + rightNeighborDistance + 1].min()
                                            < rightNeighborThreshold):
                                        idel[i] = 1
                                        isCurrPeakValid = False
                                        break
                                else:
                                    for pair in pairList:
                                        rightNeighborDistance, rightNeighborThreshold = pair
                                        if (x[ind[i]] - x[max(0, ind[i] - rightNeighborDistance):ind[i]].min()
                                                < rightNeighborThreshold):
                                            idel[i] = 1
                                            isCurrPeakValid = False
                                        else:
                                            isCurrPeakValid = True
                                            break
                                    if not isCurrPeakValid:
                                        break
                        if not isCurrPeakValid:
                            continue

                        idel[i] = 0  # Keep current peak

            # remove the small peaks and sort back the indices by their occurrence
            ind = np.sort(ind[~idel])
        return ind
