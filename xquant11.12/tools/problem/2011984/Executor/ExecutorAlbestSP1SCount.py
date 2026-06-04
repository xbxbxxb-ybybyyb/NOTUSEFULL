"""Albest 1秒频策略（股票T+0策略）下单Executor——update @2022.4.29"""

import time
import math
import numpy as np
from Executor.SignalExecutorBase import SignalExecutorBase
from Manager.UtilsModel.OrderSide import OrderSide


class ExecutorAlbestSP1SCount(SignalExecutorBase):
    def __init__(self, position_manager, param_manager, total_position_manager):
        SignalExecutorBase.__init__(self, position_manager, param_manager)
        self._positionMgrTotal = total_position_manager

        self.__order = {}
        self.__pre_net_position = 0

        self.triggersDict = dict()
        # 初始开仓阈值参数
        self.__init_open_long_threshold = None
        self.__init_close_long_threshold = None
        self.__init_long_risk_threshold = None
        self.__init_open_short_threshold = None
        self.__init_close_short_threshold = None
        self.__init_short_risk_threshold = None
        # 连续开仓阈值参数
        self.__open_long_threshold = None
        self.__open_short_threshold = None
        self.__close_long_threshold = None
        self.__close_short_threshold = None

        self.__first_long_price = 0
        self.__first_short_price = 0
        self.__open_long_times = 0
        self.__open_short_times = 0
        self.__MAX_QTY_PER_ORDER = 0.0  # 最大单笔委托数量（OrderCapacity）
        self.__waitForNormalCount = 0  # 涨跌停之后多少个tick内不开仓

    def on_new_day(self, trade_date):
        if 'triggers_by_date' not in self._param.keys():  # 所有日期都是一套阈值
            self.triggersDict = self._param['triggers']
        else:  # 阈值按天更新
            self.triggersDict = self._param['triggers_by_date'][str(trade_date)]
        self.__pre_net_position = 0
        if str(trade_date) in self._param['order_capacity'].keys():  # 没有值的话就不更新，沿用前一天的值
            self.__MAX_QTY_PER_ORDER = max(self._param['order_capacity'][str(trade_date)] * self._param['order_capacity_ratio'], 100)
        self.__waitForNormalCount = self._param['wait_for_normal_count']

    # onNewTick
    def update_predict_info(self, predictions, slice_data):
        valid = self._process_tick_data_1s(predictions, slice_data)
        self.__pre_processing()
        if not valid or self._positionMgr.has_non_finished():
            self.__order = dict()
            return

        slice_data = self.get_next_slice_data(slice_data)  # 创业板股票，由于交易所数据延迟，slice_data取后一个

        if self.__process_zdt_close(slice_data):  # 临近涨跌停处理
            return

        if self.__process_market_closed(slice_data):  # 午盘/尾盘平仓处理
            return

        curr_return = self.__cal_return(slice_data)
        self.reset_params(predictions)

        if self._positionMgr.is_position_closed():  # 没有头寸
            if predictions[0] > self.__init_open_long_threshold:
                self.__process_open_signal(predictions, slice_data, OrderSide.Buy)
            elif predictions[1] < self.__init_open_short_threshold:
                self.__process_open_signal(predictions, slice_data, OrderSide.Sell)
        elif self._positionMgr.is_position_positive():  # 持有多头
            if predictions[1] < self.__cal_close_trigger():
                self.__process_close_signal(predictions, slice_data, OrderSide.Sell)
            elif curr_return < self._param['stop_loss_ratio']:
                self.__process_stop_loss(predictions, slice_data, OrderSide.Sell)
            elif predictions[0] > self.__cal_open_trigger():
                self.__process_open_signal(predictions, slice_data, OrderSide.Buy, is_init_open=False)
        elif self._positionMgr.is_position_negative():  # 持有空头
            if predictions[0] > self.__cal_close_trigger():
                self.__process_close_signal(predictions, slice_data, OrderSide.Buy)
            elif curr_return < self._param['stop_loss_ratio']:
                self.__process_stop_loss(predictions, slice_data, OrderSide.Buy)
            elif predictions[1] < self.__cal_open_trigger():
                self.__process_open_signal(predictions, slice_data, OrderSide.Sell, is_init_open=False)

        if self._param['is_reset_order_price']:
            self.__reset_order_price(slice_data)
        self.__reset_order_volume()
        self.__pre_net_position = self._positionMgr.get_net_position()

    def __process_open_signal(self, predictions, slice_data, side, is_init_open=True):
        # 处理开仓信号
        if side == OrderSide.Buy:
            price = slice_data.askPrice[0] * self._param['open_long_coef']
            volume = self.__cal_open_quantity(side, predictions[0], slice_data, is_init_open)
            self.__order.update({'OpenLong': (price, volume)})
            self.__open_long_threshold = predictions[0]
            self.__open_long_times += 1
        elif side == OrderSide.Sell:
            price = slice_data.bidPrice[0] * self._param['open_short_coef']
            volume = self.__cal_open_quantity(side, predictions[1], slice_data, is_init_open)
            self.__order.update({'OpenShort': (price, volume)})
            self.__open_short_threshold = predictions[1]
            self.__open_short_times += 1

    def __process_close_signal(self, predictions, slice_data, side):
        # 处理平仓信号
        vol_ema = self.__ema_volume()
        ask0, bid0 = slice_data.askPrice[0], slice_data.bidPrice[0]
        net_position = self._positionMgr.get_net_position()
        available_vol = self._positionMgr.get_avail_qty()
        if side == OrderSide.Buy:
            if predictions[0] > self.__init_open_long_threshold:  # 平仓且反向开多
                close_price = ask0 * self._param['close_short_coef']
                volume = min(self.__MAX_QTY_PER_ORDER, max(slice_data.askVolume[0], 0.5 * vol_ema), 1.5 * vol_ema, available_vol)
                volume += abs(net_position)
                self.__open_long_threshold = predictions[0]
                self.__open_long_times += 1
            else:  # 只平仓
                if predictions[0] > self.__init_short_risk_threshold:
                    close_price = ask0 * self._param['close_short_coef']
                elif self.__close_short_threshold is None:
                    close_price = min(bid0 + 0.02, ask0)
                else:
                    close_price = ask0
                volume = min(self.__MAX_QTY_PER_ORDER * 10, vol_ema * 2.5, abs(net_position))
                self.__close_short_threshold = predictions[0]
            self.__order.update({'CloseShort': (close_price, volume)})
        elif side == OrderSide.Sell:
            if predictions[1] < self.__init_open_short_threshold:  # 平仓且反向开空
                close_price = bid0 * self._param['close_long_coef']
                volume = min(self.__MAX_QTY_PER_ORDER, max(slice_data.bidVolume[0], 0.5 * vol_ema), 1.5 * vol_ema, available_vol)
                volume += abs(net_position)
                self.__open_short_threshold = predictions[1]
                self.__open_short_times += 1
            else:  # 只平仓
                if predictions[1] < self.__init_long_risk_threshold:
                    close_price = bid0 * self._param['close_long_coef']
                elif self.__close_long_threshold is None:
                    close_price = max(ask0 - 0.02, bid0)
                else:
                    close_price = bid0
                volume = min(self.__MAX_QTY_PER_ORDER * 10, vol_ema * 2.5, abs(net_position))
                self.__close_long_threshold = predictions[1]
            self.__order.update({'CloseLong': (close_price, volume)})

    def __process_stop_loss(self, predictions, slice_data, side):
        ask0, bid0 = slice_data.askPrice[0], slice_data.bidPrice[0]
        vol_ema = self.__ema_volume()
        net_position = self._positionMgr.get_net_position()
        volume = min(vol_ema * 3, abs(net_position))
        if side == OrderSide.Buy:
            if predictions[0] > self.__init_open_long_threshold:
                price = ask0
            else:
                price = min(bid0 + 0.02, ask0)
            self.__order.update({'CloseShort': (price, volume)})
        else:
            if predictions[1] < self.__init_open_short_threshold:
                price = bid0
            else:
                price = max(ask0 - 0.02, bid0)
            self.__order.update({'CloseLong': (price, volume)})

    # --------------------------------------------------------------------------------------------------
    def __cal_open_quantity(self, side, prediction, slice_data, is_init_open=True):
        vol_ema = self.__ema_volume()
        if side == OrderSide.Buy:
            oppo_vol = slice_data.askVolume[0]
            delta = self._bid_predictions[-1] - self.__exponential_predict(np.array(self._bid_predictions[-5:]))
            vol_ratio = self.__cal_vol_ratio(prediction, self.triggersDict['longTriggerRatio'], delta, self.__open_long_times)
        else:  # side == OrderSide.Sell
            oppo_vol = slice_data.bidVolume[0]
            delta = self._ask_predictions[-1] - self.__exponential_predict(np.array(self._ask_predictions[-5:]))
            vol_ratio = self.__cal_vol_ratio(prediction, self.triggersDict['shortTriggerRatio'], delta, self.__open_short_times)

        open_vol = (1 + 9 * min(1, vol_ratio)) * self.__MAX_QTY_PER_ORDER
        available_vol = self._positionMgr.get_avail_qty()
        quantity = min(open_vol, max(oppo_vol, 0.5 * vol_ema), 1.5 * vol_ema, available_vol)

        if not is_init_open:
            limit_total_vol = min(max(vol_ema * 5, self.__MAX_QTY_PER_ORDER * 5), self.__MAX_QTY_PER_ORDER * 18)
            abs_net_position = abs(self._positionMgr.get_net_position())
            if abs_net_position + quantity > limit_total_vol:  # 累计下单量超过上限
                quantity = max(0, limit_total_vol - abs_net_position)
        quantity = max(min(quantity, int(self._param['init_qty'] / self._param['trading_times'])), 100)
        return quantity

    @staticmethod
    def __cal_vol_ratio(prediction, base, delta, times):
        return abs(prediction) / (abs(base) + 0.1) * abs(delta) / (times + 1)

    # 计算开仓阈值
    def __cal_open_trigger(self):
        open_th = 0
        if self._positionMgr.is_position_positive():
            if self.__open_long_threshold is None:
                open_th = self.__init_open_long_threshold
            else:
                open_th = self.__open_long_threshold
        elif self._positionMgr.is_position_negative():
            if self.__open_short_threshold is None:
                open_th = self.__init_open_short_threshold
            else:
                open_th = self.__open_short_threshold
        return open_th

    # 计算平仓阈值
    def __cal_close_trigger(self):
        close_th = 0
        if self._positionMgr.is_position_negative():
            if self.__close_short_threshold is None:
                close_th = self.__init_close_short_threshold
            else:
                close_th = self.__close_short_threshold
            close_th = min(close_th, self.__init_short_risk_threshold)
        elif self._positionMgr.is_position_positive():
            if self.__close_long_threshold is None:
                close_th = self.__init_close_long_threshold
            else:
                close_th = self.__close_long_threshold
            close_th = max(close_th, self.__init_long_risk_threshold)
        return close_th

    # 处理午盘/尾盘平仓的逻辑
    def __process_market_closed(self, slice_data):
        tick_time = time.strftime('%H:%M:%S', time.localtime(slice_data.timeStamp))
        if self._param['close_time_morning'] <= tick_time <= '11:30:00' or self._param['close_time_afternoon'] <= tick_time <= '14:59:59':
            if self._positionMgr.is_position_closed():
                return True
            is_close_at_ease = False
            if (self._param['close_time_morning'] <= tick_time < self._param['easy_close_time_morning']) or \
                    (self._param['close_time_afternoon'] < tick_time < self._param['easy_close_time_afternoon']):
                is_close_at_ease = True

            net_position = self._positionMgr.get_net_position()
            vol_limit = abs(net_position) / 6
            vol_ema = self.__ema_volume()
            quantity = min(max(vol_ema * self._param['ema_ratio_market_close'], vol_limit), abs(net_position))

            ask0, bid0 = slice_data.askPrice[0], slice_data.bidPrice[0]
            if net_position > 0:
                if is_close_at_ease:
                    price = max(min(ask0 * self._param['close_long_coef'], ask0 - 0.01), ask0 - 0.02, bid0)
                else:
                    price = bid0
                self.__order.update({'CloseLong': (price, quantity)})
            else:
                if is_close_at_ease:
                    price = min(max(bid0 * self._param['close_short_coef'], bid0 + 0.01), bid0 + 0.02, ask0)
                else:
                    price = ask0
                self.__order.update({'CloseShort': (price, quantity)})
            return True
        return False

    # 处理临近涨跌停时的逻辑
    def __process_zdt_close(self, slice_data):
        self.__waitForNormalCount += 1
        curr_pct = slice_data.lastPrice / slice_data.previousClosingPrice - 1
        if abs(curr_pct) > self._param['open_forbidden_pct']:
            self.__waitForNormalCount = 0
        if abs(curr_pct) > self._param['open_forbidden_pct'] or self.__waitForNormalCount < self._param['wait_for_normal_count']:
            if not self._positionMgr.is_position_closed():
                price = slice_data.maxPrice if curr_pct > 0 else slice_data.minPrice
                net_position = self._positionMgr.get_net_position()
                if net_position > 0:
                    self.__order.update({'CloseLong': (price, net_position)})
                else:
                    self.__order.update({'CloseShort': (price, -net_position)})
            return True
        return False

    def __pre_processing(self):
        self.__order = {}
        last_net_position = int(self.__pre_net_position)
        curr_net_position = int(self._positionMgr.get_net_position())
        if curr_net_position < 0 <= last_net_position:
            self.__first_short_price = self._positionMgr.get_finished_orders()[-1].setPrice
        elif last_net_position < 100 <= curr_net_position:
            self.__first_long_price = self._positionMgr.get_finished_orders()[-1].setPrice
        self.__init_open_long_threshold = self.triggersDict['longTriggerRatio']
        self.__init_close_long_threshold = self.triggersDict['longCloseRatio']
        self.__init_long_risk_threshold = self.triggersDict['longRiskRatio']
        self.__init_open_short_threshold = self.triggersDict['shortTriggerRatio']
        self.__init_close_short_threshold = self.triggersDict['shortCloseRatio']
        self.__init_short_risk_threshold = self.triggersDict['shortRiskRatio']

    def reset_params(self, predictions):
        if not self._positionMgr.is_position_negative():  # 没有持仓，或者持有多头仓位
            self.__open_short_threshold = None
            self.__close_short_threshold = None
            self.__open_short_times = 0
            if self._positionMgr.is_position_positive():
                if predictions[0] < self.__init_close_short_threshold:
                    self.__open_long_threshold = None
        if not self._positionMgr.is_position_positive():  # 没有持仓，或者持有空头仓位
            self.__open_long_threshold = None
            self.__close_long_threshold = None
            self.__open_long_times = 0
            if self._positionMgr.is_position_negative():
                if predictions[1] > self.__init_close_long_threshold:
                    self.__open_short_threshold = None

    def __reset_order_price(self, slice_data):
        if len(self.__order) == 0:
            return
        order_flag = list(self.__order.keys())[0]

        price, volume = self.__order[order_flag]
        if order_flag.startswith('Close'):
            return

        ask_p0 = slice_data.askPrice[0]
        ask_v0 = slice_data.askVolume[0]
        bid_p0 = slice_data.bidPrice[0]
        bid_v0 = slice_data.bidVolume[0]
        mid_price = (ask_p0 + bid_p0) / 2
        if ask_p0 < 0.02 or bid_p0 < 0.02:
            return

        reset_price = price
        if order_flag == 'OpenLong':
            if ask_v0 > bid_v0 * 5:
                reset_price = min(ask_p0, mid_price)
            else:
                if (ask_p0 - bid_p0 - 0.01) / bid_p0 * 1000 > 0.5:
                    reset_price = min(ask_p0, mid_price)

        elif order_flag == 'OpenShort':
            if bid_v0 > ask_v0 * 5:
                reset_price = max(bid_p0, mid_price)
            else:
                if (ask_p0 - bid_p0 - 0.01) / bid_p0 * 1000 > 0.5:
                    reset_price = max(bid_p0, mid_price)

        self.__order = {order_flag: (reset_price, volume)}

    def __reset_order_volume(self):
        if len(self.__order) == 0:
            return

        order_flag = list(self.__order.keys())[0]
        if order_flag == 'OpenLong' or order_flag == 'OpenShort':
            price, volume = self.__order[order_flag]
            self.__order = {order_flag: (price, min(volume, self._param['max_order_volume']))}

    # --------------------------------------------------------------------------------------------------
    # 风控指标
    def __check_trade_vol_percentage(self, qty, side, slice_data):
        # 检查成交量占比
        upper_limit = sum(self._volume_today[-60:]) * 0.2
        traded_volume = 0
        finished_orders = self._positionMgrTotal.get_finished_orders()
        for order in finished_orders:
            if order.lastUpdateTime.timestamp() >= slice_data.timeStamp - 180:
                if order.BSFlag == side:
                    traded_volume += order.volume
        new_qty = math.floor(min(qty, max((upper_limit - traded_volume), 0)))
        return new_qty

    # --------------------------------------------------------------------------------------------------
    # Helper Functions
    def __ema_volume(self):  # ema成交量
        alpha = 0.9
        if self._volume_today is None or len(self._volume_today) == 0:
            return 100
        length = len(self._volume_today)
        start = max(0, length - 40)
        ema = self._volume_today[start]
        for i in range(start + 1, length):
            ema = self.__cal_ema(alpha, ema, self._volume_today[i])
        value = max(100.0, math.ceil(ema / 100.0) * 100.0)
        return value

    @staticmethod
    def __cal_ema(alpha, ema, value):
        return alpha * ema + (1 - alpha) * value

    def __cal_return(self, slice_data):
        # 计算当前收益率，输出结果单位为：千分之
        curr_return = 0
        if self._positionMgr.is_position_positive():
            if self.__first_long_price != 0:
                curr_return = (slice_data.askPrice[0] / self.__first_long_price - 1) * 1000
        elif self._positionMgr.is_position_negative():
            if self.__first_short_price != 0:
                curr_return = -(slice_data.bidPrice[0] / self.__first_short_price - 1) * 1000
        return curr_return

    @staticmethod
    def __exponential_smoothing(alpha, s):
        s2 = np.zeros(s.shape)
        s2[0] = s[0]
        for i in range(1, len(s2)):
            s2[i] = alpha * s[i] + (1 - alpha) * s2[i - 1]
        return s2

    def __exponential_predict(self, predictions):
        if predictions.shape[0] == 0:
            return None

        if predictions.shape[0] == 1:
            return predictions[-1]

        alpha = 0.6
        s_single = self.__exponential_smoothing(alpha, predictions)
        s_double = self.__exponential_smoothing(alpha, s_single)

        a_double = 2 * s_single[-1] - s_double[-1]
        b_double = (alpha / (1 - alpha)) * (s_single[-1] - s_double[-1])

        return a_double + b_double

    # --------------------------------------------------------------------------------------------------
    # 供SignalEvaluate使用的模块
    def is_open_long(self, predictions, slice_data):
        if 'OpenLong' in self.__order:
            price, volume = self.__order['OpenLong']
            volume = self.__check_trade_vol_percentage(volume, 'B', slice_data)
            return {'price': price, 'volume': volume}
        return False

    def is_open_short(self, predictions, slice_data):
        if 'OpenShort' in self.__order:
            price, volume = self.__order['OpenShort']
            volume = self.__check_trade_vol_percentage(volume, 'S', slice_data)
            return {'price': price, 'volume': volume}
        return False

    def is_close_long(self, predictions, slice_data):
        if 'CloseLong' in self.__order:
            price, volume = self.__order['CloseLong']
            volume = self.__check_trade_vol_percentage(volume, 'S', slice_data)
            return {'price': price, 'volume': volume}
        return False

    def is_close_short(self, predictions, slice_data):
        if 'CloseShort' in self.__order:
            price, volume = self.__order['CloseShort']
            volume = self.__check_trade_vol_percentage(volume, 'B', slice_data)
            return {'price': price, 'volume': volume}
        return False

    # onIsCancel
    def is_cancel(self, predictions, slice_data):
        self.__init_open_long_threshold = self.triggersDict['longTriggerRatio']
        self.__init_close_long_threshold = self.triggersDict['longCloseRatio']
        self.__init_long_risk_threshold = self.triggersDict['longRiskRatio']
        self.__init_open_short_threshold = self.triggersDict['shortTriggerRatio']
        self.__init_close_short_threshold = self.triggersDict['shortCloseRatio']
        self.__init_short_risk_threshold = self.triggersDict['shortRiskRatio']

        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]

        if abs(slice_data.lastPrice / slice_data.previousClosingPrice - 1) > self._param['open_forbidden_pct']:
            return True

        tick_time = time.strftime('%H:%M:%S', time.localtime(slice_data.timeStamp))
        if self._param['close_time_morning'] <= tick_time <= '11:30:00' or self._param['close_time_afternoon'] <= tick_time <= '14:59:59':
            return True

        if self.__first_long_price is not None and self.__first_long_price != 0:
            buy_curr_return = (ask0 - self.__first_long_price) / self.__first_long_price * 1000
            if buy_curr_return < self._param['stop_loss_ratio']:
                return True

        if self.__first_short_price is not None and self.__first_short_price != 0:
            sell_curr_return = (self.__first_short_price - bid0) / self.__first_short_price * 1000
            if sell_curr_return < self._param['stop_loss_ratio']:
                return True

        if predictions[0] > self.__init_open_long_threshold:
            return True

        if predictions[1] < self.__init_open_short_threshold:
            return True

        if predictions[0] > self.__init_close_short_threshold:
            return True

        if predictions[1] < self.__init_close_long_threshold:
            return True

        return False
