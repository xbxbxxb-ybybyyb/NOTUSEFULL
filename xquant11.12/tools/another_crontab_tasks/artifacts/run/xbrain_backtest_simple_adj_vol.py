# -*- coding: utf-8 -*-
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from xbrain import Order
import pandas as pd
import numpy as np
import time
from datetime import datetime
from collections import defaultdict
import os
import json
pd.set_option('display.max_columns', None)



class StrategySignalT0AdjVol(StrategyBase):  # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('init_open_long_th', 1.6),
        ('init_open_short_th', -1.6),
        ('init_close_long_th', -1.6),
        ('init_close_short_th', 1.6),
        ('init_close_long_risk_th', -6.0),
        ('init_close_short_risk_th', 6.0),
        ('START_PERIOD', '09:30:30'),
        ('UNIT_QTY_PER_ORDER', 1000),  # 标准每笔委托的成交笔数, 根据股票成交是否活跃设置
        ('ADJUST_VOLUME', False),  #暂未使用
        ('optimal_price_stoploss_th', -3),  # 订单最优价止损比例
        ('stoploss_th', -5),  # 订单单价止损比例
        ('takeprofit_th', 30),  # 止盈比例
        ('tradesize', 400),  # 每笔交易股数
        ('OPEN_PRICE_MODE', 0),
        ('CLOSE_LOSE_PRICE_MODE', 0),  #平仓止损
        ('CLOSE_WIN_PRICE_MODE', 0),  # 平仓止盈
        ("DEVIATION_SELF_PRICE", 2),  # 己方最优报价偏移Tick数
        ('HOLD_POSITION_LIMIT', 5000),  #单边敞口上限
        ('SELL_POSITION_LIMIT', 10000),  #单日卖出底仓限制
        ('CANCEL_WAIT_SECONDS', 3),  #未成交订单的等待撤单时间
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
        self.close_long_th_weak = 0.0
        self.close_short_th_weak = 0.0
        self.open_long_times = 0  # 以多头开仓的次数
        self.open_short_times = 0
        self.i = 0

        self.init_position = {}
        self.set_init_open_close_th()
        self.cancel_wait_time =  self.p.CANCEL_WAIT_SECONDS
        self.deviation_self_price = self.p.DEVIATION_SELF_PRICE
        self.open_price_mode = self.p.OPEN_PRICE_MODE
        self.close_lose_price_mode = self.p.CLOSE_LOSE_PRICE_MODE
        self.close_win_price_mode = self.p.CLOSE_WIN_PRICE_MODE
        self.net_position = defaultdict(int)  # 相对于底仓的持仓变化值,负值表示空头
        self.buy_position_order_dict ={} #多头持仓订单表
        self.sell_position_order_dict = {} #空头持仓订单表
        self.buysize_onway = 0
        self.sellsize_onway = 0
        self.wait_for_normal_count_limit = 241
        self.net_position_his_high = defaultdict(float) #当前持仓的最大价格
        self.net_position_his_low= defaultdict(float)  # 当前持仓的最小价格


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
        self.hold_position_limit = self.p.HOLD_POSITION_LIMIT
        self.sellable_position = self.p.SELL_POSITION_LIMIT


    def get_up_down_limit(self, stock):
        # 获取涨跌停
        return 0.195 if stock.startswith('3') or stock.startswith('68') else 0.095

    def order_to_dict(self, order):
        return {
            "ref": order.ref,
            "dataname": order.dataname,
            "bs_str": order.bs_str,
            "status_str": order.status_str,
            "size": order.size,
            "price": order.price,
            "exec_size": order.exec_size,
            "exec_remsize": order.exec_remsize
        }


    def notify_order(self, order):
        super().notify_order(order)
        stock = order.data.getdataname()
        last_net_position = self.net_position[stock]

        if order.status in [order.Partial, order.Completed]:
            position = self.get_position_by_name(stock)
            # 订单成交时，更新净持仓s
            if self.net_position[stock] == 0:
                #记录开仓单的时间
                self.last_open_time = xb.num2date(self.get_data_by_name(stock).datetime[0])
                assert len(self.buy_position_order_dict) ==0 or pd.DataFrame(self.buy_position_order_dict).T["open_size"].sum()==0 \
                       and len(self.sell_position_order_dict)==0 or pd.DataFrame(self.sell_position_order_dict).T["open_size"].sum()==0, "持仓为0"


            # 更新持仓表
            new_order_data = self.order_to_dict(order)
            if order.isbuy():
                # 更新在途
                self.buysize_onway = self.buysize_onway - abs(order.executed.incresize)
                buy_open_size = abs(order.executed.incresize)
                if self.net_position[stock]<0:
                    # buy_open_size先去消耗sell_position_order
                    for hedge_order_ref in self.sell_position_order_dict:
                        sell_hedge_order_data = self.sell_position_order_dict[hedge_order_ref]
                        if sell_hedge_order_data["open_size"]==0:
                            # self.log("info 可平仓数量为0", sell_hedge_order_data, level = self.log_level)
                            continue
                        hedge_size = min(buy_open_size, abs(sell_hedge_order_data["open_size"]))
                        sell_hedge_order_data["open_size"] = sell_hedge_order_data["open_size"]-hedge_size #更新开仓量
                        sell_hedge_order_data["hedge_size"].append((order.ref, hedge_size))
                        buy_open_size -= hedge_size
                        if buy_open_size<=0:
                            break

                    # 剩余buy_open_size新加入到buy_position_order
                    if buy_open_size:
                        # 当前卖单未全部对冲，先加入买方持仓订单，等待后续卖单对冲
                        self.buy_position_order_dict[order.ref] = new_order_data
                        self.buy_position_order_dict[order.ref]["open_size"] = buy_open_size
                        self.buy_position_order_dict[order.ref]["hedge_size"] = []
                        self.buy_position_order_dict[order.ref]["order"] = order
                else:
                    # buy_open_size增加buy_position_order
                    if not self.buy_position_order_dict.get(order.ref, None):
                        self.buy_position_order_dict[order.ref] = new_order_data
                        self.buy_position_order_dict[order.ref]["open_size"] = buy_open_size
                        self.buy_position_order_dict[order.ref]["hedge_size"] = []
                        self.buy_position_order_dict[order.ref]["order"] = order
                    else:
                        order_data = self.buy_position_order_dict.get(order.ref)
                        order_data["open_size"] = order_data["open_size"]+buy_open_size
                        order_data["exec_size"] = order.executed.size
                        order_data["exec_remsize"] = order.executed.remsize
            elif order.issell():
                # 更新在途
                self.sellsize_onway = self.sellsize_onway - abs(order.executed.incresize)
                sell_open_size = abs(order.executed.incresize)
                if self.net_position[stock] >0:
                    # sell_open_size 先消耗buy_position_order中的open_size
                    for buy_order_ref in self.buy_position_order_dict:
                        buy_hedge_order_data = self.buy_position_order_dict[buy_order_ref]
                        if buy_hedge_order_data["open_size"]<=0:
                            # self.log("info：可平仓数量为0 ", buy_hedge_order_data, level = self.log_level)
                            continue
                        hedge_size = min(sell_open_size, abs(buy_hedge_order_data["open_size"]))
                        buy_hedge_order_data["open_size"] = buy_hedge_order_data["open_size"]-hedge_size
                        buy_hedge_order_data["hedge_size"].append((order.ref, hedge_size))
                        sell_open_size = sell_open_size-hedge_size
                        if sell_open_size<=0:
                            break
                    if sell_open_size:
                        self.sell_position_order_dict[order.ref] = new_order_data
                        self.sell_position_order_dict[order.ref]["open_size"] = sell_open_size
                        self.sell_position_order_dict[order.ref]["hedge_size"] = []
                        self.sell_position_order_dict[order.ref]["order"] = order
                else:
                    if not self.sell_position_order_dict.get(order.ref, None):
                        self.sell_position_order_dict[order.ref] = new_order_data
                        self.sell_position_order_dict[order.ref]["open_size"] = sell_open_size
                        self.sell_position_order_dict[order.ref]["hedge_size"] = []
                        self.sell_position_order_dict[order.ref]["order"] = order
                    else:
                        order_data = self.sell_position_order_dict.get(order.ref)
                        order_data["open_size"] =  order_data["open_size"]+sell_open_size
                        order_data["exec_size"] = order.executed.size
                        order_data["exec_remsize"] = order.executed.remsize
            if order.isbuy():
                self.net_position[stock] = self.net_position[stock] + abs(order.executed.incresize)
            else:
                self.net_position[stock] = self.net_position[stock] - abs(order.executed.incresize)

            if self.net_position[stock]*last_net_position <= 0:
                #记录平仓时间
                self.net_position_his_high[stock] = 0
                last_price_df = self.get_past_feed_price_df(datanames=stock, lagged_bar=1)[stock].iloc[-1]
                self.net_position_his_low[stock] = self._midprice(last_price_df)    #   中间价止损/close价止损  self.datas[0].close[0]
                if self.net_position[stock] == 0:
                    self.last_open_time = None
                    self.open_short_times = 0
                    self.open_long_times = 0
                    self.open_long_th = 0.0
                    self.open_short_th = 0.0
                    self.close_long_th_weak = 0.0
                    self.close_short_th_weak = 0.0
                else:
                    if self.net_position[stock]>0:
                        self.open_short_th = 0
                        self.open_short_times = 0
                        self.open_long_times = 1
                        self.close_long_th_weak = 0.0
                        self.close_short_th_weak = 0.0
                    else:
                        self.open_long_th = 0
                        self.open_short_times = 1
                        self.open_long_times = 0
                        self.close_long_th_weak = 0.0
                        self.close_short_th_weak = 0.0


        if order.status in [order.Canceled]:
            if order.issell():
                #如果一笔卖订单分多次成交时，成交量变动需要扣除相对变化值
                self.sellable_position = self.sellable_position + abs(order.created.size) - abs(order.executed.size)

            if order.isbuy():
                self.buysize_onway = self.buysize_onway - (abs(order.created.size)-abs(order.executed.size))
            if order.issell():
                self.sellsize_onway = self.sellsize_onway - (abs(order.created.size)-abs(order.executed.size))


    def __update_hedge_order_closing_size(self, hedge_order, parent_order):
        pass

    def sell(self, size=None, price=None, exectype=None, parent_order=None):
        size = int(size)
        net_position = self.net_position[self.datas[0]._name]
        if self.sellable_position - size >= 0:
            if net_position > 0:
                if abs(net_position - size - self.sellsize_onway) <= self.hold_position_limit:
                    sell_order = super(StrategySignalT0AdjVol, self).sell(price=price, size=size,
                                                                          exectype=xb.Order.Limit)
                    self.sellable_position = self.sellable_position - size
                    self.sellsize_onway = self.sellsize_onway + size
                    if parent_order:
                        self.__update_hedge_order_closing_size(sell_order, parent_order)
                    return sell_order
                else:
                    self.log("无法下卖单：超过单边敞口！", level = self.log_level)
            else:
                if abs(net_position) + abs(size) + self.sellsize_onway <= self.hold_position_limit:
                    sell_order = super(StrategySignalT0AdjVol, self).sell(price=price, size=size,
                                                                          exectype=xb.Order.Limit)
                    self.sellable_position = self.sellable_position - size
                    self.sellsize_onway = self.sellsize_onway + size
                    if parent_order:
                        self.__update_hedge_order_closing_size(sell_order, parent_order)
                    return sell_order
                else:
                    self.log("无法下卖单：超过单边敞口！", level = self.log_level)
        else:
            if not net_position:
                self.global_stop_flag = True
            self.log("今日底仓已用完，不再开仓！", level = self.log_level)


    def buy(self, size=None, price=None, exectype=None, parent_order=None):
        size = int(size)
        net_position = self.net_position[self.datas[0]._name]
        if self.sellable_position - net_position - size - self.buysize_onway >= 0:
            if net_position >= 0:
                if abs(net_position) + abs(size) + self.buysize_onway <= self.hold_position_limit:
                    buy_order = super(StrategySignalT0AdjVol, self).buy(price=price, size=int(size),
                                                                        exectype=xb.Order.Limit)
                    self.buysize_onway = self.buysize_onway + size
                    if parent_order:
                        # 当前订单是对冲单，更新对冲单状态
                        self.__update_hedge_order_closing_size(buy_order, parent_order)
                    return buy_order
                else:
                    self.log("无法下买单：超过单边敞口！", level = self.log_level)
            else:
                if abs(net_position + size + self.buysize_onway) <= self.hold_position_limit:
                    buy_order = super(StrategySignalT0AdjVol, self).buy(price=price, size=int(size),
                                                                        exectype=xb.Order.Limit)
                    self.buysize_onway = self.buysize_onway + size
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

    def cal_sigth_vol_ratio(self, prediction, base, times):
        return abs(prediction) / (abs(base) + 0.1) / (times + 1)

    def calc_adjust_base_qty(self, side, last_price_df):
        # delta = self.signal_long_delta[-1] if side == Order.Buy else self.signal_short_delta[-1]
        ema_vol = self.ema_vol[0]
        ask_vol = last_price_df.ask1qty
        bid_vol = last_price_df.bid1qty
        base_size = max(0.5*ema_vol, ask_vol if side == Order.Buy else bid_vol)
        base_size = int(min(base_size, 1.5*ema_vol)/100)*100
        return base_size

        if not position_size:
            if side == Order.Buy:
                open_vol = self.p.UNIT_QTY_PER_ORDER * 10
                size = min(base_size, open_vol)
            elif side == Order.Sell:
                open_vol = self.p.UNIT_QTY_PER_ORDER * 10
                size = min(base_size, open_vol)
        else:
            if position_size>0:
                if side == Order.Buy:
                    # open_vol = vol_min + vol_range * min(1, vol_ratio)
                    # quantity = min(self._positionMgr.getBuyAvailQty(self.__symbol),
                    #                self._positionMgr.getSellAvailQty(self.__symbol),
                    #                , open_vol, limit_vol)
                    vol_ratio = __cal_vol_ratio(prediction, self.init_open_long_th, self.open_long_time)
                    # open_vol = self.p.UNIT_QTY_PER_ORDER * (1 + 10 * vol_ratio * delta)
                    open_vol = self.p.UNIT_QTY_PER_ORDER * (1 + vol_ratio)
                    size = min(ema_vol * 0.5, max(ema_vol * 0.2, ask_vol), open_vol)
                elif side == Order.Sell:
                    if True:  # price == 0:
                        short_percent = self.get_position_percent_in_market(self.__tick_count_since_init_open_short - 1)
                        amt_list = []
                        for i in range(self.__tick_count_since_init_open_short + 1):
                            amt_list.append(self.vol[0 - i])
                        total_market_amt_since_open = sum(amt_list)
                        limit_vol = total_market_amt_since_open * short_percent / price - position_size
                        limit_vol = max(limit_vol, 0)
                    else:
                        limit_vol = 0
                    vol_ratio = __cal_vol_ratio(prediction, self.init_close_long_th, self.open_short_times)
                    # open_vol = self.p.UNIT_QTY_PER_ORDER * (1 + 10 * vol_ratio* delta)
                    open_vol = self.p.UNIT_QTY_PER_ORDER * (4 + vol_ratio)
                    size = min(ema_vol * 0.5, max(ema_vol * 0.2, bid_vol), open_vol)
        return int(size / 100) * 100


    def process_init_openning(self, stock, side, last_price_df):
        # 根据信号和行情下单逻辑
        signal_long = self.signal_long[-1]
        signal_short = self.signal_short[-1]
        net_position = self.net_position[stock]

        price = self.calc_adjust_price(side, last_price_df, mode=self.open_price_mode)
        if side == Order.Buy:
            # if net_position > 0 and signal_long < self.open_long_th:
            #     return
            # 开多
            self.open_long_th = signal_long  # 上一次开仓的阈值
            if self.p.ADJUST_VOLUME:
                base_size = self.calc_adjust_base_qty(side, last_price_df)
                sig_size = 100 * int(1 + 8 * self.cal_sigth_vol_ratio(signal_long, self.init_open_long_th, self.open_long_times))
                sig_size = int(sig_size / 100) * 100
                size = min(base_size, sig_size)
                # print("size:", size, "open_size:", open_size)
            else:
                size= self.p.tradesize
            # size = self.p.tradesize
            if abs(net_position + size) <= self.hold_position_limit:
                self.log("开仓多头下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size, self.signal_long[-5:]), level = self.log_level)
                order = self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                if order:
                    self.open_long_times = self.open_long_times + 1
        elif side == Order.Sell:
            # if net_position < 0 and signal_short > self.open_short_th:
            #     return
            # 开空
            self.open_short_th = signal_short  # 上一次开仓的阈值
            self.tick_count_since_init_open_short = 0
            # size = int(self.ema_vol[0]*0.5/100+1)*100
            if self.p.ADJUST_VOLUME:
                base_size = self.calc_adjust_base_qty(side, last_price_df)
                sig_size = 100 * (
                            1 + 8 * self.cal_sigth_vol_ratio(signal_short, self.init_open_short_th, self.open_short_times))
                sig_size = int(sig_size/100)*100
                size = min(base_size, sig_size)
            else:
                size = self.p.tradesize

            if abs(net_position - size) <= self.hold_position_limit and self.sellable_position > 0:
                self.log("开仓空头下单:  price {}, volume {}, self.signal_short[-5;] {}!".format(price, size, self.signal_short[-5:]), level = self.log_level)
                order = self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
                if order:
                    self.open_short_times = self.open_short_times + 1


    def process_multi_open_close(self, stock, last_price_df):
        signal_long = self.signal_long[-1]
        signal_short = self.signal_short[-1]
        net_position = self.net_position[stock]
        ema_vol = self.ema_vol[0]

        if net_position>0:
            volume_close = abs(net_position)
            OPEN_TH = self.open_long_th if self.open_long_th else self.init_open_long_th
            CLOSE_TH = self.close_long_th_weak if self.close_long_th_weak else self.init_open_short_th+0.2

            if signal_short < CLOSE_TH:
                if signal_short<self.init_open_short_th:
                    # 平仓并反向开多
                    base_size = self.calc_adjust_base_qty(Order.Sell, last_price_df)
                    size = min(base_size, 100*4, self.sellable_position)+volume_close
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode=self.open_price_mode)
                    order = self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.open_short_times = self.open_short_times + 1
                    self.open_short_th = signal_short
                    self.log("全部平多头并反向下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size,
                                                                                               self.signal_long[-5:]),
                             level=self.log_level)
                else:
                    # 只平仓
                    size = min(volume_close, (ema_vol * 2.5 / 100)*100, 1000)
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode=self.open_price_mode)
                    order = self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.close_long_th_weak = signal_short
                    self.log("部分平多头下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size,
                                                                                                self.signal_long[-5:]),
                             level=self.log_level)
            if signal_long > OPEN_TH:
                if self.p.ADJUST_VOLUME:
                    up = min(5.0* max(ema_vol / 1000, 1.0), 12.0)*100
                    base_size = self.calc_adjust_base_qty(Order.Buy, last_price_df)
                    sig_size = 100 * (
                            1 + 8 * self.cal_sigth_vol_ratio(signal_long, self.init_open_long_th, self.open_long_times))
                    sig_size = int(sig_size / 100) * 100
                    sig_size = min(base_size, sig_size)
                    size = sig_size if sig_size+volume_close<up else up - volume_close
                else:
                    size = self.p.tradesize
                price = self.calc_adjust_price(Order.Buy, last_price_df, mode=self.open_price_mode)
                if size > 0:
                    self.log("连续开仓多头下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size,
                                                                                              self.signal_long[-5:]),
                             level=self.log_level)
                    order = self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.open_long_times = self.open_long_times + 1
                    self.open_long_th = signal_long
        elif net_position<0:
            volume_close = abs(net_position)
            OPEN_TH = self.open_short_th if self.open_short_th else self.init_open_short_th
            CLOSE_TH = self.close_short_th_weak if self.close_short_th_weak else self.init_open_long_th-0.2

            if signal_long > CLOSE_TH:
                if signal_long > self.init_open_long_th:
                    # 平仓并反向开多
                    base_size = self.calc_adjust_base_qty(Order.Buy, last_price_df)
                    size = min(base_size, 100 * 4, self.sellable_position) + volume_close
                    price = self.calc_adjust_price(Order.Buy, last_price_df, mode=self.open_price_mode)
                    order = self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.open_long_times = self.open_long_times + 1
                    self.open_long_th = signal_long
                    self.log("全部平空头并反向下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size,
                                                                                               self.signal_short[
                                                                                               -5:]),
                             level=self.log_level)
                else:
                    # 只平仓
                    size = min(volume_close, (ema_vol * 2.5 / 100)*100, 1000)
                    price = self.calc_adjust_price(Order.Buy, last_price_df, mode=self.open_price_mode)
                    order = self.buy(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.close_short_th_weak = signal_long
                    self.log("部分平空头下单:  price {}, volume {}, self.singal_long[-5:] {}!".format(price, size,
                                                                                               self.signal_short[
                                                                                               -5:]),
                             level=self.log_level)
            if signal_short < OPEN_TH:
                if self.p.ADJUST_VOLUME:
                    up = min(5.0 * max(ema_vol / 1000, 1.0), 12.0) * 100
                    base_size = self.calc_adjust_base_qty(Order.Sell, last_price_df)
                    sig_size = 100 * (
                            1 + 8 * self.cal_sigth_vol_ratio(signal_short, self.init_open_short_th,
                                                             self.open_short_times))
                    sig_size = int(sig_size / 100) * 100
                    sig_size = min(base_size, sig_size)
                    size = sig_size if sig_size + volume_close < up else up - sig_size
                else:
                    size = self.p.tradesize
                if size >0:
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode=self.open_price_mode)
                    order = self.sell(price=price, size=int(size), exectype=xb.Order.Limit)
                    self.open_short_times = self.open_short_times + 1
                    self.open_short_th = signal_short
                    self.log("连续开仓空头下单:  price {}, volume {}, self.signal_short[-5;] {}!".format(price, size,
                                                                                               self.signal_short[
                                                                                               -5:]),
                             level=self.log_level)


    def process_morning_close(self, stock, last_price_df):
        size = abs(int(self.net_position[stock]))
        if self.net_position[stock] > 0:
            # 设置为激进挂单价格
            price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_lose_price_mode)
        elif self.net_position[stock] < 0:
            price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_lose_price_mode)

        if self.net_position[stock] > 0:
            self.log("尾盘平仓: signal short {}, price {}, volume {}!".format(self.signal_short[-1], price, size), level = self.log_level)
            self.sell(price=price, size=size, exectype=xb.Order.Limit)
            self.open_long_times = 0
        elif self.net_position[stock] < 0:
            self.log("尾盘平仓: signal long {}, price {}, volume {}!".format(self.signal_long[-1], price, size), level = self.log_level)
            self.buy(price=price, size= size, exectype=xb.Order.Limit)
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
        net_position = self.net_position[symbol]
        # 相对于历史最优价计算收益率
        msg = "历史最优价"
        if self.net_position[symbol] > 0:
            base_price = self.net_position_his_high[symbol]
            ret_base_price = self.__calc_return(position_side=Order.Buy, base_price = base_price, last_price_df = last_price_df)
            if abs(ret_base_price) >= abs(self.p.optimal_price_stoploss_th):
                net_size = self.net_position[symbol]
                # 如果已有在途多单，不需要再重复平多头
                size = net_size - self.sellsize_onway
                if size > 0:
                    price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_win_price_mode)
                    self.log("最优价止损平多头: 到达开仓单{}止损线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(msg, ret_base_price, net_size,
                                                                                        price), level = self.log_level)
                    hedge_order = self.sell(price=price, size=size, exectype=xb.Order.Limit)
            else:
                for p_order_ref in self.buy_position_order_dict:
                    p_order = self.buy_position_order_dict[p_order_ref]["order"]
                    net_size = abs(self.buy_position_order_dict[p_order_ref]["open_size"])
                    if net_size<=0:
                        continue
                    ret_single_price = self.__calc_return(position_side=Order.Buy, base_price=p_order.price,
                                                          last_price_df=last_price_df)
                    # 如果已有在途多单，不需要再重复平多头
                    size = net_size - self.sellsize_onway
                    if size > 0:
                        if ret_single_price <= self.p.stoploss_th:
                            price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_lose_price_mode)
                            self.log(
                                "止损平多头: 到达开仓单执行价止损线: ret 千分之{}，平仓数量 {}，平仓价格 {}。".format(ret_single_price, net_size, price),
                                level = self.log_level)
                            hedge_order = self.sell(price=price, size=net_size, exectype=xb.Order.Limit,
                                                    parent_order=p_order)
                        elif ret_single_price >= self.p.takeprofit_th:
                            price = self.calc_adjust_price(Order.Sell, last_price_df, mode = self.close_lose_price_mode)  # 止盈按本方最优
                            self.log(
                                "止盈平多头，到达开仓单执行价止盈线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(ret_single_price, net_size, price),
                                level = self.log_level)
                            hedge_order = self.sell(price=price, size=net_size, exectype=xb.Order.Limit,
                                                    parent_order=p_order)
        else:
            base_price = self.net_position_his_low[symbol]
            ret_base_price = self.__calc_return(Order.Sell, base_price, last_price_df)
            if abs(ret_base_price) >= abs(self.p.optimal_price_stoploss_th):
                price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_win_price_mode)
                net_size = abs(self.net_position[symbol])
                # 如果已有在途多单，不需要再重复平空头
                size = net_size-self.buysize_onway
                if size >0:
                    self.log("最优价止损平空头：到达开仓单最优价{}止损线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(msg, ret_base_price, net_size,
                                                                                          price), level = self.log_level)
                    hedge_order = self.buy(price=price, size=abs(size), exectype=xb.Order.Limit)
            else:
                for p_order_ref in self.sell_position_order_dict:
                    p_order = self.sell_position_order_dict[p_order_ref]["order"]
                    net_size = abs(self.sell_position_order_dict[p_order_ref]["open_size"])
                    if net_size<=0:
                        continue
                    ret_single_price = self.__calc_return(Order.Sell, p_order.price, last_price_df)
                    # 如果已有在途多单，不需要再重复平空头
                    size = abs(net_size) - self.buysize_onway
                    if size > 0:
                        if ret_single_price <= self.p.stoploss_th:
                            price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_lose_price_mode)
                            self.log("止损平空头：到达开仓单执行价止损线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(ret_single_price, net_size, price), level = self.log_level)
                            hedge_order = self.buy(price=price, size=abs(size), exectype=xb.Order.Limit, parent_order=p_order)
                        elif ret_single_price >= self.p.takeprofit_th:
                            price = self.calc_adjust_price(Order.Buy, last_price_df, mode = self.close_lose_price_mode)  # 止盈按本方最优
                            self.log("止盈平多头： 到达开仓单执行价止盈线: ret 千分之{}，平仓数量 {}， 平仓价格 {}。".format(ret_single_price, net_size, price), level = self.log_level)
                            hedge_order = self.buy(price=price, size=abs(size), exectype=xb.Order.Limit, parent_order=p_order)

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
            return last_signal_df["PERIOD_BEGIN"], last_signal_df["PREDICTED"]
        elif self.signal_df.iloc[next_signal_idx]["PERIOD_BEGIN"] > now_datetime:
            return now_datetime, 0

    def next(self):
        if self.global_stop_flag:
            return
        self.i = self.i + 1
        stock = self.datas[0]._name
        now_datetime = xb.num2date(self.datas[0].datetime[0])
        nowtime = now_datetime.time().strftime('%H:%M:%S')
        # 传入标的查询行情数据
        price_df = self.get_past_feed_price_df(datanames=stock, lagged_bar=1)
        last_price_df = price_df[stock].iloc[-1]

        # 查询信号数据
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
        for order in self.get_pending_orders().setdefault(stock, {}):
            if (xb.num2date(order.data.datetime[0])-xb.num2date(order.created.dt)).total_seconds()>=self.cancel_wait_time :
                self.cancel(order)

        if nowtime == "09:47:28":#"09:36:06":
            print(1)

        if '11:00:00' >= nowtime >= self.p.START_PERIOD or '14:54:00' >= nowtime >= '13:00:00':
            net_position = self.net_position[stock]
            if not net_position:
                if (self.signal_long[-1] >= self.init_open_long_th):
                    self.process_init_openning(stock, Order.Buy, last_price_df)
                else:
                    if abs(self.signal_short[-1]) >= abs(self.init_open_short_th):
                        self.process_init_openning(stock, Order.Sell, last_price_df)
                    # self.log("未达到开仓阈值: signal long {}!".format(signal_long), level="debug")
            else:
                self.net_position_his_high[stock] = max(self.net_position_his_high[stock], self._midprice(last_price_df))  # self.datas[0].close[0]
                self.net_position_his_low[stock] = min(self.net_position_his_low[stock], self._midprice(last_price_df))  # self.datas[0].close[0]
                self.check_and_process_stop_loss(stock, last_price_df, mode = -2)#mode为负，按历史最优价止盈
                self.process_multi_open_close(stock, last_price_df)

        # elif '11:30:00' >= nowtime >= '11:27:00':
        #     # 上午收盘平仓, 且不发开仓单
        #     self.process_morning_close(stock, last_price_df)
        elif '14:57:00' >= nowtime >= '14:54:00':
            self.process_morning_close(stock, last_price_df)
        else:
            pass
        return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()), level = self.log_level)

