# -*- coding: utf-8 -*-

from xbrain import XBrain
from xbrain.strategy_base import StrategyBase

# 演示策略行情播放（期货），并通过get_past_feed_price_df获取df格式的已回放过的历史行情数据
# 期货相当于股票基金回测设置有所差异，期货回测时，可以设置相应的保证金倍率
# 实例化XBrain时添加margin_multi（保证金倍率）参数，实际保证金比例为品种最低要求保证金比率（margin） * 保证金倍率。
# 合约乘数和品种最低要求的保证金比率（margin）由框架自动获取，比如沪深300指数期货的合约乘数为300，最低要求的保证金比率为10%。

# 策略类，是用户需要实现的主要内容。
# 此例是一个简单策略，主要展示如何在 XBrain 框架中获取数据，并使用 log 功能进行打印。
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

        # TICK数据返回的是key为标的，value为DataFrame的字典，日频数据返回的是multiindex的DataFrame数据
        data_df = self.get_past_feed_price_df(['IC00.CF'], 10)['IC00.CF']


# 程序主体，设置保证金倍率，设置换点倍率
def main():
    instrument_type = "FUTURE"                  # 回测品种类型，目前支持 "STOCK", "FUTURE", "FUND"
    start = "20210608 000930000"                # 回测开始时间, 默认
    end = "20210608 100059000"                  # 回测结束时间，默认
    live = False                                # 是否模拟跟踪，True为模拟跟踪，False为策略回测， 默认为False
    time_frame = "TICK"                        # 回测频度，目前支持 "K_1MIN", "K_DAY", "TICK"
    instrument = "IC00.CF"                         # 回测品种，目前支持"ICZL", "IFZL", "IHZL"以及全A股
    init_amount = 2000000                       # 回测金额，默认为1000000
    margin_multi = 2                            # 保证金倍率
    slippage_multi = 1                          # 滑点倍率, 实际滑点为品种价格最小变动单位 * 滑点倍率
    commission = 0.0003                        # 佣金比例，commission 为佣金占该笔交易总成交金额比例

    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date=start, end_date=end, init_amount=init_amount, slippage_multi=slippage_multi,
                   commission=commission, margin_multi=margin_multi, live=live)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames=instrument,                    # 期货标的名称，IC2001.CF表示真实合约，IC00.CF表示合成的主力合约行情（未复权）
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

    # 生成回测报告
    brain.generate_report(plot=True, plotname="StrategyFuturePlay")
    ####################################################################

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())

if __name__ == '__main__':
    main()
