# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
from talib import SMA

# 使用简单指标，SMA指标，并进行买入卖出操作
# 策略中展示以不同方式计算双均线，init中统一计算sma30，回放中实时计算sma10，并在数据回放时以不同形式获取
# 获取Analyzer分析总体评价，以及逐笔订单详情


# 策略类，是用户需要实现的主要内容。
# 此例是一个完整有意义的策略，主要展示如何在 XBrain 框架中获得信号，并对应下单。
# 策略介绍：收盘价站上 SMA 均线时开仓买入，+10%止盈，-10%止损。
# 演示了两种指标计算方式：（1）init中按xbrain函数一次算完全部指标；（2）next方法通过get_past_feed_price_df获取行情增量计算。
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
        # init中统一计算sma30
        self.sma30 = xb.talib.SMA(                                  # 调用 xbrain 集成的 talib 因子计算功能，计算中期 SMA 值
            self.data.close, timeperiod=self.params.middle_period   # 指定 SMA 参数为 self.params.middle_period
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

        # 回放中计算十日均线
        sma_df = self.get_past_feed_price_df(['000001.SZ'], 10)
        sma10 = SMA(sma_df['close'].values, timeperiod=10)

        # 如果无持仓，收盘价站上SMA10，金叉时开仓买入
        if pos_size == 0 and self.close[0] > self.sma30[0] and self.close[-1] <= sma10[-1]:
            self.buy(size=self.params.tradesize)
            return

        # 如果无持仓，且10日均线上穿SMA30均线时买入
        if pos_size == 0 and sma10[-1] > self.sma30[0] and sma10[-2] < self.sma30[-1]:
            self.buy(size=self.params.tradesize)
            return

        # 若当前持仓可卖空，且十日均线下穿30日线时清仓操作
        if pos.closeable_amount() > 0 and sma10[-1] < self.sma30[0] and sma10[-2] > self.sma30[-1]:
            self.closeout(data=self.get_data_by_name('000001.SZ'))

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
    brain = XBrain(start_date="20190107 000000000", end_date="20191231 235959000", live=False)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    stock = '000001.SZ'
    brain.add_feeds(
        datanames=stock,                               # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="K_DAY",                            # 回测频度
        instrument_type='STOCK',                      # 标的品种，枚举变量，可选有 STOCK, FUTURE
        method = True,                                # 为True使用后复权价格，False使用原始价格，仅日频股票数据有复权价格
    )
    ####################################################################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategySMA)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################


    # 生成回测报告文件
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot=True, plotname="StrategySMA")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())


    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 1093090.38
    # StrategyProfitRate       : 0.09309037734640313
    # AnnualProfitRate         : 0.0975402502365319
    # SharpeRatio              : 0.5444212782566664
    # MaxDrawDown              : 0.08016499710721937
    # MaxDrawDownFrom          : 2019-04-19
    # MaxDrawDownTo            : 2019-06-19
    # WinLostRatio             : 1.5371690308559396
    # WinRate                  : 0.6666666666666666
    # ================================================================================
