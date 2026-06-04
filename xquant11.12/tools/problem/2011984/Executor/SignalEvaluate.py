"""SignalEvaluate——update @2021.8.13"""

import sys
import math
import importlib
import datetime as dt
from DataAPI.ExchangeHouse.ExchangeHouse import ExchangeHouse
from DataAPI.ExchangeHouse.ExchangeOrder import ExchangeOrder
from DataAPI.ExchangeHouse.Data.Data import Data
from DataAPI.ExchangeHouse.Order import Order
from DataAPI.TradingDay import trading_day
from Manager.PositionManager import PositionManager
from Manager.OutputManager import OutputManager
from Manager.UtilsModel.OrderSide import OrderSide
from Analyzer.BTAnalyzer.ExcelWriter import output_spread_sheet, trading_evaluate
from Utils.UtilsCode import get_cost_rate


class SignalEvaluate:
    def __init__(self, code, executor_str, tick_data, transaction_data, tick_dict, output_path, signal_params_pairs):
        self.__code = code
        self.__executor_str = executor_str
        self.__tick = tick_data
        self.__transaction = transaction_data
        self.__data_dict = tick_dict
        self._param = None
        self.__output_path = output_path
        self.signal_params_pairs = signal_params_pairs  # signal_data和param组合的list

        self.__outputManager = None
        self.__signalExecutor = None
        self.__positionManager = PositionManager()
        self.__exchangeHouse = None

        self.__trading_params = {
            'maxRatePerOrder': 0.2,  # 每笔最大委托占比
            'openWithdrawSeconds': 2.5,  # 开仓单驱动时间
            'closeWithdrawSeconds': 3,  # 平仓单驱动时间，建议始终设为3
            'buyLevel': 1,  # 1-based index, not 0-based
            'sellLevel': 1,  # 1-based index, not 0-based
            'buyDeviation': 0,
            'sellDeviation': -0.01,
        }
        self.__cost_rate = get_cost_rate(code, 'bt')
        self.__preTagInfo = {}
        self.__pre_net_position = {}
        self.__orderInfo = {}
        self.__exePriceQty = {}

    def evaluate(self, show=None, dfs=None):
        combine_trading_order = self.run_backtest(show)
        st_date = trading_day(self._param['st_date'], self._param['ed_date'])[0]
        if len(self.__tick) > 0:
            for x in self.__tick:
                if x is not None and len(x) > 0:
                    st_date = str(x['Date'][0])
                    break
        trading_evaluate(combine_trading_order, self._param['init_qty'], self.__code, st_date, self.__cost_rate, False)
        detailed_orders = combine_trading_order.get('detailedOrders')
        combine_trading_order.pop('detailedOrders', None)
        if show is not None:
            output_path = f'{self.__output_path}/result_{show}.xlsx'
            output_spread_sheet(detailed_orders, combine_trading_order, output_path, dfs=dfs)
        return combine_trading_order

    def run_backtest(self, show):
        modules = importlib.import_module(self.__executor_str)  # 通过String来生成的Executor的实例，先import
        self.__outputManager = OutputManager(self.__cost_rate, show is None)
        for signal_data, params_dict in self.signal_params_pairs:
            self._param = params_dict
            self.__exchangeHouse = ExchangeHouse(Data(self.__tick, self.__transaction), is_holo=self._param['is_holo'], delay=self._param['delay'])
            self.__signalExecutor = getattr(modules, self.__executor_str.split('.')[-1])(self.__positionManager, self._param)
            self.__signalExecutor.set_data_dict(self.__data_dict, self.__tick)

            for index, row in signal_data.iterrows():
                timestamp = row[0]
                slice_data = self.__data_dict.get(timestamp)
                if slice_data is not None:
                    predictions = [row[1], row[2]]
                    if self.__is_new_day(slice_data.timeStamp):
                        self.__coming_new_day(slice_data.date)
                    self.__make_order(slice_data)  # 撮合上一个tick的订单（相邻2个tick的时间差不是固定的）
                    if self.__valid_slice_data(slice_data):
                        if slice_data.time < int(self._param['market_close_time'].replace(':', '')) * 1000:
                            self.__mock_trading(predictions, slice_data)
                        if index == signal_data.index[-1] or dt.datetime.fromtimestamp(timestamp).date() != \
                                dt.datetime.fromtimestamp(signal_data.at[index + 1, 'Timestamp']).date():
                            self.__process_market_close(slice_data)
                    self.__preTagInfo.update({self.__code: slice_data})
        return self.__return_tradings()

    @staticmethod
    def __valid_slice_data(slice_data):
        if slice_data.bidPrice[0] <= 1 and slice_data.askPrice[0] <= 1:
            return False
        return True

    def __mock_trading(self, predictions, slice_data):
        if self.__positionManager.has_non_finished():
            if self.__is_order_valid(slice_data):
                self.__on_new_tick(predictions, slice_data)
                return
            else:
                self.__drive_invalid_nonfinished_order()
        self.__on_new_tick(predictions, slice_data)
        self.__on_predict_updated(predictions, slice_data)

    # this method will now be called as every tick comes, to update tick info
    def __on_new_tick(self, predictions, slice_data):
        self.__signalExecutor.update_predict_info(predictions, slice_data)

    def __on_predict_updated(self, predictions, slice_data):
        if self.__positionManager.is_position_closed():
            self.__outputManager.register_output(self.__code, slice_data.timeStamp)  # 平仓状态，outputMgr负责生成order统计
            if self.__is_open_long(predictions, slice_data):
                self.__process_open_signal(OrderSide.Buy, slice_data)
            elif self.__is_open_short(predictions, slice_data):
                self.__process_open_signal(OrderSide.Sell, slice_data)
        elif self.__positionManager.is_position_positive():
            if self.__is_close_long(predictions, slice_data):
                self.__process_close_signal(OrderSide.Sell, slice_data)
            elif self.__is_open_long(predictions, slice_data):
                self.__process_open_signal(OrderSide.Buy, slice_data)
        elif self.__positionManager.is_position_negative():
            if self.__is_close_short(predictions, slice_data):
                self.__process_close_signal(OrderSide.Buy, slice_data)
            elif self.__is_open_short(predictions, slice_data):
                self.__process_open_signal(OrderSide.Sell, slice_data)

    def __process_open_signal(self, side, slice_data):
        price = self.__cal_price(side, True, slice_data)
        quantity = self.__cal_open_qty(price)
        if quantity < self._param['min_vol_qty']:
            return
        ratio = abs(price / slice_data.previousClosingPrice - 1.0)
        if price <= 1 or ratio >= self._param['open_forbidden_pct']:
            return
        self.__place_order(self.__code, side, price, quantity, True, slice_data.timeStamp)

    def __process_close_signal(self, side, slice_data):
        price = self.__cal_price(side, False, slice_data)
        quantity = self.__cal_close_qty(price)
        if quantity <= 0 or price <= 1:
            return
        self.__place_order(self.__code, side, price, quantity, False, slice_data.timeStamp)

    def __cal_price(self, side, is_open, slice_data):
        if self.__code in self.__exePriceQty and 'price' in self.__exePriceQty.get(self.__code):
            # 指定下单价格
            price = self.__exePriceQty.get(self.__code).get('price')
            if price < slice_data.minPrice or price > slice_data.maxPrice:
                price = slice_data.lastPrice
        else:
            if is_open:  # process open signal
                if side == OrderSide.Buy:
                    price_level = self.__trading_params['buyLevel']
                    deviation = self.__trading_params['buyDeviation']
                else:
                    price_level = -self.__trading_params['buyLevel']
                    deviation = -self.__trading_params['buyDeviation']
            else:  # process close signal
                if side == OrderSide.Buy:
                    price_level = -self.__trading_params['sellLevel']
                    deviation = -self.__trading_params['sellDeviation']
                else:
                    price_level = self.__trading_params['sellLevel']
                    deviation = self.__trading_params['sellDeviation']
            if price_level > 0:
                price_list = slice_data.askPrice
            else:
                price_list = slice_data.bidPrice
            price = price_list[abs(price_level) - 1]

            if price < slice_data.minPrice or price > slice_data.maxPrice:
                price = slice_data.lastPrice
            price += deviation
            price = max(min(price, slice_data.maxPrice), slice_data.minPrice)
        price = self.__price_digits(price, side)
        return price

    def __cal_open_qty(self, price):
        if price == 0:
            return 0
        liquid_qty = sys.maxsize
        if self.__code in self.__exePriceQty and 'volume' in self.__exePriceQty.get(self.__code):
            volume = self.__exePriceQty.get(self.__code).get('volume')
            liquid_qty = self._param['maxExposure'] / price
            avail_space = int(liquid_qty - abs(self.__positionManager.get_net_position()))
            quantity = min(volume, avail_space, self._param['maxTurnoverPerOrder'] / price,
                           self.__positionManager.get_avail_qty())
        else:
            liquid_qty = min(liquid_qty, self._param['maxExposure'] / price)
            avail_space = int(liquid_qty - abs(self.__positionManager.get_net_position()))
            quantity = min(avail_space, self._param['maxTurnoverPerOrder'] / price,
                           self.__positionManager.get_initial_qty() * self.__trading_params['maxRatePerOrder'],
                           self.__positionManager.get_avail_qty())
        quantity = round(math.floor(quantity / self._param['min_vol_qty']) * self._param['min_vol_qty'])
        if quantity > 0:
            quantity = max(self._param['min_vol_qty_sum'], quantity)
        return quantity

    def __cal_close_qty(self, price):
        if price == 0:
            return 0
        net_position = abs(self.__positionManager.get_net_position())
        if self._param['is_close_maxTurnoverPerOrder']:
            vol_limit = int(self._param['maxTurnoverPerOrder'] / price)
        else:
            vol_limit = 1e10
        if self.__code in self.__exePriceQty and 'volume' in self.__exePriceQty.get(self.__code):
            volume = int(self.__exePriceQty.get(self.__code).get('volume'))
            volume = min(volume, vol_limit)
            if volume > net_position:  # 翻转下单
                exposure = volume - net_position
                exposure = min(exposure, self._param['maxExposure'] / price, self._param['maxTurnoverPerOrder'] / price,
                               self.__positionManager.get_avail_qty())
                return int(exposure + net_position)
            else:
                return volume
        else:
            return min(net_position, vol_limit)

    def __place_order(self, code, side, price, quantity, is_open, timestamp):
        date_timestamp = dt.datetime.fromtimestamp(timestamp)
        date_time = str(date_timestamp.time())
        # 若在禁止开仓时刻之后，且为开仓单，则不再开仓。平仓单不受影响
        if (date_time < self._param['trading_start_morning'] or date_time >= self._param['market_close_time']) and is_open:
            return
        if side == OrderSide.Buy:
            side_str = 'B'
        else:
            side_str = 'S'
        order = Order(code, None, price, quantity, side_str, date_timestamp)
        order_number = self.__exchangeHouse.send(order)
        self.__orderInfo.update({code: OrderInfo(order_number, is_open)})

    def __make_order(self, slice_data):
        if self.__code not in self.__orderInfo or self.__orderInfo.get(self.__code) is None:
            return
        order_info = self.__orderInfo.get(self.__code)
        order_number = order_info.orderNo
        if order_number is None:
            self.__orderInfo.pop(self.__code, None)
            return

        is_open = order_info.isOpen
        curr_timestamp = slice_data.timeStamp
        exchange_order = self.__exchangeHouse.drive(order_number, self.__get_drive_time(self.__code, is_open, curr_timestamp))
        if exchange_order is None or exchange_order.orderNumber is None:
            self.__orderInfo.pop(self.__code, None)
            return

        # 开仓单必撤，平仓单需要在下一个Tick（当前）检查盘口
        exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
        self.__order_finished(exchange_order)

    def __is_new_day(self, curr_timestamp):
        flag = False
        if len(self.__preTagInfo) == 0 or self.__code not in self.__preTagInfo:
            flag = True
        elif dt.datetime.fromtimestamp(curr_timestamp).date() != dt.datetime.fromtimestamp(self.__preTagInfo.get(self.__code).timeStamp).date():
            flag = True
        return flag

    def __coming_new_day(self, trade_date):
        if isinstance(self._param['init_qty'], dict):
            init_qty_day = self._param['init_qty'][str(trade_date)]
        else:
            init_qty_day = self._param['init_qty']
        init_qty = math.floor(init_qty_day / self._param['min_vol_qty'] - 1) * self._param['min_vol_qty']
        self.__signalExecutor.reset_new_day(trade_date)
        self.__positionManager.init_position(init_qty)
        self.__pre_net_position.update({self.__code: 0})
        self.__outputManager.clear_non_closed(self.__code)
        self.__outputManager.add_one_day(self.__code)
        self.__orderInfo.pop(self.__code, None)

    @staticmethod
    def __split_reversed_cum_qty(last_net_position, net_position):
        if last_net_position * net_position < 0:
            return abs(last_net_position), abs(net_position)
        else:
            return None

    #  判断这笔平仓订单是否在一档盘口及以内：如果订单inValid，则return False，需要撤单；如果订单Valid，则return True，不需要撤单
    def __is_order_valid(self, slice_data):
        exchange_order = self.__positionManager.get_non_finished_order()
        price = exchange_order.setPrice
        ask1 = slice_data.askPrice[0]
        bid1 = slice_data.bidPrice[0]
        if self.__get_order_side(exchange_order.BSFlag) == OrderSide.Sell and price > ask1:
            return False
        elif self.__get_order_side(exchange_order.BSFlag) == OrderSide.Buy and price < bid1:
            return False
        else:
            return True

    def __drive_invalid_nonfinished_order(self):
        exchange_order = self.__positionManager.get_non_finished_order()
        exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
        self.__order_finished(exchange_order)

    def __order_finished(self, exchange_order):
        code = exchange_order.code
        self.__orderInfo.pop(code, None)
        self.__positionManager.update_position(exchange_order)
        net_position = self.__positionManager.get_net_position()
        self.__outputManager.add_order(exchange_order, self.__split_reversed_cum_qty(self.__pre_net_position.get(code), net_position))
        self.__pre_net_position.update({code: net_position})

    def __is_open_long(self, predictions, slice_data):
        result = self.__signalExecutor.is_open_long(predictions, slice_data)
        return self.__check_executor_output(result)

    def __is_open_short(self, predictions, slice_data):
        result = self.__signalExecutor.is_open_short(predictions, slice_data)
        return self.__check_executor_output(result)

    def __is_close_long(self, predictions, slice_data):
        result = self.__signalExecutor.is_close_long(predictions, slice_data)
        return self.__check_executor_output(result)

    def __is_close_short(self, predictions, slice_data):
        result = self.__signalExecutor.is_close_short(predictions, slice_data)
        return self.__check_executor_output(result)

    # the returned value of signalExecutor may be one of three types
    # check SignalExecutorBase for more detailed info
    def __check_executor_output(self, result):
        self.__exePriceQty.pop(self.__code, None)
        # please do not change the sequence below!!
        if result is None:
            return False
        elif isinstance(result, bool):
            if result:
                return True
            else:
                return False
        elif isinstance(result, dict):
            self.__exePriceQty.update({self.__code: result})
            return True

    def __get_drive_time(self, code, is_open, curr_timestamp):
        pre_timestamp = self.__preTagInfo.get(code).timeStamp
        time_span = curr_timestamp - pre_timestamp
        if is_open:
            return min(time_span, self.__trading_params['openWithdrawSeconds'])
        else:
            return time_span

    def __process_market_close(self, slice_data):
        if self.__positionManager.has_non_finished():
            exchange_order = self.__positionManager.get_non_finished_order()
            exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
            self.__order_finished(exchange_order)
        if not self.__positionManager.is_position_closed():
            # 如果当天收盘还有头寸未平，则fake一个ExchangeOrder，以市价盘口的思路去平仓
            # 如果十档内的量，能全部撮合，则价格为加权价格
            # 如果十档内的量，不能全部撮合，则价格为第十档价格
            date_time = dt.datetime.fromtimestamp(slice_data.timeStamp)
            net_position = self.__positionManager.get_net_position()
            price, acc_amount = self.__cal_market_close_data(net_position, slice_data)
            if net_position > 0:
                quantity = net_position
                side_str = 'S'
            else:
                quantity = -net_position
                side_str = 'B'
            if price <= 1:
                return
            order = Order(self.__code, None, price, quantity, side_str, date_time)
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
            self.__outputManager.register_output(self.__code, slice_data.timeStamp)

    # -----------------------------------------------------------------------------
    # helper functions
    @staticmethod
    def __is_order_finished(exchange_order):
        status = exchange_order.order_state()
        if status == 'cancelled' or status == 'filled' or status == 'partially_cancelled':
            return True
        else:
            return False

    def __cal_market_close_data(self, net_position, last_slice_data):
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
                acc_volume = abs_position
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
            side = OrderSide.Buy if net_position < 0 else OrderSide.Sell
            price = self.__price_digits(price, side)
            return price, acc_amount

    @staticmethod
    def __get_order_side(bs_flag):
        if bs_flag == 'B':
            return OrderSide.Buy
        else:
            return OrderSide.Sell

    def __price_digits(self, price, side):
        """价格的小数点位处理"""
        if self._param['type'] == 'stock':
            price = round(price, self._param['price_digits'])
        elif self._param['type'] == 'cb':
            if side == OrderSide.Buy:
                price = math.ceil(price * 10 ** self._param['price_digits']) / (10 ** self._param['price_digits'])
            else:
                price = math.floor(price * 10 ** self._param['price_digits']) / (10 ** self._param['price_digits'])
        return price

    # -----------------------------------------------------------------------------------
    # 交易结果分析
    def __return_tradings(self):
        code = self.__code
        trading_order = {
            'order': self.__outputManager.get_order(code),
            'preCostProfit': self.__outputManager.get_profit(code),
            'cumOpenAmount': self.__outputManager.get_cum_open_amount(code),
            'detailedOrders': self.__outputManager.get_detailed_order(code),
            'preCostDailyProfit': self.__outputManager.get_daily_profit_dict(code),
            'afterCostDailyProfit': self.__outputManager.get_after_cost_daily_profit_dict(code),
            'dailyOpenAmount': self.__outputManager.get_daily_open_amount_dict(code),
            'dayCounts': self.__outputManager.get_day_counts(code),
            'dailyCancelledRatio': self.__outputManager.get_daily_cancelled_ratio(code),
            'cancelledRatio': self.__outputManager.get_sum_cancelled_ratio(code)
        }
        trading_order.update(self._param['triggers'])
        return trading_order


class OrderInfo:
    def __init__(self, order_number, is_open):
        self.orderNo = order_number
        self.isOpen = is_open
