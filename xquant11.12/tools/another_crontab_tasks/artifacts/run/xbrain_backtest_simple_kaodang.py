# -*- coding: utf-8 -*-
# 单边买，按单笔执行价，止损订单
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from xbrain_position_manager import PositionManager
from xbrain import Order
import pandas as pd
import numpy as np
import time
from datetime import datetime
from collections import defaultdict
import os
import json
pd.set_option('display.max_columns', None)


class StrategySignalT0SwiftProfit(StrategyBase):  # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('init_open_long_th', 1.6),
        ('init_open_short_th', -1.6),
        ('init_close_long_th', -1.6),
        ('init_close_short_th', 1.6),
        ('init_close_long_risk_th', -6.0),
        ('init_close_short_risk_th', 6.0),
        ('START_PERIOD', "09:30:30"),
        ('UNIT_QTY_PER_ORDER', 1000),  # 标准每笔委托的成交笔数, 根据股票成交是否活跃设置
        ('ADJUST_VOLUME', False),  #暂未使用
        ('optimal_price_stoploss_th', -3),  # 订单最优价止损比例
        ('stoploss_th', -5),  # 订单单价止损比例
        ('takeprofit_th', 2),  # 最大止盈比例
        ('swift_takeprofit_th', 1.4),  # 初始止盈比例
        ('tradesize', 400),  # 每笔交易股数
        ('OPEN_PRICE_MODE', 0),
        ('CLOSE_LOSE_PRICE_MODE', 0),  #平仓止损
        ('CLOSE_WIN_PRICE_MODE', 0),  # 平仓止盈
        ("DEVIATION_SELF_PRICE", 1),  # 己方最优报价偏移Tick数
        ('HOLD_POSITION_LIMIT', 1600),  #单边敞口上限
        ('SELL_POSITION_LIMIT', 10000),  #单日卖出底仓限制
        ('CANCEL_WAIT_SECONDS', 1),  #未成交订单的等待撤单时间
        ('WIN_CANCEL_WAIT_SECONDS', 120),  # 未成交订单的等待撤单时间
        ("signal_file", None),
        ("log_level", "info")
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.vol = self.data.volume
        self.ema_vol = xb.talib.EMA(self.data.volume, timeperiod=5)
        self.signal_df = pd.read_parquet(self.p.signal_file)
        self.next_signal_idx = 0
        self.max_signal_idx = len(self.signal_df)
        print("long short th:", self.p.init_open_long_th, self.p.init_open_short_th)
        self.global_stop_flag = False
        self.log_level = self.p.log_level
        self.position_mgr = PositionManager(self.p.HOLD_POSITION_LIMIT, self.p.SELL_POSITION_LIMIT)
        self.last_tick_position = 0
        print(self.params.__dict__)


    def start(self):
        # 新的一天重置策略
        self.reset_on_new_day()

    def _midprice(self, last_price_df):
        if not last_price_df.ask1price and not last_price_df.bid1price:
            curr_price = last_price_df.close
        elif not last_price_df.ask1price:
            curr_price = last_price_df.bid1price
        elif not last_price_df.bid1price:
            curr_price = last_price_df.bid1price
        else:
            curr_price = (last_price_df.ask1price + last_price_df.bid1price) / 2
        return curr_price

    def _calc_ema(self, arr, alpha=0.75, window=5):
        if len(arr) == 0:
            return 0
        else:
            start_idx = max(0, len(arr) - window)
            ema = arr[start_idx]
            for a in arr[start_idx:]:
                ema = (1 - alpha) * ema + alpha * a
            return ema

    def reset_on_new_day(self):
        self.signal_long = np.array([0.0])
        self.signal_short = np.array([0.0])
        self.signal_long_delta = np.array([0.0])
        self.signal_short_delta = np.array([0.0])

        self.open_long_th = 0.0
        self.open_short_th = 0.0
        self.close_long_th = 0.0
        self.close_short_th = 0.0
        self.open_long_times = 0  # 以多头开仓的次数
        self.open_short_times = 0
        self.i = 0

        self.init_position = {}
        self.set_init_open_close_th()
        self.cancel_wait_time =  self.p.CANCEL_WAIT_SECONDS
        self.win_cancel_wait_time = self.p.WIN_CANCEL_WAIT_SECONDS
        self.deviation_self_price = self.p.DEVIATION_SELF_PRICE
        self.open_price_mode = self.p.OPEN_PRICE_MODE
        self.close_lose_price_mode = self.p.CLOSE_LOSE_PRICE_MODE
        self.close_win_price_mode = self.p.CLOSE_WIN_PRICE_MODE
        self.wait_for_normal_count_limit = 241
        self.wining_price = 0.0



    def set_init_open_close_th(self):
        # 设置初始信号阈值
        self.init_open_long_th = self.p.init_open_long_th
        self.init_open_short_th = self.p.init_open_short_th
        self.init_close_long_th = self.p.init_close_long_th
        self.init_close_short_th = self.p.init_close_short_th
        self.init_close_long_risk_th = self.p.init_close_long_risk_th
        self.init_close_short_risk_th = self.p.init_close_short_risk_th
        self.init_takeprofit_th = self.p.takeprofit_th
        self.init_stoploss_th = self.p.stoploss_th
        self.init_optimal_price_stoploss_th = self.p.optimal_price_stoploss_th



    def get_up_down_limit(self, stock):
        # 获取涨跌停
        return 0.195 if stock.startswith('3') or stock.startswith('68') else 0.095


    def notify_order(self, order):
        super().notify_order(order)
        stock = order.data.getdataname()

        if order.status in [order.Partial, order.Completed]:
            position = self.get_position_by_name(stock)
            # 订单成交时，更新净持仓s
            if self.position_mgr.net_position == 0:
                #记录开仓单的时间
                self.last_open_time = xb.num2date(self.get_data_by_name(stock).datetime[0])
                assert (len(self.position_mgr.buy_position_order_dict) ==0 or pd.DataFrame(self.position_mgr.buy_position_order_dict).T["open_size"].sum()==0) \
                       and (len(self.position_mgr.sell_position_order_dict)==0 or pd.DataFrame(self.position_mgr.sell_position_order_dict).T["open_size"].sum()==0), "持仓为0"

            # 更新持仓表
            self.position_mgr.update_position_exec(order)
            if self.position_mgr.net_position == 0:
                #记录平仓时间
                self.last_open_time = None
                self.open_short_times = 0
                self.open_long_times = 0
                self.open_long_th = 0.0
                self.open_short_th = 0.0

            if self.position_mgr.net_position*self.position_mgr.last_net_position<=0:
                # 撤回所有止盈单
                for order_ref in self.position_mgr.wining_pending_order:
                    self.cancel(self.position_mgr.wining_pending_order[order_ref]["order"])
                self.position_mgr.wining_pending_order.clear()

            if self.position_mgr.net_position > 0 and self.position_mgr.net_position > self.position_mgr.last_net_position and order.isbuy():
                self.wining_price = round(order.exec_price * (1 + self.p.swift_takeprofit_th / 1000), 2)
                print("self.wining_price:", self.wining_price)
            if self.position_mgr.net_position < 0 and self.position_mgr.net_position < self.position_mgr.last_net_position and order.issell():
                self.wining_price = round(order.exec_price * (1 - self.p.swift_takeprofit_th / 1000), 2)
                print("self.wining_price:", self.wining_price)

        if order.status in [order.Canceled]:
            self.position_mgr.update_position_cancel(order)

    def __update_hedge_order_closing_size(self, hedge_order, parent_order):
        pass

    def sell(self, size=None, price=None, exectype=None, parent_order=None):
        size = int(size)
        net_position = self.position_mgr.net_position
        if self.position_mgr.sellable_position - size >= 0:
            if net_position > 0:
                if abs(net_position - size - self.position_mgr.sellsize_onway) <= self.position_mgr.hold_position_limit:
                    sell_order = super(StrategySignalT0SwiftProfit, self).sell(price=price, size=size,
                                                                          exectype=xb.Order.Limit)
                    self.position_mgr.sellable_position = self.position_mgr.sellable_position - size
                    self.position_mgr.sellsize_onway = self.position_mgr.sellsize_onway + size
                    if parent_order:
                        self.__update_hedge_order_closing_size(sell_order, parent_order)
                    return sell_order
                else:
                    self.log("无法下卖单：超过单边敞口！", level = self.log_level)
            else:
                if abs(net_position) + abs(size) + self.position_mgr.sellsize_onway <= self.position_mgr.hold_position_limit:
                    sell_order = super(StrategySignalT0SwiftProfit, self).sell(price=price, size=size,
                                                                          exectype=xb.Order.Limit)
                    self.position_mgr.sellable_position = self.position_mgr.sellable_position - size
                    self.position_mgr.sellsize_onway = self.position_mgr.sellsize_onway + size
                    if parent_order:
                        self.__update_hedge_order_closing_size(sell_order, parent_order)
                    # print("==========================================")
                    # print(f"""tmk.send_order(stock_code="688390.SH", order_time={self.now_datetime.strftime("%Y%m%d%H%M%S%f")}, order_price={price}, order_volume={size},bs_flag="S")""")
                    return sell_order
                else:
                    self.log("无法下卖单：超过单边敞口！", level = self.log_level)
        else:
            if not net_position:
                self.global_stop_flag = True
            self.log("今日底仓已用完，不再开仓！", level = self.log_level)


    def buy(self, size=None, price=None, exectype=None, parent_order=None):
        if self.now_datetime.strftime("%H%M%S")=="100214":
            a = 1
        size = int(size)
        net_position = self.position_mgr.net_position
        if self.position_mgr.sellable_position - net_position - size - self.position_mgr.buysize_onway >= 0:
            if net_position >= 0:
                if abs(net_position) + abs(size) + self.position_mgr.buysize_onway <= self.position_mgr.hold_position_limit:
                    buy_order = super(StrategySignalT0SwiftProfit, self).buy(price=price, size=int(size),
                                                                        exectype=xb.Order.Limit)
                    self.position_mgr.buysize_onway = self.position_mgr.buysize_onway + size
                    if parent_order:
                        # 当前订单是对冲单，更新对冲单状态
                        self.__update_hedge_order_closing_size(buy_order, parent_order)
                    return buy_order
                else:
                    self.log("无法下买单：超过单边敞口！", level = self.log_level)
            else:
                if abs(net_position + size + self.position_mgr.buysize_onway) <= self.position_mgr.hold_position_limit:
                    buy_order = super(StrategySignalT0SwiftProfit, self).buy(price=price, size=int(size),
                                                                        exectype=xb.Order.Limit)
                    self.position_mgr.buysize_onway = self.position_mgr.buysize_onway + size
                    if parent_order:
                        # 当前订单是对冲单，更新对冲单状态
                        self.__update_hedge_order_closing_size(buy_order, parent_order)
                    return buy_order
                else:
                    self.log("无法下买单：超过单边敞口！", level = self.log_level)
        else:
            if not net_position:
                self.global_stop_flag = True
            self.log("今日底仓已用完，不再开仓！", level = self.log_level)


    def calc_adjust_price(self, side, last_price_df, mode = -2):
        #preference值越大，价格越保守，值越小，价格约激进
        if mode < 0:
            #对手方最优
            if side == Order.Buy:
                price = last_price_df.ask1price if last_price_df.ask1price else  round(last_price_df.bid1price*1.0002, 2)
            else:
                price = last_price_df.bid1price if last_price_df.bid1price else round(last_price_df.ask1price*0.9998, 2)
        elif mode == 0:
            # 本方最优, 增加一个tick
            if side == Order.Buy:
                # price = round(last_price_df.bid1price*1.0002, 2)
                price = min(last_price_df.bid1price+self.deviation_self_price*0.01, last_price_df.ask1price)
            else:
                # price = round(last_price_df.ask1price * 0.9998, 2)
                price = max(last_price_df.ask1price-self.deviation_self_price*0.01, last_price_df.bid1price)
                # price = last_price_df.bid1price - 0.01
        elif mode > 0:
            #本方最优
            if side == Order.Buy:
                price = last_price_df.bid1price if last_price_df.bid1price else round(last_price_df.ask1price*0.9998, 2)
            else:
                price = last_price_df.ask1price if last_price_df.ask1price else round(last_price_df.bid1price*1.0002, 2)
        return price



    def calc_adjust_price_wining(self, side, last_price_df, wining_price):
        if side == Order.Buy:
            price_list = [last_price_df.bid1price, last_price_df.bid2price, last_price_df.bid3price,
                          last_price_df.bid4price, last_price_df.bid5price, last_price_df.bid6price,
                          last_price_df.bid7price, last_price_df.bid8price, last_price_df.bid9price, last_price_df.bid10price
                          ]
            price = wining_price
            for p in price_list:
                if wining_price <= p:
                    # 挂靠最近一档价格
                    price = p
                else:
                    price = p
                    break
        elif side == Order.Sell:
            price_list = [last_price_df.ask1price, last_price_df.ask2price, last_price_df.ask3price,
                          last_price_df.ask4price, last_price_df.ask5price, last_price_df.ask6price,
                          last_price_df.ask7price, last_price_df.ask8price, last_price_df.ask9price,
                          last_price_df.ask10price]
            price = wining_price
            for p in price_list:
                if wining_price >= p:
                    # 挂靠最近一档价格
                    price = p
                else:
                    price = p
                    break
        else:
            raise Exception()
        return price


    def process_init_openning(self, stock, side, last_price_df):
        def __cal_vol_ratio(prediction, base, times):
            return abs(prediction) / (abs(base) + 0.1) / (times + 1)

        # 根据信号和行情下单逻辑
        signal_long = self.signal_long[-1]
        signal_short = self.signal_short[-1]
        net_position = self.position_mgr.net_position

        price = self.calc_adjust_price(side, last_price_df, mode=self.open_price_mode)
        if side == Order.Buy:
            # 开多, 判断大于上一次阈值才开
            # if net_position > 0 and signal_long < self.open_long_th:
            #     return
            self.open_long_th = signal_long  # 上一次开仓的阈值
            size= self.p.tradesize
            if abs(net_position + size) <= self.position_mgr.hold_position_limit:
                self.log("开仓多头下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size, self.signal_long[-5:]), level = self.log_level)
                order = self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                if order:
                    self.position_mgr.add_signal_pending_order(order)
                    self.open_long_times = self.open_long_times + 1
        elif side == Order.Sell:
            # 开空， 判断大于上一次阈值才开
            # if net_position < 0 and signal_short > self.open_short_th:
            #     return
            self.open_short_th = signal_short  # 上一次开仓的阈值
            self.tick_count_since_init_open_short = 0
            size = self.p.tradesize
            if abs(net_position - size) <= self.position_mgr.hold_position_limit and self.position_mgr.sellable_position > 0:
                self.log("开仓空头下单:  price {}, volume {}, self.signal_short[-5;] {}!".format(price, size, self.signal_short[-5:]), level = self.log_level)
                order = self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
                if order:
                    self.position_mgr.add_signal_pending_order(order)
                    self.open_short_times = self.open_short_times + 1


    def process_morning_close(self, stock, last_price_df):
        size = abs(int(self.position_mgr.net_position))
        # size = int(size / 100) * 100
        if self.position_mgr.net_position > 0:
            # 设置为激进挂单价格
            price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_lose_price_mode)
        elif self.position_mgr.net_position < 0:
            price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_lose_price_mode)

        if self.position_mgr.net_position > 0:
            self.log("尾盘平仓: signal short {}, price {}, volume {}!".format(self.signal_short[-1], price, size), level = self.log_level)
            order = self.sell(price=price, size=size, exectype=xb.Order.Limit)
            if order:
                self.position_mgr.add_signal_pending_order(order)
            self.open_long_times = 0
        elif self.position_mgr.net_position < 0:
            self.log("尾盘平仓: signal long {}, price {}, volume {}!".format(self.signal_long[-1], price, size), level = self.log_level)
            order = self.buy(price=price, size= size, exectype=xb.Order.Limit)
            if order:
                self.position_mgr.add_signal_pending_order(order)
            self.open_short_times = 0

    # 计算当前收益率(单位千分数)
    def __calc_return(self, position_side, base_price, last_price_df, mode = "midprice"):
        if mode == "midprice":
            # 中间价计算收益率
            curr_price = self._midprice(last_price_df)
            curr_return = 0
            if position_side == Order.Sell:
                if base_price is not None and base_price != 0:
                    curr_return = (base_price - curr_price) / base_price * 1000
            elif position_side == Order.Buy:
                if base_price is not None and base_price != 0:
                    curr_return = (curr_price - base_price) / base_price * 1000
            else:
                raise Exception("OrderSide Error!")
            return curr_return

    def check_and_process_stop_loss(self, symbol, last_price_df, mode = 0):
        net_position = self.position_mgr.net_position
        # 相对于历史最优价计算收益率
        msg = "历史最优价"
        if self.position_mgr.net_position > 0:
            base_price = self.position_mgr.net_position_his_high[symbol]
            ret_base_price = self.__calc_return(position_side=Order.Buy, base_price = base_price, last_price_df = last_price_df)
            if abs(ret_base_price) >= abs(self.p.optimal_price_stoploss_th):
                net_size = self.position_mgr.net_position
                # 如果已有在途多单，不需要再重复平多头
                # 如果已有在途多单，不需要再重复平多头
                size = net_size - self.position_mgr.sellsize_onway
                if size > 0:
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_win_price_mode)
                    self.log("最优价止损平多头: 到达开仓单{}止损线: ret 千分之{}，持仓数量 {}，平仓数量 {}， 平仓价格 {}。".format(msg, ret_base_price,
                                                                                                net_size,net_size, price), level = self.log_level)
                    hedge_order = self.sell(price=price, size=net_size, exectype=xb.Order.Limit)
                    if hedge_order:
                        self.position_mgr.add_stop_pending_order(hedge_order)
                else:
                    # 撤回止盈单
                    for order_ref in self.position_mgr.wining_pending_order:
                        w_order_data = self.position_mgr.wining_pending_order[order_ref]
                        w_order = w_order_data["order"]
                        self.cancel(w_order)
            else:
                buy_position_order_dict =  self.position_mgr.buy_position_order_dict
                for p_order_ref in buy_position_order_dict:
                    p_order = buy_position_order_dict[p_order_ref]["order"]
                    net_size = abs(buy_position_order_dict[p_order_ref]["open_size"])
                    if net_size<=0:
                        continue
                    ret_single_price = self.__calc_return(position_side=Order.Buy, base_price=p_order.price,
                                                          last_price_df=last_price_df)
                    # 如果已有在途多单，不需要再重复平多头
                    size = net_size - self.position_mgr.sellsize_onway
                    if size > 0:
                        if ret_single_price <= self.p.stoploss_th:
                            price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_lose_price_mode)
                            self.log(
                                "止损平多头: 到达开仓单执行价止损线: ret 千分之{}，持仓数量 {}， 平仓数量 {}，平仓价格 {}。".format(ret_single_price,
                                                                                        net_size,net_size, price),
                                level = self.log_level)
                            hedge_order = self.sell(price=price, size=net_size, exectype=xb.Order.Limit,
                                                    parent_order=p_order)
                            if hedge_order:
                                self.position_mgr.add_stop_pending_order(hedge_order)
                        elif ret_single_price >= self.p.takeprofit_th:
                            price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_lose_price_mode)  # 止盈按本方最优
                            self.log(
                                "止盈平多头，到达开仓单执行价止盈线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(ret_single_price, net_size, price),
                                level = self.log_level)
                            hedge_order = self.sell(price=price, size=net_size, exectype=xb.Order.Limit,
                                                    parent_order=p_order)
                            if hedge_order:
                                self.position_mgr.add_stop_pending_order(hedge_order)
                    else:
                        # 撤回止盈单
                        for order_ref in self.position_mgr.wining_pending_order:
                            w_order_data = self.position_mgr.wining_pending_order[order_ref]
                            w_order = w_order_data["order"]
                            self.cancel(w_order)
        else:
            base_price = self.position_mgr.net_position_his_low[symbol]
            ret_base_price = self.__calc_return(Order.Sell, base_price, last_price_df)
            if abs(ret_base_price) >= abs(self.p.optimal_price_stoploss_th):
                price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_win_price_mode)
                net_size = abs(self.position_mgr.net_position)
                # 如果已有在途多单，不需要再重复平空头
                size = net_size - self.position_mgr.buysize_onway
                if size > 0:
                    self.log("最优价止损平空头：到达开仓单最优价{}止损线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(msg, ret_base_price, net_size,
                                                                                          price), level = self.log_level)
                    hedge_order = self.buy(price=price, size=abs(net_size), exectype=xb.Order.Limit)
                    if hedge_order:
                        self.position_mgr.add_stop_pending_order(hedge_order)
                else:
                    # 撤回止盈单
                    for order_ref in self.position_mgr.wining_pending_order:
                        w_order_data = self.position_mgr.wining_pending_order[order_ref]
                        w_order = w_order_data["order"]
                        self.cancel(w_order)
            else:
                sell_position_order_dict = self.position_mgr.sell_position_order_dict
                for p_order_ref in sell_position_order_dict:
                    p_order = sell_position_order_dict[p_order_ref]["order"]
                    net_size = abs(sell_position_order_dict[p_order_ref]["open_size"])
                    if net_size<=0:
                        continue
                    ret_single_price = self.__calc_return(Order.Sell, p_order.price, last_price_df)
                    # 如果已有在途多单，不需要再重复平空头
                    size = abs(net_size) - self.position_mgr.buysize_onway
                    if size > 0:
                        if ret_single_price <= self.p.stoploss_th:
                            price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_lose_price_mode)
                            self.log("止损平空头：到达开仓单执行价止损线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(ret_single_price, net_size, price), level = self.log_level)
                            hedge_order = self.buy(price=price, size=abs(net_size), exectype=xb.Order.Limit, parent_order=p_order)
                            if hedge_order:
                                self.position_mgr.add_stop_pending_order(hedge_order)
                        elif ret_single_price >= self.p.takeprofit_th:
                            price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_lose_price_mode)  # 止盈按本方最优
                            self.log("止盈平多头： 到达开仓单执行价止盈线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(ret_single_price, net_size, price), level = self.log_level)
                            hedge_order = self.buy(price=price, size=abs(net_size), exectype=xb.Order.Limit, parent_order=p_order)
                            if hedge_order:
                                self.position_mgr.add_stop_pending_order(hedge_order)
                    else:
                        # 撤回止盈单
                        for order_ref in self.position_mgr.wining_pending_order:
                            w_order_data = self.position_mgr.wining_pending_order[order_ref]
                            w_order = w_order_data["order"]
                            self.cancel(w_order)


    def check_win_hedge_order(self, symbol, last_price_df):
        wining_price = self.wining_price
        net_postion = self.position_mgr.net_position
        wining_pending_order = self.position_mgr.wining_pending_order

        if net_postion > 0 :
            assert pd.DataFrame(self.position_mgr.buy_position_order_dict).T["open_size"].sum() == net_postion, "持仓不一致！"
            accu_hedge_size = 0
            # 暂不更新wining_pending_order,等到notify_order时再移除
            win_order_refs = list(wining_pending_order.keys())
            for order_ref in win_order_refs:
                w_order_data = wining_pending_order[order_ref]
                w_order = w_order_data["order"]
                # 理论上只会有一边的wining_pending_order
                if w_order.isbuy() and self.position_mgr.net_position*self.position_mgr.last_net_position>0:
                    raise Exception()
                # 注意：hedge_size也有正负，和net_position一样
                accu_hedge_size = accu_hedge_size + w_order_data["exec_remsize"]
                if (xb.num2date(w_order_data["order"].data.datetime[0]) - xb.num2date(
                        w_order_data["create_dt"])).total_seconds() >= self.win_cancel_wait_time:
                    # 到达持仓时间
                    self.cancel(w_order)
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode=self.close_lose_price_mode)
                    size = abs(w_order_data["exec_remsize"])
                    order = self.sell(price = price, size=size, exectype=xb.Order.Limit)
                    if order:
                        self.position_mgr.add_stop_pending_order(order)
                    self.log("持仓多头，到达持仓时间撤回止盈：持仓 {}，止盈单量转换为止损单，数量为 {}".format(net_postion, size
                                                                              ), level=self.log_level)
                    continue

                if accu_hedge_size + net_postion < 0:
                    # 持仓已止损了一部分，撤回来报剩余的那部分
                    self.cancel(w_order)
                    cancel_size = min(abs(accu_hedge_size + net_postion), abs(w_order_data["exec_remsize"]))
                    size = abs(w_order_data["exec_remsize"]) - cancel_size
                    if size > 0:
                        if wining_price and wining_price > w_order.created.price:
                            price = self.calc_adjust_price_wining(Order.Sell, last_price_df, wining_price)
                        else:
                            price = w_order.created.price
                        order = self.sell(price=price, size=abs(size), exectype=xb.Order.Limit)
                        self.log("持仓多头，已止盈或止损并撤回部分止盈单：持仓 {}，撤回止盈单量 {}".format(net_postion, cancel_size,
                                                                           ), level=self.log_level)
                        if order:
                            self.position_mgr.add_wining_pending_order(order, create_dt=w_order_data["create_dt"])
                    continue

                if wining_price and wining_price > w_order.created.price:
                    # 重挂止盈线
                    size = abs(w_order_data["exec_remsize"])
                    price = self.calc_adjust_price_wining(Order.Sell, last_price_df, wining_price)
                    if price > w_order.created.price:
                        self.cancel(w_order)
                        order = self.sell(price=price, size=abs(size), exectype=xb.Order.Limit)
                        self.log("持仓多头：重挂止盈线：持仓 {}，挂单量 {} old {} new {}".format(net_postion, size, w_order.created.price,  wining_price), level = self.log_level)
                        if order:
                            self.position_mgr.add_wining_pending_order(order, create_dt=w_order_data["create_dt"])
                    else:
                        self.log("持仓多头：止盈线未变高，无需重挂止盈线！")
                    self.wining_price =0.0 #当前的止盈价格已使用

            if accu_hedge_size + net_postion>0:
                size = net_postion - abs(accu_hedge_size)
                if not wining_price:
                    print("WARNING: 未更新止盈价！")
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode=self.close_lose_price_mode)
                    # 止盈价已使用过，不再重复止盈
                    return
                else:
                    price = self.calc_adjust_price_wining(Order.Sell, last_price_df, wining_price)
                order = self.sell(price = price, size = size, exectype=xb.Order.Limit)
                if order:
                    self.position_mgr.add_wining_pending_order(order)
                self.wining_price = 0.0  # 当前的止盈价格已使用
                self.log("持仓多头，新增止盈单：持仓 {}，新增止盈单 价{}，量 {}".format(net_postion,wining_price, size), level=self.log_level)
        elif self.position_mgr.net_position<0:
            assert pd.DataFrame(self.position_mgr.sell_position_order_dict).T["open_size"].sum() == abs(net_postion), "持仓不一致！"
            accu_hedge_size = 0
            # 暂不更新wining_pending_order,等到notify_order时再移除
            win_order_refs = list(wining_pending_order.keys())
            for order_ref in win_order_refs:
                w_order_data = wining_pending_order[order_ref]
                w_order = w_order_data["order"]
                # 理论上只会有一边的wining_pending_order
                if w_order.issell() and self.position_mgr.net_position*self.position_mgr.last_net_position>0:
                    raise Exception()
                accu_hedge_size = accu_hedge_size + w_order_data["exec_remsize"]
                if (xb.num2date(w_order_data["order"].data.datetime[0]) - xb.num2date(
                        w_order_data["create_dt"])).total_seconds() >= self.win_cancel_wait_time:
                    # 到达持仓时间
                    self.cancel(w_order)
                    price = self.calc_adjust_price(Order.Buy, last_price_df, mode=self.close_lose_price_mode)
                    size = w_order_data["exec_remsize"]
                    order = self.buy(price = price, size = size, exectype=xb.Order.Limit)
                    if order:
                        self.position_mgr.add_stop_pending_order(order)
                    self.log("持仓空头，到达持仓时间撤回止盈：持仓 {}，撤回止盈单量 {}".format(net_postion, w_order_data["exec_remsize"]
                                                                      ), level=self.log_level)
                    continue
                if accu_hedge_size + net_postion > 0:
                    # 持仓已止损了一部分，撤回来报剩余的那部分
                    self.cancel(w_order)
                    cancel_size = min(accu_hedge_size - abs(net_postion), w_order_data["exec_remsize"])
                    size = w_order_data["exec_remsize"] - cancel_size
                    if size > 0:
                        if wining_price and wining_price > w_order.created.price:
                            price = self.calc_adjust_price_wining(Order.Buy, last_price_df, wining_price)
                        else:
                            price = w_order.created.price
                        order = self.buy(price=price, size=abs(size), exectype=xb.Order.Limit)
                        self.log("持仓空头，已止盈或止损并撤回部分止盈单：持仓 {}，撤回止盈单量 {}".format(net_postion,
                                                                           cancel_size), level=self.log_level)
                        if order:
                            self.position_mgr.add_wining_pending_order(order, create_dt=w_order_data["create_dt"])
                    continue
                if wining_price and wining_price < w_order.created.price:
                    # 重挂止盈线
                    size = w_order_data["exec_remsize"]
                    price = self.calc_adjust_price_wining(Order.Buy, last_price_df, wining_price)
                    if price < w_order.created.price:
                        self.cancel(w_order)
                        order = self.buy(price=price, size=abs(size), exectype=xb.Order.Limit)
                        self.log("持仓空头：重挂止盈线：持仓 {}，挂单量 {} old {} new {}".format(net_postion, size, w_order.created.price,
                                                                                wining_price), level=self.log_level)
                        if order:
                            self.position_mgr.add_wining_pending_order(order, create_dt=w_order_data["create_dt"])
                    else:
                        self.log("持仓空头：止盈线未变低，无需重挂止盈线！")
                    self.wining_price = 0.0  # 当前的止盈价格已使用


            if accu_hedge_size + net_postion < 0:
                size = abs(net_postion) - accu_hedge_size
                if not wining_price:
                    print("WARNING: 未更新止盈价！")
                    price = self.calc_adjust_price(Order.Buy, last_price_df, mode=self.close_lose_price_mode)
                    # 止盈价已使用过，不再重复止盈
                    return
                else:
                    price = self.calc_adjust_price_wining(Order.Buy, last_price_df, wining_price)
                order = self.buy(price = price, size = size, exectype=xb.Order.Limit)
                if order:
                    self.position_mgr.add_wining_pending_order(order)
                self.wining_price = 0.0  # 当前的止盈价格已使用
                self.log("持仓空头，新增止盈单：持仓 {}，新增止盈单,价 {}，量 {}".format(net_postion, wining_price, size), level=self.log_level)
        elif net_postion==0:
            wining_pending_order = self.position_mgr.wining_pending_order
            win_order_refs = list(wining_pending_order.keys())
            for order_ref in win_order_refs:
                w_order_data = wining_pending_order.pop(order_ref)
                self.cancel(w_order_data["order"])

    def get_last_signal(self, now_datetime):
        next_signal_idx = self.next_signal_idx
        # print(now_datetime, self.signal_df.iloc[next_signal_idx]["PERIOD_BEGIN"])
        if self.signal_df.iloc[next_signal_idx]["PERIOD_BEGIN"] <= now_datetime:
            # 下一个信号，生效
            last_signal_df = self.signal_df.iloc[next_signal_idx]
            while self.next_signal_idx + 1 < self.max_signal_idx and self.signal_df.iloc[self.next_signal_idx][
                "PERIOD_BEGIN"] <= now_datetime:
                # 准备下一个信号，待生效
                self.next_signal_idx = self.next_signal_idx + 1
            return last_signal_df["PERIOD_BEGIN"],last_signal_df["PREDICTED"]
        elif self.signal_df.iloc[next_signal_idx]["PERIOD_BEGIN"] > now_datetime:
            return now_datetime,0

    def next(self):
        if self.global_stop_flag:
            return
        self.i = self.i + 1
        stock = self.datas[0]._name
        now_datetime = xb.num2date(self.datas[0].datetime[0])
        self.now_datetime = now_datetime
        nowtime = now_datetime.time().strftime('%H:%M:%S')
        # 传入标的查询行情数据
        price_df = self.get_past_feed_price_df(datanames=stock, lagged_bar=1)
        last_price_df = price_df[stock].iloc[-1]

        # 查询信号数据
        if nowtime=="10:59:06":
            a = 1
        signal_now_datetime, predict = self.get_last_signal(now_datetime)
        if (now_datetime - signal_now_datetime).seconds > 1.5:
            self.log(f"信号滞后2s以上，跳过预测。行情：{now_datetime}， 信号：{signal_now_datetime}。", level="debug")
        if predict == 0:
            return

        signal_long = predict if predict > 0 else 0.1
        signal_short = predict if predict < 0 else -0.1

        self.signal_long_delta = np.append(self.signal_long_delta, np.abs(signal_long - self.signal_long[-1]))
        self.signal_short_delta = np.append(self.signal_short_delta, np.abs(signal_short - self.signal_short[-1]))
        self.signal_long = np.append(self.signal_long, signal_long)
        self.signal_short = np.append(self.signal_short, signal_short)

        ################################################################
        # 未成交订单直接撤单
        for order_ref, order_data in self.position_mgr.signal_pending_order.items():
            order = order_data["order"]
            if (xb.num2date(order.data.datetime[0])-xb.num2date(order.created.dt)).total_seconds()>=self.cancel_wait_time :
                self.cancel(order)

        for order_ref, order_data in self.position_mgr.stop_pending_order.items():
            order = order_data["order"]
            if (xb.num2date(order.data.datetime[0])-xb.num2date(order.created.dt)).total_seconds()>=self.cancel_wait_time :
                self.cancel(order)

        net_position = self.position_mgr.net_position
        if '11:00:00' >= nowtime >= self.p.START_PERIOD or '14:54:00' >= nowtime >= '13:00:00':
            if self.last_tick_position*net_position<=0:
                # 如果仓位发生反转
                self.position_mgr.net_position_his_high[stock] = 0
                self.position_mgr.net_position_his_low[stock] = self._midprice(last_price_df)    #   中间价止损/close价止损  self.datas[0].close[0]
            if not net_position:
                self.check_win_hedge_order(stock, last_price_df)
                self.position_mgr.net_position_his_high[stock] = 0
                self.position_mgr.net_position_his_low[stock] = self._midprice(last_price_df)    #   中间价止损/close价止损  self.datas[0].close[0]
                if (self.signal_long[-1] >= self.init_open_long_th):
                    self.process_init_openning(stock, Order.Buy, last_price_df)
                else:
                    if abs(self.signal_short[-1]) >= abs(self.init_open_short_th):
                        self.process_init_openning(stock, Order.Sell, last_price_df)
                    # self.log("未达到开仓阈值: signal long {}!".format(signal_long), level="debug")
            else:
                self.position_mgr.net_position_his_high[stock] = max(self.position_mgr.net_position_his_high[stock], self._midprice(last_price_df))  # self.datas[0].close[0]
                self.position_mgr.net_position_his_low[stock] = min(self.position_mgr.net_position_his_low[stock], self._midprice(last_price_df))  # self.datas[0].close[0]
                self.check_win_hedge_order(stock, last_price_df)
                self.check_and_process_stop_loss(stock, last_price_df, mode = -2)#mode为负，按历史最优价止盈
                if self.signal_long[-1] >= self.init_open_long_th:
                    self.process_init_openning(stock, Order.Buy, last_price_df)
                if abs(self.signal_short[-1]) >= abs(self.init_open_short_th):
                    self.process_init_openning(stock, Order.Sell, last_price_df)

        # elif '11:30:00' >= nowtime >= '11:27:00':
        #     # 上午收盘平仓, 且不发开仓单
        #     self.process_morning_close(stock, last_price_df)
        elif '14:57:00' >= nowtime >= '14:54:00':
            self.process_morning_close(stock, last_price_df)
        else:
            if net_position:
                self.check_and_process_stop_loss(stock, last_price_df, mode=-2)  # mode为负，按历史最优价止盈

        self.last_tick_position = net_position
        return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()), level = self.log_level)




