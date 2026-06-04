# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase


# 演示高频T0策略模拟撮合订单。
# 在根据sma指标买入卖出基础上，设置撮合模式为Trade_Mocker按实际逐笔成交和逐笔委托数据模拟撮合，比较撮合模式普通、己方最优、对手方最优差别。
# 根据模拟撮合模式的不同，撮合明细有所差异，在get_analyzer_result接口中获取打印成交明细与撮合明细（一笔成交可能由多档盘口的成交按vwap汇总而得）。

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
            self.data.close, timeperiod=self.params.period  # 指定 SMA 参数为 self.params.p1
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

        #self.log('close: {}, SMA: {}, Pos: {} @ {}'.format(
        #    self.close[0], self.sma[0], pos_size, pos_cost))

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
    brain = XBrain(start_date="20190301 000000000", end_date="20190430 235959000", live=False)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    stock = '000001.SZ'
    brain.add_feeds(
        datanames=stock,                # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="TICK",              # 回测频度
        instrument_type='STOCK',        # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 设置撮合目标价为当前bar的open价，模式为模拟撮合
    # 常规模拟撮合
    brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='TRADE_MOCKER', mocker_type='NORMAL')
    # 己方最优
    # brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='TRADE_MOCKER', mocker_type='SAMESIDE_BEST')
    # 对手方最优
    # brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='TRADE_MOCKER', mocker_type='COUNTER_BEST')

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
    brain.generate_report(plot=True, plotname="StrategyTradeMocker")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())

    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 1004483.85
    # StrategyProfitRate       : 0.004483854000000065
    # AnnualProfitRate         : 0.02720650722732909
    # SharpeRatio              : -0.8748752969441289
    # MaxDrawDown              : 0.0029932983223458897
    # MaxDrawDownFrom          : 2019-03-06
    # MaxDrawDownTo            : 2019-03-26
    # WinLostRatio             : 0
    # WinRate                  : 1.0
    # ================================================================================
