"""
SignalExecutorOppo

Please note:
isOpenLong, isOpenShort, isCloseLong, isCloseShort can return 3 types of value:
1. bool: True, False. If True, then processSignal will be called.
2. None: False. ProcessSignal will not be called
3. dict: True. key = "price", "volume". ProcessSignal will be called and the returned value is the order value.

In this executor, the dict will be returned.

Input:
outSamplePredict[bid, ask]

by 011478
"""
from ModelSystem.SignalExecutorBase import SignalExecutorBase
from ModelSystem.Util.OrderSide import OrderSide
import datetime as dt
import math
import json
import os
import numpy as np


class SignalExecutorOppoV3(SignalExecutorBase):
    def __init__(self, positionMgr, riskMgr):
        SignalExecutorBase.__init__(self, positionMgr, riskMgr)
        # constants
        self.__start_time_morning = dt.time(9, 30, 15)  # 早上开盘从该时刻起，才认为是正常的行情，开始接收早盘行情信号
        self.__start_time_afternoon = dt.time(13, 00, 15)  # 下午开盘从该时刻起，才认为是正常的行情，开始接收午盘行情信号
        self.__trading_start_morning = dt.time(9, 31, 15)  # 早上开盘从该时刻起，才认为信号是合理的，开始交易
        self.__trading_start_afternoon = dt.time(13, 1, 15)  # 下午开盘从该时刻起，才认为信号是合理的，开始交易
        self.__close_time_morning = dt.time(11, 29, 0)  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
        self.__easy_close_time_morning = dt.time(11, 29, 30)  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓
        self.__MAX_QTY_PER_ORDER = 10000  # 最大单笔委托数量（下入到SignalEvaluate后，只会被可买、可卖限制，不会被流动性限制。因为内部已经对流动性进行了处理）
        self.__STOP_LOSS_RATIO = -10  # 止损参数，单位千分之，-10代表1%止损（一定是负值，因直接跟return比较）
        self.__symbol = ""
        self.__longTriggerRatio = 0
        self.__shortTriggerRatio = 0
        self.__longCloseRatio = 0
        self.__longCloseRiskRatio = 0
        self.__shortCloseRatio = 0
        self.__shortCloseRiskRatio = 0
        
        self.__tickData = None
        self.__volume_today = []  # 当天行情的volume
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

    def generateTriggerRatio(self, symbol, trigger_ratio_dict, tickData):
        if tickData is None:
            raise Exception("tickData in SignalExecutorOppo is None. Please load the tickData through SignalEvaluate.")
            
        self.__symbol = symbol
        self.__longTriggerRatio = 0.7
        self.__shortTriggerRatio = -0.7
        self.__longCloseRatio = -0.35
        self.__longCloseRiskRatio = -0.5249999999999999
        self.__shortCloseRatio = 0.35
        self.__shortCloseRiskRatio = 0.5249999999999999

        self.__tickData = tickData
        self.__MAX_QTY_PER_ORDER = 2770.6378941638477
        
    def setMaxVolumePerOrders(self, max_volume_per_orders):
        self.__max_volume_per_orders = max_volume_per_orders
    
    def setUpdatedPara(self, updated_para):
        self.__updated_para = updated_para
        
    def __updateParam(self, para):
        self.__longTriggerRatio = para['longMinTriggerRatio']
        self.__shortTriggerRatio = para['shortMinTriggerRatio']
        self.__longCloseRatio = para['closeRatio']
        self.__longCloseRiskRatio = para['riskRatio']
        self.__shortCloseRatio = -para['closeRatio']
        self.__shortCloseRiskRatio = -para['riskRatio']
           
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
        self.__first_long_price = 0
        self.__first_short_price = 0
        self.__last_long_prediction = 0
        self.__last_short_prediction = 0
        self.__order = {}
        self.__pre_net_position = 0

     # onNewTick
    def updatePredictInfo(self, predictions, slice_data):
        # if there is non finished order? will it be called?
        valid = self.__process_tickData(slice_data)
        self.__pre_processing()

        if not valid or self._positionMgr.hasNonFinished(self.__symbol):
            return

        # CAUTION!
        self.__store_predictions(predictions)
        # 11:29:00起，进行午盘平仓，且不发开仓单
        if self.__is_close_time_morning(slice_data):
            self.__process_morning_close(self.__symbol, slice_data)
            return

        if self._positionMgr.isPositionClosed(self.__symbol):
            # 初始化上笔开平仓阈值
            self.__close_long_threshold = None
            self.__close_short_threshold = None
            self.__open_long_threshold = None
            self.__open_short_threshold = None
            self.__open_long_times = 0
            self.__open_short_times = 0

            # net position is 0
            if predictions[0] > self.__longTriggerRatio:
                self.__initial_open(predictions, slice_data, OrderSide.Buy)
            elif predictions[1] < self.__shortTriggerRatio:
                self.__initial_open(predictions, slice_data, OrderSide.Sell)
        else:
            bid0 = slice_data.bidPrice[0]
            ask0 = slice_data.askPrice[0]
            if self._positionMgr.isPositionNegative(self.__symbol):
                curr_return = self.__cal_return(bid0)   
                           
                self.__open_long_threshold = None
                self.__close_long_threshold = None
                self.__open_long_times = 0

                if predictions[1] > self.__longCloseRatio:
                    self.__open_short_threshold = None
                if predictions[0] > self.__cal_close_trigger():
                    self.__process_close_signal(predictions, slice_data, OrderSide.Buy)
                elif curr_return < self.__STOP_LOSS_RATIO:
                    self.__process_stop_loss(OrderSide.Buy, predictions, slice_data)
                elif predictions[1] < self.__cal_open_trigger():
                    self.__process_multi_open(predictions, slice_data, OrderSide.Sell)
            elif self._positionMgr.isPositionPositive(self.__symbol):                                                                
                curr_return = self.__cal_return(ask0)           
                self.__open_short_threshold = None
                self.__close_short_threshold = None
                self.__open_short_times = 0

                if predictions[0] < self.__shortCloseRatio:
                    self.__open_long_threshold = None
                if predictions[1] < self.__cal_close_trigger():
                    self.__process_close_signal(predictions, slice_data, OrderSide.Sell)
                elif curr_return < self.__STOP_LOSS_RATIO:
                    self.__process_stop_loss(OrderSide.Sell, predictions, slice_data)
                elif predictions[0] > self.__cal_open_trigger():
                    self.__process_multi_open(predictions, slice_data, OrderSide.Buy)
                    
        self.__pre_net_position = self._positionMgr.getNetPosition(self.__symbol)

    def isOpenLong(self, predictions, slice_data):
        if "OpenLong" not in self.__order:
            return False
        else:
            price, volume = self.__order["OpenLong"]
            dict = {}
            dict.update({"price": price, "volume": volume})
            return dict

    def isOpenShort(self, predictions, slice_data):
        if "OpenShort" not in self.__order:
            return False
        else:
            price, volume = self.__order["OpenShort"]
            dict = {}
            dict.update({"price": price, "volume": volume})
            return dict

    def isCloseLong(self, predictions, slice_data):
        if "CloseLong" not in self.__order:
            return False
        else:
            price, volume = self.__order["CloseLong"]
            dict = {}
            dict.update({"price": price, "volume": volume})
            return dict

    def isCloseShort(self, predictions, slice_data):
        if "CloseShort" not in self.__order:
            return False
        else:
            price, volume = self.__order["CloseShort"]
            dict = {}
            dict.update({"price": price, "volume": volume})
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

    # 通过对上一个净头寸和当前净头寸的变动进行辨别开平方向
    def __pre_processing(self):
        self.__order = {}
        last_net_position = int(self.__pre_net_position)
        curr_net_position = int(self._positionMgr.getNetPosition(self.__symbol))

        if curr_net_position < 0 <= last_net_position:
            self.__first_short_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice

        elif last_net_position < 0 < curr_net_position:
            self.__first_long_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice

        elif last_net_position == 0 and curr_net_position > 0:
            self.__first_long_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice


    # 存放预测值
    def __store_predictions(self, predictions):
        self.__ask_predictions.append(predictions[1])
        self.__bid_predictions.append(predictions[0])

    # 第一次开仓
    def __initial_open(self, predictions, slice_data, side):
        open_long_coef = 1.0002
        open_short_coef = 0.9998
        bid_delta = abs(self.__bid_predictions[-1] - self.__exponential_predict(np.array(self.__bid_predictions[-5:])))
        ask_delta = abs(self.__ask_predictions[-1] - self.__exponential_predict(np.array(self.__ask_predictions[-5:])))

        if side == OrderSide.Buy:
            price = slice_data.askPrice[0]
            self.__last_long_prediction = predictions[0]
            self.__open_long_threshold = predictions[0]
            volume = self.__cal_dynamic_open_quantity(price, side, bid_delta, predictions[0], slice_data)
            self.__open_long_times += 1
            if volume is not None:
                price = round(price * open_long_coef, 2)
                self.__order.update({"OpenLong": (price, volume)})
        else:
            price = slice_data.bidPrice[0]
            self.__last_short_prediction = predictions[1]
            self.__open_short_threshold = predictions[1]
            volume = self.__cal_dynamic_open_quantity(price, side, ask_delta, predictions[1], slice_data)
            self.__open_short_times += 1
            if volume is not None:
                price = round(price * open_short_coef, 2)
                self.__order.update({"OpenShort": (price, volume)})
    
    def __cal_dynamic_open_quantity(self, price, side, delta, prediction, slice_data):
        quantity = 0
        open_vol = 0
        ema = self.__ema_volume()

        vol_min = self.__MAX_QTY_PER_ORDER
        vol_range = self.__MAX_QTY_PER_ORDER * 9

        if side == OrderSide.Buy:
            vol_ratio = self.__cal_vol_ratio(delta, prediction, self.__longTriggerRatio, self.__open_long_times)
            open_vol = vol_min + vol_range * min(1, vol_ratio)
            
            k1 = open_vol / ema
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), k1, 1.5)
                      
            quantity = min(self._positionMgr.getBuyAvailQty(self.__symbol), self._positionMgr.getSellAvailQty(self.__symbol),
                           ema * k)
        elif side == OrderSide.Sell:
            vol_ratio = self.__cal_vol_ratio(delta, prediction, self.__shortTriggerRatio, self.__open_short_times)
            open_vol = vol_min + vol_range * min(1, vol_ratio)
         
            k1 = open_vol / ema
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), k1, 1.5)
           
            quantity = min(self._positionMgr.getBuyAvailQty(self.__symbol), self._positionMgr.getSellAvailQty(self.__symbol),
                           ema * k)
        return int(quantity / 100) * 100

    # 计算下单量
    def __order_quantity(self, price, side, slice_data):
        volume = 0
        ema = self.__ema_volume()
        if side == OrderSide.Buy:
            k1 = self.__MAX_QTY_PER_ORDER / ema
            k2 = slice_data.askVolume[0] / ema
            k = min(max(k2, 0.5), k1, 1.5)
            volume = min(self._positionMgr.getBuyAvailQty(self.__symbol),
                         self._positionMgr.getSellAvailQty(self.__symbol),
                         k * ema)
        elif side == OrderSide.Sell:
            k1 = self.__MAX_QTY_PER_ORDER / ema
            k2 = slice_data.bidVolume[0] / ema
            k = min(max(k2, 0.5), k1, 1.5)
            volume = min(self._positionMgr.getBuyAvailQty(self.__symbol),
                         self._positionMgr.getSellAvailQty(self.__symbol),
                         k * ema)
        return int(volume / 100) * 100
        
    # 计算连续开仓下单量
    def __cal_multi_dynamic_open_quantity(self, side, price, prediction, delta, slice_data):
        volume = self.__cal_dynamic_open_quantity(price, side, delta, prediction, slice_data)
        ema = self.__ema_volume()
        if volume is not None:
            net_position = self._positionMgr.getNetPosition(self.__symbol)
            vol_ratio = min(5 * max(ema / self.__MAX_QTY_PER_ORDER, 1), 18)
            limit = self.__MAX_QTY_PER_ORDER * vol_ratio
            # limit = min(20 * self.__MAX_QTY_PER_ORDER, max(4 * ema, 5 * self.__MAX_QTY_PER_ORDER))
            if abs(net_position) + volume > limit:
                volume = limit - abs(net_position)
                if volume <= 0:
                    return None
                else:
                    return int(volume / 100) * 100
            else:
                return volume
        else:
            return None

    # ema成交量
    def __ema_volume(self):
        alpha = 0.9
        ema = 0
        if self.__volume_today is None or len(self.__volume_today) == 0:
            return 100
        length = len(self.__volume_today)
        start = max(0, length - 40)
        ema = self.__volume_today[start]
        for i in range(start + 1, length):
            ema = self.__cal_ema(alpha, ema, self.__volume_today[i])
        return ema + 100

    # 处理平仓信号
    def __process_close_signal(self, predictions, slice_data, side):
        close_long_coef = 0.9998
        close_short_coef = 1.0002
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        close_price = 0

        volume_ema = self.__ema_volume()
        net_position = self._positionMgr.getNetPosition(self.__symbol)
        volume_close = min(abs(net_position), self.__MAX_QTY_PER_ORDER * 10, 2.5 * volume_ema)
        if side == OrderSide.Buy:
            if predictions[0] > self.__longTriggerRatio:
                volume = self.__order_quantity(ask0, OrderSide.Buy, slice_data)
                self.__open_long_times += 1
                close_price = ask0 * close_short_coef
                if volume is not None:
                    volume += abs(net_position)
                    volume = math.ceil(volume / 100) * 100
                    self.__last_long_prediction = predictions[0]
                    self.__open_long_threshold = predictions[0]
                    self.__order.update({"CloseShort": (close_price, volume)})
            else:
                if predictions[0] > self.__shortCloseRiskRatio:
                    close_price = ask0 * close_short_coef
                elif self.__close_short_threshold is None:
                    close_price = self.__close_price(predictions, slice_data)
                else:
                    close_price = ask0
                volume = volume_close
                self.__order.update({"CloseShort": (close_price, volume)})
                self.__close_short_threshold = predictions[0]
        else:           
            if predictions[1] < self.__shortTriggerRatio:
                volume = self.__order_quantity(bid0, OrderSide.Sell, slice_data)
                self.__open_short_times += 1
                close_price = bid0 * close_long_coef
                if volume is not None:
                    volume += abs(net_position)
                    volume = math.ceil(volume / 100) * 100
                    self.__last_short_prediction = predictions[1]
                    self.__open_short_threshold = predictions[1]
                    self.__order.update({"CloseLong": (close_price, volume)})
            else:
                if predictions[1] < self.__longCloseRiskRatio:
                    close_price = bid0 * close_long_coef
                elif self.__close_long_threshold is None:
                    close_price = self.__close_price(predictions, slice_data)
                else:
                    close_price = bid0
                volume = volume_close
                self.__order.update({"CloseLong": (close_price, volume)})
                self.__close_long_threshold = predictions[1]

    # 处理连续开仓信号
    def __process_multi_open(self, predictions, slice_data, side):
        open_long_coef = 1.0002
        open_short_coef = 0.9998
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        bid_delta = abs(self.__bid_predictions[-1] - self.__exponential_predict(np.array(self.__bid_predictions[-5:])))
        ask_delta = abs(self.__ask_predictions[-1] - self.__exponential_predict(np.array(self.__ask_predictions[-5:])))
        volume = 0
        open_price = 0

        if side == OrderSide.Buy:            
            open_price = ask0 * open_long_coef
            volume = self.__cal_multi_dynamic_open_quantity(side, ask0, predictions[0], bid_delta, slice_data)
            if volume is not None:
                self.__order.update({"OpenLong": (open_price, volume)})
            self.__open_long_threshold = predictions[0]
            self.__open_long_times += 1
        else:  # OrderSide.Sell
            open_price = bid0 * open_short_coef
            volume = self.__cal_multi_dynamic_open_quantity(side, bid0, predictions[1], ask_delta, slice_data)
            if volume is not None:
                self.__order.update({"OpenShort": (open_price, volume)})
            self.__open_short_threshold = predictions[1]
            self.__open_short_times += 1

    # 计算平仓价格
    def __close_price(self, predictions, slice_data):
        bid = predictions[0]
        ask = predictions[1]
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        price = 0

        if self._positionMgr.isPositionPositive(self.__symbol):
            if ask < self.__shortTriggerRatio:
                price = bid0
            else:
                price = max(ask0 - 0.02, bid0)
        elif self._positionMgr.isPositionNegative(self.__symbol):
            if bid > self.__longTriggerRatio:
                price = ask0
            else:
                price = min(bid0 + 0.02, ask0)
        return price

    def __process_stop_loss(self, side, predictions, slice_data):
        ema = self.__ema_volume()
        net_position = self._positionMgr.getNetPosition(self.__symbol)
        close_vol = min(abs(net_position), ema * 3)
        if side == OrderSide.Buy:
            price = self.__close_price(predictions, slice_data)
            self.__order.update({'CloseShort': (price, close_vol)})
        else:
            price = self.__close_price(predictions, slice_data)
            self.__order.update({'CloseLong': (price, close_vol)})

    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    # some simple helper functions
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def __cal_vol_ratio(self, delta, prediction, base, times):
        return abs(prediction) * abs(delta) / (abs(base) + 0.1) / (times + 1)

    # 计算当前收益率
    def __cal_return(self, price):
        curr_return = 0
        if self._positionMgr.isPositionPositive(self.__symbol):
            open_price = self.__first_long_price
            if open_price is not None and open_price != 0:
                curr_return = (price - open_price) / open_price * 1000
        elif self._positionMgr.isPositionNegative(self.__symbol):
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
            s2[i] = alpha * s[i] + (1-alpha) * s2[i-1]
        return s2
    
    def __exponential_predict(self, predictions):
        if predictions.shape[0] == 0:
            return None
            
        if predictions.shape[0] == 1:
            return predictions[-1]
     
        alpha = 0.6
        s_single = self.__exponential_smoothing(alpha, predictions)
        s_double = self.__exponential_smoothing(alpha, s_single)

        a_double = 2 * s_single - s_double
        b_double = (alpha / (1 - alpha)) * (s_single - s_double)
                    
        return (a_double[-1] + b_double[-1])
        
    # 计算开仓阈值
    def __cal_open_trigger(self):
        open_th = 0
        if self._positionMgr.isPositionNegative(self.__symbol):
            open_short_threshold = self.__open_short_threshold
            if open_short_threshold is None:
                open_th = self.__shortTriggerRatio
            else:
                open_th = open_short_threshold               
        if self._positionMgr.isPositionPositive(self.__symbol):
            open_long_threshold = self.__open_long_threshold
            if open_long_threshold is None:
                open_th = self.__longTriggerRatio
            else:
                open_th = open_long_threshold              
        return open_th
        
    # 计算平仓阈值，NEW方法
    def __cal_close_trigger(self):
        close_th = 0
        if self._positionMgr.isPositionNegative(self.__symbol):
            close_short_threshold = self.__close_short_threshold
            if close_short_threshold is None:
                close_th = self.__shortCloseRatio
            else:
                close_th = close_short_threshold        
            if close_th > self.__shortCloseRiskRatio:
                close_th = self.__shortCloseRiskRatio
        elif self._positionMgr.isPositionPositive(self.__symbol):
            close_long_threshold = self.__close_long_threshold
            if close_long_threshold is None:
                close_th = self.__longCloseRatio
            else:
                 close_th = close_long_threshold 
            if close_th < self.__longCloseRiskRatio:
                close_th = self.__longCloseRiskRatio
        return close_th
    # XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
    def __process_tickData(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        tick_datetime = dt.datetime.fromtimestamp(tick_timestamp)

        if self.__last_tagInfo is not None and self.__last_tagInfo.time <= 113000000 and slice_data.time >= 130000000:
            self.__last_tagInfo = None
            self.__bid_predictions = []
            self.__ask_predictions = []
            self.__volume_today = []

        if not self.__volume_today:
            date_index = 0
            for i in range(len(self.__tickData)):
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
                    if dt.datetime.fromtimestamp(self.__tickData[date_index]['TimeStamp'][i]).time() >= self.__start_time_morning:
                        start_index = i
                        break
                else:
                    if dt.datetime.fromtimestamp(self.__tickData[date_index]['TimeStamp'][i]).time() >= self.__start_time_afternoon:
                        start_index = i
                        break
            for i in range(start_index, tick_index + 1):
                pre_acc_volume = self.__tickData[date_index]["AccVolume"][max(0, i - 1)]
                cur_acc_volume = self.__tickData[date_index]["AccVolume"][i]
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
        else:
            if self.__start_time_morning <= tick_datetime.time() < dt.time(11, 30, 0) or self.__start_time_afternoon <= tick_datetime.time() < dt.time(14, 57, 0):
                pre_acc_volume = self.__last_tagInfo.totalVolume
                cur_acc_volume = slice_data.totalVolume
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
        self.__last_tagInfo = slice_data

        if self.__trading_start_morning <= tick_datetime.time() < dt.time(11, 30, 0) or self.__trading_start_afternoon <= tick_datetime.time() < dt.time(14, 57, 0):
            return True
        else:
            return False

    # onNewTick 数据预处理，从tickData获取当日的volume，以便计算ema成交量
    def __process_tickData_2(self, slice_data):
        valid = True  # 标识符，如果行情没有在合理tick，比如9:30:00到9:30:15则会直接return至SignalEvaluate
        tick_timestamp = slice_data.timeStamp
        tick_datetime = dt.datetime.fromtimestamp(tick_timestamp)
        if len(self.__volume_today) == 0:
            date_index = 0
            for i in range(len(self.__tickData)):
                if dt.datetime.fromtimestamp(self.__tickData[i]["TimeStamp"][0]).date() == tick_datetime.date():
                    date_index = i
                    break
            tick_index = 0
            for i in range(len(self.__tickData[date_index]["TimeStamp"])):
                if self.__tickData[date_index]["TimeStamp"][i] >= tick_timestamp:  # float type >=
                    tick_index = i  # index is first valid
                    break
            start_index = 0
            for i in range(len(self.__tickData[date_index]["TimeStamp"])):
                if dt.datetime.fromtimestamp(
                        self.__tickData[date_index]["TimeStamp"][i]).time() >= self.__start_time_morning:
                    start_index = i
                    break
            for i in range(start_index, tick_index + 1):
                pre_acc_volume = self.__tickData[date_index]["AccVolume"][i - 1]
                cur_acc_volume = self.__tickData[date_index]["AccVolume"][i]
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
        if self.__last_tagInfo is not None:
            if self.__start_time_morning <= tick_datetime.time() < dt.time(11,30,0) or self.__start_time_afternoon <= tick_datetime.time() < dt.time(14, 57, 0):
                if dt.datetime.fromtimestamp(
                        self.__last_tagInfo.startTimeStamp).time() < self.__start_time_afternoon <= tick_datetime.time():
                    self.__volume_today.append(slice_data.volume)
                else:
                    pre_acc_volume = self.__last_tagInfo.startSliceData.totalVolume
                    cur_acc_volume = slice_data.totalVolume
                    self.__volume_today.append(cur_acc_volume - pre_acc_volume)
            else:
                valid = False
        self.__last_tagInfo = slice_data
        return valid

    # 以下为处理午盘平仓的逻辑
    # 判断时间是否在午盘平仓区间，返回boolean，若True，则可以在onNewTick中，直接返回，不再进行开平仓逻辑的处理
    def __is_close_time_morning(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        if self.__close_time_morning <= dt.datetime.fromtimestamp(tick_timestamp).time() <= dt.time(11, 30, 0):
            return True
        else:
            return False

    # 若在午盘平仓区间，则处理头寸
    def __process_morning_close(self, symbol, slice_data):
        if self._positionMgr.isPositionClosed(symbol):
            return
        netPosition = self._positionMgr.getNetPosition(symbol)
        volLimit = netPosition / 10
        ema = self.__ema_volume()
        quantity = min(max(ema * 3, volLimit), netPosition)

        # if netPosition > 0:
        #     positionQty = int(quantity / 100) * 100
        # else:
        #     positionQty = int(-quantity / 100) * 100
        positionQty = abs(int(quantity))

        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        isCloseAtEase = False
        if dt.datetime.fromtimestamp(slice_data.timeStamp).time() < self.__easy_close_time_morning:
            isCloseAtEase = True
        if netPosition > 0:
            if isCloseAtEase:
                price = max(ask0 * 0.9998, bid0)
            else:
                price = bid0
            self.__order.update({"CloseLong": (price, positionQty)})
        else:
            if isCloseAtEase:
                price = min(bid0 * 1.0002, ask0)
            else:
                price = ask0
            self.__order.update({"CloseShort": (price, positionQty)})

# end of file