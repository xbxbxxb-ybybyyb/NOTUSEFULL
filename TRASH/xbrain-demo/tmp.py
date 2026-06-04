# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase

# 演示高频T0策略，设置撮合模式目标价参数为THIS_OPEN，按当前bar open价格为目标价撮合成交订单
# 撮合目标价有两种模式， THIS_CLOSE, THIS_OPEN，THIS_OPEN市价单按当前Bar的Open价格撮合成交



# 策略类，是用户需要实现的主要内容。
class StrategySMA(StrategyBase): # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义
    params = (
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 3000),                   # 每笔交易手数
        ('period', 120),                    # SMA参数
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.sma = xb.talib.SMA(                   # 调用 xbrain 集成的 talib 因子计算功能，计算短期 SMA 值
            self.data.close, timeperiod=self.params.period  # 指定 SMA 参数为 self.params.period
        )

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def next(self):
        # 通过 get_position 方法，获得持仓信息，
        # 持仓信息即 Position 对象包含属性：
        # -- size: 头寸大小
        # -- price: 平均成本价
        pos = self.get_position(self.datas[0])
        pos_size = pos.size
        pos_cost = pos.price

        # 如果无持仓，收盘价站上（即金叉）SMA 时开仓买入
        if pos_size == 0 and self.close[0] > self.sma[0] and self.close[-1] <= self.sma[-1]:
            self.buy(size=self.params.tradesize)
            return

        # 如果有持仓，则计算盈亏情况，决定是否止盈止损
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
    brain = XBrain(start_date="20230109 000000000", end_date="20230109 235959000", live=False)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    stock = '508066.SH'
    brain.add_feeds(
        datanames=stock,                # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",              # 回测频度
        instrument_type='FUND',        # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 设置撮合目标价为当前bar的open价，模式为默认PENCENT，按比例撮合
    brain.set_fill_method(fill_price='THIS_OPEN')
    # brain.set_fill_method(fill_price='THIS_CLOSE')

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
    brain.generate_report(plot=True, plotname="StrategyThisOpen")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())

    # 回测结果：
    # THIS_OPEN模式：
    #
    # ================================================================================
    # Final Portfolio Value    : 1004573.98
    # StrategyProfitRate       : 0.004573976999999951
    # AnnualProfitRate         : 0.0277596014292123
    # SharpeRatio              : -0.833980087636887
    # MaxDrawDown              : 0.0029930294708118074
    # MaxDrawDownFrom          : 2019-03-06
    # MaxDrawDownTo            : 2019-03-26
    # WinLostRatio             : 0
    # WinRate                  : 1.0
    # ================================================================================
    #
    #
    # MaxDrawDownTo  SharpeRatio  RewardRiskRatio  WinRate
    # 0    2019-03-26      -0.8340                0   1.0000
    # is_sub_trade             Datetime       Code Direction OrderType  Size \
    #     0             0  2019-03-01T09:39:15  000001.SZ      LONG    MARKET  3000
    # 1             0  2019-04-04T09:41:00  000001.SZ     SHORT    MARKET -3000
    # 2             0  2019-04-04T09:43:33  000001.SZ      LONG    MARKET  3000
    #
    # ExecutedPrice       Value    Comm  OrderSize CreatedPrice     Status \
    #     0        12.3100  36930.0000 11.0790       3000               COMPLETED
    # 1        13.5300 -40590.0000 52.7670      -3000               COMPLETED
    # 2        13.5300  40590.0000 12.1770       3000               COMPLETED
    #
    # RealizedPnl        LastTradeTime  Type  AccountEquity
    # 0       0.0000  2019-03-01T09:39:15   BUY   1000000.0000
    # 1    3596.1540  2019-04-04T09:41:00  SELL   1003708.9210
    # 2       0.0000  2019-04-04T09:43:33   BUY   1003596.1540
    #
    #
    #
    # THIS_CLOSE模式：
    #
    # ================================================================================
    # Final Portfolio Value    : 1004093.59
    # StrategyProfitRate       : 0.0040935929999998955
    # AnnualProfitRate         : 0.024814296741847652
    # SharpeRatio              : -1.0524719953215562
    # MaxDrawDown              : 0.0029933879502574957
    # MaxDrawDownFrom          : 2019-03-06
    # MaxDrawDownTo            : 2019-03-26
    # WinLostRatio             : 0
    # WinRate                  : 1.0
    # ================================================================================
    #
    #
    # StrategyProfitRate  AnnualProfitRate  MaxDrawDown MaxDrawDownFrom \
    #     0              0.0041            0.0248       0.0030      2019-03-06
    #
    # MaxDrawDownTo  SharpeRatio  RewardRiskRatio  WinRate
    # 0    2019-03-26      -1.0525                0   1.0000
    # is_sub_trade             Datetime       Code Direction OrderType  Size \
    #     0             0  2019-03-01T09:39:15  000001.SZ      LONG    MARKET  3000
    # 1             0  2019-04-04T09:55:24  000001.SZ     SHORT    MARKET -3000
    # 2             0  2019-04-04T10:04:45  000001.SZ      LONG    MARKET  3000
    #
    # ExecutedPrice       Value    Comm  OrderSize CreatedPrice     Status \
    #     0        12.3500  37050.0000 11.1150       3000               COMPLETED
    # 1        13.5800 -40740.0000 52.9620      -3000               COMPLETED
    # 2        13.7000  41100.0000 12.3300       3000               COMPLETED
    #
    # RealizedPnl        LastTradeTime  Type  AccountEquity
    # 0       0.0000  2019-03-01T09:39:15   BUY   1000000.0000
    # 1    3625.9230  2019-04-04T09:55:24  SELL   1003708.8850
    # 2       0.0000  2019-04-04T10:04:45   BUY   1003625.9230

