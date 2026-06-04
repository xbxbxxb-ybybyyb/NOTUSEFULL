# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
import datetime


# 演示高频TICK策略使用Timer定时器，进行定时操作，可添加多个timer
# 定时器执行定时方法，总是在next方法之前执行，具体参数见文档注释
# 如下展示了一个定时6秒的TICK策略，在定时函数中对两根bar的数据进行重采样
# 并设置一个定时60s的定时器，进行触发式操作

# 策略类，是用户需要实现的主要内容。
class StrategyTimer(StrategyBase): # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 3000),                   # 每笔交易手数
        ('period', 120),                    # SMA参数
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.sma = xb.talib.SMA(                            # 调用 xbrain 集成的 talib 因子计算功能，计算短期 SMA 值
            self.data.close, timeperiod=self.params.period  # 指定 SMA 参数为 self.params.period
        )
        # add Timer设置定时器
        # when执行时机
        # offset执行时机偏移
        # repeat可以指定一段时间间隔之后重复执行定时函数
        # 可以自定义kwargs额外参数，比如name，作为notify时区分多个timer的标识
        self.add_timer(name='6s', when=xb.timer.SESSION_START, offset=datetime.timedelta(seconds=6),
                       repeat=datetime.timedelta(seconds=6))
        self.add_timer(name='60s', when=xb.timer.SESSION_START, offset=datetime.timedelta(seconds=60),
                      repeat=datetime.timedelta(seconds=60))

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def notify_timer(self, timer, when, *args, **kwargs):
        # 达到指定时间条件会触发一次计算
        if kwargs.get('name') == '6s':
            close = self.close[0]
            high = max(self.datas[0].high[0], self.datas[0].high[-1])
            opent = self.datas[0].open[-1]
            low = min(self.datas[0].low[0], self.datas[0].low[-1])
            volume = self.datas[0].volume[-1] + self.datas[0].volume[0]
            self.log('notify_timer 6s: open: {} close: {}, high: {}, low: {},  volume: {}'.format(
                opent, close, high, low, volume
            ))
        else:
            self.log('notify_timer 60s:open: {} close: {}, high: {}, low: {},  volume: {}'.format(
                self.datas[0].open[0], self.datas[0].close[0], self.datas[0].high[0],
                self.datas[0].low[0], self.datas[0].volume[0]
            ))

    def next(self):
        # 通过 get_position 方法，获得持仓信息，
        pos = self.get_position(self.datas[0])

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20190401 093000000", end_date="20190410 235959000", live=False)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    stock = '000001.SZ'
    brain.add_feeds(
        datanames=stock,                # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",              # 回测频度
        instrument_type='STOCK',        # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyTimer)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot=True, plotname="StrategyTimer")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())