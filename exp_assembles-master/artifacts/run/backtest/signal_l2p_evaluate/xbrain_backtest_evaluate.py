# -*- coding: utf-8 -*-
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from xbrain import *
from artifacts.parse_format import parse_signal_txt
import pandas as pd
import numpy as np
import time
import helper_price
from manager_position import PositionManager
from pprint import pprint
from artifacts.backtest_save_and_evaluate import backtest_trade_evaluation
from artifacts.parse_format import parse_xbrain_trade_records
pd.set_option('display.max_columns', None)


class StrategySignalEvaluate(StrategyBase):  # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params 访问
    params = (
        ('INIT_PRED_UP', 1.6), # 信号初始阈值
        ('INIT_PRED_DW', -1.6), # 信号初始阈值
        ('MDD_LOSS_LIMIT', -2),  # 订单最优价止损比例
        ('LOSS_LIMIT', -2),  # 订单单价止损线
        ('WIN_LIMIT', 1.5),   # 止盈线
        ("PRICE_DEVIATION", 1),  # 己方最优报价偏移Tick数
        ('UNIT_TRADE_SIZE', 400),  # 单笔交易股数
        ('MAX_HOLD_SIZE', 1600),  # 单边敞口上限
        ('MAX_SELL_SIZE', 10000),  # 单日卖出底仓限制
        ('CANCEL_WAIT_SECONDS', 3),  #未成交订单的等待撤单时间
        ('UNIT_PRICE', 0.01), # 价格的最小单位
        ("SIGNAL_FILE", None),
        ("LOG_LEVEL", "info"),
        ('AM_START_PERIOD', "09:33:00"),
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.vol = self.data.volume
        self.am_start_time = self.p.AM_START_PERIOD
        self.am_end_time = "11:29:30"
        self.pm_start_time = "13:00:00"
        self.pm_end_time = "14:54:00"
        self.signal_df = parse_signal_txt(self.p.SIGNAL_FILE)
        # 将时间格式转换为时分秒
        self.signal_df["NOW_TIME"] = pd.to_datetime(self.signal_df["PERIOD_BEGIN"]).apply(lambda x:x.strftime('%H:%M:%S'))
        self.global_stop_flag = False
        ######### 策略参数初始化 ##########
        self.init_open_long_th = self.p.INIT_PRED_UP
        self.init_open_short_th = self.p.INIT_PRED_DW
        self.init_win_limit = self.p.WIN_LIMIT
        self.init_loss_limit = self.p.LOSS_LIMIT
        self.init_mdd_loss_limit = self.p.MDD_LOSS_LIMIT
        self.unit_trade_size = self.p.UNIT_TRADE_SIZE
        self.cancel_wait_seconds = self.p.CANCEL_WAIT_SECONDS
        self.price_deviation = self.p.PRICE_DEVIATION*self.p.UNIT_PRICE
        self.log_level = self.p.LOG_LEVEL
        self.position_mgr = PositionManager(max_hold_size = self.p.MAX_HOLD_SIZE, max_sell_size = self.p.MAX_SELL_SIZE, strategy_class = self)# 持仓管理
        print("######### 策略回测参数 ##########")
        pprint(self.params.__dict__)

        ######### 策略变量初始化 ##########
        self.signal_long = np.array([0.0])
        self.signal_short = np.array([0.0])
        self.signal_long_delta = np.array([0.0])
        self.signal_short_delta = np.array([0.0])
        self.signal_list = np.array([0.0])

        self.open_long_th = 0.0
        self.open_short_th = 0.0
        self.close_long_th = 0.0
        self.close_short_th = 0.0
        self.open_long_times = 0  # 以多头开仓的次数
        self.open_short_times = 0

        self.init_position = {}
        self.i = 0


    def get_current_signal(self, lasttime, nowtime, now_datetime):
        # 查询信号数据
        sub_signal_df = self.signal_df[(lasttime < self.signal_df["NOW_TIME"]) & (self.signal_df["NOW_TIME"] <= nowtime)]
        if sub_signal_df.empty:
            return 0.0, 0.0
        if sub_signal_df["PREDICTED"].mean() >= 0:
            last_signal_df = sub_signal_df[sub_signal_df["PREDICTED"] == sub_signal_df["PREDICTED"].max()].iloc[-1]
        else:
            last_signal_df = sub_signal_df[sub_signal_df["PREDICTED"] == sub_signal_df["PREDICTED"].min()].iloc[-1]
        if (now_datetime - last_signal_df["PERIOD_BEGIN"]).seconds > 1.5:
            self.log(f"信号滞后2s以上，跳过预测。行情：{now_datetime}， 信号：{last_signal_df['PERIOD_BEGIN']}。", level="debug")
        signal_long = last_signal_df["PREDICTED"] if last_signal_df["PREDICTED"] > 0 else 0.1
        signal_short = last_signal_df["PREDICTED"] if last_signal_df["PREDICTED"] < 0 else -0.1

        self.signal_long_delta = np.append(self.signal_long_delta, np.abs(signal_long - self.signal_long[-1]))
        self.signal_short_delta = np.append(self.signal_short_delta, np.abs(signal_short - self.signal_short[-1]))
        self.signal_long = np.append(self.signal_long, signal_long)
        self.signal_short = np.append(self.signal_short, signal_short)
        self.signal_list = np.append(self.signal_list, last_signal_df["PREDICTED"])
        return signal_long, signal_short


    def log_order_msg(self, order = None, msg = None, **kwargs):
        if order:
            line = ""
            for key, value in kwargs.items():
                line+=f"{key}={value}, "
            line +="."
            self.log(f"{msg}:  price {order.created.price}, volume {order.created.size}, {line}", level=self.log_level)
        else:
            if not msg:
                self.log(f"未下单！{msg}", level = "debug")
            else:
                self.log(f"未下单！", level="debug")

    def notify_order(self, order):
        if order.status in [order.Accepted]:
            self.position_mgr.update_position_created(order)
        elif order.status in [order.Partial, order.Completed]:
            self.position_mgr.update_position_executed(order)
        elif order.status in [order.Canceled]:
            self.position_mgr.update_position_cancel(order)
        super().notify_order(order)


    def sell(self, size=None, price=None, exectype=None, **kwargs):
        size = self.position_mgr.get_restrict_order_size(size, xb.Order.Sell)
        if size > 0 :
            sell_order = super().sell(price=price, size=size, exectype=xb.Order.Limit, **kwargs)
            return sell_order


    def buy(self, size=None, price=None, exectype=None, **kwargs):
        size = self.position_mgr.get_restrict_order_size(size, xb.Order.Buy)
        if size > 0 :
            buy_order = super().buy(price=price, size=int(size), exectype=xb.Order.Limit, **kwargs)
            return buy_order


    def check_and_process_stop_loss(self, symbol, last_price_df, mode = 0):
        current_price = helper_price.get_midprice(last_price_df)
        # 相对于历史最优价计算收益率
        position_mdd_ret = self.position_mgr.get_position_mdd_ret(current_price, mode="midprice")
        # 相对于持仓均价计算收益率
        position_avg_ret = self.position_mgr.get_position_avg_ret(current_price, mode="midprice")
        net_size = self.position_mgr.position.size

        if net_size > 0:
            # 如果已有在途空单，不需要再重复平多头
            size = net_size - self.position_mgr.sell_size_on_way
            if size > 0:
                if position_mdd_ret <= -abs(self.init_mdd_loss_limit):
                    price = helper_price.calc_adjust_price(xb.Order.Sell, last_price_df, deviation = self.price_deviation, mode = helper_price.PriceMode.THIS_SIDE_DEVIATION)
                    hedge_order = self.sell(price=price, size=size, exectype=xb.Order.Limit, msg = "持仓最优价止损")
                    self.log_order_msg(hedge_order, msg = "持仓最优价止损平多头", position_size = net_size, mdd_ret = position_mdd_ret)
                elif position_avg_ret <= -abs(self.init_loss_limit):
                    price = helper_price.calc_adjust_price(xb.Order.Sell, last_price_df, deviation = self.price_deviation, mode = helper_price.PriceMode.THIS_SIDE_DEVIATION)
                    hedge_order = self.sell(price=price, size=size, exectype=xb.Order.Limit, msg = "持仓均价止损")
                    self.log_order_msg(hedge_order, msg = "持仓均价止损平多头", position_size = net_size, mdd_ret = position_avg_ret)
                elif position_avg_ret >= self.init_win_limit:
                    price = helper_price.calc_adjust_price(xb.Order.Sell, last_price_df, deviation = self.price_deviation, mode = helper_price.PriceMode.THIS_SIDE_DEVIATION)  # 止盈按本方最优
                    hedge_order = self.sell(price=price, size=size, exectype=xb.Order.Limit, msg = "持仓均价止盈")
                    self.log_order_msg(hedge_order, msg = "持仓均价止盈平多头", position_size = net_size, mdd_ret = position_avg_ret)
        elif net_size<0:
            # 如果已有在途空单，不需要再重复平多头
            size = abs(net_size) - self.position_mgr.buy_size_on_way
            if size > 0:
                if position_mdd_ret <= -abs(self.init_mdd_loss_limit):
                    price = helper_price.calc_adjust_price(xb.Order.Buy, last_price_df, deviation = self.price_deviation, mode = helper_price.PriceMode.THIS_SIDE_DEVIATION)
                    hedge_order = self.buy(price=price, size=size, exectype=xb.Order.Limit, msg="持仓最优价止损")
                    self.log_order_msg(hedge_order, msg="持仓最优价止损平空头", position_size=net_size, mdd_ret=position_mdd_ret)
                elif position_avg_ret <= -abs(self.init_loss_limit):
                    price = helper_price.calc_adjust_price(xb.Order.Buy, last_price_df, deviation = self.price_deviation, mode = helper_price.PriceMode.THIS_SIDE_DEVIATION)
                    hedge_order = self.buy(price=price, size=size, exectype=xb.Order.Limit, msg="持仓最优价止损")
                    self.log_order_msg(hedge_order, msg="持仓均价止损平空头", position_size=net_size, mdd_ret=position_avg_ret)
                elif position_avg_ret >= self.init_win_limit:
                    price = helper_price.calc_adjust_price(xb.Order.Buy, last_price_df, deviation=self.price_deviation,
                                                   mode=helper_price.PriceMode.THIS_SIDE_DEVIATION)
                    hedge_order = self.buy(price=price, size=size, exectype=xb.Order.Limit, msg="持仓最优价止损")
                    self.log_order_msg(hedge_order, msg="持仓均价止盈平空头", position_size=net_size, mdd_ret=position_avg_ret)


    def next(self):
        if self.global_stop_flag:
            return
        self.i = self.i + 1
        stock = self.datas[0]._name
        now_datetime = xb.num2date(self.datas[0].datetime[0])
        nowtime = str(xb.num2time(self.datas[0].datetime[0]))
        lasttime = str(xb.num2time(self.datas[0].datetime[-1]))
        # 传入标的查询行情数据
        price_df = self.get_past_feed_price_df(datanames=stock, lagged_bar=1)
        last_price_df = price_df[stock].iloc[-1]

        signal_long, signal_short = self.get_current_signal(lasttime, nowtime, now_datetime)
        ################################################################
        # 超时未成交订单直接撤单
        for order in self.get_pending_orders().setdefault(stock, {}):
            if (xb.num2date(order.data.datetime[0])-xb.num2date(order.created.dt)).total_seconds()>=self.cancel_wait_seconds :
                self.cancel(order)

        if nowtime == "14:46:24":
            print(1)

        if self.am_end_time >= nowtime >= self.am_start_time or self.pm_end_time >= nowtime >= self.pm_start_time:
            current_price = helper_price.get_midprice(last_price_df)
            self.position_mgr.update_position_optimal_price(current_price)# 更新持仓最优价格
            net_position = self.position_mgr.position.size
            if not net_position:
                if self.signal_long[-1] >= self.init_open_long_th:
                    order = self.buy(price=self.datas[0].bid1price[0]+self.price_deviation,
                                     size=self.unit_trade_size, exectype=xb.Order.Limit, msg="信号多头开仓")
                    self.log_order_msg(order, msg = "信号多头开仓", position_size = net_position, signal_long = self.signal_list[-5:])
                elif abs(self.signal_short[-1]) >= abs(self.init_open_short_th):
                    order = self.sell(price=self.datas[0].ask1price[0] - self.price_deviation,
                                         size=self.unit_trade_size, exectype=xb.Order.Limit, msg="信号空头开仓")
                    self.log_order_msg(order, msg = "信号空头开仓", position_size = net_position, signal_long = self.signal_list[-5:])
                else:
                    self.log("未达到开仓阈值: signal long {}!".format(signal_long), level="debug")
            else:
                self.check_and_process_stop_loss(stock, last_price_df, mode = -2)#mode为负，按历史最优价止盈

                if self.signal_long[-1] >= self.init_open_long_th:
                    order = self.buy(price=self.datas[0].bid1price[0] + self.price_deviation,
                                     size=self.unit_trade_size, exectype=xb.Order.Limit, msg="信号多头加仓")
                    self.log_order_msg(order, msg = "信号多头加仓", position_size = net_position, signal_long = self.signal_list[-5:])
                if abs(self.signal_short[-1]) >= abs(self.init_open_short_th):
                    order = self.sell(price=self.datas[0].ask1price[0] - self.price_deviation,
                                      size=self.unit_trade_size, exectype=xb.Order.Limit, msg="信号空头加仓")
                    self.log_order_msg(order, msg="信号空头加仓",position_size = net_position, signal_long=self.signal_list[-5:])

        elif '14:57:00' >= nowtime >= '14:54:00':
            self.closeout(self.datas[0]) # 强平
        return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()), level = self.log_level)


if __name__=="__main__":
    t1 = time.time()
    # 创建回测框架 XBrain 实例
    stock = '688012.SH'
    backtest_date = "20240930"
    brain = XBrain(start_date="{} 000000000".format(backtest_date), end_date="{} 235959000".format(backtest_date), allow_short=True)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames=stock,  # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="EnhancedTick",  # 回测频度
        instrument_type='STOCK',  # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 设置撮合目标价为当前bar的open价，模式为模拟撮合
    # 常规模拟撮合
    brain.set_fill_method(FillParamOrder(), FillPrice.THIS_CLOSE)

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    SIGNAL_FILE = "/dfs/group/800657/exp_results/KG101_model/HS_tick2/LabelFirstPeak_th10_120s-{}/pred_th_up@1.10-pred_th_dw@1.10/signal_files_processed/{}.txt".format(stock,
                                                                                                                            pd.to_datetime(backtest_date).strftime("%Y-%m-%d"))
    brain.add_strategy(StrategySignalEvaluate, SIGNAL_FILE = SIGNAL_FILE)
    ####################################################################

    # 运行回测
    backtest_reults = brain.backtest_run()
    ####################################################################

    # 获取Analyzers分析的结果
    brain.generate_report(plot=False, plotname="StrategySignalEvaluate")
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary)
    # print(trade_records)
    # trade_records_df = parse_xbrain_trade_records(trade_records)
    # trade_summary = backtest_trade_evaluation(trade_records_df)
    # print(trade_summary)
    print("耗时：", time.time()-t1)





