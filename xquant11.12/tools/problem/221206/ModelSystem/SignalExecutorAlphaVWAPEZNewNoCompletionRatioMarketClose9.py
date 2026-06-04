import datetime as dt
from ModelSystem.Util.OrderSide import OrderSide
from ModelSystem.Util.SignalType import SignalType
from ModelSystem.SignalExecutorAlphaVWAPEZNew import SignalExecutorAlphaVWAPEZNew


class SignalExecutorAlphaVWAPEZNewNoCompletionRatioMarketClose9(SignalExecutorAlphaVWAPEZNew):
    def __init__(self, position_manager):
        SignalExecutorAlphaVWAPEZNew.__init__(self, position_manager)

        self._MARKET_CLOSE_START_TIME_MORNING = dt.time(11, 25, 00)
        self._MARKET_CLOSE_REMEDY_START_TIME_AFTERNOON = dt.time(14, 30, 00)
        self._MARKET_CLOSE_START_TIME_AFTERNOON = dt.time(14, 50, 00)

        self._is_market_close_brought_forward = False

    def onNewDay(self, date):
        self._volume_today = []
        self._bid_predictions = []
        self._ask_predictions = []
        self._previous_slice_data = None
        self._time_table = None
        self._target_qty_interval = None
        self._cum_qty = 0
        self._cum_amt = 0
        self._reset_triggers()
        self._is_market_close_brought_forward = False

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
            self._reset_triggers()

        elif self._is_price_limit_open(slice_data):
            self._process_tick_when_price_limit_open(slice_data)
            self._reset_triggers()

        elif self._is_market_close(slice_data):
            self._process_tick_when_market_close(slice_data)
            self._reset_triggers()

        elif self._is_market_close_brought_forward or self._is_market_close_need_to_be_brought_forward(slice_data):
            self._is_market_close_brought_forward = True
            self._process_tick_when_market_close_brought_forward(slice_data, unfinished_order)
            self._reset_triggers()

        elif self._is_market_close_morning(slice_data):
            self._process_tick_when_market_close_morning(slice_data, unfinished_order)
            self._reset_triggers()

        elif not self._is_in_valid_signal_period(slice_data):
            self._process_tick_in_invalid_signal_period(slice_data, unfinished_order)
            self._reset_triggers()

        elif predictions[0] is not None and predictions[1] is not None:
            self._process_tick_using_signals(predictions, slice_data, unfinished_order)

        self._previous_slice_data = slice_data

    def _is_market_close_morning(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        return self._MARKET_CLOSE_START_TIME_MORNING <= tick_time <= self._MARKET_CLOSE_END_TIME_MORNING

    def _process_tick_when_market_close_morning(self, slice_data, unfinished_order):
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
            quantity = min(quantity, int(self._last_60_ticks_total_volume() * 3 / 1000) * 100)

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.market_close_morning,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0, slice_data.minPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)
            quantity = min(quantity, int(self._last_60_ticks_total_volume() * 3 / 1000) * 100)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.market_close_morning,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _open_when_market_close(self, slice_data):
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

            quantity = self._cal_dynamic_open_quantity(slice_data)
            quantity = min(quantity, int(self._last_60_ticks_total_volume() * 3 / 1000) * 100)

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.market_close,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0, slice_data.minPrice)
            price = round(price, 2)

            quantity = self._cal_dynamic_open_quantity(slice_data)
            quantity = min(quantity, int(self._last_60_ticks_total_volume() * 3 / 1000) * 100)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.market_close,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _is_market_close_need_to_be_brought_forward(self, slice_data):
        tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
        time_mask = tick_time >= self._MARKET_CLOSE_REMEDY_START_TIME_AFTERNOON

        volume_mask = self._target_qty_to_order() > 0.5 * (abs(self._target_qty) - self._cum_qty)

        return time_mask & volume_mask

    def _process_tick_when_market_close_brought_forward(self, slice_data, unfinished_order):
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
            quantity = min(quantity, int(self._last_60_ticks_total_volume() * 3 / 1000) * 100)

            quote_volume = slice_data.askVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.market_close,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)
        else:
            price = max(min(ask0 * (1 - self._PRICE_MULTI), ask0 - 0.01), ask0 - 0.02, bid0, slice_data.minPrice)
            price = round(price, 2)

            if unfinished_order is not None and unfinished_order.price == price:
                return

            self._cancel_non_finished_order()
            quantity = self._cal_dynamic_open_quantity(slice_data)
            quantity = min(quantity, int(self._last_60_ticks_total_volume() * 3 / 1000) * 100)

            quote_volume = slice_data.bidVolume[0]

            if quantity >= 100:
                self.placeOrder(self._symbol, self._side, price, quantity, slice_data.timeStamp,
                                SignalType.market_close,
                                market_vwap=self._calculate_market_realized_vwap(slice_data),
                                strategy_vwap=self._calculate_strategy_realized_vwap(),
                                ema_volume=self._ema_volume(),
                                quote_volume=quote_volume)

    def _process_tick_using_signals(self, predictions, slice_data, unfinished_order):
        if self._side == OrderSide.Buy.name:
            if predictions[1] < self._short_aggressive_ratio:
                self._long_passive_trigger = None
                self._long_aggressive_trigger = None

            long_aggressive_ratio = self._cal_aggressive_trigger()
            long_passive_ratio = self._cal_passive_trigger()

            if predictions[0] > long_aggressive_ratio:
                self._long_aggressive_trigger = predictions[0]
                self._aggressive_open(slice_data, unfinished_order)
                return
            elif (predictions[0] <= self._long_aggressive_ratio) and (predictions[0] > long_passive_ratio):
                self._long_passive_trigger = predictions[0]
                self._passive_open(slice_data, unfinished_order)
                return
        else:
            if predictions[0] > self._long_aggressive_ratio:
                self._short_passive_trigger = None
                self._short_aggressive_trigger = None

            short_aggressive_ratio = self._cal_aggressive_trigger()
            short_passive_ratio = self._cal_passive_trigger()

            if predictions[1] < short_aggressive_ratio:
                self._short_aggressive_trigger = predictions[1]
                self._aggressive_open(slice_data, unfinished_order)
                return
            elif (predictions[1] >= self._short_aggressive_ratio) and (predictions[1] < short_passive_ratio):
                self._short_passive_trigger = predictions[1]
                self._passive_open(slice_data, unfinished_order)
                return

    def _last_60_ticks_total_volume(self):
        return sum(self._volume_today[-60:])
