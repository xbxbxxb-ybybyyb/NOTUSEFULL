"""Kunlun策略（转债策略）下单Executor——update @2021.8.4"""

import math
import time
import numpy as np
from Executor.SignalExecutorBase import SignalExecutorBase
from Manager.LimitProcess import LimitProcess


class ExecutorKunlunSP(SignalExecutorBase):
    def __init__(self, position_manager, param_manager):
        SignalExecutorBase.__init__(self, position_manager, param_manager)

        self.__order = {}
        self.__pre_net_position = 0
        self.__max_volume_per_orders = {}

        self.triggersDict = dict()
        # 初始开仓阈值参数
        self.__init_open_long_threshold = None
        self.__init_close_long_threshold = None
        self.__init_long_risk_threshold = None
        self.__init_open_short_threshold = None
        self.__init_close_short_threshold = None
        # 连续开仓阈值参数
        self.__open_long_threshold = None
        self.__close_long_threshold = None

        self.__first_long_price = 0
        self.__open_long_times = 0
        self.__stop_loss_times = 0
        self.__tick_count_since_init_open_long = 0
        self.__tick_count_since_init_close_long = None
        self.__cum_qty_since_init_open_long = 0
        self.__cum_qty_since_init_close_long = 0
        self._cum_open_tick_count1 = 0
        self._cum_open_tick_count2 = 0
        self.__max_bid = 0
        self.__max_long_return_rate = None
        self.limit_process = None  # 临停处理

    def on_new_day(self, trade_date):
        if 'triggers_by_date' not in self._param.keys():  # 所有日期都是一套阈值
            self.triggersDict = self._param['triggers']
        else:  # 阈值按天更新
            self.triggersDict = self._param['triggers_by_date'][str(trade_date)]
        self.__pre_net_position = 0
        self.limit_process = LimitProcess(self._param['limit'])

    # onNewTick
    def update_predict_info(self, predictions, slice_data):
        valid = self._process_tick_data(predictions, slice_data)
        self.__pre_processing()
        self.limit_process.on_new_tick(slice_data)  # 临停处理
        if not valid or self._positionMgr.has_non_finished() or len(self._volume_today) <= self._param['allow_open_tick']:
            return

        if self.__process_market_closed(slice_data, predictions):  # 午盘/尾盘平仓处理
            return

        curr_return = self.__cal_return(slice_data)
        self.reset_params(predictions)
        self.dynamic_threshold(predictions, slice_data, curr_return)

        if self._positionMgr.is_position_closed():  # 没有头寸
            if self.limit_process.process_no_position(slice_data):  # 临停处理
                self.__pre_net_position = self._positionMgr.get_net_position()
                return
            if self.spread_limit(slice_data):
                if (predictions[0] > self.__init_open_long_threshold) or \
                        (self.__signal_sorted(self._bid_predictions[-5:]) and predictions[0] > self.__init_open_long_threshold - 0.3):
                    if predictions[1] >= self.__init_close_long_threshold and self.open_filter():
                        self.__process_open_signal(predictions, slice_data)
        elif self._positionMgr.is_position_positive():  # 持有多头
            if predictions[1] < self.__cal_close_trigger():
                self.__process_close_signal(predictions, slice_data)
            elif curr_return < self._param['stop_loss_ratio']:
                self.__process_stop_loss(predictions, slice_data)
            elif self.limit_process.is_price_limit_deal(slice_data) or self.limit_process.is_price_limit_clear():  # 临停处理
                self.__process_price_limit_close(slice_data)
            elif self.spread_limit(slice_data) and predictions[0] > self.__cal_open_trigger():
                if self.open_filter():
                    self.__process_open_signal(predictions, slice_data, is_init_open=False)

        self.__pre_net_position = self._positionMgr.get_net_position()

    def __process_open_signal(self, predictions, slice_data, is_init_open=True):
        # 处理开仓信号
        price_limit_coef = self._param['initial_open_long_limit_coef'] if is_init_open else self._param['multi_open_long_limit_coef']
        price = min(slice_data.askPrice[0] * self._param['open_long_coef'], slice_data.bidPrice[0] * price_limit_coef)
        volume = self.__cal_open_quantity(predictions[0], slice_data, is_init_open)
        self.__order.update({"OpenLong": (price, volume)})
        self.__open_long_threshold = predictions[0]
        self.__open_long_times += 1

    def __process_close_signal(self, predictions, slice_data):
        # 处理平仓信号
        vol_ema = self.__ema_volume()
        net_position = self._positionMgr.get_net_position()
        close_price = self.__cal_close_price(predictions, slice_data)
        volume_close = min(abs(net_position), 2.5 * vol_ema)
        if self.__tick_count_since_init_close_long is None:
            self.__tick_count_since_init_close_long = 0
        limit_vol = self.__cal_limit_vol(side='sell')
        volume = min(volume_close, limit_vol * self._param['limit_vol_close_ratio'])
        self.__order.update({"CloseLong": (close_price, volume)})
        self.__close_long_threshold = predictions[1]
        self.__stop_loss_times = 0

    def __process_stop_loss(self, predictions, slice_data):
        self.__stop_loss_times += 1
        ask0, bid0 = slice_data.askPrice[0], slice_data.bidPrice[0]
        vol_ema = self.__ema_volume()
        net_position = self._positionMgr.get_net_position()
        if predictions[1] < self.__init_open_short_threshold:
            price = max(bid0 * (self._param['close_long_coef'] - 0.0002), ask0 * self._param['stop_loss_limit_coef'])
        else:
            price = max(bid0 * self._param['close_long_coef'], ask0 * self._param['stop_loss_limit_coef'])
        volume = min(abs(net_position), vol_ema * 3)
        self.__order.update({'CloseLong': (price, volume)})

    # --------------------------------------------------------------------------------------------------
    def __cal_open_quantity(self, prediction, slice_data, is_init_open=True):
        vol_ema = self.__ema_volume()
        delta = self._bid_predictions[-1] - self.__exponential_predict(np.array(self._bid_predictions[-5:]))
        vol_ratio = self.__cal_vol_ratio(prediction, self.triggersDict['longTriggerRatio'], delta, self.__open_long_times)
        k_vol_ratio = 0.5 + min(1, vol_ratio)
        limit_vol = self.__cal_limit_vol(side='buy')
        available_vol = self._positionMgr.get_avail_qty()
        quantity = min(max(slice_data.askVolume[0], k_vol_ratio * vol_ema), 1.5 * vol_ema,
                       limit_vol * self._param['limit_vol_open_ratio'], available_vol)

        if not is_init_open:
            limit_total_vol = vol_ema * 20
            abs_net_position = abs(self._positionMgr.get_net_position())
            if abs_net_position + quantity > limit_total_vol:  # 累计下单量超过上限
                quantity = max(0, limit_total_vol - abs_net_position)
        return quantity

    @staticmethod
    def __cal_vol_ratio(prediction, base, delta, times):
        return abs(prediction - base + 0.05) / 0.05 * abs(delta) / np.sqrt(times + 1)

    def __cal_close_price(self, predictions, slice_data):
        ask0, bid0 = slice_data.askPrice[0], slice_data.bidPrice[0]
        if predictions[1] < self.__init_long_risk_threshold:
            close_price = bid0 * (self._param['close_long_coef'] - 0.0002)
        elif self.__close_long_threshold is None:
            if predictions[1] < self.__init_open_short_threshold:
                close_price = bid0 * (self._param['close_long_coef'] - 0.0002)
            else:
                close_price = bid0
        else:
            close_price = bid0 * self._param['close_long_coef']
        close_price = max(close_price, ask0 * self._param['close_long_limited_coef'])  # 价差限制
        return close_price

    # 计算开仓阈值
    def __cal_open_trigger(self):
        if self.__open_long_threshold is None:
            open_th = self.__init_open_long_threshold
        else:
            open_th = self.__open_long_threshold
        return open_th

    # 计算平仓阈值
    def __cal_close_trigger(self):
        if self.__close_long_threshold is None:
            close_th = self.__init_close_long_threshold
        else:
            close_th = self.__close_long_threshold
        close_th = max(close_th, self.__init_long_risk_threshold)
        return close_th

    def __process_market_closed(self, slice_data, predictions):
        # 处理午盘/尾盘平仓的逻辑
        tick_time = time.strftime("%H:%M:%S", time.localtime(slice_data.timeStamp))
        if self._param['close_time_morning'] <= tick_time <= '11:30:00' or self._param['close_time_afternoon'] <= tick_time <= '14:59:59':
            if self._positionMgr.is_position_closed():
                return True
            net_position = self._positionMgr.get_net_position()
            vol_limit = abs(net_position) / 6
            vol_ema = self.__ema_volume()
            quantity = min(max(vol_ema * 4, vol_limit), abs(net_position))

            ask0, bid0 = slice_data.askPrice[0], slice_data.bidPrice[0]
            close_long_limited_coef = 0.995

            if net_position > 0:
                if self._param['close_time_morning'] <= tick_time < self._param['easy_close_time_morning']:  # 上午第一阶段平仓
                    if (predictions[0] > self.__init_open_long_threshold) or \
                            (self.__signal_sorted(self._bid_predictions[-5:]) and predictions[0] > self.__init_open_long_threshold - 0.3):
                        price = max(round((ask0 + bid0) / 2, 3) - 0.01, bid0, ask0 * close_long_limited_coef)
                    else:
                        price = max(ask0 - 0.5, bid0, ask0 * close_long_limited_coef)
                elif self._param['close_time_afternoon'] < tick_time < self._param['easy_close_time_afternoon']:  # 下午第一阶段平仓
                    price = max(ask0 - 0.5, bid0, ask0 * close_long_limited_coef)
                else:  # 上午与下午第二阶段平仓
                    price = bid0
                self.__order.update({"CloseLong": (price, quantity)})
            return True
        return False

    def __process_price_limit_close(self, slice_data):
        if self._positionMgr.is_position_closed():
            return
        price = self.limit_process.get_limit_price(slice_data)
        net_position = self._positionMgr.get_net_position()
        vol_limit = abs(net_position) / 6
        vol_ema = self.__ema_volume()
        quantity = min(max(vol_ema * 4, vol_limit), abs(net_position))
        self.__order.update({"CloseLong": (price, quantity)})

    def open_filter(self):
        """开仓过滤，返回单边最大金额的放大系数"""
        bid0_price_list = list(filter(lambda x: x is not None, self._bid0_price_today))
        select_bid0_list = bid0_price_list[-self._param['open_filter_tick_num']:]  # 过去一段时间的涨跌幅
        pct_last_period = select_bid0_list[-1] / np.nanmax(select_bid0_list) - 1 if np.nanmax(select_bid0_list) != 0 else 0
        if pct_last_period < self._param['open_filter_pct']:
            return False
        return True

    def __pre_processing(self):
        self.__order = {}
        self.__init_open_long_threshold = self.triggersDict['longTriggerRatio']
        self.__init_close_long_threshold = self.triggersDict['longCloseRatio']
        self.__init_long_risk_threshold = self.triggersDict['longRiskRatio']
        self.__init_open_short_threshold = self.triggersDict['shortTriggerRatio']
        self.__init_close_short_threshold = self.triggersDict['shortCloseRatio']
        last_net_position = int(self.__pre_net_position)
        curr_net_position = int(self._positionMgr.get_net_position())
        if last_net_position == 0 < curr_net_position:
            self.__first_long_price = self._positionMgr.get_finished_orders()[-1].setPrice
        if last_net_position > curr_net_position:
            self.__cum_qty_since_init_close_long += (last_net_position - curr_net_position)
        elif last_net_position < curr_net_position:
            self.__cum_qty_since_init_open_long += (curr_net_position - last_net_position)

    def reset_params(self, predictions):
        if self._positionMgr.is_position_closed():
            self.__open_long_threshold = None
            self.__close_long_threshold = None
            self.__open_long_times = 0
            self.__stop_loss_times = 0
            self.__tick_count_since_init_open_long = 0
            self.__tick_count_since_init_close_long = None
            self._cum_open_tick_count1 = 0
            self._cum_open_tick_count2 = 0
            self.__cum_qty_since_init_close_long = 0
            self.__cum_qty_since_init_open_long = 0
        elif self._positionMgr.is_position_positive():
            self.__tick_count_since_init_open_long += 1
            if self.__tick_count_since_init_close_long is not None:
                self.__tick_count_since_init_close_long += 1
            self._cum_open_tick_count1 += 1
            self._cum_open_tick_count2 += 1
            if predictions[0] < self.__init_close_short_threshold:
                self.__open_long_threshold = None

    def dynamic_threshold(self, predictions, slice_data, curr_return):
        # 动态阈值逻辑
        if self._positionMgr.is_position_closed():
            self.__max_bid = predictions[0]
            self.__max_long_return_rate = 0
        if self._positionMgr.is_position_positive():
            self.__max_long_return_rate = max(self.__max_long_return_rate, curr_return)
            self.__max_bid = max(predictions[0], self.__max_bid)
            long_close_threshold_offset = max(0, self.__max_bid - self.__init_open_long_threshold) / 5.0
            self.__init_open_short_threshold -= long_close_threshold_offset
            self.__init_close_long_threshold -= long_close_threshold_offset
            self.__init_long_risk_threshold -= long_close_threshold_offset
            if time.strftime("%H:%M:%S", time.localtime(slice_data.timeStamp)) >= self._param['high_vol_start_time']:
                log_vol_ma_200 = self.__log_vol_ma_200()
                if log_vol_ma_200 <= self._param['high_vol']:
                    loss_ratio = min(self.__max_long_return_rate - curr_return, 1.0) / 5
                    vol_ratio = min((self._param['high_vol'] - log_vol_ma_200) / np.log(2), 1.0)
                    long_open_threshold_offset = loss_ratio * vol_ratio
                    self.__init_open_long_threshold += 0.1
                    self.__init_close_long_threshold += long_open_threshold_offset
                    self.__init_long_risk_threshold += long_open_threshold_offset

            if self.__close_long_threshold is None:
                loss_ratio = self.__max_long_return_rate - curr_return
                tick_decrease_ratio = 0.1 * int(self._cum_open_tick_count2 / self._param['close_decrease_interval'])
                self.__init_close_long_threshold += tick_decrease_ratio * loss_ratio
            else:
                tick_reset_ratio = 0.1 * int(self._cum_open_tick_count1 / self._param['close_reset_interval'])
                self.__close_long_threshold = min(self.__init_close_long_threshold, self.__close_long_threshold + tick_reset_ratio)
                if self._cum_open_tick_count1 > self._param['close_reset_interval']:
                    self._cum_open_tick_count1 -= self._param['close_reset_interval']
                self._cum_open_tick_count2 = 0

    # --------------------------------------------------------------------------------------------------
    # 风控指标
    def __cal_limit_vol(self, side):
        limit_vol = 1e10
        if side == 'buy':
            if self.__tick_count_since_init_open_long > 0:
                long_percent = self.__get_position_percent_in_market(self.__tick_count_since_init_open_long - 1)
                total_market_vol_since_open = sum(self._volume_today[-self.__tick_count_since_init_open_long - 1:])
                limit_vol = total_market_vol_since_open * long_percent - self.__cum_qty_since_init_open_long
        else:  # side == 'sell'
            short_percent = self.__get_position_percent_in_market(self.__tick_count_since_init_close_long - 1)
            total_market_vol_since_close = sum(self._volume_today[-self.__tick_count_since_init_close_long - 1:])
            limit_vol = short_percent * total_market_vol_since_close - self.__cum_qty_since_init_close_long
            limit_vol = math.ceil(limit_vol / 10) * 10
        return limit_vol

    def __get_position_percent_in_market(self, tick_num):
        tick_num_list = [5, 10, 20, 40, 60, 80, 100, 200, 999999]
        if self._param['is_conservative_mode']:
            ratio_list = [1.0, 0.5, 0.25, 0.12, 0.10, 0.09, 0.08, 0.05, 0.03]  # 保守参数
        else:
            ratio_list = [1.0, 0.5, 0.3, 0.2, 0.15, 0.15, 0.15, 0.10, 0.05]  # 激进参数
        ratio = ratio_list[np.argwhere(tick_num <= np.array(tick_num_list))[0][0]]
        return ratio

    def __check_trade_vol_percentage(self, qty, side, slice_data):
        # 检查成交量占比
        upper_limit = sum(self._volume_today[-60:]) * self._param['check_trade_vol_percentage_limit_ratio']
        traded_volume = 0
        finished_orders = self._positionMgr.get_finished_orders()
        for order in finished_orders:
            if order.lastUpdateTime.timestamp() >= slice_data.timeStamp - self._param['check_trade_vol_percentage_count']:
                if self._param['check_is_double_side_control'] or order.BSFlag == side:
                    traded_volume += order.volume
        new_qty = math.floor(min(qty, upper_limit - traded_volume))
        return new_qty

    def __check_trade_amt_percentage(self, price, qty, side, slice_data):
        # 检查成交额占比
        traded_amount = 0
        finished_orders = self._positionMgr.get_finished_orders()
        for order in finished_orders:
            if order.lastUpdateTime.timestamp() >= slice_data.timeStamp - self._param['check_trade_amt_percentage_count']:
                if self._param['check_is_double_side_control'] or order.BSFlag == side:
                    traded_amount += order.accMount
        new_qty = math.floor(min(qty, (self._param['check_trade_amt_percentage_limit_amt'] - traded_amount) / price))
        return new_qty

    def __check_price_deviate(self, price, side, slice_data):
        if side == 'B':
            new_price = min(price, slice_data.lastPrice * (1 + self._param['max_price_deviate_ratio']))
        else:
            new_price = max(price, slice_data.lastPrice * (1 - self._param['max_price_deviate_ratio']))
        return new_price

    # --------------------------------------------------------------------------------------------------
    # Helper Functions
    def spread_limit(self, slice_data):
        # 买卖价差是否达到禁止开仓的阈值
        if slice_data.askPrice[0] == 0:
            return False
        bid_ask_spread = (slice_data.bidPrice[0] / slice_data.askPrice[0] - 1) * 1000
        return bid_ask_spread >= self._param['unallowed_open_loss_ratio']

    @staticmethod
    def __signal_sorted(predictions, is_reverse=False):
        if len(predictions) < 5:
            return False
        if is_reverse:
            for index in range(1, len(predictions)):
                if predictions[index] >= predictions[index - 1]:
                    return False
            return True
        else:
            for index in range(1, len(predictions)):
                if predictions[index] <= predictions[index - 1]:
                    return False
            return True

    def __ema_volume(self):
        if self._volume_today is None or len(self._volume_today) == 0:
            return 10.0
        length = len(self._volume_today)

        # 计算ma volume
        start = max(0, length - 50)
        ma = sum(self._volume_today[start:length]) * self._param['liquidity_ratio']

        # 计算ema volume
        alpha = 0.6
        start = max(0, length - 40)
        ema = self._volume_today[start]
        for i in range(start + 1, length):
            ema = alpha * ema + (1 - alpha) * self._volume_today[i]
        ema = ema * self._param['liquidity_ratio'] / 0.02

        value = max(ma, ema * self._param['ema2_ratio'])
        return max(0, math.ceil(value / 10) * 10) + 10

    def __cal_return(self, slice_data):
        # 计算当前收益率，输出结果单位为：千分之
        curr_return = 0
        if self._positionMgr.is_position_positive():
            if self.__first_long_price != 0:
                curr_return = (slice_data.askPrice[0] / self.__first_long_price - 1) * 1000
        return curr_return

    def __log_vol_ma_200(self):
        if self._volume_today is None or len(self._volume_today) == 0:
            return 0.0
        return np.mean(np.log(np.array(self._volume_today[-200:]) + 10.))

    def __exponential_predict(self, predictions):
        if predictions.shape[0] == 0:
            return None
        elif predictions.shape[0] == 1:
            return predictions[-1]
        else:
            alpha = 0.6
            s_single = self.__exponential_smoothing(alpha, predictions)
            s_double = self.__exponential_smoothing(alpha, s_single)
            a_double = 2 * s_single[-1] - s_double[-1]
            b_double = (alpha / (1 - alpha)) * (s_single[-1] - s_double[-1])
            return a_double + b_double

    @staticmethod
    def __exponential_smoothing(alpha, s):
        s2 = np.zeros(s.shape)
        s2[0] = s[0]
        for i in range(1, len(s2)):
            s2[i] = alpha * s[i] + (1 - alpha) * s2[i - 1]
        return s2

    # --------------------------------------------------------------------------------------------------
    # 供SignalEvaluate使用的模块
    def is_open_long(self, predictions, slice_data):
        if "OpenLong" in self.__order:
            price, volume = self.__order["OpenLong"]
            price = self.__check_price_deviate(price, 'B', slice_data)  # 检查价格偏离度
            volume = self.__check_trade_vol_percentage(volume, "B", slice_data)  # 检查成交占比
            volume = self.__check_trade_amt_percentage(price, volume, "B", slice_data)  # 检查成交金额
            if volume < self._param['min_vol_qty']:
                return False
            else:
                return {"price": price, "volume": volume}
        return False

    def is_close_long(self, predictions, slice_data):
        if "CloseLong" in self.__order:
            price, volume = self.__order["CloseLong"]
            price = self.__check_price_deviate(price, 'S', slice_data)  # 检查价格偏离度
            if self._param['check_is_close_control']:
                volume = self.__check_trade_vol_percentage(volume, "S", slice_data)  # 检查成交占比
                volume = self.__check_trade_amt_percentage(price, volume, "S", slice_data)  # 检查成交金额
            return {"price": price, "volume": volume}
        return False
