import datetime as dt
import sys
import importlib
from enum import Enum
import math
from typing import Tuple, Dict
from Manager.PositionManager import PositionManager
from Manager.OutputManager import OutputManager
from Manager.RiskManager import RiskManager
from Utils.OrderSide import OrderSide
from ExchangeHouse.ExchangeHouse import ExchangeHouse
from ExchangeHouse.ExchangeOrder import ExchangeOrder
from ExchangeHouse.Data.Data import Data
from ExchangeHouse.Order import Order
from Utils.SimpleSignalHandler import *
from Utils.ExcelWriter import OutputSpreadSheet
from Manager.InputManager import Input


class SignalEvaluate:
    def __init__(self, inputs: 'Input', signal_trigger_pairs: List[Tuple[pd.DataFrame, Dict[str, float]]]):
        # 定义一些常量
        mock_trade_para = inputs.mock_trade_para
        self.__STOP_LOSS = abs(mock_trade_para["maxLose"])  # 止损线参数（不考虑手续费）
        self.__COST_RATE = 0.0001  # 手续费
        self.__NOON = 120000000  # 12:00:00
        self.__MARKET_CLOSE = 150000000  # 14:55:00

        self.__symbol = inputs.symbol
        self.__short_symbol = self.__symbol[: -3]
        self.__output_path = inputs.output_path_dir

        self.__tick = inputs.tick
        self.__transaction = inputs.transaction
        self.__data_dict = inputs.tick_dict
        self.__signal_trigger_paris: List[Tuple[pd.DataFrame, Dict[str, float]]] = signal_trigger_pairs
        for signal_data, _ in self.__signal_trigger_paris:
            if signal_data.columns[0] != 'Timestamp':
                raise Exception('The first column is not Timestamp!')
            elif len(signal_data.columns) != 3:
                raise Exception('There are NOT three columns in the data frame!')

        self.__executorStr = inputs.executor_str

        self.__outputMgr = OutputManager(self.__COST_RATE, True)
        self.__positionManager = PositionManager()
        self.__riskMgr = RiskManager(self.__STOP_LOSS)

        self.__exchangeHouse = ExchangeHouse(Data(self.__tick, self.__transaction))
        self.__modules = importlib.import_module('ModelSystem.' + inputs.executor_str)  # 通过String来生成的Executor的实例，先import
        self.__signalExecutor = getattr(self.__modules, inputs.executor_str)(self.__positionManager, self.__riskMgr)
        self.__signalExecutor.set_data_dict(self.__data_dict)

        self.__START_OPEN_TIME = mock_trade_para["start_open_time"]
        self.__LAST_OPEN_TIME = mock_trade_para["last_open_time"]  # 从该时刻起，禁止开仓。 若要赋值，须为dt.time(9, 45, 0)格式
        self.__initQty = mock_trade_para["initQty"]  # 初始额度
        self.__maxExposure = mock_trade_para["maxExposure"]  # 单边最大暴露金额(会动态调整）
        self.__maxTurnoverPerOrder = mock_trade_para["maxTurnoverPerOrder"]  # 每笔最大委托金额
        self.__maxRatePerOrder = mock_trade_para["maxRatePerOrder"]  # 每笔最大委托占比
        self.__openWithdrawSeconds = mock_trade_para["openWithdrawSeconds"]  # 开仓单驱动时间
        self.__closeWithdrawSeconds = mock_trade_para["closeWithdrawSeconds"]  # 平仓单驱动时间，建议始终设为3
        self.__buyLevel = mock_trade_para["buyLevel"]  # 1-based index, not 0-based
        self.__sellLevel = mock_trade_para["sellLevel"]  # 1-based index, not 0-based
        self.__buyDeviation = mock_trade_para["buyDeviation"]
        self.__sellDeviation = mock_trade_para["sellDeviation"]
        self.__MIN_ORDER_QTY = mock_trade_para["MIN_ORDER_QTY"]
        self.__initAmount = None

        self.__preTagInfo = {}
        self.__pre_net_position = {}
        self.__orderInfo = {}  # record the order info for each sent order: orderNo, isOpen
        self.__exePriceQty = {}  # the dictionary (key = price, volume) (may be) returned in the signal executor
        self.__noonRange = {}  # the noon range is not a constant value. It may vary.

        self.__funStr = None
        self.__predictions = []
        self.__order_capacity = inputs.json_param

    def evaluate(self, show=None):
        self.__signalExecutor.set_json_param_before_start(self.__order_capacity)
        combine_trading_order = self.run_backtest(show)
        self.trading_evaluate(combine_trading_order, False)
        detailed_orders = combine_trading_order.get("detailedOrders")
        combine_trading_order.pop("detailedOrders", None)
        if show is not None:
            output_path = self.__output_path + 'result_' + show + '.xls'
            OutputSpreadSheet(detailed_orders, combine_trading_order, output_path, self.__funStr)

    def run_backtest(self, show):
        if show is None:
            self.__outputMgr = OutputManager(self.__COST_RATE, True)
        else:
            self.__outputMgr = OutputManager(self.__COST_RATE, False)
        for signals, trigger_dict in self.__signal_trigger_paris:
            self.__reset_init_amount(signals)
            self.__signalExecutor.generateTriggerRatio(self.__symbol, trigger_dict, self.__tick)
            for index, row in signals.iterrows():
                timestamp = row[0]
                slice_data = self.__data_dict.get(timestamp)
                if slice_data is not None:
                    predictions = [row[1], row[2]]
                    self.__predictions.append(predictions)
                    self.__set_noon_range(self.__symbol, slice_data)
                    if self.__is_new_day(self.__symbol, slice_data.timeStamp):
                        self.__coming_new_day(self.__symbol)
                    self.__make_order(self.__symbol, slice_data)  # 撮合上一个tick的订单（相邻2个tick的时间差不是固定的）
                    if self.__valid_slice_data(slice_data):
                        if self.__valid_trading_time(slice_data.time):
                            self.__mock_trading(self.__symbol, predictions, slice_data)
                        else:
                            self.__process_market_close(self.__symbol, slice_data)
                    self.__preTagInfo.update({self.__symbol: slice_data})
        return self.__return_tradings(self.__symbol)

    @staticmethod
    def __valid_slice_data(slice_data):
        if slice_data.bidPrice[0] <= 1 or slice_data.askPrice[0] <= 1:
            return False
        return True

    def __mock_trading(self, symbol, predictions, slice_data):
        self.__riskMgr.checkStopLoss(symbol, slice_data)
        # check non finished close order status
        if self.__positionManager.has_non_finished(symbol):
            if self.__is_order_valid(symbol, slice_data) and \
                    not self.__riskMgr.isStopLoss(symbol) and not self.__riskMgr.isInDanger(symbol):
                # drive the non-finished order and return to the next predict slice directly
                self.__on_new_tick(predictions, slice_data)
                return
            else:
                self.__drive_invalid_nonfinished_order(symbol)
        # do mock trading
        self.__on_new_tick(predictions, slice_data)
        self.__on_predict_updated(symbol, predictions, slice_data)

    #  判断这笔平仓订单是否在一档盘口及以内：如果订单inValid，则return False，需要撤单；如果订单Valid，则return True，不需要撤单
    def __is_order_valid(self, symbol, slice_data):
        exchange_order = self.__positionManager.get_non_finished_order(symbol)
        price = exchange_order.setPrice
        ask1 = slice_data.askPrice[0]
        bid1 = slice_data.bidPrice[0]
        if self.__get_order_side(exchange_order.BSFlag) == OrderSide.Sell and price > ask1:
            return False
        elif self.__get_order_side(exchange_order.BSFlag) == OrderSide.Buy and price < bid1:
            return False
        else:
            return True

    def __drive_invalid_nonfinished_order(self, symbol):
        exchange_order = self.__positionManager.get_non_finished_order(symbol)
        exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
        self.__order_finished(exchange_order)

    # this method will now be called as every tick comes, to update tick info
    def __on_new_tick(self, predictions, slice_data):
        self.__signalExecutor.updatePredictInfo(predictions, slice_data)

    def __on_predict_updated(self, symbol, predictions, slice_data):
        if self.__positionManager.is_position_closed(symbol):
            self.__outputMgr.registerOutput(symbol, slice_data.timeStamp)  # 平仓状态，outputMgr负责生成order统计
            if self.__is_open_long(symbol, predictions, slice_data):
                self.__process_open_signal(symbol, OrderSide.Buy, slice_data)
        elif self.__positionManager.is_position_positive(symbol):
            if self.__is_close_long(symbol, predictions, slice_data) or \
                    self.__riskMgr.isStopLoss(symbol) or self.__riskMgr.isInDanger(symbol):
                self.__process_close_signal(symbol, OrderSide.Sell, slice_data)
            elif self.__is_open_long(symbol, predictions, slice_data):
                self.__process_open_signal(symbol, OrderSide.Buy, slice_data)

    def __process_open_signal(self, symbol, side, slice_data):
        # if self.__calc_holding_ret(slice_data) > 0.01:
        #     self.__maxExposure *= 2
        price = self.__cal_price(symbol, side, True, slice_data)
        quantity = self.__cal_qty(symbol, price, slice_data)
        if quantity <= 0:
            return
        elif quantity < self.__MIN_ORDER_QTY:
            return
        if price <= 1:
            return
        self.__place_order(symbol, side, price, quantity, True, slice_data.timeStamp)

    def __process_close_signal(self, symbol, side, slice_data):
        price = self.__cal_price(symbol, side, False, slice_data)
        quantity = self.__cal_close_qty(symbol, price)
        if quantity <= 0 or price <= 1:
            return
        self.__place_order(symbol, side, price, quantity, False, slice_data.timeStamp)

    def __cal_price(self, symbol, side, is_open, slice_data):
        if is_open:  # process open signal
            price_level = self.__buyLevel
            deviation = self.__buyDeviation
        else:  # process close signal
            price_level = self.__sellLevel
            deviation = self.__sellDeviation
        if price_level > 0:
            price_list = slice_data.askPrice
        else:
            price_list = slice_data.bidPrice
        price = price_list[abs(price_level) - 1]

        # use the price given in the signal executor
        if symbol in self.__exePriceQty and "price" in self.__exePriceQty.get(symbol):
            # 指定下单价格
            price = self.__exePriceQty.get(symbol).get("price")
            if price < slice_data.minPrice or price > slice_data.maxPrice:
                price = slice_data.lastPrice
        elif not self.__riskMgr.isStopLoss(symbol) and not self.__riskMgr.isInDanger(symbol):
            # mostly deprecated
            if price < slice_data.minPrice or price > slice_data.maxPrice:
                price = slice_data.lastPrice
            price += deviation
            if price > slice_data.maxPrice:
                price = slice_data.maxPrice
            elif price < slice_data.minPrice:
                price = slice_data.minPrice
        else:  # stop loss in risk manager or price reaches high/low limits
            if side == OrderSide.Buy:
                ask = slice_data.askPrice[0]
                price = slice_data.maxPrice if ask == 0 else ask
            else:
                bid = slice_data.bidPrice[0]
                price = slice_data.minPrice if bid == 0 else bid
        return round(price, 3)

    def __cal_qty(self, symbol, price, slice_data):
        liquid_qty = sys.maxsize
        if symbol in self.__exePriceQty and "volume" in self.__exePriceQty.get(symbol):
            if self.__maxExposure is not None:
                liquid_qty = self.__maxExposure / price

                # if "adj_ratio" in self.__exePriceQty.get(symbol):
                #     adj_ratio = self.__exePriceQty.get(symbol).get("adj_ratio")
                #     if adj_ratio is not None:
                #         liquid_qty *= adj_ratio
                #
                # holding_ret = self.__calc_holding_ret(slice_data)
                # if holding_ret > 0.005:
                #     liquid_qty *= 2
                # elif holding_ret < -0.005:
                #     liquid_qty *= 1/2
            else:
                liquid_qty = sys.maxsize
            avail_space = int(liquid_qty - abs(self.__positionManager.get_net_position(symbol)))
            volume = self.__exePriceQty.get(symbol).get("volume")
            quantity = min(avail_space, volume, self.__maxTurnoverPerOrder / price,
                           self.__positionManager.get_buy_avail_qty(symbol),
                           self.__positionManager.get_sell_avail_qty(symbol))
        else:
            if self.__maxExposure is not None:
                liquid_qty = min(liquid_qty, self.__maxExposure / price)
            avail_space = int(liquid_qty - abs(self.__positionManager.get_net_position(symbol)))
            quantity = min(avail_space, self.__maxTurnoverPerOrder / price,
                           self.__positionManager.get_initial_qty(symbol) * self.__maxRatePerOrder,
                           self.__positionManager.get_buy_avail_qty(symbol),
                           self.__positionManager.get_sell_avail_qty(symbol))
        return int(math.floor(quantity / 10) * 10)

    def __cal_close_qty(self, symbol, price):
        if symbol in self.__exePriceQty and "volume" in self.__exePriceQty.get(symbol):
            volume = int(self.__exePriceQty.get(symbol).get("volume"))
            volume = min(volume, int(self.__maxTurnoverPerOrder / price))
            if not self.__riskMgr.isInDanger(symbol):
                return volume
        net_position = abs(self.__positionManager.get_net_position(symbol))
        return min(net_position, int(self.__maxTurnoverPerOrder / price))

    def __place_order(self, symbol, side, price, quantity, is_open, timestamp):
        date_time = dt.datetime.fromtimestamp(timestamp)
        # 若在禁止开仓时刻之后，且为开仓单，则不再开仓。平仓单不受影响
        if (date_time.time() < self.__START_OPEN_TIME or date_time.time() >= self.__LAST_OPEN_TIME) and is_open:
            return
        if side == OrderSide.Buy:
            side_str = 'B'
        else:
            side_str = 'S'
        order = Order(symbol, None, price, quantity, side_str, date_time)
        order_number = self.__exchangeHouse.send(order)
        self.__orderInfo.update({symbol: OrderInfo(order_number, is_open)})

    def __make_order(self, symbol, slice_data):
        if symbol not in self.__orderInfo or self.__orderInfo.get(symbol) is None:
            return
        order_info = self.__orderInfo.get(symbol)
        order_number = order_info.orderNo
        if order_number is None:
            self.__orderInfo.pop(symbol, None)
            return

        is_open = order_info.isOpen
        curr_timestamp = slice_data.timeStamp
        exchange_order = self.__exchangeHouse.drive(order_number, self.__get_drive_time(symbol, is_open, curr_timestamp))
        if exchange_order.orderNumber is None or exchange_order is None:
            self.__orderInfo.pop(symbol, None)
            return

        # 开仓单必撤，平仓单需要在下一个Tick（当前）检查盘口
        exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
        self.__order_finished(exchange_order)

    def __is_new_day(self, symbol, curr_timestamp):
        flag = False
        if len(self.__preTagInfo) == 0 or symbol not in self.__preTagInfo:
            flag = True
        elif dt.datetime.fromtimestamp(curr_timestamp).date() != dt.datetime.fromtimestamp(
                self.__preTagInfo.get(symbol).timeStamp).date():
            flag = True
        return flag

    def __coming_new_day(self, symbol):
        self.__signalExecutor.resetNewDay()
        self.__riskMgr.resetNewDay()
        self.__positionManager.init_position(symbol, self.__initQty)
        self.__pre_net_position.update({symbol: 0})
        self.__outputMgr.clearNonClosed(symbol)
        self.__outputMgr.addOneDay(symbol)
        self.__orderInfo.pop(symbol, None)

    @staticmethod
    def __split_reversed_cum_qty(last_net_position, net_position):
        if last_net_position * net_position < 0:
            return abs(last_net_position), abs(net_position)
        else:
            return None

    def __order_finished(self, exchange_order):
        code = exchange_order.code
        self.__orderInfo.pop(code, None)
        self.__positionManager.update_position(exchange_order)
        net_position = self.__positionManager.get_net_position(code)
        self.__outputMgr.addOrder(exchange_order, self.__split_reversed_cum_qty(self.__pre_net_position.get(code), net_position))
        self.__riskMgr.updateCost(exchange_order, self.__positionManager.get_net_position(code))
        self.__pre_net_position.update({code: net_position})

    def __is_open_long(self, symbol, predictions, slice_data):
        result = self.__signalExecutor.isOpenLong(predictions, slice_data)
        return self.__check_executor_output(symbol, result)

    def __is_close_long(self, symbol, predictions, slice_data):
        result = self.__signalExecutor.isCloseLong(predictions, slice_data)
        return self.__check_executor_output(symbol, result)

    # the returned value of signalExecutor may be one of three types
    # check SignalExecutorBase for more detailed info
    def __check_executor_output(self, symbol, result):
        self.__exePriceQty.pop(symbol, None)
        # please do not change the sequence below!!
        if result is None:
            return False
        elif isinstance(result, bool):
            if result:
                return True
            else:
                return False
        elif isinstance(result, dict):
            self.__exePriceQty.update({symbol: result})
            return True

    def __process_market_close(self, symbol, slice_data):
        if self.__positionManager.has_non_finished(symbol):
            exchange_order = self.__positionManager.get_non_finished_order(symbol)
            exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
            self.__order_finished(exchange_order)
        if not self.__positionManager.is_position_closed(symbol):
            self.__close_position_at_market_close(symbol, slice_data)

    # 如果当天收盘还有头寸未平，则fake一个ExchangeOrder，以市价盘口的思路去平仓
    # 如果十档内的量，能全部撮合，则价格为加权价格
    # 如果十档内的量，不能全部撮合，则价格为第十档价格
    def __close_position_at_market_close(self, symbol, slice_data):
        date_time = dt.datetime.fromtimestamp(slice_data.timeStamp)
        net_position = self.__positionManager.get_net_position(symbol)
        price, acc_amount = self.__cal_market_close_data(net_position, slice_data)
        if net_position > 0:
            quantity = net_position
            side_str = 'S'
        else:
            quantity = -net_position
            side_str = 'B'
        if price <= 1:
            return
        order = Order(symbol, None, price, quantity, side_str, date_time)
        order_number = self.__exchangeHouse.send(order)
        exchange_order = None
        # fake an exchange order
        if order_number is not None:
            exchange_order = self.__exchangeHouse.drive(order_number, 0)
        if order_number is None or exchange_order is None:
            exchange_order = ExchangeOrder(order)
        if exchange_order.setVolume != exchange_order.volume:
            exchange_order.volume = int(quantity)
            exchange_order.accMount = acc_amount
            exchange_order.isback = True
        self.__order_finished(exchange_order)
        self.__outputMgr.registerOutput(symbol, slice_data.timeStamp)

    def __get_drive_time(self, symbol, is_open, curr_timestamp):
        pre_timestamp = self.__preTagInfo.get(symbol).timeStamp
        time_span = curr_timestamp - pre_timestamp
        if is_open:
            if time_span >= self.__openWithdrawSeconds:
                return self.__openWithdrawSeconds
            else:
                return time_span
        else:
            return time_span

    def __valid_trading_time(self, curr_time):
        if curr_time < self.__MARKET_CLOSE:
            return True
        else:
            return False

    # -----------------------------------------------------------------------------
    # helper functions
    @staticmethod
    def __is_order_finished(exchange_order):
        status = exchange_order.order_state()
        if status == 'cancelled' or status == 'filled' or status == 'partially_cancelled':
            return True
        else:
            return False

    # 目前持有订单的收益率情况
    def __calc_holding_ret(self, slice_data):
        net_position = self.__positionManager.get_net_position(self.__symbol)
        if net_position > 0:
            orders = self.__positionManager.get_finished_orders(self.__symbol)
            if len(orders) > 0:
                net_amt = sum([-x.accMount if x.BSFlag == 'B' else x.accMount for x in orders])
                buy1_price = slice_data.bidPrice[0]
                ret = (buy1_price * net_position + net_amt) / abs(net_amt)
                return ret
        return 0

    def __reset_init_amount(self, signals: pd.DataFrame):
        self.__initAmount = None
        try_times = 20
        for i in range(try_times):
            timestamp = signals.iloc[i, 0]
            if timestamp in self.__data_dict:
                base_price = self.__data_dict[timestamp].previousClosingPrice
                self.__initAmount = base_price * self.__initQty
                break
        if self.__initAmount is None:
            raise Exception('Initialize amount failed! The first {} timestamps are not in the Data.pickle {}'.format(try_times, self.__symbol))

    @staticmethod
    def __cal_market_close_data(net_position, last_slice_data):
        if net_position > 0:
            price_list = last_slice_data.bidPrice
            volume_list = last_slice_data.bidVolume
        else:
            price_list = last_slice_data.askPrice
            volume_list = last_slice_data.askVolume

        abs_position = abs(net_position)
        acc_volume = 0
        acc_amount = 0
        for i in range(len(price_list)):
            temp = acc_volume
            temp += volume_list[i]
            if temp >= abs_position:
                rest = abs_position - acc_volume
                acc_amount += rest * price_list[i]
                acc_amount = abs_position
                break
            else:
                acc_volume += volume_list[i]
                acc_amount += volume_list[i] * price_list[i]
        if acc_volume < abs_position:
            price = price_list[-1]
            if price == 0:
                for k in range(len(price_list) - 1, -1, -1):
                    if price_list[k] != 0:
                        price = price_list[k]
                if price == 0:
                    if net_position > 0:
                        price = last_slice_data.askPrice[0]
                    else:
                        price = last_slice_data.bidPrice[0]
            acc_amount = price * abs_position
            return price, acc_amount
        else:
            price = acc_amount / acc_volume
            if net_position > 0:
                return round(math.floor(price * 1000) / 1000, 3), acc_amount
            else:
                return round(math.ceil(price * 1000) / 1000, 3), acc_amount

    @staticmethod
    def __get_order_side(bs_flag):
        if bs_flag == 'B':
            return OrderSide.Buy
        else:
            return OrderSide.Sell

    def __in_time_range(self, t):  # e.g. t = 93003000
        if t < self.__NOON:
            return TimeRange.Morning
        else:
            return TimeRange.Afternoon

    def __set_noon_range(self, symbol, slice_data):
        curr_time = slice_data.time
        curr_timestamp = slice_data.timeStamp
        if symbol not in self.__preTagInfo:
            return
        if self.__in_time_range(self.__preTagInfo.get(symbol).time) == TimeRange.Morning \
                and self.__in_time_range(curr_time) == TimeRange.Afternoon:
            value = curr_timestamp - self.__preTagInfo.get(symbol).timeStamp
            self.__noonRange.update({symbol: value})

    # -----------------------------------------------------------------------------------
    # 交易结果分析
    def __return_tradings(self, symbol):
        trading_order = {}
        trading_order.update({"order": self.__outputMgr.getOrder(symbol)})
        trading_order.update({"preCostProfit": self.__outputMgr.getProfit(symbol)})
        trading_order.update({"cumOpenAmount": self.__outputMgr.getCumOpenAmount(symbol)})
        trading_order.update({'detailedOrders': self.__outputMgr.getDetailedOrder(symbol)})
        trading_order.update({"longTriggerRatio": self.__signalExecutor.getLongTriggerRatio()})
        trading_order.update({"longCloseRatio": self.__signalExecutor.getLongCloseRatio()})
        trading_order.update({"longCloseRiskRatio": self.__signalExecutor.getLongCloseRiskRatio()})
        trading_order.update({"shortTriggerRatio": self.__signalExecutor.getShortTriggerRatio()})
        trading_order.update({"shortCloseRatio": self.__signalExecutor.getShortCloseRatio()})
        trading_order.update({"shortCloseRiskRatio": self.__signalExecutor.getShortCloseRiskRatio()})
        trading_order.update({"preCostDailyProfit": self.__outputMgr.getDailyProfitDict(symbol)})
        trading_order.update({"afterCostDailyProfit": self.__outputMgr.getAfterCostDailyProfitDict(symbol)})
        trading_order.update({"dailyOpenAmount": self.__outputMgr.getDailyOpenAmountDict(symbol)})
        trading_order.update({"dayCounts": self.__outputMgr.getDayCounts(symbol)})
        trading_order.update({'dailyCancelledRatio': self.__outputMgr.getDailyCancelledRatio(symbol)})
        trading_order.update({'cancelledRatio': self.__outputMgr.getSumCancelledRatio(symbol)})
        return trading_order

    def trading_evaluate(self, trading_order, show):
        threshold = 0.001  # 盈利阈值
        trigger_times = trading_order["order"].__len__()  # 触发次数
        win_times = 0  # 获利次数
        win_rate = 0  # 胜率
        times_per_day = 0  # 日均开仓次数
        long_times = 0  # 开多仓次数
        short_times = 0  # 开空仓次数
        average_return_rate = 0  # 平均收益率
        average_return_rate_profit = 0  # 平均获利收益率
        average_return_rate_loss = 0  # 平均亏损收益率
        profit_loss_ratio = 0  # 盈亏比
        max_loss = 0  # 最大亏损
        average_position_time = 0  # 平均持仓时间
        after_cost_profit = 0  # 算上手续费的总盈亏
        ave_daily_cum_amount = 0  # 日均成交额
        max_daily_cum_amount = 0  # 最大日成交额
        annual_return_mv = 0  # 年化市值收益率
        average_trading_return_rate = 0  # 交易收益率
        day_winning_rate = 0  # 日胜率
        cum_open_amount = 0
        if trigger_times != 0:
            win_rate = win_times / trigger_times
            if self.__funStr is None:
                cum_open_amount = trading_order["cumOpenAmount"]
                pre_cost_profit = trading_order["preCostProfit"]
                after_cost_profit = pre_cost_profit - self.__COST_RATE * cum_open_amount
                after_cost_profit = round(after_cost_profit, 2)
                day_counts = trading_order["dayCounts"]
                if day_counts != 0:
                    ave_daily_cum_amount = cum_open_amount / day_counts
                    for item in trading_order["dailyOpenAmount"].values():
                        if item > max_daily_cum_amount:
                            max_daily_cum_amount = item
                    annual_return_mv = after_cost_profit / self.__initAmount / day_counts * 250
                    after_cost_daily_profit = trading_order["afterCostDailyProfit"]
                    day_winning_times = 0
                    for daily_profit in after_cost_daily_profit.values():
                        if daily_profit > 0:
                            day_winning_times += 1
                    day_winning_rate = day_winning_times / len(after_cost_daily_profit.values())
            else:
                day_counts = len(self.__predictions) / 4800
            if day_counts != 0:
                times_per_day = trigger_times / day_counts
        if trigger_times > 0:
            for order in trading_order["order"]:
                if show:
                    print(order)
                # 计算持仓时间(min)
                start_time = dt.datetime.strptime(order["startTime"], "%m/%d/%y-%H:%M:%S")
                end_time = dt.datetime.strptime(order["endTime"], "%m/%d/%y-%H:%M:%S")
                if start_time.hour <= 11 and end_time.hour >= 13:
                    average_position_time += (end_time - start_time).seconds / 60 - 90
                else:
                    average_position_time += (end_time - start_time).seconds / 60
                # 计算开多和开空次数
                if order["direction"] == 'long ':
                    long_times += 1
                else:
                    short_times += 1
                # 计算收益率相关值
                average_return_rate += order["returnRate"]
                if order["returnRate"] > threshold:
                    win_times += 1
                    average_return_rate_profit += order["returnRate"] - threshold
                else:
                    average_return_rate_loss += order["returnRate"] - threshold
                    if order["returnRate"] < max_loss:
                        max_loss = order["returnRate"]
            average_position_time /= trigger_times
            win_rate = win_times / trigger_times
            average_return_rate /= trigger_times
            if win_times > 0:
                average_return_rate_profit /= win_times
            if trigger_times > win_times:
                average_return_rate_loss /= (trigger_times - win_times)
                if abs(average_return_rate_loss) > 0:
                    profit_loss_ratio = average_return_rate_profit / abs(average_return_rate_loss)
        trading_order.update({"triggerTimes": trigger_times})
        trading_order.update({"timesPerDay": times_per_day})
        trading_order.update({"winTimes": win_times})
        trading_order.update({"winRate": win_rate})
        trading_order.update({"longTimes": long_times})
        trading_order.update({"shortTimes": short_times})
        trading_order.update({"averageReturnRate": average_return_rate})
        trading_order.update({"averageReturnRateProfit": average_return_rate_profit})
        trading_order.update({"averageReturnRateLoss": average_return_rate_loss})
        trading_order.update({"profitLossRatio": profit_loss_ratio})
        trading_order.update({"maxLoss": max_loss})
        trading_order.update({"averagePositionTime": average_position_time})
        if self.__funStr is None:
            if cum_open_amount != 0:
                average_trading_return_rate = after_cost_profit / cum_open_amount
            trading_order.update({"dayWinningRate": day_winning_rate})
            trading_order.update({"averageTradingReturnRate": average_trading_return_rate})
            trading_order.update({"afterCostProfit": after_cost_profit})
            trading_order.update({"initQty": self.__initQty})
            trading_order.update({'initAmount': self.__initAmount})
            trading_order.update({"aveDailyCumAmount": ave_daily_cum_amount})
            trading_order.update({"maxDailyCumAmount": max_daily_cum_amount})
            trading_order.update({"annualReturnMV": annual_return_mv})
        return trading_order


class OrderInfo:
    def __init__(self, order_number, is_open):
        self.orderNo = order_number
        self.isOpen = is_open


class TimeRange(Enum):
    Morning = 0
    Afternoon = 1
