import datetime as dt
from typing import Dict


class OutputManager:
    def __init__(self, cost, truncated=False):
        self.__non_closed_order_dict = {}  # 存入没有平仓的order; key = symbol, value = list
        self.__order_dict = {}  # key = symbol, value = list
        self.__detailed_order_dict = {}  # key = symbol, value = list
        self.__total_profit_dict: Dict[str, Dict[dt.date, float]] = {}  # key=symbol, value=dict{key=date, value=float}
        self.__daily_info_dict = {}  # key = symbol, value = dict: key = date, value = DailyInfo
        self.__cum_open_amount: Dict[str, Dict[dt.date, float]] = {}  # key=symbol, value=dict{key=date, value=float}
        self.__day_counts = {}  # key = symbol, value = int
        self.__trading_days_set = set()
        self.__split_cum_qty = {}  # key = symbol, value = tuple: closed position and open position
        self.__COST = cost
        self.__truncated = truncated
        self.__max_profit = None  # 获利最多日
        self.__min_profit = None  # 获利最少日
        self.__after_cost_earnings: Dict[str, Dict[dt.date, float]] = {}  # 净利润 value=dict{ key=date, value=float}

    def clear_non_closed(self, symbol):
        if symbol not in self.__detailed_order_dict:
            self.__detailed_order_dict.update({symbol: []})
        self.__update_detailed(symbol)
        self.__non_closed_order_dict.update({symbol: []})

    def add_order(self, exchange_order, split_reversed_cum_qty):
        symbol = exchange_order.code
        if symbol not in self.__non_closed_order_dict:
            self.__non_closed_order_dict.update({symbol: []})
        self.__non_closed_order_dict.get(symbol).append(exchange_order)
        if split_reversed_cum_qty is not None:
            self.__split_cum_qty.update({exchange_order.orderNumber: split_reversed_cum_qty})
            self.__do_output(symbol, exchange_order.orderTime.timestamp())
            self.__non_closed_order_dict.get(symbol).append(exchange_order)

    def register_output(self, symbol, start_timestamp):
        if symbol not in self.__non_closed_order_dict or len(self.__non_closed_order_dict.get(symbol)) == 0:
            return
        else:
            self.__do_output(symbol, start_timestamp)

    def __do_output(self, symbol, start_timestamp):
        if symbol not in self.__order_dict:
            self.__order_dict.update({symbol: []})
        if symbol not in self.__detailed_order_dict:
            self.__detailed_order_dict.update({symbol: []})
        size = len(self.__non_closed_order_dict.get(symbol))
        # make sure there are two directions
        process = False
        direction = self.__non_closed_order_dict.get(symbol)[0].BSFlag
        for i in range(size):
            if self.__non_closed_order_dict.get(symbol)[i].BSFlag != direction:
                process = True
                break
        if not process:
            self.clear_non_closed(symbol)
            return

        # update the self.__order_dict
        sum_open_amount_cum = 0
        sum_open_amount_order = 0
        sum_close_amount = 0
        sum_open_volume = 0
        sum_close_volume = 0
        temp_order = {}
        for i in range(size):
            exchange_order = self.__non_closed_order_dict.get(symbol)[i]
            if i == 0:
                temp_order.update({'code': symbol})
                temp_order.update({'startTime': exchange_order.orderTime.strftime('%m/%d/%y-%H:%M:%S')})
                if direction == 'B':
                    temp_order.update({'direction': 'long '})
                else:
                    temp_order.update({'direction': 'short'})
                temp_order.update({'startPrice': exchange_order.setPrice})
                if exchange_order.orderNumber in self.__split_cum_qty:
                    cum_qty_close = self.__split_cum_qty.get(exchange_order.orderNumber)[0]
                    cum_qty_open = self.__split_cum_qty.get(exchange_order.orderNumber)[1]
                    sum_open_amount_cum += cum_qty_open * exchange_order.price()
                    sum_open_amount_order += exchange_order.setPrice * (exchange_order.setVolume - cum_qty_close)
                    sum_open_volume += cum_qty_open
                else:
                    sum_open_amount_cum += exchange_order.accMount
                    sum_open_amount_order += exchange_order.setPrice * exchange_order.setVolume
                    sum_open_volume += exchange_order.volume
            elif i == size - 1:
                temp_order.update({'endPrice': exchange_order.setPrice})
                temp_order.update({'endTime': exchange_order.orderTime.strftime('%m/%d/%y-%H:%M:%S')})
                if exchange_order.BSFlag == direction:
                    if exchange_order.orderNumber in self.__split_cum_qty:
                        cum_qty_close = self.__split_cum_qty.get(exchange_order.orderNumber)[0]
                        sum_open_amount_cum += cum_qty_close * exchange_order.price()
                        sum_open_amount_order += exchange_order.setPrice * cum_qty_close
                        sum_open_volume += cum_qty_close
                    else:
                        sum_open_amount_cum += exchange_order.accMount
                        sum_open_amount_order += exchange_order.setPrice * exchange_order.setVolume
                        sum_open_volume += exchange_order.volume
                else:
                    if exchange_order.orderNumber in self.__split_cum_qty:
                        cum_qty_close = self.__split_cum_qty.get(exchange_order.orderNumber)[0]
                        sum_close_amount += cum_qty_close * exchange_order.price()
                        sum_close_volume += cum_qty_close
                    else:
                        sum_close_amount += exchange_order.accMount
                        sum_close_volume += exchange_order.volume
            else:
                if exchange_order.BSFlag == direction:
                    # open side
                    sum_open_amount_cum += exchange_order.accMount
                    sum_open_amount_order += exchange_order.setPrice * exchange_order.setVolume
                    sum_open_volume += exchange_order.volume
                else:
                    # close side
                    sum_close_amount += exchange_order.accMount
                    sum_close_volume += exchange_order.volume
        return_info = self.__cal_return(symbol, sum_open_amount_cum, sum_close_amount, direction, start_timestamp)
        if return_info is None:
            self.clear_non_closed(symbol)
            return
        temp_order.update({'orderAmount': sum_open_amount_order})
        temp_order.update({'cumAmount': sum_open_amount_cum})
        temp_order.update({'returnRate': return_info.return_rate})
        temp_order.update({'afterCostProfit': return_info.after_cost_profit})
        self.__order_dict.get(symbol).append(temp_order)
        self.clear_non_closed(symbol)

    def __update_detailed(self, symbol):
        combined_order = []
        if symbol not in self.__non_closed_order_dict or len(self.__non_closed_order_dict.get(symbol)) == 0:
            return
        else:
            for i in range(len(self.__non_closed_order_dict.get(symbol))):
                exchange_order = self.__non_closed_order_dict.get(symbol)[i]
                temp_order = {}
                temp_order.update({'code': symbol})
                temp_order.update({'orderTime': exchange_order.orderTime.strftime('%m/%d/%y-%H:%M:%S')})
                if exchange_order.BSFlag == 'B':
                    temp_order.update({'direction': 'long '})
                else:
                    temp_order.update({'direction': 'short'})
                temp_order.update({'price': exchange_order.setPrice})
                temp_order.update({'avgPrice': exchange_order.price()})
                temp_order.update({'status': exchange_order.order_state()})
                if exchange_order.orderNumber in self.__split_cum_qty:
                    if i == 0:
                        cum_qty_close = self.__split_cum_qty.get(exchange_order.orderNumber)[0]
                        cum_qty_open = self.__split_cum_qty.get(exchange_order.orderNumber)[1]
                        temp_order.update({'quantity': exchange_order.setVolume - cum_qty_close})
                        temp_order.update({'cumQty': cum_qty_open})
                        order_amount = (exchange_order.setVolume - cum_qty_close) * exchange_order.setPrice
                        temp_order.update({'orderAmount': round(order_amount, 2)})
                        temp_order.update({'cumAmount': exchange_order.price() * cum_qty_open})
                    else:
                        cum_qty_close = self.__split_cum_qty.get(exchange_order.orderNumber)[0]
                        temp_order.update({'quantity': cum_qty_close})
                        temp_order.update({'cumQty': cum_qty_close})
                        order_amount = cum_qty_close * exchange_order.setPrice
                        temp_order.update({'orderAmount': round(order_amount, 2)})
                        temp_order.update({'cumAmount': exchange_order.price() * cum_qty_close})
                else:
                    temp_order.update({'quantity': exchange_order.setVolume})
                    temp_order.update({'cumQty': exchange_order.volume})
                    order_amount = exchange_order.setVolume * exchange_order.setPrice
                    temp_order.update({'orderAmount': round(order_amount, 2)})
                    temp_order.update({'cumAmount': exchange_order.accMount})
                combined_order.append(temp_order)
            self.__detailed_order_dict.get(symbol).append(combined_order)

    def __cal_return(self, symbol, sum_open_amount_cum, sum_close_amount, direction, start_timestamp):
        if symbol not in self.__total_profit_dict:
            self.__total_profit_dict.update({symbol: {}})
        if symbol not in self.__cum_open_amount:
            self.__cum_open_amount.update({symbol: {}})
        if symbol not in self.__daily_info_dict:
            self.__daily_info_dict.update({symbol: {}})
        if symbol not in self.__after_cost_earnings:
            self.__after_cost_earnings.update({symbol: {}})
        adjusted_open_amount = sum_open_amount_cum
        adjusted_close_amount = sum_close_amount

        date = dt.datetime.fromtimestamp(start_timestamp).date()
        self.__trading_days_set.add(date)
        if date not in self.__daily_info_dict.get(symbol):
            self.__daily_info_dict.get(symbol).update({date: DailyInfo(0, 0)})
            self.__total_profit_dict.get(symbol).update({date: 0})
            self.__after_cost_earnings.get(symbol).update({date: 0})
            self.__cum_open_amount.get(symbol).update({date: 0})

        temp_cum_open_amount = self.__cum_open_amount.get(symbol).get(date)
        temp_cum_open_amount += adjusted_open_amount
        self.__cum_open_amount.get(symbol).update({date: temp_cum_open_amount})

        daily_info = self.__daily_info_dict.get(symbol).get(date)
        profit = self.__total_profit_dict.get(symbol).get(date)
        if direction == 'B':
            earning = adjusted_close_amount - adjusted_open_amount
            profit += earning
            daily_info.daily_profit += earning
            daily_info.daily_open_amount += adjusted_open_amount
            self.__daily_info_dict.get(symbol).update({date: daily_info})
            self.__total_profit_dict.get(symbol).update({date: profit})
            after_cost_earning = earning - self.__COST * adjusted_open_amount
            return_rate = round(adjusted_close_amount / adjusted_open_amount - 1, 5) if adjusted_open_amount != 0 else 0
        else:
            earning = adjusted_open_amount - adjusted_close_amount
            profit += earning
            daily_info.daily_profit += earning
            daily_info.daily_open_amount += adjusted_open_amount
            self.__daily_info_dict.get(symbol).update({date: daily_info})
            self.__total_profit_dict.get(symbol).update({date: profit})
            after_cost_earning = earning - self.__COST * adjusted_open_amount
            return_rate = round(1 - adjusted_close_amount / adjusted_open_amount, 5) if adjusted_open_amount != 0 else 0
        # Update the max and min profit, after cost
        if self.__max_profit is None:
            self.__max_profit = (date, after_cost_earning)
            self.__min_profit = (date, after_cost_earning)
        else:
            pre_earning = self.__after_cost_earnings.get(symbol).get(date)
            temp_earning = pre_earning + after_cost_earning
            if temp_earning > self.__max_profit[1]:
                self.__max_profit = (date, profit)
            self.__after_cost_earnings.get(symbol).update({date: temp_earning})
            min_key = min(self.__after_cost_earnings.get(symbol), key=self.__after_cost_earnings.get(symbol).get)
            self.__min_profit = (min_key, self.__after_cost_earnings.get(symbol).get(min_key))
        return ReturnInfo(round(after_cost_earning, 2), round(return_rate, 5))

    def add_one_day(self, symbol):
        if symbol not in self.__day_counts:
            self.__day_counts.update({symbol: 1})
        else:
            self.__day_counts[symbol] += 1

    def get_day_counts(self, symbol):
        if symbol not in self.__day_counts:
            return 0
        else:
            counts = len(self.__trading_days_set)
            if self.__truncated:
                if counts >= 5:
                    return counts - 2
                else:
                    return counts
            else:
                return counts

    def get_profit(self, symbol):
        if symbol not in self.__total_profit_dict:
            return 0
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                total = 0
                for date in self.__total_profit_dict.get(symbol).keys():
                    if date == self.__max_profit[0] or date == self.__min_profit[0]:
                        continue
                    else:
                        total += self.__total_profit_dict.get(symbol).get(date)
                return round(total, 2)
            else:
                total = 0
                for value in self.__total_profit_dict.get(symbol).values():
                    total += value
                return round(total, 2)

    def get_cum_open_amount(self, symbol):
        if symbol not in self.__cum_open_amount:
            return 0
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                total = 0
                for date in self.__cum_open_amount.get(symbol).keys():
                    if date == self.__max_profit[0] or date == self.__min_profit[0]:
                        continue
                    else:
                        total += self.__cum_open_amount.get(symbol).get(date)
                return round(total, 2)
            else:
                total = 0
                for value in self.__cum_open_amount.get(symbol).values():
                    total += value
                return round(total, 2)

    def get_order(self, symbol):
        if symbol not in self.__order_dict:
            return []
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                temp = []
                for order in self.__order_dict.get(symbol):
                    date = dt.datetime.strptime(order["startTime"], '%m/%d/%y-%H:%M:%S').date()
                    if date == self.__max_profit[0] or date == self.__min_profit[0]:
                        continue
                    else:
                        temp.append(order)
                return temp
            else:
                return self.__order_dict.get(symbol)

    def get_detailed_order(self, symbol):
        if symbol not in self.__detailed_order_dict:
            return []
        else:
            return self.__detailed_order_dict.get(symbol)

    def get_daily_profit_dict(self, symbol):
        if symbol not in self.__daily_info_dict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                daily_profit_dict = {}
                for date in self.__daily_info_dict.get(symbol).keys():
                    if date == self.__max_profit[0] or date == self.__min_profit[0]:
                        continue
                    else:
                        daily_profit_dict.update({str(date): round(self.__daily_info_dict.get(symbol).get(date).daily_profit, 2)})
                return daily_profit_dict
            else:
                daily_profit_dict = {}
                for date in self.__daily_info_dict.get(symbol).keys():
                    daily_profit_dict.update({str(date): round(self.__daily_info_dict.get(symbol).get(date).daily_profit, 2)})
                return daily_profit_dict

    def get_after_cost_daily_profit_dict(self, symbol):
        if symbol not in self.__daily_info_dict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                daily_profit_dict = {}
                for date in self.__daily_info_dict.get(symbol).keys():
                    if date == self.__max_profit[0] or date == self.__min_profit[0]:
                        continue
                    else:
                        daily_profit = self.__daily_info_dict.get(symbol).get(date).daily_profit
                        daily_open_amount = self.__daily_info_dict.get(symbol).get(date).daily_open_amount
                        after_cost_profit = daily_profit - self.__COST * daily_open_amount
                        daily_profit_dict.update({str(date): round(after_cost_profit, 2)})
                return daily_profit_dict
            else:
                daily_profit_dict = {}
                for date in self.__daily_info_dict.get(symbol).keys():
                    daily_profit = self.__daily_info_dict.get(symbol).get(date).daily_profit
                    daily_open_amount = self.__daily_info_dict.get(symbol).get(date).daily_open_amount
                    after_cost_profit = daily_profit - self.__COST * daily_open_amount
                    daily_profit_dict.update({str(date): round(after_cost_profit, 2)})
                return daily_profit_dict

    def get_daily_open_amount_dict(self, symbol):
        if symbol not in self.__daily_info_dict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                open_amount_dict = {}
                for date in self.__daily_info_dict.get(symbol).keys():
                    if date == self.__max_profit[0] or date == self.__min_profit[0]:
                        continue
                    else:
                        open_amount_dict.update({str(date): round(self.__daily_info_dict.get(symbol).get(date).daily_open_amount, 2)})
                return open_amount_dict
            else:
                open_amount_dict = {}
                for date in self.__daily_info_dict.get(symbol).keys():
                    open_amount_dict.update({str(date): round(self.__daily_info_dict.get(symbol).get(date).daily_open_amount, 2)})
                return open_amount_dict

    def get_daily_cancelled_ratio(self, symbol):
        if symbol not in self.__detailed_order_dict:
            return {}
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                cancelled_ratio_dict = {}
                for orders in self.__detailed_order_dict.get(symbol):
                    for order in orders:
                        date = dt.datetime.strptime(order["orderTime"], '%m/%d/%y-%H:%M:%S').date()
                        if date == self.__max_profit[0] or date == self.__min_profit[0]:
                            continue
                        else:
                            if str(date) not in cancelled_ratio_dict:
                                cancelled_ratio_dict.update({str(date): (0, 0)})
                            status = order["status"]
                            if 'cancelled' in status:  # cancelled, partially_cancelled
                                temp = list(cancelled_ratio_dict[str(date)])
                                temp[0] += 1
                                cancelled_ratio_dict[str(date)] = tuple(temp)
                            temp = list(cancelled_ratio_dict[str(date)])
                            temp[1] += 1
                            cancelled_ratio_dict[str(date)] = tuple(temp)
                for date in cancelled_ratio_dict.keys():
                    a, b = cancelled_ratio_dict[date]
                    ratio = a / b
                    cancelled_ratio_dict.update({date: ratio})
                return cancelled_ratio_dict
            else:
                cancelled_ratio_dict = {}
                for orders in self.__detailed_order_dict.get(symbol):
                    for order in orders:
                        date = dt.datetime.strptime(order["orderTime"], '%m/%d/%y-%H:%M:%S').date()
                        if str(date) not in cancelled_ratio_dict:
                            cancelled_ratio_dict.update({str(date): (0, 0)})
                        status = order["status"]
                        if 'cancelled' in status:  # cancelled, partially_cancelled
                            temp = list(cancelled_ratio_dict[str(date)])
                            temp[0] += 1
                            cancelled_ratio_dict[str(date)] = tuple(temp)
                        temp = list(cancelled_ratio_dict[str(date)])
                        temp[1] += 1
                        cancelled_ratio_dict[str(date)] = tuple(temp)
                for date in cancelled_ratio_dict.keys():
                    a, b = cancelled_ratio_dict[date]
                    ratio = a / b
                    cancelled_ratio_dict.update({date: ratio})
                return cancelled_ratio_dict

    def get_sum_cancelled_ratio(self, symbol):
        if symbol not in self.__detailed_order_dict:
            return 0
        else:
            if self.__truncated and len(self.__trading_days_set) >= 5:
                order_num = 0
                cancelled_num = 0
                for orders in self.__detailed_order_dict.get(symbol):
                    for order in orders:
                        date = dt.datetime.strptime(order["orderTime"], '%m/%d/%y-%H:%M:%S').date()
                        if date == self.__max_profit[0] or date == self.__min_profit[0]:
                            continue
                        status = order['status']
                        if 'cancelled' in status:
                            cancelled_num += 1
                        order_num += 1
                if order_num == 0:
                    ratio = 0.0
                else:
                    ratio = cancelled_num / order_num
                return ratio
            else:
                order_num = 0
                cancelled_num = 0
                for orders in self.__detailed_order_dict.get(symbol):
                    for order in orders:
                        status = order['status']
                        if 'cancelled' in status:
                            cancelled_num += 1
                        order_num += 1
                if order_num == 0:
                    ratio = 0.0
                else:
                    ratio = cancelled_num / order_num
                return ratio


class DailyInfo:
    def __init__(self, daily_profit, daily_open_amount):
        self.daily_profit = daily_profit
        self.daily_open_amount = daily_open_amount


class ReturnInfo:
    # profit is after cost; return rate is pre-cost
    def __init__(self, after_cost_profit, return_rate):
        self.after_cost_profit = after_cost_profit
        self.return_rate = return_rate
