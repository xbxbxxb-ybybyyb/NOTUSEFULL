"""
SignalExecutorEasy

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
import os
import math


class SignalExecutorSimple(SignalExecutorBase):
    def __init__(self, positionMgr, riskMgr, counterMgr):
        SignalExecutorBase.__init__(self, positionMgr, riskMgr, counterMgr)
        # constants
        self.__trading_start_morning = dt.time(9, 31, 15)  # 早上开盘从该时刻起，才认为信号是合理的，开始交易
        self.__trading_start_afternoon = dt.time(13, 1, 15)  # 下午开盘从该时刻起，才认为信号是合理的，开始交易
        self.__start_time_morning = dt.time(9, 30, 15)  # 早上开盘从该时刻起，才认为是正常的行情，开始接收早盘行情信号
        self.__start_time_afternoon = dt.time(13, 00, 15)  # 下午开盘从该时刻起，才认为是正常的行情，开始接收午盘行情信号
        self.__close_time_morning = dt.time(11, 29, 0)  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
        self.__easy_close_time_morning = dt.time(11, 29, 30)  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓
        self.__MAX_QTY_PER_ORDER = None  # 最大单笔委托数量（下入到SignalEvaluate后，只会被可买、可卖限制，不会被流动性限制。因为内部已经对流动性进行了处理）
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

        self.__init_open_long_threshold = None
        self.__init_close_long_threshold = None
        self.__init_close_long_risk_threshold = None
        self.__init_open_short_threshold = None
        self.__init_close_short_threshold = None
        self.__init_close_short_risk_threshold = None
        
        self.__first_long_price = 0  # may have to adjust the assignment position
        self.__first_short_price = 0

        self.__order = {}  # have to reset the dict at the beginning of every tick, key = open/close side, value = (price, volume)
        self.__pre_net_position = 0  # the net position of last tick
        self.__order_capacity = None
        self.__is_holo = False
        self.__next_slice_data = None  # reserved for holo use

        # print or remote_print
        self.__is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ
        
    def set_json_param_before_start(self, param):
        self.__order_capacity = param
        self.set_holo(param)

    def set_holo(self, param):
        if 'Holo' in param:
            value = (param['Holo'].lower() == 'true')
            self.__is_holo = value

    def check_holo_price(self, price, side, slice_data) -> float:
        """
        如果应用盘口还原，则该方法会去检查挂单价格
        :param price: 下单价格
        :param side: 下单方向 字符串 'buy', 'sell'
        :param slice_data: 当前收到的quote（非下一quote）
        :return: 调整过后的2位小数精度的价格
        """
        if not self.__is_holo:
            return price
        max_price = slice_data.maxPrice
        min_price = slice_data.minPrice
        bidP1 = slice_data.bidPrice[0]
        askP1 = slice_data.askPrice[0]
        askP10 = slice_data.askPrice[9]
        bidP10 = slice_data.bidPrice[9]
        # 尽管涨跌停的情况不会再收到行情，但还是做一下处理
        if bidP1 == 0:
            mid = askP1
        elif askP1 == 0:
            mid = bidP1
        else:
            mid = (askP1 + bidP1) / 2

        if askP10 == 0:
            askP10 = max_price
        elif bidP10 == 0:
            bidP10 = min_price

        if side == 'buy':
            if self.__next_slice_data.askPrice[0] == 0 or self.__next_slice_data.askPrice[0] > askP10 or price > askP10:
                # 下一盘口的卖一档价格为0
                # 或者下一盘口的卖一档价格 大于 当前盘口的第十档价格（类似实盘的下一盘口卖一档价格为0）
                # 或者下单价格 大于 当前盘口的第十档价格
                price = askP10 + 0.01  # 上述条件下，下单价格调整为第十档价格 + 0.01
                if price > mid * 1.01:  # 超过了中间价格的1%
                    price = math.floor(mid * 1.01 * 100) / 100.0  # 向下取2位小数
                    return round(price, 2)  # 用中间价的1%下单
                else:
                    return round(price, 2)  # 用第十档 + 0.01下单
            else:
                return round(price, 2)  # 用指定价格下单

        elif side == 'sell':
            if self.__next_slice_data.bidPrice[0] == 0 or self.__next_slice_data.bidPrice[0] < bidP10 or price < bidP10:
                # 下一盘口的买一价格为0
                # 或者下一盘口的买一档价格 小于 当前盘口的第十档价格（类似实盘的下一盘口买一档价格为0）
                # 或者下单价格 小于 当前盘口的第十档价格
                price = bidP10 - 0.01  # 上述条件下，下单价格调整为第十档价格 - 0.01
                if price < mid * 0.99:  # 超过了中间价格的1%
                    price = math.ceil(mid * 0.99 * 100) / 100.0  # 向上取2位小数
                    return round(price, 2)  # 用中间价的1%下单
                else:
                    return round(price, 2)  # 用第十档 - 0.01下单
            else:
                return round(price, 2)  # 用指定价格下单
                
    def generateTriggerRatio(self, symbol, trigger_ratio_dict, tickData):
        if tickData is None:
            raise Exception("tickData in SignalExecutor is None. Please load the tickData through SignalEvaluate.")
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
        self.__last_tagInfo = None
        self.__volume_today = []
        self.__first_long_price = 0
        self.__first_short_price = 0
        self.__order = {}
        self.__pre_net_position = 0
        self.__MAX_QTY_PER_ORDER = None

        self.__init_open_long_threshold = None
        self.__init_close_long_threshold = None
        self.__init_close_long_risk_threshold = None
        self.__init_open_short_threshold = None
        self.__init_close_short_threshold = None
        self.__init_close_short_risk_threshold = None

        self._counterMgr.reset()

    def __reset_default(self):
        self.__init_open_long_threshold = self.__longTriggerRatio
        self.__init_close_long_threshold = self.__longCloseRatio
        self.__init_close_long_risk_threshold = self.__longCloseRiskRatio
        self.__init_open_short_threshold = self.__shortTriggerRatio
        self.__init_close_short_threshold = self.__shortCloseRatio
        self.__init_close_short_risk_threshold = self.__shortCloseRiskRatio        
        
    # onNewTick
    def updatePredictInfo(self, outSamplePredict, slice_data):

        valid = self.__process_tickData(slice_data)

        self.__pre_processing(slice_data)
        
        if not valid or self._positionMgr.hasNonFinished(self.__symbol):
            return

        self.__reset_default()

        # 11:29:00起，进行午盘平仓，且不发开仓单
        if self.__is_close_time_morning(slice_data):
            self.__process_morning_close(self.__symbol, slice_data)
            return
        
        if self._positionMgr.isPositionClosed(self.__symbol):
            # net position is 0
            if outSamplePredict[0] > self.__init_open_long_threshold:
                my_slice_data = self.get_next_slice_data(slice_data)
                self.__initial_open(outSamplePredict, my_slice_data, OrderSide.Buy)
            elif outSamplePredict[1] < self.__init_open_short_threshold:
                my_slice_data = self.get_next_slice_data(slice_data)
                self.__initial_open(outSamplePredict, my_slice_data, OrderSide.Sell)
        else:
            my_slice_data = self.get_next_slice_data(slice_data)
            bid0 = my_slice_data.bidPrice[0]
            ask0 = my_slice_data.askPrice[0]

            if self._positionMgr.isPositionNegative(self.__symbol):
                curr_return = self.__cal_return(bid0)

                if outSamplePredict[0] > self.__init_close_short_threshold:
                    self.__process_close_signal(outSamplePredict, my_slice_data, OrderSide.Buy)
                elif curr_return < self.__STOP_LOSS_RATIO:
                    self.__process_stop_loss(OrderSide.Buy, outSamplePredict, my_slice_data)
                elif outSamplePredict[1] < self.__init_open_short_threshold:
                    self.__process_multi_open(outSamplePredict, my_slice_data, OrderSide.Sell)

            elif self._positionMgr.isPositionPositive(self.__symbol):
                curr_return = self.__cal_return(ask0)

                if outSamplePredict[1] < self.__init_close_long_threshold:
                    self.__process_close_signal(outSamplePredict, my_slice_data, OrderSide.Sell)
                elif curr_return < self.__STOP_LOSS_RATIO:
                    self.__process_stop_loss(OrderSide.Sell, outSamplePredict, my_slice_data)
                elif outSamplePredict[0] > self.__init_open_long_threshold:
                    self.__process_multi_open(outSamplePredict, my_slice_data, OrderSide.Buy)
           
        self.__pre_net_position = self._positionMgr.getNetPosition(self.__symbol)

    def get_next_slice_data(self, slice_data):
        if self.__is_holo:
            next_slice_data = self.__get_my_next_slice_data(slice_data)
            self.__next_slice_data = next_slice_data
            return next_slice_data
        else:
            return slice_data

    def __get_my_next_slice_data(self, slice_data):
        return self.next_slice_data_speed(slice_data)
                
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

    # 通过对上一个净头寸和当前净头寸的变动进行辨别开平方向, 计算curr_ret函数需要， 对应Java中updateOpenPriceAfterCompleteOrder函数
    def __pre_processing(self, slice_data):
        if self.__MAX_QTY_PER_ORDER is None:
            self.__MAX_QTY_PER_ORDER = self.__get_qty_per_order(slice_data)

        self.__order = {}
        last_net_position = int(self.__pre_net_position)
        curr_net_position = int(self._positionMgr.getNetPosition(self.__symbol))

        if curr_net_position < 0 <= last_net_position:
            self.__first_short_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice
        elif last_net_position < 100 <= curr_net_position:
            self.__first_long_price = self._positionMgr.getFinishedOrders(self.__symbol)[-1].setPrice

    # 第一次开仓
    def __initial_open(self, outSamplePredict, slice_data, side):
        open_long_coef = 1.0002
        open_short_coef = 0.9998

        if side == OrderSide.Buy:
            price = slice_data.askPrice[0]
            volume = self.__cal_dynamic_open_quantity(price, side, outSamplePredict[0], slice_data)
            if volume is not None:
                price = round(price * open_long_coef, 2)
                self.__order.update({"OpenLong": (price, volume)})
        else:
            price = slice_data.bidPrice[0]
            volume = self.__cal_dynamic_open_quantity(price, side, outSamplePredict[1], slice_data)
            if volume is not None:
                price = round(price * open_short_coef, 2)
                self.__order.update({"OpenShort": (price, volume)})

    def __cal_dynamic_open_quantity(self, price, side, prediction, slice_data):
        ema = self.__ema_volume()

        if side == OrderSide.Buy:
            quantity = min(self._positionMgr.getBuyAvailQty(self.__symbol), self._positionMgr.getSellAvailQty(self.__symbol),
                           max(slice_data.askVolume[0], 0.5 * ema), ema * 1.5)
        elif side == OrderSide.Sell:
            quantity = min(self._positionMgr.getBuyAvailQty(self.__symbol), self._positionMgr.getSellAvailQty(self.__symbol),
                           max(slice_data.bidVolume[0], 0.5 * ema), ema * 1.5)
        return round(quantity / 100) * 100

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
        return round(volume / 100) * 100

    # 计算连续开仓下单量
    def __cal_multi_dynamic_open_quantity(self, side, price, prediction, slice_data):
        volume = self.__cal_dynamic_open_quantity(price, side, prediction, slice_data)
        ema = self.__ema_volume()
        if volume is not None:
            net_position = self._positionMgr.getNetPosition(self.__symbol)
            limit = min(20 * self.__MAX_QTY_PER_ORDER, max(4 * ema, 5 * self.__MAX_QTY_PER_ORDER))
            if abs(net_position) + volume > limit:
                volume = limit - abs(net_position)
                if volume <= 0:
                    return None
                else:
                    return round(volume / 100) * 100
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

    # 处理平仓信号
    def __process_close_signal(self, outSamplePredict, slice_data, side):
        close_long_coef = 0.9998
        close_short_coef = 1.0002
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]

        volume_ema = self.__ema_volume()
        net_position = self._positionMgr.getNetPosition(self.__symbol)
        volume_close = min(abs(net_position), self.__MAX_QTY_PER_ORDER * 10, 2.5 * volume_ema)
        if side == OrderSide.Buy:
            if outSamplePredict[0] > self.__init_open_long_threshold:
            # 平仓且反向开多    
                volume = self.__order_quantity(ask0, OrderSide.Buy, slice_data)
                close_price = ask0 * close_short_coef
                if volume is not None:
                    volume += abs(net_position)
                    volume = int(volume)
                    self.__order.update({"CloseShort": (close_price, volume)})

            else:
                # 只平仓
                if outSamplePredict[0] > self.__init_close_short_risk_threshold:
                    close_price = ask0 * close_short_coef
                else:
                    close_price = ask0
                volume = int(volume_close)
                self.__order.update({"CloseShort": (close_price, volume)})

        else:
            if outSamplePredict[1] < self.__init_open_short_threshold:
                volume = self.__order_quantity(bid0, OrderSide.Sell, slice_data)
                close_price = bid0 * close_long_coef
                if volume is not None:
                    volume += abs(net_position)
                    volume = int(volume)
                    self.__order.update({"CloseLong": (close_price, volume)})

            else:
                if outSamplePredict[1] < self.__init_close_long_risk_threshold:
                    close_price = bid0 * close_long_coef
                else:
                    close_price = bid0
                volume = int(volume_close)
                self.__order.update({"CloseLong": (close_price, volume)})

    # 处理连续开仓信号
    def __process_multi_open(self, outSamplePredict, slice_data, side):
        open_long_coef = 1.0002
        open_short_coef = 0.9998
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]

        if side == OrderSide.Buy:
            open_price = ask0 * open_long_coef
            volume = self.__cal_multi_dynamic_open_quantity(side, ask0, outSamplePredict[0], slice_data)
            if volume is not None:
                self.__order.update({"OpenLong": (open_price, volume)})

        else:  # OrderSide.Sell
            open_price = bid0 * open_short_coef
            volume = self.__cal_multi_dynamic_open_quantity(side, bid0, outSamplePredict[1], slice_data)
            if volume is not None:
                self.__order.update({"OpenShort": (open_price, volume)})

    # 计算平仓价格
    def __close_price(self, outSamplePredict, slice_data):
        price = 0
        bid0 = slice_data.bidPrice[0]
        ask0 = slice_data.askPrice[0]

        if self._positionMgr.isPositionPositive(self.__symbol):    ### side.isSell，本身仓位为正，平仓Sell
            if outSamplePredict[1] < self.__init_open_short_threshold:
                price = bid0
            else:
                price = max(ask0 - 0.02, bid0)
        elif self._positionMgr.isPositionNegative(self.__symbol):  ### side.isBuy, 本身仓位为负，平仓Buy
            if outSamplePredict[0] > self.__init_open_long_threshold:
                price = ask0
            else:
                price = min(bid0 + 0.02, ask0)
        return price

    def __process_stop_loss(self, side, outSamplePredict, slice_data):
        ema = self.__ema_volume()
        net_position = self._positionMgr.getNetPosition(self.__symbol)
        close_vol = min(abs(net_position), self.__MAX_QTY_PER_ORDER * 5, ema * 2.5)
        close_vol = int(close_vol / 100) * 100
        if side == OrderSide.Buy:
            price = self.__close_price(outSamplePredict, slice_data)
            self.__order.update({'CloseShort': (price, close_vol)})
        else:
            price = self.__close_price(outSamplePredict, slice_data)
            self.__order.update({'CloseLong': (price, close_vol)})

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

    def __process_tickData(self, slice_data):
        tick_timestamp = slice_data.timeStamp
        tick_datetime = dt.datetime.fromtimestamp(tick_timestamp)

        if self.__last_tagInfo is not None and self.__last_tagInfo.time <= 113000000 and slice_data.time >= 130000000:
            self.__last_tagInfo = None
            self.__bid_predictions = []
            self.__ask_predictions = []
            self.__volume_today = []
            self.__amt_today = []

        if not self.__volume_today:
            date_index = 0
            for i in range(len(self.__tickData)):
                if self.__tickData[i] is None:
                    continue
                if dt.datetime.fromtimestamp(self.__tickData[i]['Timestamp'][0]).date() == tick_datetime.date():
                    date_index = i
                    break
            tick_index = 0
            for i in range(len(self.__tickData[date_index]["Timestamp"])):
                if self.__tickData[date_index]["Timestamp"][i] >= tick_timestamp:  # float type >=
                    tick_index = i  # index is first valid
                    break
            start_index = 0
            for i in range(len(self.__tickData[date_index]["Timestamp"])):
                if slice_data.time < 120000000:
                    if dt.datetime.fromtimestamp(
                            self.__tickData[date_index]['Timestamp'][i]).time() >= self.__start_time_morning:
                        start_index = i
                        break
                else:
                    if dt.datetime.fromtimestamp(
                            self.__tickData[date_index]['Timestamp'][i]).time() >= self.__start_time_afternoon:
                        start_index = i
                        break
            for i in range(start_index, tick_index + 1):
                pre_acc_volume = self.__tickData[date_index]["TotalVolume"][max(0, i - 1)]
                cur_acc_volume = self.__tickData[date_index]["TotalVolume"][i]
                pre_acc_amt = self.__tickData[date_index]["TotalAmount"][max(0, i - 1)]
                cur_acc_amt = self.__tickData[date_index]["TotalAmount"][i]
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
                self.__amt_today.append(cur_acc_amt - pre_acc_amt)
        else:
            if self.__start_time_morning <= tick_datetime.time() < dt.time(11, 30,
                                                                           0) or self.__start_time_afternoon <= tick_datetime.time() < dt.time(
                    14, 57, 0):
                pre_acc_volume = self.__last_tagInfo.totalVolume
                cur_acc_volume = slice_data.totalVolume
                pre_acc_amt = self.__last_tagInfo.totalAmount
                cur_acc_amt = slice_data.totalAmount
                self.__volume_today.append(cur_acc_volume - pre_acc_volume)
                self.__amt_today.append(cur_acc_amt - pre_acc_amt)
        self.__last_tagInfo = slice_data

        if self.__trading_start_morning <= tick_datetime.time() < dt.time(11, 30,
                                                                          0) or self.__trading_start_afternoon <= tick_datetime.time() < dt.time(
                14, 57, 0):
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
        volLimit = abs(netPosition) / 5
        ema = self.__ema_volume()
        quantity = min(max(ema * 5, volLimit), abs(netPosition))

        positionQty = int(quantity / 100) * 100

        ask0 = slice_data.askPrice[0]
        bid0 = slice_data.bidPrice[0]

        isCloseAtEase = False
        if dt.datetime.fromtimestamp(slice_data.timeStamp).time() < self.__easy_close_time_morning:
            isCloseAtEase = True
        if netPosition > 0:
            if isCloseAtEase:
                price = max(ask0 - 0.02, bid0)
            else:
                price = bid0
            self.__order.update({"CloseLong": (price, positionQty)})
        elif netPosition < 0:
            if isCloseAtEase:
                price = min(bid0 + 0.02, ask0)
            else:
                price = ask0
            self.__order.update({"CloseShort": (price, positionQty)})
