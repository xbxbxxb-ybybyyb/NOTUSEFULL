# -*- coding: utf-8 -*-

from xbrain import XBrain
from xbrain.strategy_base import StrategyBase

# 演示并行策略实时回测多个不同标的，对应相同策略场景


# 此例是一个简单策略，主要展示如何在 XBrain 框架策略中获取数据，并使用 log 功能进行打印。
class StrategyLogExample(StrategyBase):  # 需继承 StrategyBase 基类，

    def __init__(self):
        # XBrain 支持多数据源，多时间窗口回测，并自动进行时间对齐。
        # 用户通过 xbrain.add_feeds，添加任意多数据，并在策略类中通过 self.datas[n] 访问对应顺序的数据
        # self.datas[0] 即为第一个数据源，以此类推。
        # 具体 OHLCV 字段的获取方式如下。
        self.open = self.datas[0].open
        self.high = self.datas[0].high
        self.low = self.datas[0].low
        self.close = self.datas[0].close
        self.vol = self.datas[0].volume

    def next(self):
        # XBrain 使用 LineBuffer 数据结构进行时间对齐。
        # 在策略的 next 方法获取数据时，[0] 表示当前数值，[-1] 表示前一个值，[-n] 表示前 n 个值。
        self.log('Open: {}, High: {}, Low: {}, Close: {}, Vol: {}'.format(
            self.open[0], self.high[0], self.low[0], self.close[0], self.vol[0]
        ))


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20210301 000000000", end_date="20210310 151559000", live=True, live_mode='playback')
    # ###########################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyLogExample)
    stocks = ['000001.SZ']
    brain.add_feeds(
        datanames=stocks,                             # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",                            # 回测频度
        instrument_type='STOCK',                      # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )

    brain.add_feeds(
        datanames=['600600.SH'],                      # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",                            # 回测频度
        instrument_type='STOCK',                      # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )

    ####################################################################

    # 运行回测
    # 参数parallel_run: 是否并行，类型bool，True按笛卡尔积并行运行，False为单进程运行，默认False不并行
    # 参数parallel_on_feeds: True按加载feeds并行，False按自定义加载的data并行，默认True按feeds并行
    brain.backtest_run(parallel_run=True, parallel_on_feeds=True)
    ####################################################################
