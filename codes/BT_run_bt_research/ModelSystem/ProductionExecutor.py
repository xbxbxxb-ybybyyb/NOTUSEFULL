from ModelSystem.SignalExecutorBase import SignalExecutorBase
from Utils.OrderSide import OrderSide
import datetime as dt
import math
import numpy as np


class ProductionExecutor(SignalExecutorBase):
    def __init__(self, positionMgr, riskMgr):
        SignalExecutorBase.__init__(self, positionMgr, riskMgr)
        # constants
        self.__start_time_morning = dt.time(9, 30, 15)  # 早上开盘从该时刻起，才认为是正常的行情，开始接收早盘行情信号
        self.__start_time_afternoon = dt.time(13, 00, 15)  # 下午开盘从该时刻起，才认为是正常的行情，开始接收午盘行情信号
        self.__trading_start_morning = dt.time(9, 31, 15)  # 早上开盘从该时刻起，才认为信号是合理的，开始交易
        self.__trading_start_afternoon = dt.time(13, 1, 15)  # 下午开盘从该时刻起，才认为信号是合理的，开始交易
        self.__close_time_morning = dt.time(11, 29, 0)  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
        self.__easy_close_time_morning = dt.time(11, 29, 30)  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓
        self.__close_time_afternoon = dt.time(14, 55, 0)  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
        self.__easy_close_time_afternoon = dt.time(14, 56, 00)  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓
        self.__high_vol_start_time = dt.time(9, 41, 15)  # 使用活跃度指标进行阈值调整
        self.__vol_limit_start_time = dt.time(10, 30, 00)  # 使用活跃度指标进行阈值调整
        self.__MAX_QTY_PER_ORDER = None  # 最大单笔委托数量（下入到SignalEvaluate后，只会被可买、可卖限制，不会被流动性限制。因为内部已经对流动性进行了处理）
        self.__STOP_LOSS_RATIO = -10  # 止损参数，单位千分之，-10代表1%止损（一定是负值，因直接跟return比较）
        self.__UNALLOWED_OPENLOSS_RATIO = self.__STOP_LOSS_RATIO + 5
        self.__symbol = ""
        self.__longTriggerRatio = 0
        self.__shortTriggerRatio = 0
        self.__longCloseRatio = 0
        self.__longCloseRiskRatio = 0
        self.__shortCloseRatio = 0
        self.__shortCloseRiskRatio = 0

        self.__tickData = None
        self.__volume_today = []  # 当天行情的volume
        self.__amt_today = []  # 当天行情的volume
        self.__mid_price_today = []  # 当天行情的mid_price
        self.__bs_vwap_price_today = []  # 当天行情买卖均价（10当盘口成交量加权平均的价格）
        self.__last_tagInfo = None  # 上一个tick的tagInfo
        # new parameters
        self.__bid_predictions = []  # 存放当天的所有预测值 index 0
        self.__ask_predictions = []  # 存放当天的所有预测值 index 1

        self.__close_long_threshold = None
        self.__close_short_threshold = None
        self.__open_long_threshold = None
        self.__open_short_threshold = None
        self.__open_long_times = 0
        self.__open_short_times = 0

        self.__first_long_price = 0  # may have to adjust the assignment position
        self.__first_short_price = 0
        self.__last_long_prediction = 0
        self.__last_short_prediction = 0

        self.__order = {}  # have to reset the dict at the beginning of every tick, key = open/close side, value = (price, volume)
        self.__pre_net_position = 0  # the net position of last tick
        self.__max_volume_per_orders = {}
        self.__updated_para = None
        self.__order_capacity = None
        self.__is_holo = False
        self.__next_slice_data = None  # reserved for holo use
        self.__tick_count_since_init_open_long = None
        self.__tick_count_since_init_close_long = None
        self.__cum_qty_since_init_close_long = None
        self.__cum_qty_since_init_open_long = None
        self.__FIRST_UP_LIMIT = 200
        self.__SECOND_UP_LIMIT = 300
        self.__FIRST_DOWN_LIMIT = -200
        self.__SECOND_DOWN_LIMIT = -300
        self.__UP_OFFSET = 5
        self.__DOWN_OFFSET = 10
        self.__LIMIT_STATUS = None
        self.__stop_loss_times = None
        self.__pre_slice_data = None
        self.__is_first_up = False
        self.__is_first_down = False
        self.__init_open_long_threshold = None
        self.__init_close_long_threshold = None
        self.__init_close_long_risk_threshold = None
        self.__init_open_short_threshold = None
        self.__init_close_short_threshold = None
        self.__max_long_return_rate = None

        self.__HIGH_VOL = None
        self.__other_trigger = None
        self.STOP_PROFIT_LOSS = 20
        self.DROP_LOSS = 5
        self.__timestamp_today = []
        self.__bid0_price_today = []
        self.__ask0_price_today = []
        self._cum_open_tick_count1 = 0
        self._cum_open_tick_count2 = 0

    def set_json_param_before_start(self, param):
        self.__order_capacity = param
        self.set_holo(param)
        self.set_high_vol()

    def set_holo(self, param):
        if 'Holo' in param:
            value = (param['Holo'].lower() == 'true')
            self.__is_holo = value

    def set_high_vol(self):
        self.__HIGH_VOL = 0.0

    def set_other_triggers(self, other_triggers):
        self.__other_triggers = other_triggers

    def generateTriggerRatio(self, symbol, trigger_ratio_dict, tickData):
        if tickData is None:
            raise Exception("tickData in SignalExecutorOppo is None. Please load the tickData through SignalEvaluate.")
        self.__tickData = tickData
        self.__symbol = symbol
        if trigger_ratio_dict:
            self.__longTriggerRatio = trigger_ratio_dict['longTriggerRatio']
            self.__shortTriggerRatio = trigger_ratio_dict['shortTriggerRatio']
            self.__longCloseRiskRatio = trigger_ratio_dict['longRiskRatio']
            self.__shortCloseRiskRatio = trigger_ratio_dict['shortRiskRatio']
            self.__longCloseRatio = trigger_ratio_dict['longCloseRatio']
            self.__shortCloseRatio = trigger_ratio_dict['shortCloseRatio']

    def resetNewDay(self):
        self.__bid_predictions = []
        self.__ask_predictions = []
        self.__close_long_threshold = None
        self.__close_short_threshold = None
        self.__open_long_threshold = None
        self.__open_short_threshold = None
        self.__open_long_times = 0
        self.__open_short_times = 0
        self.__last_tagInfo = None
        self.__volume_today = []
        self.__amt_today = []
        self.__mid_price_today = []
        self.__bs_vwap_price_today = []
        self.__timestamp_today = []
        self.__bid0_price_today = []
        self.__ask0_price_today = []
        self.__first_long_price = 0
        self.__first_short_price = 0
        self.__last_long_prediction = 0
        self.__last_short_prediction = 0
        self.__order = {}
        self.__pre_net_position = 0
        self.__MAX_QTY_PER_ORDER = None
        self.__tick_count_since_init_open_long = None
        self.__tick_count_since_init_close_long = None
        self.__cum_qty_since_init_close_long = None
        self.__cum_qty_since_init_open_long = None
        self.__LIMIT_STATUS = None
        self.__stop_loss_times = None
        self.__pre_slice_data = None
        self.__is_first_up = False
        self.__is_first_down = False
        self.__init_open_long_threshold = None
        self.__init_close_long_threshold = None
        self.__init_close_long_risk_threshold = None
        self.__init_open_short_threshold = None
        self.__init_close_short_threshold = None
        self.__max_long_return_rate = None
        self.__other_trigger = None
        self._cum_open_tick_count1 = 0
        self._cum_open_tick_count2 = 0

    def __reset_default(self):
        self.__init_open_long_threshold = self.__longTriggerRatio
        self.__init_close_long_threshold = self.__longCloseRatio
        self.__init_close_long_risk_threshold = self.__longCloseRiskRatio
        self.__init_open_short_threshold = self.__shortTriggerRatio
        self.__init_close_short_threshold = self.__shortCloseRatio

    def __signal_sorted(self, predictions, is_reverse=False):
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

    def open_filter(self):
        """开仓过滤，返回单笔和单边最大金额的放大系数"""
        mid_price_list = list(filter(lambda x: x is not None, self.__mid_price_today))
        # 过去1min的涨跌幅
        select_mid_list = mid_price_list[-20:]
        pct_1min = select_mid_list[-1] / select_mid_list[0] - 1 if select_mid_list[0] != 0 else 0
        if pct_1min < -0.01:
            # 当前位置在当天的分位数
            percentile = 1 - (np.array(mid_price_list) > mid_price_list[-1]).sum() / len(mid_price_list)
            if percentile > 0.3:
                return 0
            elif percentile < 0.1:
                return None
        return None

    def __check_first_price_limit(self, slice_data):
        if self.__symbol[-2:] == "SZ":
            return False
        price_ratio = 1000 * (slice_data.lastPrice / slice_data.previousClosingPrice - 1)
        if price_ratio >= self.__FIRST_UP_LIMIT:
            self.__is_first_up = True
        elif price_ratio <= self.__FIRST_DOWN_LIMIT:
            self.__is_first_down = True

    def __is_price_limit_deal(self, slice_data):
        if self.__symbol[-2:] == "SZ":
            return False

        price_ratio = 1000 * (slice_data.lastPrice / slice_data.previousClosingPrice - 1)
        if price_ratio < self.__SECOND_DOWN_LIMIT + self.__DOWN_OFFSET and price_ratio >= self.__SECOND_DOWN_LIMIT:
            self.__LIMIT_STATUS = "SECOND_DOWN_LIMIT"
            return True
        elif price_ratio > self.__SECOND_UP_LIMIT - self.__UP_OFFSET and price_ratio <= self.__SECOND_UP_LIMIT:
            self.__LIMIT_STATUS = "SECOND_UP_LIMIT"
            return True
        elif not (self.__is_first_up or self.__is_first_down):
            if price_ratio > self.__FIRST_UP_LIMIT - self.__UP_OFFSET and price_ratio <= self.__FIRST_UP_LIMIT:
                self.__LIMIT_STATUS = "FIRST_UP_LIMIT"
                return True
            elif price_ratio < self.__FIRST_DOWN_LIMIT + self.__DOWN_OFFSET and price_ratio >= self.__FIRST_DOWN_LIMIT:
                self.__LIMIT_STATUS = "FIRST_DOWN_LIMIT"
                return True

        return False

    def __get_close_long_offset(self):
        if self.__max_bid is None:
            return 0
        return max(0, self.__max_bid - self.__init_open_long_threshold) / 5.0

    def __get_open_long_offset(self, log_vol_ma_200, cur_return):
        loss_ratio = min(self.__max_long_return_rate - cur_return, 1.0) / 5
        vol_ratio = min((self.__HIGH_VOL - log_vol_ma_200) / np.log(2), 1.0)
        return loss_ratio * vol_ratio

    # onNewTick
    def updatePredictInfo(self, predictions, slice_data):
        valid = self.__process_tickData(slice_data)
        self.__pre_processing(slice_data)
        self.__check_first_price_limit(slice_data)

        if not valid or self._positionMgr.has_non_finished(self.__symbol):
            return

        if len(self.__volume_today) <= 1:
            return

        self.__reset_default()
        self.__store_predictions(predictions)

        # 14:55:00起，进行午盘平仓，且不发开仓单
        if self.__is_close_time_afternoon(slice_data):
            self.__process_afternoon_close(self.__symbol, slice_data, predictions)
            return

        # 11:29:00起，进行午盘平仓，且不发开仓单
        if self.__is_close_time_morning(slice_data):
            self.__process_morning_close(self.__symbol, slice_data, predictions)
            return

        if self._positionMgr.is_position_closed(self.__symbol):
            # 初始化上笔开平仓阈值
            self.__close_long_threshold = None
            self.__open_long_threshold = None
            self.__open_long_times = 0
            self.__stop_loss_times = 0
            self.__tick_count_since_init_open_long = None
            self.__tick_count_since_init_close_long = None
            self.__cum_qty_since_init_close_long = None
            self.__cum_qty_since_init_open_long = None
            self.__max_long_return_rate = 0
            self._cum_open_tick_count1 = 0
            self._cum_open_tick_count2 = 0
            bid0 = slice_data.bidPrice[0]
            ask0 = slice_data.askPrice[0]
            self.__max_bid = predictions[0]
            # net position is 0
            if self.__is_price_limit_deal(slice_data) or (bid0 / ask0 - 1) * 1000 < self.__UNALLOWED_OPENLOSS_RATIO:
                self.__pre_net_position = self._positionMgr.get_net_position(self.__symbol)
                return

            # 第一次开仓
            if (predictions[0] > self.__init_open_long_threshold) or \
                    (self.__signal_sorted(self.__bid_predictions[-5:]) and predictions[0] > self.__init_open_long_threshold - 0.3):
                if predictions[1] < self.__init_close_long_threshold:
                    self.__pre_net_position = self._positionMgr.get_net_position(self.__symbol)
                    return
                adj_ratio = self.open_filter()
                self.__initial_open(predictions, slice_data, OrderSide.Buy, adj_ratio)
        else:
            ask0 = slice_data.askPrice[0]
            bid0 = slice_data.bidPrice[0]
            if self._positionMgr.is_position_positive(self.__symbol):
                curr_return = self.__cal_return(ask0)
                self.__max_long_return_rate = max(self.__max_long_return_rate, curr_return)
                self.__max_bid = max(predictions[0], self.__max_bid)

                long_close_threshold_offset = self.__get_close_long_offset()
                self.__init_open_short_threshold -= long_close_threshold_offset
                self.__init_close_long_threshold -= long_close_threshold_offset
                self.__init_close_long_risk_threshold -= long_close_threshold_offset

                ### 市场活跃度指标
                long_open_threshold_offset = None
                tick_time = dt.datetime.fromtimestamp(slice_data.timeStamp).time()
                if tick_time >= self.__high_vol_start_time:
                    log_vol_ma_200 = self.__log_vol_ma_200()
                    if log_vol_ma_200 <= self.__HIGH_VOL:
                        long_open_threshold_offset = self.__get_open_long_offset(log_vol_ma_200, curr_return)

                if long_open_threshold_offset is not None:
                    self.__init_open_long_threshold += 0.1
                    self.__init_close_long_threshold += long_open_threshold_offset
                    self.__init_close_long_risk_threshold += long_open_threshold_offset

                self.__tick_count_since_init_open_long += 1
                self._cum_open_tick_count1 += 1
                self._cum_open_tick_count2 += 1
                if self.__tick_count_since_init_close_long is not None:
                    self.__tick_count_since_init_close_long += 1

                close_reset_interval = 50
                if self.__close_long_threshold is not None:
                    self.__close_long_threshold = min(self.__init_close_long_threshold,
                                                      self.__close_long_threshold + 0.1 * int(
                                                          self._cum_open_tick_count1 / close_reset_interval))
                    if self._cum_open_tick_count1 > close_reset_interval:
                        self._cum_open_tick_count1 -= close_reset_interval
                    self._cum_open_tick_count2 = 0

                close_decrease_interval = 20
                if self.__close_long_threshold is None:
                    loss_ratio = (self.__max_long_return_rate - curr_return) / 10
                    self.__init_close_long_threshold += int(self._cum_open_tick_count2 / close_decrease_interval) * loss_ratio

                if predictions[0] < self.__init_close_short_threshold:
                    self.__open_long_threshold = None
                if predictions[1] < self.__cal_close_trigger():  # 平仓
                    self.__process_close_signal(predictions, slice_data, OrderSide.Sell)
                elif curr_return < self.__STOP_LOSS_RATIO:  # 止损
                    self.__process_stop_loss(OrderSide.Sell, predictions, slice_data)
                elif self.__is_price_limit_deal(slice_data):  # 临停处理
                    self.__process_price_limit_close(self.__symbol, slice_data)
                elif (bid0 / ask0 - 1) * 1000 > self.__UNALLOWED_OPENLOSS_RATIO and predictions[0] > self.__cal_open_trigger():  # 连续开仓
                    adj_ratio = self.open_filter()
                    self.__process_multi_open(predictions, slice_data, OrderSide.Buy, adj_ratio)

        self.__pre_net_position = self._positionMgr.get_net_position(self.__symbol)
        self.__pre_slice_data = slice_data

    def get_next_slice_data(self, slice_data):
        return slice_data

    def __get_my_next_slice_data(self, slice_data):
        return self.next_slice_data_speed(slice_data)

    def isOpenLong(self, predictions, slice_data):
        if "OpenLong" not in self.__order:
            return False
        else:
            price, volume, adj_ratio = self.__order["OpenLong"]
            newQty = self.__checkCJZB(volume, "B", slice_data)  # 检查成交占比
            newQty = self.__checkCJJE(price, newQty, "B", slice_data)  # 检查成交金额
            if newQty < 10:
                return False
            else:
                return {"price": price, "volume": newQty, "adj_ratio": adj_ratio}

    def isCloseLong(self, predictions, slice_data):
        if "CloseLong" not in self.__order:
            return False
        else:
            price, volume, adj_ratio = self.__order["CloseLong"]
            dict = {}
            dict.update({"price": price, "volume": volume, "adj_ratio": adj_ratio})
            return dict

    def getLongTriggerRatio(self):
        return self.__longTriggerRatio

    def getShortTriggerRatio(self):
        return self.__shortTriggerRatio

    def getLongCloseRatio(self):
        return self.__longCloseRatio

    def getLongCloseRiskRatio(self):
        return self.__longCloseRiskRatio

    def getShortCloseRatio(self):
        return self.__shortCloseRatio

    def getShortCloseRiskRatio(self):
        return self.__shortCloseRiskRatio

    def __get_qty_per_order(self, slice_data):
        date_str = dt.datetime.fromtimestamp(slice_data.timeStamp).strftime('%Y%m%d')
        value = self.__order_capacity["OrderCapacity"][date_str]
        return value

    # 通过对上一个净头寸和当前净头寸的变动进行辨别开平方向
    def __pre_processing(self, slice_data):
        if self.__MAX_QTY_PER_ORDER is None:
            self.__MAX_QTY_PER_ORDER = self.__get_qty_per_order(slice_data)

        self.__order = {}
        last_net_position = int(self.__pre_net_position)
        curr_net_position = int(self._positionMgr.get_net_position(self.__symbol))

        if curr_net_position < 0 <= last_net_position:
            self.__first_short_price = self._positionMgr.get_finished_orders(self.__symbol)[-1].setPrice

        elif last_net_position < 0 < curr_net_position:
            self.__first_long_price = self._positionMgr.get_finished_orders(self.__symbol)[-1].setPrice

        elif last_net_position == 0 and curr_net_position > 0:
            self.__first_long_price = self._positionMgr.get_finished_orders(self.__symbol)[-1].setPrice

        if last_net_position > curr_net_position:
            if self.__cum_qty_since_init_close_long is None:
                self.__cum_qty_since_init_close_long = (last_net_position - curr_net_position)
            else:
                self.__cum_qty_since_init_close_long += (last_net_position - curr_net_position)

        if curr_net_position > last_net_position:
            if self.__cum_qty_since_init_open_long is None:
                self.__cum_qty_since_init_open_long = (curr_net_position - last_net_position)
            else:
                self.__cum_qty_since_init_open_long += (curr_net_position - last_net_position)

    # 存放预测值
    def __store_predictions(self, predictions):
        self.__ask_predictions.append(predictions[1])
        self.__bid_predictions.append(predictions[0])

    # 第一次开仓
    def __initial_open(self, predictions, slice_data, side, adj_ratio):
        open_long_coef = 1.0003
        open_long_limit_coef = 1.01
        bid_delta = abs(self.__bid_predictions[-1] - self.__exponential_predict(np.array(self.__bid_predictions[-5:])))
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        if side == OrderSide.Buy:
            self.__last_long_prediction = predictions[0]
            self.__open_long_threshold = predictions[0]
            self.__tick_count_since_init_open_long = 0
            price = round(min(ask0 * open_long_coef, bid0 * open_long_limit_coef), 3)
            volume = self.__cal_dynamic_open_quantity(price, side, bid_delta, predictions[0], slice_data)
            self.__open_long_times += 1
            if volume is not None:
                self.__order.update({"OpenLong": (price, volume, adj_ratio)})

    def __get_position_percent_in_market(self, tick_num):
        if tick_num <= 5:
            ratio = 1.0
        elif tick_num <= 10:
            ratio = 0.5
        elif tick_num <= 20:
            ratio = 0.3
        elif tick_num <= 40:
            ratio = 0.2
        elif tick_num <= 100:
            ratio = 0.15
        elif tick_num <= 200:
            ratio = 0.10
        else:
            ratio = 0.05

        return ratio

    def __cal_dynamic_open_quantity(self, price, side, delta, prediction, slice_data):
        quantity = 0
        ema = self.__ema_volume()

        vol_min = 0.5
        vol_range = 1

        if side == OrderSide.Buy:
            vol_ratio = self.__cal_vol_ratio(delta, prediction, self.__init_open_long_threshold, self.__open_long_times)
            k1 = vol_min + vol_range * min(1, vol_ratio)
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), k1, 1.5)
            long_percent = self.__get_position_percent_in_market(self.__tick_count_since_init_open_long - 1)
            total_market_vol_since_open = sum(self.__volume_today[-self.__tick_count_since_init_open_long - 1:])
            if self.__cum_qty_since_init_open_long is None:
                limit_vol = total_market_vol_since_open * long_percent
            else:
                limit_vol = total_market_vol_since_open * long_percent - self.__cum_qty_since_init_open_long
            limit_vol = int(math.ceil(limit_vol / 10)) * 10
            quantity = min(self._positionMgr.get_buy_avail_qty(self.__symbol),
                           self._positionMgr.get_sell_avail_qty(self.__symbol),
                           ema * k, limit_vol)
        elif side == OrderSide.Sell:
            vol_ratio = self.__cal_vol_ratio(delta, prediction, self.__init_open_short_threshold,
                                             self.__open_short_times)
            k1 = vol_min + vol_range * min(1, vol_ratio)
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), k1, 1.5)

            quantity = min(self._positionMgr.get_buy_avail_qty(self.__symbol),
                           self._positionMgr.get_sell_avail_qty(self.__symbol),
                           ema * k)
        return int(quantity / 10) * 10

    # 计算下单量
    def __order_quantity(self, price, side, slice_data):
        volume = 0
        ema = self.__ema_volume()
        if side == OrderSide.Buy:
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)
            volume = min(self._positionMgr.get_buy_avail_qty(self.__symbol),
                         self._positionMgr.get_sell_avail_qty(self.__symbol),
                         k * ema)
        elif side == OrderSide.Sell:
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), 1.5)
            volume = min(self._positionMgr.get_buy_avail_qty(self.__symbol),
                         self._positionMgr.get_sell_avail_qty(self.__symbol),
                         k * ema)
        return int(volume / 10) * 10

    # 计算连续开仓下单量
    def __cal_multi_dynamic_open_quantity(self, side, price, prediction, delta, slice_data):
        volume = self.__cal_dynamic_open_quantity(price, side, delta, prediction, slice_data)
        ema = self.__ema_volume()

        if volume is not None:
            net_position = self._positionMgr.get_net_position(self.__symbol)
            vol_ratio = 20
            limit = ema * vol_ratio
            if abs(net_position) + volume > limit:
                volume = limit - abs(net_position)
                if volume <= 0:
                    return None
                else:
                    return int(volume / 10) * 10
            else:
                return volume
        else:
            return None

    def __ema_volume(self):
        alpha = 0.9
        ema = 0
        if self.__volume_today is None or len(self.__volume_today) == 0:
            return 10.0
        length = len(self.__volume_today)
        start = max(0, length - 50)
        ema = sum(self.__volume_today[start:length]) * 0.1
        value = math.ceil(ema / 10) * 10
        if value == 0:
            return 10.0
        else:
            return value + 10.0

    def __ema_volume_new(self):
        alpha = 0.9
        ema = 0
        if self.__volume_today is None or len(self.__volume_today) == 0:
            return 10.0
        length = len(self.__volume_today)
        start = max(0, length - 200)
        for i in range(start + 1, length):
            ema = self.__cal_ema(alpha, ema, self.__volume_today[i])
        value = math.ceil(ema / 10) * 10
        if value == 0:
            return 10.0
        else:
            return value + 10.0

    def __log_vol_ma_200(self):
        if self.__volume_today is None or len(self.__volume_today) == 0:
            return 0.0
        return np.mean(np.log(np.array(self.__volume_today[-200:]) + 10.))  # 注意可转债最小交易单位为10张，此处改为10。 股票最小单位为100股。

    # 处理平仓信号
    def __process_close_signal(self, predictions, slice_data, side):
        close_long_coef = 0.9997
        close_long_limited_coef = 0.995
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        pct_last_3_ticks = self.__bs_vwap_price_today[-1][1] / self.__bs_vwap_price_today[-3][1] - 1

        volume_ema = self.__ema_volume()
        net_position = self._positionMgr.get_net_position(self.__symbol)

        volume_close = min(abs(net_position), 2.5 * volume_ema)
        if side == OrderSide.Sell:
            if pct_last_3_ticks < -0.003:
                close_price = bid0 * (1 - 0.002)
            elif predictions[1] < self.__init_close_long_risk_threshold:
                close_price = max(bid0 * (close_long_coef - 0.0002), ask0 * close_long_limited_coef)
            elif self.__close_long_threshold is None:
                close_price = self.__close_price(predictions, slice_data)
            else:
                close_price = max(bid0 * close_long_coef, ask0 * close_long_limited_coef)
            if self.__tick_count_since_init_close_long is None:
                self.__tick_count_since_init_close_long = 0
            short_percent = self.__get_position_percent_in_market(self.__tick_count_since_init_close_long - 1)
            total_market_vol_since_close = sum(self.__volume_today[-self.__tick_count_since_init_close_long - 1:])
            if self.__cum_qty_since_init_close_long is None:
                limit_vol = short_percent * total_market_vol_since_close
            else:
                limit_vol = short_percent * total_market_vol_since_close - self.__cum_qty_since_init_close_long
            limit_vol = int(math.ceil(limit_vol / 10)) * 10
            volume = min(limit_vol, volume_close)
            self.__order.update({"CloseLong": (close_price, volume, None)})
            self.__close_long_threshold = predictions[1]
            self.__stop_loss_times = 0

    # 处理连续开仓信号
    def __process_multi_open(self, predictions, slice_data, side, adj_ratio):
        open_long_coef = 1.0003
        open_long_limit_coef = 1.01
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        bid_delta = abs(self.__bid_predictions[-1] - self.__exponential_predict(np.array(self.__bid_predictions[-5:])))

        if side == OrderSide.Buy:
            open_price = min(ask0 * open_long_coef, bid0 * open_long_limit_coef)
            volume = self.__cal_multi_dynamic_open_quantity(side, ask0, predictions[0], bid_delta, slice_data)
            if volume is not None:
                self.__order.update({"OpenLong": (open_price, volume, adj_ratio)})
            self.__open_long_threshold = predictions[0]
            self.__open_long_times += 1
            self.__stop_loss_times = 0

    # 计算平仓价格
    def __close_price(self, predictions, slice_data):
        ask = predictions[1]
        bid0 = slice_data.bidPrice[0]  # 买一价
        ask0 = slice_data.askPrice[0]  # 卖一价
        price = 0
        close_long_limited_coef = 0.995
        close_long_coef = 0.9997
        if self._positionMgr.is_position_positive(self.__symbol):
            if ask < self.__init_open_short_threshold:  # 触发了做空阈值，以更激进价格下单
                price = max(bid0 * (close_long_coef - 0.0002), ask0 * close_long_limited_coef)
            else:
                price = max(bid0, ask0 * close_long_limited_coef)
        return price

    # 计算平仓价格
    def __stop_loss_price(self, predictions, slice_data):
        ask = predictions[1]
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        price = 0
        close_long_coef = 0.9997
        if self.__stop_loss_times < 3:
            close_long_limited_coef = 0.995
        elif self.__stop_loss_times < 6:
            close_long_limited_coef = 0.99
        else:
            close_long_limited_coef = 0.98

        if self._positionMgr.is_position_positive(self.__symbol):
            if ask < self.__init_open_short_threshold:
                price = max(bid0 * (close_long_coef - 0.0002), ask0 * close_long_limited_coef)
            else:
                price = max(bid0 * close_long_coef, ask0 * close_long_limited_coef)
        return price

    def __process_stop_loss(self, side, predictions, slice_data):
        ema = self.__ema_volume()
        self.__stop_loss_times += 1
        net_position = self._positionMgr.get_net_position(self.__symbol)
        close_vol = min(abs(net_position), ema * 3)
        if side == OrderSide.Buy:
            price = self.__stop_loss_price(predictions, slice_data)
            self.__order.update({'CloseShort': (price, close_vol, None)})
        else:
            price = self.__stop_loss_price(predictions, slice_data)
            self.__order.update({'CloseLong': (price, close_vol, None)})

    # -----------------------------------------------------------------------------
    # some simple helper functions
    def __cal_vol_ratio(self, delta, prediction, base, times):
        return abs(prediction - base + 0.05) * abs(delta) / (0.05) / (times + 1)

    # 计算当前收益率
    def __cal_return(self, price):
        curr_return = 0
        if self._positionMgr.is_position_positive(self.__symbol):
            open_price = self.__first_long_price
            if open_price is not None and open_price != 0:
                curr_return = (price - open_price) / open_price * 1000
        elif self._positionMgr.is_position_negative(self.__symbol):
            open_price = self.__first_short_price
            if open_price is not None and open_price != 0:
                curr_return = (open_price - price) / open_price * 1000
        return curr_return

    def __cal_ema(self, alpha, ema, value):
        return alpha * ema + (1 - alpha) * value

    def __exponential_smoothing(self, alpha, s):
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

        return (a_double + b_double)

    # 计算开仓阈值
    def __cal_open_trigger(self):
        open_th = 0
        if self._positionMgr.is_position_negative(self.__symbol):
            open_short_threshold = self.__open_short_threshold
            if open_short_threshold is None:
                open_th = self.__init_open_short_threshold
            else:
                open_th = open_short_threshold
        if self._positionMgr.is_position_positive(self.__symbol):
            open_long_threshold = self.__open_long_threshold
            if open_long_threshold is None:
                open_th = self.__init_open_long_threshold
            else:
                open_th = open_long_threshold
        return open_th

    # 计算平仓阈值，NEW方法
    def __cal_close_trigger(self):
        close_th = 0
        if self._positionMgr.is_position_negative(self.__symbol):
            close_short_threshold = self.__close_short_threshold
            if close_short_threshold is None:
                close_th = self.__init_close_short_threshold
            else:
                close_th = close_short_threshold
            if close_th > self.__shortCloseRiskRatio:
                close_th = self.__shortCloseRiskRatio
        elif self._positionMgr.is_position_positive(self.__symbol):
            close_long_threshold = self.__close_long_threshold
            if close_long_threshold is None:
                close_th = self.__init_close_long_threshold
            else:
                close_th = close_long_threshold
            if close_th < self.__init_close_long_risk_threshold:
                close_th = self.__init_close_long_risk_threshold
        return close_th

    # -----------------------------------------------------------------------------
    def __process_tickData(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        tick_datetime = dt.datetime.fromtimestamp(tick_timestamp)

        if self.__last_tagInfo is not None and self.__last_tagInfo.time <= 113000000 and slice_data.time >= 130000000:
            self.__last_tagInfo = None
            self.__bid_predictions = []
            self.__ask_predictions = []
            self.__volume_today = []
            self.__amt_today = []
            self.__mid_price_today = []
            self.__bs_vwap_price_today = []
            self.__timestamp_today = []
            self.__bid0_price_today = []
            self.__ask0_price_today = []

        if not self.__volume_today:
            date_index = 0
            for i in range(len(self.__tickData)):
                if self.__tickData[i] is None:
                    continue
                if dt.datetime.fromtimestamp(self.__tickData[i]['TimeStamp'][0]).date() == tick_datetime.date():
                    date_index = i
                    break
            tick_index = 0
            for i in range(len(self.__tickData[date_index]["TimeStamp"])):
                if self.__tickData[date_index]["TimeStamp"][i] >= tick_timestamp:  # float type >=
                    tick_index = i  # index is first valid
                    break
            start_index = 0
            for i in range(len(self.__tickData[date_index]["TimeStamp"])):
                if slice_data.time < 120000000:
                    if dt.datetime.fromtimestamp(
                            self.__tickData[date_index]['TimeStamp'][i]).time() >= self.__start_time_morning:
                        start_index = i
                        break
                else:
                    if dt.datetime.fromtimestamp(
                            self.__tickData[date_index]['TimeStamp'][i]).time() >= self.__start_time_afternoon:
                        start_index = i
                        break
            for i in range(start_index, tick_index + 1):
                tick_data = self.__tickData[date_index]
                pre_acc_volume = tick_data["AccVolume"][max(0, i - 1)]
                cur_acc_volume = tick_data["AccVolume"][i]
                pre_acc_amt = tick_data["AccTurover"][max(0, i - 1)]
                cur_acc_amt = tick_data["AccTurover"][i]
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
                self.__amt_today.append(cur_acc_amt - pre_acc_amt)
                self.__mid_price_today.append((tick_data["AskP1"][i] + tick_data["BidP1"][i]) / 2)
                ask_p_array = np.array([tick_data['AskP' + str(x)][i] for x in range(1, 11)])
                ask_v_array = np.array([tick_data['AskV' + str(x)][i] for x in range(1, 11)])
                bid_p_array = np.array([tick_data['BidP' + str(x)][i] for x in range(1, 11)])
                bid_v_array = np.array([tick_data['BidV' + str(x)][i] for x in range(1, 11)])
                ask_vwap = (ask_p_array * ask_v_array).sum() / ask_v_array.sum()
                bid_vwap = (bid_p_array * bid_v_array).sum() / bid_v_array.sum()
                self.__bs_vwap_price_today.append([ask_vwap, bid_vwap])
                self.__timestamp_today.append(slice_data.timeStamp)
                self.__bid0_price_today.append(slice_data.bidPrice[0])
                self.__ask0_price_today.append(slice_data.askPrice[0])
        else:
            if self.__start_time_morning <= tick_datetime.time() < dt.time(11, 30, 0) \
                    or self.__start_time_afternoon <= tick_datetime.time() < dt.time(14, 57, 0):
                pre_acc_volume = self.__last_tagInfo.totalVolume
                cur_acc_volume = slice_data.totalVolume
                pre_acc_amt = self.__last_tagInfo.totalAmount
                cur_acc_amt = slice_data.totalAmount
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
                self.__amt_today.append(cur_acc_amt - pre_acc_amt)
                self.__mid_price_today.append((slice_data.bidPrice[0] + slice_data.askPrice[0]) / 2)
                ask_vwap = (np.array(slice_data.askPrice) * np.array(slice_data.askVolume)).sum() / sum(slice_data.askVolume)
                bid_vwap = (np.array(slice_data.bidPrice) * np.array(slice_data.bidVolume)).sum() / sum(slice_data.bidVolume)
                self.__bs_vwap_price_today.append([ask_vwap, bid_vwap])
                self.__timestamp_today.append(slice_data.timeStamp)
                self.__bid0_price_today.append(slice_data.bidPrice[0])
                self.__ask0_price_today.append(slice_data.askPrice[0])
        self.__last_tagInfo = slice_data

        if self.__trading_start_morning <= tick_datetime.time() < dt.time(11, 30,0) or \
                self.__trading_start_afternoon <= tick_datetime.time() < dt.time(14, 57, 0):
            return True
        else:
            return False

    # 以下为处理午盘平仓的逻辑
    # 判断时间是否在午盘平仓区间，返回boolean，若True，则可以在onNewTick中，直接返回，不再进行开平仓逻辑的处理
    def __is_close_time_morning(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        if self.__close_time_morning <= dt.datetime.fromtimestamp(tick_timestamp).time() <= dt.time(11, 30, 0):
            return True
        else:
            return False

    def __is_close_time_afternoon(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        if self.__close_time_afternoon <= dt.datetime.fromtimestamp(tick_timestamp).time() <= dt.time(14, 59, 59):
            return True
        else:
            return False

    # 若在午盘平仓区间，则处理头寸
    def __process_morning_close(self, symbol, slice_data, predictions):
        if self._positionMgr.is_position_closed(symbol):
            return
        netPosition = self._positionMgr.get_net_position(symbol)
        volLimit = abs(netPosition) / 6
        ema = self.__ema_volume()
        quantity = min(max(ema * 4, volLimit), abs(netPosition))

        positionQty = abs(int(quantity))

        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]
        close_long_limited_coef = 0.995
        isCloseAtEase = False
        if dt.datetime.fromtimestamp(slice_data.timeStamp).time() < self.__easy_close_time_morning:
            isCloseAtEase = True
        if netPosition > 0:
            if isCloseAtEase:
                if (predictions[0] > self.__init_open_long_threshold) or \
                        (self.__signal_sorted(self.__bid_predictions[-5:]) and predictions[0] > self.__init_open_long_threshold - 0.3):
                    price = max(round((ask0 + bid0) / 2, 3) - 0.01, bid0, ask0 * close_long_limited_coef)
                else:
                    price = max(ask0 - 0.5, bid0, ask0 * close_long_limited_coef)
            else:
                price = bid0
            self.__order.update({"CloseLong": (price, positionQty, None)})

    # 若在午盘平仓区间，则处理头寸
    def __process_afternoon_close(self, symbol, slice_data, predictions):
        if self._positionMgr.is_position_closed(symbol):
            return
        netPosition = self._positionMgr.get_net_position(symbol)
        volLimit = abs(netPosition) / 6
        ema = self.__ema_volume()
        quantity = min(max(ema * 4, volLimit), abs(netPosition))

        positionQty = abs(int(quantity))

        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]
        close_long_limited_coef = 0.995

        isCloseAtEase = False
        if dt.datetime.fromtimestamp(slice_data.timeStamp).time() < self.__easy_close_time_afternoon:
            isCloseAtEase = True
        if netPosition > 0:
            if isCloseAtEase:
                price = max(ask0 - 0.5, bid0, ask0 * close_long_limited_coef)
            else:
                price = bid0
            self.__order.update({"CloseLong": (price, positionQty, None)})

    def __process_price_limit_close(self, symbol, slice_data):
        if self._positionMgr.is_position_closed(symbol):
            return
        netPosition = self._positionMgr.get_net_position(symbol)
        volLimit = abs(netPosition) / 6
        ema = self.__ema_volume()
        quantity = min(max(ema * 4, volLimit), abs(netPosition))

        positionQty = abs(int(quantity))

        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]
        first_close_long_limited_coef = 0.995
        second_close_long_limited_coef = 0.99

        if netPosition > 0:
            if self.__LIMIT_STATUS == "FIRST_UP_LIMIT":
                price = max(bid0, ask0 - 0.01)

            elif self.__LIMIT_STATUS == "SECOND_UP_LIMIT":
                price = max(bid0, ask0 - 0.02)

            elif self.__LIMIT_STATUS == "FIRST_DOWN_LIMIT":
                price = max(bid0 - 0.01, ask0 * first_close_long_limited_coef)

            elif self.__LIMIT_STATUS == "SECOND_DOWN_LIMIT":
                price = max(bid0 - 0.01, ask0 * second_close_long_limited_coef)

            self.__order.update({"CloseLong": (price, positionQty, None)})

    def __checkCJZB(self, qty, side, slice_data):
        # 检查成交占比
        upperLimit = sum(self.__volume_today[-60:]) * 0.3
        tradedVolume = 0
        finishedOrders = self._positionMgr.get_finished_orders(self.__symbol)
        for order in finishedOrders:
            if order.lastUpdateTime.timestamp() >= slice_data.timeStamp - 180:
                if order.BSFlag == side:
                    tradedVolume += order.volume

        newQty = min(qty, upperLimit - tradedVolume)
        newQty = math.floor(newQty)
        return newQty

    def __checkCJJE(self, price, qty, side, slice_data):
        # 检查成交金额
        upperLimit = 1000000
        tradedAmount = 0
        finishedOrders = self._positionMgr.get_finished_orders(self.__symbol)
        for order in finishedOrders:
            if order.lastUpdateTime.timestamp() >= slice_data.timeStamp - 180:
                if order.BSFlag == side:
                    tradedAmount += order.accMount

        newQty = min(qty, (upperLimit - tradedAmount) / price)
        newQty = math.floor(newQty)
        return newQty
