from xbrain import XBrain
from xbrain.strategy_base import StrategyBase
import pandas as pd
from xbrain import num2date, Order
import numpy as np

# 演示用户加载用户自定义数据，并在回放行情中使用
# 1.自定义加载数据必须包含的字段['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',]，且区分大小写
# 2.额外可选字段(可在回放行情中，以self.datas[0].sellvol[0]方式读取，字段名以及大小写需保持一致)：
#   K_DAY数据可额外包括：['PreClose', 'Amount', 'IOPV','Buyvol', 'Sellvol']
#   TICK或K_1MIN可额外包括：['Amount', 'IOPV', 'Buyvol', 'Sellvol', 'Preclose',"bid1price", "bid1qty","ask1price", "ask1qty"]
# 3.对于特殊自定义字段，可以在数据回放中通过self.get_past_feed_price_df，最后行获取到当前bar对应的自定义字段

def cal_profit(open_px, close_px, direction='long'):
    if direction == 'long':
        return np.log(close_px) - np.log(open_px)
    elif direction == 'short':
        return -1 * (np.log(close_px) - np.log(open_px))


class StrategySignal(StrategyBase):  # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params.stoploss 访问
    params = (
        ('stoploss', -0.002),                  # 止损比例
        ('takeprofit', np.inf),                # 止盈比例
        ('long_thres', 1.7),
        ('short_thres', -2.6),
        ('ratio', 0.5)
    )

    def __init__(self):
        # 载入信号文件
        # self.
        self.exec_once = False
        self.status = 'EMPTY'
        self.last_order = None
        self.last_trade = None
        self.cash_flow = []
        self.turnover = []
        self.commission = []
        self.pnl = 0

    def start(self):
        self.log("初始持仓", self.get_position(self.datas[0]))
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def prenext(self):
        self.log(
            "Current index: {}. Preparing for MA calculations.".format(len(self)))

    def next(self):
        # 通过get_past_feed_price_df获取原始dataframe的方法，直接获取自定义字段的数据，如下直接获取当前bar自定义的买卖信号
        past_feed_df = self.get_past_feed_price_df('002158.SZ', 1)['002158.SZ'].iloc[-1, :]
        long_signal = past_feed_df.long_signal
        short_signal = past_feed_df.short_signal

        # 通过TICK数据额外增加的字段，直接获取回放数据
        bid_price1 = self.datas[0].bid1price[0]
        bid_size1 = self.datas[0].bid1qty[0]
        ask_price1 = self.datas[0].ask1price[0]
        ask_size1 = self.datas[0].ask1qty[0]

        pending_orders = self.get_pending_orders()
        if pending_orders:
            # 如果挂单时间过长可以尝试取消， 重新挂单
            return

        if long_signal >= self.params.long_thres and short_signal >= 0:
            # 开多
            self.log(num2date(self.datetime[0]), "收到信号 long {}". format(long_signal))
            if self.status == 'EMPTY':
                open_px = ask_price1
                size = ask_size1 * self.params.ratio // 100 * 100
                self.log(num2date(self.datetime[0]), "卖一价格 {}, 卖一数量{}, 委托数量{}".format(ask_price1, ask_size1, size))
                self.buy(self.datas[0], size=size, exectype=Order.Limit, price=open_px) # 可以设置valid 时间
                return

        if short_signal <= self.params.short_thres and long_signal <= 0:
            # 开空
            self.log(num2date(self.datetime[0]), "收到信号 short {}". format(short_signal))
            if self.status == 'EMPTY':
                open_px = bid_price1
                size = bid_size1 * self.params.ratio // 100 * 100
                self.log(num2date(self.datetime[0]), "买一价格 {}, 买一数量{}, 委托数量{}".format(bid_price1, bid_size1, size))
                self.sell(self.datas[0], size=size, exectype=Order.Limit, price=open_px) # 可以设置valid 时间
                return

        # # 状态转变
        if self.status == 'LONG_OPEN':
            profit_ratio = cal_profit(self.last_order.executed.price, bid_price1, direction="long")
            if profit_ratio <= self.params.stoploss and self.get_position(self.datas[0]).closeable_amount() > 0:
                self.log(num2date(self.datetime[0]), "止损，买一价格 {}, 买一数量{}, 委托数量{}".format(bid_price1, bid_size1, self.last_order.executed.size))
                self.sell(self.datas[0], size=self.last_order.executed.size, exectype=Order.Limit, price=bid_price1)
            elif ((long_signal < 0 and short_signal < 0) or short_signal <= self.params.short_thres) and \
                    self.get_position(self.datas[0]).closeable_amount() > 0:
                self.log(num2date(self.datetime[0]), "止盈，买一价格 {}, 买一数量{}, 委托数量{}".format(bid_price1, bid_size1, self.last_order.executed.size))
                self.sell(self.datas[0], size=self.last_order.executed.size, exectype=Order.Limit, price=bid_price1)

        if self.status == 'SHORT_OPEN':
            profit_ratio = cal_profit(self.last_order.executed.price, ask_price1, direction="short")
            if profit_ratio <= self.params.stoploss:
                self.buy(self.datas[0], size=self.last_order.executed.size, exectype=Order.Limit, price=ask_price1)
            elif (long_signal > 0 and short_signal > 0) or long_signal >= self.params.long_thres:
                self.buy(self.datas[0], size=self.last_order.executed.size, exectype=Order.Limit, price=ask_price1)

    def stop(self):
        self.log("最终持仓", self.get_position(self.datas[0]))
        self.log('End of backtest. Final value: {}'.format(self.get_value()))
        self.log('累计收益 {}'.format(self.pnl))

    def notify_trade(self, trade):
        self.log("当前的收益{}, trade.pnlcomm = {}".format(trade.pnl, trade.pnlcomm))
        self.last_trade = trade
        self.pnl += trade.pnlcomm
        return

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            self.log("订单{} 提交状态{}，委托价格 {}, 委托数量{}, 委托方向{}".format(order.ref, order.status, order.price, order.size, order.bs_str))

        # 区别开全部成交和部分成交， 部分成交的后面继续尝试挂单或者撤单
        if order.status in [order.Completed, order.Partial]:
            if order.isbuy():
                self.log(
                    '买入 委托成交 , ID = {}, Price: {:.2f}, Qty: {}, Cost: {:.2f}, Comm {:.2f}'.format
                    (order.ref, order.executed.price, order.executed.size, order.executed.value, order.executed.comm))
                # 记录执行价格
                self.last_order = order
                self.turnover.append(order.executed.value)
                self.commission.append(order.executed.comm)
                if self.status == 'EMPTY':
                    self.status = "LONG_OPEN"
                elif self.status == 'SHORT_OPEN':
                    self.status = "EMPTY"

            elif order.issell():  # Sell
                self.log(
                    '卖出 委托成交 , ID = {}, Price: {:.2f}, Qty: {}, Cost: {:.2f}, Comm {:.2f}'.format
                    (order.ref, order.executed.price, order.executed.size, order.executed.value, order.executed.comm))
                # 记录执行价格
                self.last_order = order
                self.turnover.append(order.executed.value)
                self.commission.append(order.executed.comm)

                if self.status == 'EMPTY':
                    self.status = "SHORT_OPEN"
                elif self.status == "LONG_OPEN":
                    self.log("多头完成一轮次")
                    self.status = "EMPTY"


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20210518 000000000", end_date="20210618 235959000",
                   init_amount=2000000, commission=0.0003, live=False)

    # 加载用户自定义数据
    # 如下加载额外bid1price，bid1qty，ask1price，ask1qty字段，可在回放行情中直接获取
    # 对于自定义的买卖信号，也一并加载在dataframe中，可在回放行情中，通过get_past_feed_price_df获取
    completed_df = pd.read_pickle("used_for_backtest.pkl").dropna()
    completed_df.reset_index(inplace=True)
    completed_df.rename(columns={'DateTime': 'Datetime', 'LastPx': 'Close', 'OpenPx': 'Open', 'HighPx': 'High',
                                 'LowPx': 'Low', 'TotalVolumeTrade': 'Volume', 'bid_price1': 'bid1price',
                                 'bid_size1': 'bid1qty', 'ask_price1': 'ask1price', 'ask_size1': 'ask1qty'}, inplace=True)

    # 加载数据到回测框架
    brain.add_data(df=completed_df, dataname='002158.SZ', time_frame='TICK', instrument_type='STOCK')

    # 设置底仓，支持开空
    # brain.add_initial_position(symbol='000001.SZ', size=60000, price=25.7)

    # 设置撮合模式
    brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='TRADE_MOCKER', mocker_type='NORMAL')

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategySignal)

    # 运行回测
    brain.backtest_run()

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot = True, plotname="StrategyCustomSignal")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())

    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 2045687.01
    # StrategyProfitRate       : 0.02284350529999979
    # AnnualProfitRate         : 0.29526859083519685
    # SharpeRatio              : 3.1964209547252787
    # MaxDrawDown              : 0.012036709851053606
    # MaxDrawDownFrom          : 2021-06-07
    # MaxDrawDownTo            : 2021-06-08
    # WinLostRatio             : 1.8820043565760798
    # WinRate                  : 0.5238095238095238
    # ================================================================================
