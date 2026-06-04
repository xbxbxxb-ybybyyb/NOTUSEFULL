# -*- coding: utf-8 -*-

from xbrain import XBrain
from tquant.stock_data import StockData
from xbrain.strategy_base import StrategyBase
import pandas as pd


# 演示使用加载不同的自定义行情数据，并对应同一策略并行回测，此处策略中仅进行打印操作

class StrategyLogExample(StrategyBase):  # 需继承 StrategyBase 基类，

    def __init__(self):
        # XBrain 支持多数据源，多时间窗口回测，并自动进行时间对齐。
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

        # 对于自定义加载的其他自定义字段可以通过get_past_feed_price_df获取当前回测之前的窗口数据
        df = self.get_past_feed_price_df(self.getdatanames()[0], 10)

def filter_stock_callauction_data(df):
    # 添加自定义数据进回测框架
    stock_am_pd = df[((df['MDTime'] >= '09250000') & (df['MDTime'] < '11300000')) |
                     ((df['MDTime'] >= '13000000') & (df['MDTime'] <= '15000000'))]
    return stock_am_pd

def get_stock_data_df(symbol, start_time, end_time):
    # 通过数据计算平台获取自定义数据，或自定义数据加载
    sd = StockData()
    instrument = symbol
    data = sd.get_stock_tick(trading_code=instrument, start_datetime=start_time, end_datetime=end_time)
    data = filter_stock_callauction_data(data)
    data.drop(columns = ["ClosePx"], inplace = True)
    data.rename(columns={'LastPx': 'ClosePx'}, inplace=True)
    #自定义数据必须包含如下列['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Value']；
    #自定义数据可以添加其他列，并在Strategy类中通过self.datas[0].{字段名}，来获取
    data = data[['MDDate', 'MDTime', 'OpenPx', 'HighPx', 'LowPx', 'ClosePx', 'TotalVolumeTrade', 'TotalValueTrade']]
    data.columns = ['MDDate', 'MDTime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Value']
    data['Datetime'] = data.apply(lambda x: x['MDDate'] + ' ' + x['MDTime'], axis=1)
    data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume', 'Value']]
    data['Datetime'] = pd.to_datetime(data['Datetime'], format='%Y%m%d %H%M%S%f')
    return data


def main():
    # 创建回测框架 XBrain 实例
    start_date = "20190101 000000000"
    end_date = "20190108 235959000"
    symbols = ['000001.SZ', '000002.SZ']
    brain = XBrain(start_date=start_date, end_date=end_date, live=False)
    ####################################################################

    # 加载多个自定义数据到回测框架
    for symbol in symbols:
        data = get_stock_data_df(symbol, start_date, end_date)
        brain.add_data(df=data, dataname=symbol, time_frame='TICK', instrument_type='STOCK')

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyLogExample)
    ####################################################################

    # 运行回测
    # 参数parallel_run: 是否并行，类型bool，True并行运行，False为单进程运行，默认False不并行
    # 参数parallel_on_feeds: True按加载feeds并行，False按自定义加载的data并行，默认True按feeds并行
    # 返回多个并行结果集对象
    results = brain.backtest_run(parallel_run=True, parallel_on_feeds=False)
    ####################################################################

    # 生成回测报告，并行时生成回测报告有两种方式
    # 1.根据并行运行返回的结果集选择性输出使用
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    for result in results:
        result.generate_report(plot = True, plotname="StrategyCustomData")
        # 获取Analyzers分析的结果
        # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
        trade_summary, trade_records, daily_pnl = result.get_analyzer_result()
        print(trade_summary.head())
        print(trade_records.head())
        print(daily_pnl.head())

    # 2.由XBrain对象控制统一输出使用
    # brain.generate_report(plot = True, plotname="StrategyCustomData")
    # results = brain.get_analyzer_result()

if __name__ == '__main__':
    main()