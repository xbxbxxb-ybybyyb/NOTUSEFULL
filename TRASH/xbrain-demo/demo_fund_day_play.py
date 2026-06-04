# -*- coding: utf-8 -*-

from xbrain import XBrain
from xbrain.strategy_base import StrategyBase

# 演示策略行情播放（股票或基金）
# 策略类，是用户需要实现的主要内容。
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

# 获取FUND数据，并在回放数据时打印

def main():
    instrument_type = "FUND"                    # 回测品种类型，目前支持 "STOCK", "FUTURE", "FUND"
    start = "20200101 000000000"                # 回测开始时间, 默认
    end = "20200630 235959000"                  # 回测结束时间，默认
    live = False                                # 是否模拟跟踪，True为模拟跟踪，False为策略回测， 默认为False
    time_frame = "K_DAY"                        # 回测频度，目前支持 "K_1MIN", "K_DAY", "TICK"
    instrument = "159915.SZ"                    # 回测品种，目前支持"ICZL", "IFZL", "IHZL"以及全A股
    init_amount = 2000000                       # 回测金额，默认为1000000
    commission = 0.0003                         # 佣金百分比

    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date=start, end_date=end, init_amount=init_amount, commission=commission, live=live)
    ####################################################################

    # 设置撮合模式，撮合价格THIS_CLOSE，当前Bar的Close价，按百分比撮合
    brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='PERCENT', fill_vol=1.0)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames=instrument,                    # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame=time_frame,                  # 回测频度
        instrument_type=instrument_type,        # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyLogExample)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告文件
    brain.generate_report(plot = True, plotname="StrategyFundPlay")
    ####################################################################

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())


if __name__ == '__main__':
    main()


    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 2000000.0
    # StrategyProfitRate       : 0.0
    # AnnualProfitRate         : 0.0
    # SharpeRatio              : 0
    # MaxDrawDown              : 0.0
    # MaxDrawDownFrom          : 2020-01-02
    # MaxDrawDownTo            : 2020-01-02
    # WinLostRatio             : 0
    # WinRate                  : 0
    # ================================================================================