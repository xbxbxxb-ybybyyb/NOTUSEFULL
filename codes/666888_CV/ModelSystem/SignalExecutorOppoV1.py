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


class SignalExecutorOppoV1(SignalExecutorBase):
    def __init__(self, positionMgr, riskMgr):
        SignalExecutorBase.__init__(self, positionMgr, riskMgr)
        # constants
        self.__OPEN_LONG_LAG = 0.05
        self.__OPEN_SHORT_LAG = -0.05
        self.__LONG_GAIN_GAP = 12
        self.__LONG_LOSS_GAP = 2
        self.__SHORT_GAIN_GAP = 12
        self.__SHORT_LOSS_GAP = 2
        self.__DELTA_CLOSE_SHORT_GAIN = 0.25
        self.__DELTA_CLOSE_SHORT_LOSS = 0.25
        self.__DELTA_CLOSE_LONG_GAIN = 0.25
        self.__DELTA_CLOSE_LONG_LOSS = 0.25
        self.__start_time_morning = dt.time(9, 30, 15)  # 早上开盘从该时刻起，才认为是正常的行情，开始接收早盘行情信号
        self.__start_time_afternoon = dt.time(13, 00, 15)  # 下午开盘从该时刻起，才认为是正常的行情，开始接收午盘行情信号
        self.__close_time_morning = dt.time(11, 29, 0)  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
        self.__easy_close_time_morning = dt.time(11, 29, 20)  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓
        self.__trading_start_morning = dt.time(9, 31, 15)  # 早上开盘从该时刻起，才认为信号是合理的，开始交易
        self.__trading_start_afternoon = dt.time(13, 1, 15)  # 下午开盘从该时刻起，才认为信号是合理的，开始交易
        self.__MAX_QTY_PER_ORDER = 10000  # 最大单笔委托数量（下入到SignalEvaluate后，只会被可买、可卖限制，不会被流动性限制。因为内部已经对流动性进行了处理）
        self.__STOP_LOSS_RATIO = -10  # 止损参数，单位千分之，-10代表1%止损（一定是负值，因直接跟return比较）

        self.__symbol = ""
        self.__longTriggerRatio = 0
        self.__shortTriggerRatio = 0
        self.__longCloseRatio = 0
        self.__longCloseRiskRatio = 0
        self.__shortCloseRatio = 0
        self.__shortCloseRiskRatio = 0

        self.__cum_open_predictions = None
        self.__cum_open_counts = None
        self.__cum_close_long_pred = None
        self.__cum_close_long_counts = None
        self.__cum_close_short_pred = None
        self.__cum_close_short_counts = None
        self.__tickData = None
        self.__volume_today = []  # 当天行情的volume
        self.__last_tagInfo = None  # 上一个tick的tagInfo

        self.__first_long_price = 0  # may have to adjust the assignment position
        self.__first_short_price = 0
        self.__last_long_prediction = 0
        self.__last_short_prediction = 0

        self.__order = {}  # have to reset the dict at the beginning of every tick, key = open/close side, value = (price, volume)
        self.__pre_net_position = 0  # the net position of last tick
        self.__order_capacity = None
        
    def set_json_param_before_start(self, param):
        self.__order_capacity = param

    def generateTriggerRatio(self, symbol, trigger_ratio_dict, tickData):
        if tickData is None:
            raise Exception("tickData in SignalExecutorOppo is None. Please load the tickData through SignalEvaluate.")
        self.__symbol = symbol
        self.__tickData = tickData
        if trigger_ratio_dict:
            self.__longTriggerRatio = trigger_ratio_dict['longTriggerRatio']
            self.__shortTriggerRatio = trigger_ratio_dict['shortTriggerRatio']
            self.__longCloseRiskRatio = trigger_ratio_dict['longRiskRatio']
            self.__shortCloseRiskRatio = trigger_ratio_dict['shortRiskRatio']
            self.__longCloseRatio = trigger_ratio_dict['longCloseRatio']
            self.__shortCloseRatio = trigger_ratio_dict['shortCloseRatio']

    def resetNewDay(self):
        self.__cum_open_predictions = None
        self.__cum_open_counts = None
        self.__cum_close_long_pred = None
        self.__cum_close_long_counts = None
        self.__cum_close_short_pred = None
        self.__cum_close_short_counts = None
        self.__last_tagInfo = None
        self.__volume_today = []
        self.__first_long_price = 0
        self.__first_short_price = 0
        self.__last_long_prediction = 0
        self.__last_short_prediction = 0
        self.__order = {}
        self.__pre_net_position = 0
        self.__MAX_QTY_PER_ORDER = None

    # onNewTick
    def updatePredictInfo(self, outSamplePredict, slice_data):
        # if there is non finished order? will it be called?
        valid = self.__process_tickData(slice_data)
        self.__pre_processing(slice_data)
        if not valid or self._positionMgr.hasNonFinished(self.__symbol):
            return

        # 11:29:00起，进行午盘平仓，且不发开仓单
        if self.__is_close_time_morning(slice_data):
            self.__process_morning_close(self.__symbol, slice_data)
            return

        if self._positionMgr.isPositionClosed(self.__symbol):
            # net position is 0
            if outSamplePredict[0] > self.__longTriggerRatio:
                self.__initial_open(outSamplePredict, slice_data, OrderSide.Buy)
            elif outSamplePredict[1] < self.__shortTriggerRatio:
                self.__initial_open(outSamplePredict, slice_data, OrderSide.Sell)
        else:
            bid0 = slice_data.bidPrice[0]
            ask0 = slice_data.askPrice[0]
            if self._positionMgr.isPositionNegative(self.__symbol):
                curr_return = self.__cal_return(bid0)
                if outSamplePredict[0] > self.__shortCloseRiskRatio:
                    self.__cum_close_short_pred = None
                    self.__cum_close_short_counts = None
                if outSamplePredict[1] > self.__longCloseRatio:
                    self.__cum_open_predictions = None
                    self.__cum_open_counts = None
                if outSamplePredict[0] > self.__cal_close_trigger(bid0):
                    self.__process_close_signal(outSamplePredict, slice_data, OrderSide.Buy)
                elif curr_return < self.__STOP_LOSS_RATIO:
                    self.__process_stop_loss(OrderSide.Buy, outSamplePredict, slice_data)
                elif outSamplePredict[1] < self.__cal_open_trigger():
                    self.__process_multi_open(outSamplePredict, slice_data, OrderSide.Sell)
            elif self._positionMgr.isPositionPositive(self.__symbol):
                curr_return = self.__cal_return(ask0)
                if outSamplePredict[1] < self.__longCloseRiskRatio:
                    self.__cum_close_long_pred = None
                    self.__cum_close_long_counts = None
                if outSamplePredict[0] < self.__shortCloseRatio:
                    self.__cum_open_predictions = None
                    self.__cum_open_counts = None
                if outSamplePredict[1] < self.__cal_close_trigger(ask0):
                    self.__process_close_signal(outSamplePredict, slice_data, OrderSide.Sell)
                elif curr_return < self.__STOP_LOSS_RATIO:
                    self.__process_stop_loss(OrderSide.Sell, outSamplePredict, slice_data)
                elif outSamplePredict[0] > self.__cal_open_trigger():
                    self.__process_multi_open(outSamplePredict, slice_data, OrderSide.Buy)
            else:
                self.__cum_open_predictions = 0
                self.__cum_open_counts = 0
        self.__pre_net_position = self._positionMgr.getNetPosition(self.__symbol)

    def isOpenLong(self, outSamplePredict, slice_data):
        if "OpenLong" not in self.__order:
            return False
        else:
            price, volume = self.__order["OpenLong"]
            dict = {}
            dict.update({"price": price, "volume": volume})
            return dict

    def isOpenShort(self, outSamplePredict, slice_data):
        if "OpenShort" not in self.__order:
            return False
        else:
            price, volume = self.__order["OpenShort"]
            dict = {}
            dict.update({"price": price, "volume": volume})
            return dict

    def isCloseLong(self, outSamplePredict, slice_data):
        if "CloseLong" not in self.__order:
            return False
        else:
            price, volume = self.__order["CloseLong"]
            dict = {}
            dict.update({"price": price, "volume": volume})
            return dict

    def isCloseShort(self, outSamplePredict, slice_data):
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
        
    def __get_qty_per_order(self, slice_data):
        date_str = dt.datetime.fromtimestamp(slice_data.timeStamp).strftime('%Y%m%d')
        value = self.__order_capacity['OrderCapacity'][date_str]
        return value

    # 通过对上一个净头寸和当前净头寸的变动进行辨别开平方向
    def __pre_processing(self, slice_data):
        if self.__MAX_QTY_PER_ORDER is None:
            self.__MAX_QTY_PER_ORDER = self.__get_qty_per_order(slice_data)
        
        self.__order = {}
        last_net_position = int(self.__pre_net_position)
        curr_net_position = int(self._positionMgr.getNetPosition(self.__symbol))

        # if last_net_position >= 0 and curr_net_position < 0:
        if curr_net_position < 0 <= last_net_position:
            self.__first_short_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice
            self.__cum_open_predictions = 2 * self.__last_short_prediction
            self.__cum_open_counts = 2
        # elif last_net_position < 0 and curr_net_position > 0:
        elif last_net_position < 0 < curr_net_position:
            self.__first_long_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice
            self.__cum_open_predictions = 2 * self.__last_long_prediction
            self.__cum_open_counts = 2
        elif last_net_position == 0 and curr_net_position > 0:
            self.__first_long_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice
            self.__cum_open_predictions = 2 * self.__last_long_prediction
            self.__cum_open_counts = 2

        # if last_net_position > 0 and curr_net_position < 0 or last_net_position < 0 and curr_net_position > 0 or curr_net_position == 0:
        if curr_net_position < 0 < last_net_position or last_net_position < 0 < curr_net_position or curr_net_position == 0:
            self.__cum_close_long_pred = None
            self.__cum_close_short_pred = None

    # 第一次开仓
    def __initial_open(self, outSamplePredict, slice_data, side):
        if side == OrderSide.Buy:
            price = slice_data.askPrice[0]
            self.__last_long_prediction = outSamplePredict[0]
            volume = self.__order_quantity(price, side, slice_data)
            if volume is not None:
                self.__order.update({"OpenLong": (price, volume)})
            # self.__cum_open_predictions = 2 * outSamplePredict[0]
            # self.__cum_open_counts = 2
        else:
            price = slice_data.bidPrice[0]
            self.__last_short_prediction = outSamplePredict[1]
            volume = self.__order_quantity(price, side, slice_data)
            if volume is not None:
                self.__order.update({"OpenShort": (price, volume)})
            # self.__cum_open_predictions = 2 * outSamplePredict[1]
            # self.__cum_open_counts = 2

    # 计算下单量
    def __order_quantity(self, price, side, slice_data):
        volume = 0
        ema = self.__ema_volume()
        if side == OrderSide.Buy:
            volume = min(self._positionMgr.getBuyAvailQty(self.__symbol),
                         self._positionMgr.getSellAvailQty(self.__symbol),
                         max(slice_data.askVolume[0], ema * 0.5),
                         self.__MAX_QTY_PER_ORDER, 1.5 * ema)
        elif side == OrderSide.Sell:
            volume = min(self._positionMgr.getBuyAvailQty(self.__symbol),
                         self._positionMgr.getSellAvailQty(self.__symbol),
                         max(slice_data.bidVolume[0], ema * 0.5),
                         self.__MAX_QTY_PER_ORDER, 1.5 * ema)
        return int(volume / 100) * 100

    # 计算连续开仓下单量
    def __multi_open_orderQty(self, side, price, slice_data):
        volume = self.__order_quantity(price, side, slice_data)
        ema = self.__ema_volume()
        if volume is not None:
            net_position = self._positionMgr.getNetPosition(self.__symbol)
            limit = min(10 * self.__MAX_QTY_PER_ORDER, max(4 * ema, 2.5 * self.__MAX_QTY_PER_ORDER))
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
        alpha = 0.95
        ema = 0
        if self.__volume_today is None or len(self.__volume_today) == 0:
            return ema
        length = len(self.__volume_today)
        start = max(0, length - 50)
        ema = self.__volume_today[start]
        for i in range(start + 1, length):
            ema = self.__cal_ema(alpha, ema, self.__volume_today[i])
        return ema + 100

    def __cal_ema(self, alpha, ema, value):
        return alpha * ema + (1 - alpha) * value

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

    # 计算开仓阈值
    def __cal_open_trigger(self):
        open_th = 0
        if self._positionMgr.isPositionNegative(self.__symbol):
            if self.__cum_open_predictions is None:
                open_th = self.__shortTriggerRatio
            else:
                open_th = self.__cum_open_predictions / self.__cum_open_counts + self.__OPEN_SHORT_LAG
        if self._positionMgr.isPositionPositive(self.__symbol):
            if self.__cum_open_predictions is None:
                open_th = self.__longTriggerRatio
            else:
                open_th = self.__cum_open_predictions / self.__cum_open_counts + self.__OPEN_LONG_LAG
        return open_th

    # 计算平仓阈值
    def __cal_close_trigger(self, price):
        close_th = 0
        curr_return = self.__cal_return(price)
        if self._positionMgr.isPositionNegative(self.__symbol):
            if self.__cum_close_short_pred is not None:
                close_th = self.__cum_close_short_pred / self.__cum_close_short_counts
            elif curr_return >= 0:
                close_th = self.__shortCloseRatio - min(curr_return,
                                                        self.__SHORT_GAIN_GAP) * self.__DELTA_CLOSE_SHORT_GAIN / self.__SHORT_GAIN_GAP
            else:
                close_th = self.__shortCloseRatio - min(-curr_return,
                                                        self.__SHORT_LOSS_GAP) * self.__DELTA_CLOSE_SHORT_LOSS / self.__SHORT_LOSS_GAP
        elif self._positionMgr.isPositionPositive(self.__symbol):
            if self.__cum_close_long_pred is not None:
                close_th = self.__cum_close_long_pred / self.__cum_close_long_counts
            elif curr_return >= 0:
                close_th = self.__longCloseRatio + min(curr_return,
                                                       self.__LONG_GAIN_GAP) * self.__DELTA_CLOSE_LONG_GAIN / self.__LONG_GAIN_GAP
            else:
                close_th = self.__longCloseRatio + min(-curr_return,
                                                       self.__LONG_LOSS_GAP) * self.__DELTA_CLOSE_LONG_LOSS / self.__LONG_LOSS_GAP
        return close_th

    # 处理平仓信号
    def __process_close_signal(self, outSamplePredict, slice_data, side):
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        volume_ema = self.__ema_volume()
        net_position = self._positionMgr.getNetPosition(self.__symbol)
        volume_close = min(abs(net_position), self.__MAX_QTY_PER_ORDER * 5, 2.5 * volume_ema)
        if side == OrderSide.Buy:
            if self.__cum_close_short_pred is None:
                self.__cum_close_short_pred = 2 * outSamplePredict[0]
                self.__cum_close_short_counts = 2
            else:
                self.__cum_close_short_pred += outSamplePredict[0]
                self.__cum_close_short_counts += 1
            if outSamplePredict[0] > self.__longTriggerRatio:
                volume = self.__order_quantity(ask0, OrderSide.Buy, slice_data)
                if volume is not None:
                    volume += abs(net_position)
                    volume = math.ceil(volume / 100) * 100
                    self.__last_long_prediction = outSamplePredict[0]
                    self.__order.update({"CloseShort": (ask0, volume)})
            else:
                # volume = math.ceil(volume_close / 100) * 100
                volume = volume_close
                price = self.__close_price(outSamplePredict, slice_data)
                self.__order.update({"CloseShort": (price, volume)})
        else:
            if self.__cum_close_long_pred is None:
                self.__cum_close_long_pred = 2 * outSamplePredict[1]
                self.__cum_close_long_counts = 2
            else:
                self.__cum_close_long_pred += outSamplePredict[1]
                self.__cum_close_long_counts += 1
            if outSamplePredict[1] < self.__shortTriggerRatio:
                volume = self.__order_quantity(bid0, OrderSide.Sell, slice_data)
                if volume is not None:
                    volume += abs(net_position)
                    volume = math.ceil(volume / 100) * 100
                    self.__last_short_prediction = outSamplePredict[1]
                    self.__order.update({"CloseLong": (bid0, volume)})
            else:
                # volume = math.ceil(volume_close / 100) * 100
                volume = volume_close
                price = self.__close_price(outSamplePredict, slice_data)
                self.__order.update({"CloseLong": (price, volume)})

    # 处理连续开仓信号
    def __process_multi_open(self, outSamplePredict, slice_data, side):
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]
        if side == OrderSide.Buy:
            if self.__cum_open_predictions is None:
                self.__cum_open_predictions = 2 * outSamplePredict[0]
                self.__cum_open_counts = 2
            else:
                self.__cum_open_predictions += outSamplePredict[0]
                self.__cum_open_counts += 1
            volume = self.__multi_open_orderQty(OrderSide.Buy, ask0, slice_data)
            if volume is not None:
                self.__order.update({"OpenLong": (ask0, volume)})
        else:  # OrderSide.Sell
            if self.__cum_open_predictions is None:
                self.__cum_open_predictions = 2 * outSamplePredict[1]
                self.__cum_open_counts = 2
            else:
                self.__cum_open_predictions += outSamplePredict[1]
                self.__cum_open_counts += 1
            volume = self.__multi_open_orderQty(OrderSide.Sell, bid0, slice_data)
            if volume is not None:
                self.__order.update({"OpenShort": (bid0, volume)})

    # 计算平仓价格
    def __close_price(self, outSamplePredict, slice_data):
        bid = outSamplePredict[0]
        ask = outSamplePredict[1]
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

    def __process_stop_loss(self, side, outSamplePredict, slice_data):
        ema = self.__ema_volume()
        net_position = self._positionMgr.getNetPosition(self.__symbol)
        close_vol = min(abs(net_position), self.__MAX_QTY_PER_ORDER * 5, ema * 2.5)
        if side == OrderSide.Buy:
            price = self.__close_price(outSamplePredict, slice_data)
            self.__order.update({'CloseShort': (price, close_vol)})
        else:
            price = self.__close_price(outSamplePredict, slice_data)
            self.__order.update({'CloseLong': (price, close_vol)})

    # onNewTick 数据预处理，从tickData获取当日的volume，以便计算ema成交量
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
        volLimit = netPosition / 6
        ema = self.__ema_volume()
        quantity = min(max(ema * 4, volLimit), netPosition)

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
                price = max(min(ask0 * 0.9998, ask0 - 0.01), ask0 - 0.02, bid0)
            else:
                price = bid0
            self.__order.update({"CloseLong": (price, positionQty)})
        else:
            if isCloseAtEase:
                price = min(max(bid0 * 1.0002, bid0 + 0.01), bid0 + 0.02, ask0)
            else:
                price = ask0
            self.__order.update({"CloseShort": (price, positionQty)})

# end of file
