# -*- coding: utf-8 -*-

from xbrain import XBrain
from tquant.stock_data import StockData
from xbrain.strategy_base import StrategyBase
from talib import SMA
import pandas as pd
import xbrain as xb


# 演示自定义行情加载，自定义数据加载
# 自定义加载DataFrame数据(DataFrame需存在相对应命名的列，区分大小写)
# 需包含 ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume'] 字段。

class StrategyCustomData(StrategyBase): # 策略类需继承 StrategyBase 基类
    # 策略涉及的参数在 params 中定义，通过 self.params.period 访问
    params = (
        ('stoploss', 0.1),                  # 止损比例
        ('takeprofit', 0.1),                # 止盈比例
        ('tradesize', 300),                   # 每笔交易股数
        ('period', 60),
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.count = 0

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def next(self):
        self.count += 1
        # 未达到sma最低窗口要求，直接return
        if self.count < self.params.period:
            return

        # self.log('close: {}, SMA: {}, Pos: {} @ {}'.format(
        #     self.close[0], self.sma[0], pos_size, pos_cost
        # ))

        pos = self.get_position(self.datas[0])
        pos_size = pos.size
        pos_cost = pos.price

        # 计算sma60
        smadf = self.get_past_feed_price_df(['000002.SZ'], 61)['000002.SZ']
        sma = SMA(smadf['close'].values, timeperiod=self.params.period)

        # 如果无持仓，收盘价站上（即金叉）SMA 时开仓买入
        if pos_size == 0 and self.close[0] > float(sma[-1]) and self.close[-1] <= sma[-2]:
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


def filter_stock_callauction_data(df):
    # 添加自定义数据进回测框架
    stock_am_pd = df[((df['MDTime'] >= '09250000') & (df['MDTime'] < '11300000')) |
                     ((df['MDTime'] >= '13000000') & (df['MDTime'] <= '15000000'))]
    return stock_am_pd


def main():
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20190101 000000000", end_date="20190131 235959000", live=False)
    ####################################################################

    # 通过数据计算平台获取自定义数据，或自定义数据加载
    sd = StockData()
    instrument = "000002.SZ"
    data = sd.get_stock_tick(trading_code=instrument, start_datetime='20190125 000000000', end_datetime='20190131 235959000')
    data = filter_stock_callauction_data(data)
    data.drop(columns = ["ClosePx"], inplace = True)
    data.rename(columns={'LastPx': 'ClosePx'}, inplace=True)
    #自定义数据必须包含如下列['MDDate', 'MDTime', 'Open', 'High', 'Low', 'Close', 'Volume']；
    #自定义数据可以添加其他列，并在Strategy类中通过self.datas[0].{字段名}来获取
    data = data[['MDDate', 'MDTime', 'OpenPx', 'HighPx', 'LowPx', 'ClosePx', 'TotalVolumeTrade', 'TotalValueTrade']]
    data.columns = ['MDDate', 'MDTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Value']
    data['Datetime'] = data.apply(lambda x: x['MDDate'] + ' ' + x['MDTime'], axis=1)
    data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Value']]
    data['Datetime'] = pd.to_datetime(data['Datetime'], format='%Y%m%d %H%M%S%f')

    # 加载自定义数据到回测框架
    # 注：需要告知框架数据的粒度，即 time_frame, compression，用于时间对齐。
    # 若数据为 1 分钟K，则 time_frame = 'K_1MIN', compression=1,
    # 若数据为 TICK数据，则 time_frame = 'TICK'.
    brain.add_data(df=data, dataname=instrument, time_frame='TICK', instrument_type='STOCK')

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyCustomData)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot = True, plotname="StrategyCustomData")

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
    # Final Portfolio Value    : 1000636.79
    # StrategyProfitRate       : 0.0006367860000000558
    # AnnualProfitRate         : 0.032604034131350046
    # SharpeRatio              : -5.723691099187546
    # MaxDrawDown              : 0.0
    # MaxDrawDownFrom          : 2019-01-25
    # MaxDrawDownTo            : 2019-01-25
    # WinLostRatio             : 0
    # WinRate                  : 1.0
    # ================================================================================