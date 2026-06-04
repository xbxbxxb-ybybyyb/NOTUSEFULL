# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from talib import SMA
from xbrain.indicators import ExponentialMovingAverage
from tquant import StockData

# 使用简单指标，MACD指标，演示实时买卖操作
# 实时数据为触发式行情，多标的同时播放时，若其中某只标的有行情推送过来则触发策略类NEXT方法播放行情，
# 此时其他标的行情仍然为上根Bar的行情，处理行情数据时需注意处理甄别

# 策略类，是用户需要实现的主要内容。
# 此例是一个完整有意义的策略，主要展示如何在 XBrain 框架中获得信号，并对应下单。
# 策略介绍：macd线上穿signal线时，开仓买入，+10%止盈，-10%止损。
class StrategySMA(StrategyBase): # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义
    params = (
        ('short_period', 10),               # sma10窗口
        ("middle_period", 10),              # sma30窗口
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 30),                # 每笔交易股数
    )

    def __init__(self):
        self.open = self.datas[0].open
        self.high = self.datas[0].high
        self.low = self.datas[0].low
        self.close = self.datas[0].close
        self.vol = self.datas[0].volume
        self.last_datetime = None
        me1 = ExponentialMovingAverage(self.data, period=12)
        me2 = ExponentialMovingAverage(self.data, period=26)
        self.macd = me1 - me2
        self.signal = ExponentialMovingAverage(self.macd, period=9)

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def prenext(self):
        self.log('PreNext, Open: {}, High: {}, Low: {}, Close: {}, Vol: {}'.format(
            self.open[0], self.high[0], self.low[0], self.close[0], self.vol[0]
        ))

    def next(self):
        self.log('Open: {}, High: {}, Low: {}, Close: {}, Vol: {}'.format(
            self.open[0], self.high[0], self.low[0], self.close[0], self.vol[0]
        ))

        if self.last_datetime is None:
            self.last_datetime = self.datas[0].datetime[0]
        if self.last_datetime < self.datas[0].datetime[0]:
            self.last_datetime = self.datas[0].datetime[0]

            # print(self.get_past_feed_price_df('600031.SH', 10))
            pos = self.get_position(self.datas[0])
            pos_size = pos.size
            pos_cost = pos.price

            # 如果无持仓，macd线上穿signal信号线时开仓买入
            if pos_size == 0 and self.macd[-1] < self.signal[-1] and self.macd[0] > self.signal[0]:
                # 如果没有持仓，若前一天MACD < Signal, 当天 Signal < MACD，则第二天买入
                self.buy(size=self.params.tradesize)
                return

            # 如果有可卖持仓，则计算盈亏情况，决定是否止盈止损
            # 止损
            if pos.closeable_amount() > 0 and self.close[0] <= pos_cost * (1 - self.params.stoploss):
                self.sell(size=self.params.tradesize)
                return

            # 止盈
            if pos.closeable_amount() > 0 and self.close[0] >= pos_cost * (1 + self.params.takeprofit):
                self.sell(size=self.params.tradesize)
                return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    stocks = ['000001.SZ']
    start_date = "20210922 093000000"
    end_date = "20210924 111559000"

    #live 为 True，表示通过流式行情数据回测， live_mode为'playback'表示回放历史某一天的流式数据，为'realtime'表示回放当天交易所推送的实时流式数据
    brain = XBrain(start_date=start_date, end_date=end_date, live=True, live_mode='playback')
    ###########################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames=stocks,                             # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",                            # 回测频度
        instrument_type='STOCK',                      # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 设置底仓，支持多标的添加多次
    sd = StockData()
    price = sd.get_factor_price_daily(stocks, [start_date[:8]], ["close"]).iloc[0, 0]
    print("stock {}, price: {}.".format(stocks, price))
    brain.add_initial_position(symbol=stocks[0], size=300, price=price)

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategySMA)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot=True, plotname="StrategyLive")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())
