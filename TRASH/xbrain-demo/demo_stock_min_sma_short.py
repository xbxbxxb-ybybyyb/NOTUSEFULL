# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from tquant import StockData


# 演示高频T0策略卖空和普通撮合。
# 在根据sma指标买入卖出基础上，添加底仓，允许卖空，并对比NEXT_OPEN和THIS_CLOSE两种不同撮合方式的差别。

# 策略类，是用户需要实现的主要内容。
class StrategySMA(StrategyBase): # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 300),                   # 每笔交易股数
        ('period', 120),                    # SMA参数
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.sma = xb.talib.SMA(                            # 调用 xbrain 集成的 talib 因子计算功能，计算短期 SMA 值
            self.data.close, timeperiod=self.params.period  # 指定 SMA 参数为 self.params.period
        )

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def next(self):
        # 通过 get_position 方法，获得持仓信息，
        # 持仓信息即 Position 对象包含属性：
        # -- size: 头寸大小
        # -- price: 平均成本价
        pos = self.get_position_by_name('000001.SZ')
        pos_size = pos.size
        pos_cost = pos.price

        # self.log('close: {}, SMA: {}, Pos: {} @ {}'.format(
        #     self.close[0], self.sma[0], pos_size, pos_cost
        # ))

        # 如果无持仓，收盘价站上（即金叉）SMA 时开仓买入
        if pos_size == 0 and self.close[0] > self.sma[0] and self.close[-1] <= self.sma[-1]:
            self.buy(data=self.get_data_by_name('000001.SZ'), size=self.params.tradesize)
            return

        # 如果有持仓，则计算盈亏情况，决定是否止盈止损
        # 止损
        if pos.closeable_amount() > 0 and self.close[0] <= pos_cost * (1 - self.params.stoploss):
            self.sell(data=self.get_data_by_name('000001.SZ'), size=self.params.tradesize)
            return

        # 止盈
        if pos.closeable_amount() > 0 and self.close[0] >= pos_cost * (1 + self.params.takeprofit):
            self.sell(data=self.get_data_by_name('000001.SZ'), size=self.params.tradesize)
            return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    stock = '000001.SZ'
    start_date = "20200401 093000000"
    end_date = "20200430 105959000"

    brain = XBrain(start_date=start_date, end_date=end_date, live=False)
    # 添加底仓除了使用add_initial_position接口，还可以实例化XBrain时添加allow_short参数，可以允许做空
    # brain = XBrain(start_date=start_date, end_date=end_date, live=False, allow_short=True)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames=stock,                # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="K_1MIN",              # 回测频度
        instrument_type='STOCK',        # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )

    brain.add_feed_benchmark(
        dataname='000300.SH',  # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="K_1MIN",  # 回测频度
        instrument_type='STOCK',  # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 设置底仓，支持多标的添加多次
    sd = StockData()
    price = sd.get_factor_price_daily([stock], [start_date[:8]], ["close"]).iloc[0, 0]
    print("stock {}, price: {}.".format(stock, price))
    brain.add_initial_position(symbol=stock, size=300, price=price)

    # 设置撮合模式
    # 根据需要，自定义撮合时的目标价，普通模式有两种，NEXT_OPEN，与THIS_CLOSE
    brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='PERCENT')

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
    brain.generate_report(plot=True, plotname="StrategyShort")

    # 获取Analyzers分析的结果
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())

    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 1004076.63
    # StrategyProfitRate       : 0.00020882049116055512
    # AnnualProfitRate         : 0.002508725893986874
    # BenchmarkProfitRate      : 0.06198057089917253
    # BenchmarkAnnualProfitRate: 1.0814857451342665
    # SharpeRatio              : -40.2778074571071
    # MaxDrawDown              : 8.628616197521503e-05
    # MaxDrawDownFrom          : 2020-04-07
    # MaxDrawDownTo            : 2020-04-20
    # WinLostRatio             : 2.216243630314477
    # WinRate                  : 0.45
    # ================================================================================