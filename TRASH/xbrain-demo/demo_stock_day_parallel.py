# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from talib import SMA

# 使用简单的两个策略，一个打印，一个使用SMA指标，进行并行运算
# 使用一份数据，两个策略，并行进行不同的计算
# 并行策略支持笛卡尔积的形式，提供策略与数据的并行，如添加一份数据，添加两个策略则以策略为维度两个实例并行
# 如添加两份数据，添加一个策略，则是以数据为维度两个实例并行


class StrategySMA(StrategyBase): # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义
    params = (
        ('short_period', 10),               # sma10窗口
        ("middle_period", 30),              # sma30窗口
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 300),                # 每笔交易股数
    )

    def __init__(self):
        self.close = self.datas[0].close
        # short = self.p.short_period
        # init中统一计算sma30
        self.sma30 = xb.talib.SMA(
            self.data.close, timeperiod=30   # 指定 SMA 参数为 self.params.middle_period
        )

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def next(self):
        pos = self.get_position(self.datas[0])
        pos_size = pos.size
        pos_cost = pos.price

        # 回放中计算十日均线
        sma_df = self.get_past_feed_price_df(['000001.SZ'], 10)
        sma10 = SMA(sma_df['close'].values, timeperiod=10)

        # 如果无持仓，收盘价站上SMA10，金叉时开仓买入
        if pos_size == 0 and self.close[0] > self.sma30[0] and self.close[-1] <= sma10[-1]:
            self.buy(size=300)
            return

        # 如果无持仓，且10日均线上穿SMA30均线时买入
        if pos_size == 0 and sma10[-1] > self.sma30[0] and sma10[-2] < self.sma30[-1]:
            self.buy(size=300)
            return

        # 若当前持仓可卖空，且十日均线下穿30日线时清仓操作
        if pos.closeable_amount() > 0 and sma10[-1] < self.sma30[0] and sma10[-2] > self.sma30[-1]:
            self.closeout(data=self.get_data_by_name('000001.SZ'))

        # 如果有可卖持仓，则计算盈亏情况，决定是否止盈止损
        # 止损
        if pos.closeable_amount() > 0 and self.close[0] <= pos_cost * (1 - 0.1):
            self.sell(size=300)
            return

        # 止盈
        if pos.closeable_amount() > 0 and self.close[0] >= pos_cost * (1 + 0.1):
            self.sell(size=300)
            return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


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
    brain = XBrain(start_date="20210201 000000000", end_date="20210908 235959000", live=False)
    ###################################################################


    brain.add_feeds(
        datanames='000001.SZ',                # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="K_DAY",              # 回测频度
        instrument_type='STOCK',        # 标的品种，枚举变量，可选有 STOCK, FUTURE
        method=True
    )
    brain.add_strategy(StrategyLogExample)
    brain.add_strategy(StrategySMA)

    # 运行回测
    # 参数parallel_run: 是否并行，类型bool，True按笛卡尔积并行运行，False为单进程运行，默认False不并行
    # 参数parallel_on_feeds: parallel_run为True时生效，True按加载feeds并行，False按自定义加载的data并行，默认True按feeds并行
    brains = brain.backtest_run(parallel_run=True)

    ###################################################################

    # 可以整体生成回测报告文件
    brain.generate_report(plot=True, plotname="StrategyDayParallel")
    # 同时可以根据backtest_run返回值取brain结果集对象，自定义生成需要的回测报告以及回测图例，brains[0]代表第一个并行，以此类推
    # brain[0].generate_report(plot=True, plotname="testStrategy")

    # 获取整体多个Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    records_list = brain.get_analyzer_result()
    # 或与回测报告一样，根据backtest_run返回值生成需要的结果
    # trade_summary, trade_records, daily_pnl = brains[0].get_analyzer_result()
    # print(trade_summary.head())
    # print(trade_records.head())
    # print(daily_pnl.head())


