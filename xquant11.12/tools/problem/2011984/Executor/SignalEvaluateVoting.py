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
from Manager.UtilsModel.VotingTriggers import get_voting_str_dict
from Analyzer.BTAnalyzer.ExcelWriter import output_spread_sheet, trading_evaluate
from Utils.UtilsCode import get_cost_rate


class SignalEvaluateVoting:
    def __init__(self, code, executor_str, tick_data, transaction_data, tick_dict, output_path, signal_params_pairs):
        self.__code = code
        self.__executor_str = executor_str
        self.__tick = tick_data
        self.__transaction = transaction_data
        self.__data_dict = tick_dict
        self._param = None
        self.__output_path = output_path
        self.signal_params_pairs = signal_params_pairs  # signal_data和param组合的list

        self.__vt_name_list = []
        self.__vt_dict = get_voting_str_dict()
        self.__outputManager = None
        self.__executorDict = {}
        self.__positionManagerDict = {}
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
        self.__slice_data = None
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
            output_path = '{}/result_{}.xlsx'.format(self.__output_path, show)
            output_spread_sheet(detailed_orders, combine_trading_order, output_path, dfs=dfs)
        return combine_trading_order

    def run_backtest(self, show):
        modules = importlib.import_module(self.__executor_str)  # 通过String来生成的Executor的实例，先import
        self.__outputManager = OutputManager(self.__cost_rate, show is None)
        for signal_data, params_dict in self.signal_params_pairs:
            self._param = params_dict
            self.__exchangeHouse = ExchangeHouse(Data(self.__tick, self.__transaction), is_holo=self._param['is_holo'], delay=self._param['delay'])
            self.__vt_name_list = self._param['vt_params']['vt_name_list']
            for vt_name in self.__vt_name_list:
                if vt_name not in ['0.25min', '0.5min', '1min', '2min', '5min']:
                    sel_cols = self.__vt_dict[float(vt_name[:-3])]
                    signal_data[f'{vt_name}Long'] = signal_data[[f'{x}Long' for x in sel_cols]].mean(axis=1)
                    signal_data[f'{vt_name}Short'] = signal_data[[f'{x}Short' for x in sel_cols]].mean(axis=1)
                self.__positionManagerDict[vt_name] = PositionManager()
                param_executor = self._param.copy()
                if 'triggers_by_date' in param_executor.keys():
                    param_executor['triggers_by_date'] = dict([(x, y[vt_name]) for (x, y) in param_executor['triggers_by_date'].items()])
                else:
                    param_executor['triggers'] = self._param['vt_triggers'][vt_name]
                self.__executorDict[vt_name] = getattr(modules, self.__executor_str.split('.')[-1])\
                    (self.__positionManagerDict[vt_name], param_executor, self.__get_total_net_position, self.__get_total_finished_orders)
                self.__executorDict[vt_name].set_data_dict(self.__data_dict, self.__tick)
            signal_data = signal_data.rename(columns={'15secLong': '0.25minLong', '15secShort': '0.25minShort',
                                                      '30secLong': '0.5minLong', '30secShort': '0.5minShort'})
            for index, row in signal_data.iterrows():
                timestamp = row[0]
                self.__slice_data = self.__data_dict.get(timestamp)
                if self.__slice_data is not None:
                    predictions = dict()
                    for vt_name in self.__vt_name_list:
                        predictions.update({vt_name: [row[f'{vt_name}Long'], row[f'{vt_name}Short']]})
                    if self.__is_new_day():
                        self.__coming_new_day()
                    self.__make_order()  # 撮合上一个tick的订单（相邻2个tick的时间差不是固定的）
                    if self.__valid_slice_data():
                        if self.__slice_data.time < int(self._param['market_close_time'].replace(':', '')) * 1000:
                            self.__mock_trading(predictions)
                    self.__preTagInfo.update({self.__code: self.__slice_data})
        return self.__return_tradings(self.__code)

    def __valid_slice_data(self):
        if self.__slice_data.bidPrice[0] <= 1 or self.__slice_data.askPrice[0] <= 1:
            return False
        return True

    def __mock_trading(self, predictions):
        self.__on_new_tick(predictions)
        self.__on_predict_updated(predictions)

    # this method will now be called as every tick comes, to update tick info
    def __on_new_tick(self, predictions):
        for vt_name in self.__vt_name_list:
            self.__executorDict[vt_name].update_predict_info(predictions[vt_name], self.__slice_data, vt_name)

    def __on_predict_updated(self, predictions):
        self.__orderList = []
        total_net_position = self.__get_total_net_position()
        if total_net_position == 0:
            self.__outputManager.register_output(self.__code, self.__slice_data.timeStamp)
            for vt_name in self.__vt_name_list:
                if self.__is_open_long(predictions, vt_name):
                    self.__process_open_signal(OrderSide.Buy, vt_name)
                if self.__is_open_short(predictions, vt_name):
                    self.__process_open_signal(OrderSide.Sell, vt_name)
        elif total_net_position > 0:
            for vt_name in self.__vt_name_list:
                if self.__is_open_long(predictions, vt_name):
                    self.__process_open_signal(OrderSide.Buy, vt_name)
                elif self.__is_close_long(predictions, vt_name):
                    self.__process_close_signal(OrderSide.Sell, vt_name)
                elif self.__is_market_close_long(vt_name):
                    self.__process_close_signal(OrderSide.Sell, 'MarketCloseLong')
                    break
        elif total_net_position < 0:
            for vt_name in self.__vt_name_list:
                if self.__is_open_short(predictions, vt_name):
                    self.__process_open_signal(OrderSide.Sell, vt_name)
                elif self.__is_close_short(predictions, vt_name):
                    self.__process_close_signal(OrderSide.Buy, vt_name)
                elif self.__is_market_close_short(vt_name):
                    self.__process_close_signal(OrderSide.Buy, 'MarketCloseShort')
                    break
        self.__combine_orders(total_net_position)

    def __get_total_net_position(self):
        s = 0
        for vt_name in self.__vt_name_list:
            s += self.__positionManagerDict[vt_name].get_net_position()
        return s

    def __get_total_finished_orders(self):
        ll = []
        for vt_name in self.__vt_name_list:
            ll.extend(self.__positionManagerDict[vt_name].get_finished_orders())
        return ll

    def __combine_orders(self, net_position):
        if len(self.__orderList) == 0:
            return

        if net_position >= 0:
            open_side, close_side = OrderSide.Buy, OrderSide.Sell
            open_side_str, close_side_str = 'B', 'S'
            is_price_revese = False
        else:
            open_side, close_side = OrderSide.Sell, OrderSide.Buy
            open_side_str, close_side_str = 'S', 'B'
            is_price_revese = True
        open_list, close_list = [], []
        for order in self.__orderList:
            if order[1].name[0] == open_side_str:
                open_list.append(order)
            elif order[1].name[0] == close_side_str:
                close_list.append(order)

        open_price = self.__vt_method_res([x[2] for x in open_list], self._param['vt_params']['buy_price_method'], is_reverse=is_price_revese)
        open_qty, close_qty = 0, 0
        if len(open_list) >= self._param['vt_params']['open_counter']:
            open_qty = self.__vt_method_res([x[3] for x in open_list], self._param['vt_params']['buy_vol_method'])
        if net_position == 0:
            close_price = self.__vt_method_res([x[2] for x in close_list], self._param['vt_params']['buy_price_method'], is_reverse=True)
            if len(close_list) >= self._param['vt_params']['open_counter']:
                close_qty = self.__vt_method_res([x[3] for x in close_list], self._param['vt_params']['buy_vol_method'])
        else:
            close_price = self.__vt_method_res([x[2] for x in close_list], self._param['vt_params']['sell_price_method'], is_reverse=is_price_revese)
            if len(close_list) >= self._param['vt_params']['close_counter']:
                close_qty = self.__vt_method_res([x[3] for x in close_list], self._param['vt_params']['sell_vol_method'])
        type_close = '-'.join([x[-1] for x in close_list])

        if open_qty == 0 and close_qty == 0:
            return
        elif open_qty == 0 and type_close in ['MarketCloseLong', 'MarketCloseShort']:  # 尾盘卖出交易
            set_volume_list = [abs(self.__positionManagerDict[vt_name].get_net_position()) for vt_name in self.__vt_name_list]
            type_close = '-'.join([self.__vt_name_list[i] for i in range(len(self.__vt_name_list)) if set_volume_list[i] > 0])
            set_volume_list = [x for x in set_volume_list if x > 0]
            percentile_list = [o / sum(set_volume_list) for o in set_volume_list]
            self.__place_order(self.__code, close_side, close_price, close_qty, False,
                               self.__slice_data.timeStamp, type_close, percentile_list, set_volume_list)
        else:
            deal_qty = min(open_qty, close_qty)
            set_volume_list = [o[3] for o in open_list]
            percentile_list = [o[3] / sum(set_volume_list) for o in open_list]
            deal_list = self.__split_close_order_qty(percentile_list, deal_qty, set_volume_list)
            if deal_qty != 0:
                for q, cj in zip(open_list, deal_list):
                    eo = ExchangeOrder(Order(self.__code, None, q[2], cj, open_side_str, 0, q[-1] + 'Self'), True)
                    eo.volume = cj
                    eo.accMount = cj * q[2]
                    self.__positionManagerDict[q[-1]].update_position(eo)
            if open_qty > close_qty:
                type_open = '-'.join([x[-1] for x in open_list])
                no_deal_list = [set_volume_list[i] - deal_list[i] for i in range(len(deal_list))]
                self.__place_order(self.__code, open_side, open_price, open_qty - close_qty, True,
                                   self.__slice_data.timeStamp, type_open, percentile_list, no_deal_list)

            set_volume_list = [o[3] for o in close_list]
            percentile_list = [o[3] / sum(set_volume_list) for o in close_list]
            deal_list = self.__split_close_order_qty(percentile_list, deal_qty, set_volume_list)
            if deal_qty != 0:
                for q, cj in zip(close_list, deal_list):
                    eo = ExchangeOrder(Order(self.__code, None, q[2], cj, close_side_str, 0, q[-1] + 'Self'), True)
                    eo.volume = cj
                    eo.accMount = cj * q[2]
                    self.__positionManagerDict[q[-1]].update_position(eo)
            if open_qty < close_qty:
                is_open = net_position == 0
                no_deal_list = [set_volume_list[i] - deal_list[i] for i in range(len(deal_list))]
                self.__place_order(self.__code, close_side, close_price, close_qty - open_qty, is_open,
                                   self.__slice_data.timeStamp, type_close, percentile_list, no_deal_list)

    @staticmethod
    def __split_close_order_qty(percentile_list, total_traded_qty, set_volume_list):
        deal_list = [0] * len(set_volume_list)

        deal = total_traded_qty
        for i in range(len(set_volume_list)):
            qty = int(percentile_list[i] / 10 * total_traded_qty) * 10
            deal_list[i] = qty
            deal -= qty

        for i in range(len(set_volume_list)):
            qty = min(10, deal, set_volume_list[i] - deal_list[i])
            deal_list[i] += qty
            deal -= qty

        return deal_list

    def __process_open_signal(self, side, vt_name):
        price = self.__cal_price(side, True)
        quantity = self.__cal_open_qty(price, vt_name)
        if quantity < self._param['min_vol_qty']:
            return
        ratio = abs(price / self.__slice_data.previousClosingPrice - 1.0)
        if price <= 1 or ratio >= self._param['open_forbidden_pct']:
            return
        self.__orderList.append((self.__code, side, price, quantity, True, self.__slice_data.timeStamp, vt_name))

    def __process_close_signal(self, side, vt_name):
        price = self.__cal_price(side, False)
        quantity = self.__cal_close_qty(price, vt_name)
        if quantity <= 0 or price <= 1:
            return
        self.__orderList.append((self.__code, side, price, quantity, False, self.__slice_data.timeStamp, vt_name))

    def __cal_price(self, side, is_open):
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
            price_list = self.__slice_data.askPrice
        else:
            price_list = self.__slice_data.bidPrice
        price = price_list[abs(price_level) - 1]

        if self.__code in self.__exePriceQty and 'price' in self.__exePriceQty.get(self.__code):
            # 指定下单价格
            price = self.__exePriceQty.get(self.__code).get('price')
            if price < self.__slice_data.minPrice or price > self.__slice_data.maxPrice:
                price = self.__slice_data.lastPrice
        else:
            if price < self.__slice_data.minPrice or price > self.__slice_data.maxPrice:
                price = self.__slice_data.lastPrice
            price += deviation
            price = max(min(price, self.__slice_data.maxPrice), self.__slice_data.minPrice)
        price = self.__price_digits(price, side)
        return price

    def __cal_open_qty(self, price, vt_name):
        liquid_qty = sys.maxsize
        if self.__code in self.__exePriceQty and 'volume' in self.__exePriceQty.get(self.__code):
            liquid_qty = self._param['maxExposure'] / price
            avail_space = int(liquid_qty - abs(self.__get_total_net_position()))
            volume = self.__exePriceQty.get(self.__code).get('volume')
            quantity = min(volume, avail_space, self._param['maxTurnoverPerOrder'] / price,
                           self.__positionManagerDict[vt_name].get_avail_qty())
        else:
            liquid_qty = min(liquid_qty, self._param['maxExposure'] / price)
            avail_space = int(liquid_qty - abs(self.__positionManagerDict[vt_name].get_net_position()))
            quantity = min(avail_space, self._param['maxTurnoverPerOrder'] / price,
                           self.__positionManagerDict[vt_name].get_initial_qty() * self.__trading_params['maxRatePerOrder'],
                           self.__positionManagerDict[vt_name].get_avail_qty())
        quantity = round(math.floor(quantity / self._param['min_vol_qty']) * self._param['min_vol_qty'])
        if quantity > 0:
            quantity = max(self._param['min_vol_qty_sum'], quantity)
        return quantity

    def __cal_close_qty(self, price, vt_name):
        if vt_name in ['MarketCloseLong', 'MarketCloseShort']:
            net_position = self.__get_total_net_position()
        else:
            net_position = abs(self.__positionManagerDict[vt_name].get_net_position())
        if self._param['is_close_maxTurnoverPerOrder']:
            vol_limit = int(self._param['maxTurnoverPerOrder'] / price)
        else:
            vol_limit = 1e10
        if self.__code in self.__exePriceQty and 'volume' in self.__exePriceQty.get(self.__code):
            volume = int(self.__exePriceQty.get(self.__code).get('volume'))
            volume = min(volume, vol_limit)
            if volume > net_position and vt_name not in ['MarketCloseLong', 'MarketCloseShort']:  # 翻转下单
                exposure = volume - net_position
                exposure = min(exposure, self._param['maxExposure'] / price, self._param['maxTurnoverPerOrder'] / price,
                               self.__positionManagerDict[vt_name].get_avail_qty())
                return int(exposure + net_position)
            else:
                return volume
        else:
            return min(net_position, vol_limit)

    def __place_order(self, code, side, price, quantity, is_open, timestamp, order_type, percentile_list=None, no_deal_list=None):
        date_timestamp = dt.datetime.fromtimestamp(timestamp)
        date_time = str(date_timestamp.time())
        # 若在禁止开仓时刻之后，且为开仓单，则不再开仓。平仓单不受影响
        if (date_time < self._param['trading_start_morning'] or date_time >= self._param['market_close_time']) and is_open:
            return
        if side == OrderSide.Buy:
            side_str = 'B'
        else:
            side_str = 'S'
        order = Order(code, None, price, quantity, side_str, date_timestamp, order_type, percentile_list, no_deal_list)
        order_number = self.__exchangeHouse.send(order)
        self.__orderInfo.update({code: OrderInfo(order_number, is_open)})

    def __make_order(self):
        if self.__code not in self.__orderInfo or self.__orderInfo.get(self.__code) is None:
            return
        order_info = self.__orderInfo.get(self.__code)
        order_number = order_info.orderNo
        if order_number is None:
            self.__orderInfo.pop(self.__code, None)
            return

        is_open = order_info.isOpen
        curr_timestamp = self.__slice_data.timeStamp
        exchange_order = self.__exchangeHouse.drive(order_number, self.__get_drive_time(self.__code, is_open, curr_timestamp))
        if exchange_order.orderNumber is None or exchange_order is None:
            self.__orderInfo.pop(self.__code, None)
            return

        # 开仓单必撤，平仓单需要在下一个Tick（当前）检查盘口
        exchange_order = self.__exchangeHouse.back(exchange_order.orderNumber)
        self.__order_finished(exchange_order)

    def __is_new_day(self):
        curr_timestamp = self.__slice_data.timeStamp
        flag = False
        if len(self.__preTagInfo) == 0 or self.__code not in self.__preTagInfo:
            flag = True
        elif dt.datetime.fromtimestamp(curr_timestamp).date() != dt.datetime.fromtimestamp(self.__preTagInfo.get(self.__code).timeStamp).date():
            flag = True
        return flag

    def __coming_new_day(self):
        init_qty = math.floor(self._param['init_qty'] / self._param['min_vol_qty'] - 1) * self._param['min_vol_qty']
        for vt_name in self.__vt_name_list:
            self.__executorDict[vt_name].reset_new_day(self.__slice_data.date)
            self.__positionManagerDict[vt_name].init_position(init_qty)
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

    def __order_finished(self, exchange_order):
        code = exchange_order.code
        self.__orderInfo.pop(code, None)
        order_type = exchange_order.orderType
        type_list = order_type.split('-')
        deal_list = self.__split_close_order_qty(exchange_order.bfbList, exchange_order.volume, exchange_order.mcjList)
        for i, vt_name in enumerate(type_list):
            eo = ExchangeOrder(Order(code, None, exchange_order.setPrice, exchange_order.mcjList[i], exchange_order.BSFlag, 0, vt_name), True)
            eo.lastUpdateTime = exchange_order.lastUpdateTime
            eo.volume = deal_list[i]
            eo.accMount = deal_list[i] / exchange_order.volume * exchange_order.accMount if exchange_order.volume > 0 else 0
            self.__positionManagerDict[vt_name].update_position(eo)
        net_position = self.__get_total_net_position()
        self.__outputManager.add_order(exchange_order, self.__split_reversed_cum_qty(self.__pre_net_position.get(code), net_position))
        self.__pre_net_position.update({code: net_position})

    def __is_open_long(self, predictions, vt_name):
        result = self.__executorDict[vt_name].is_open_long(predictions, self.__slice_data)
        return self.__check_executor_output(result)

    def __is_open_short(self, predictions, vt_name):
        result = self.__executorDict[vt_name].is_open_short(predictions, self.__slice_data)
        return self.__check_executor_output(result)

    def __is_close_long(self, predictions, vt_name):
        result = self.__executorDict[vt_name].is_close_long(predictions, self.__slice_data)
        return self.__check_executor_output(result)

    def __is_close_short(self, predictions, vt_name):
        result = self.__executorDict[vt_name].is_close_short(predictions, self.__slice_data)
        return self.__check_executor_output(result)

    def __is_market_close_long(self, vt_name):
        result = self.__executorDict[vt_name].is_market_close_long()
        return self.__check_executor_output(result)

    def __is_market_close_short(self, vt_name):
        result = self.__executorDict[vt_name].is_market_close_short()
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
            side = OrderSide.buy if net_position < 0 else OrderSide.sell
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

    def __vt_method_res(self, input_list, vt_method, is_reverse=False):
        if len(input_list) == 0:
            return None
        if vt_method == 'max':
            if is_reverse:
                return min(input_list)
            else:
                return max(input_list)
        elif vt_method == 'min':
            if is_reverse:
                return max(input_list)
            else:
                return min(input_list)
        elif vt_method == 'mean':
            return sum(input_list) / len(input_list)
        elif vt_method == 'sum':
            return sum(input_list)
        elif vt_method == 'vol_max_sum':
            vol_sum = sum(input_list)
            vol_max = max(input_list)
            vt_name = list(self.__executorDict.keys())[0]
            vol_ema = self.__executorDict[vt_name].get_ema_volume()
            if vol_sum < max(0.1 * vol_ema, 100):
                return vol_sum
            else:
                return vol_max
        elif vt_method in ['buy_vol_max_sum', 'sell_vol_max_sum']:
            vol_sum = sum(input_list)
            vol_max = max(input_list)
            oppo_vol = self.__slice_data.askVolume[0] if vt_method == 'buy_vol_max_sum' else self.__slice_data.bidVolume[0]
            if vol_sum < max(oppo_vol, 100):
                return vol_sum
            else:
                return vol_max

    # -----------------------------------------------------------------------------------
    # 交易结果分析
    def __return_tradings(self, code):
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
