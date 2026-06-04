# -*- coding: utf-8 -*-
from tquant.stock_data import StockData
import pandas as pd
from xbrain import XBrain
from xbrain.strategy_base import StrategyBase

# 演示加载日频multiindex的自定义因子数据，通过TQuant获取日频的换手率，振幅两个因子，并通过get_past_factor_df获取加载的df格式的因子数据


# 策略类，是用户需要实现的主要内容。
# 此例是一个简单策略，主要展示如何在 XBrain 框架中获取数据，并使用 log 功能进行打印。
class StrategyFactorExample(StrategyBase):  # 需继承 StrategyBase 基类，
    def next(self):
        # TICK数据返回的是key为标的，value为DataFrame的字典，日频数据返回的是multiindex的DataFrame数据
        data_df = self.get_past_feed_price_df(['000001.SZ'], 1)


# 程序主体，设置保证金倍率，设置换点倍率
def main():
    sd = StockData(data_source="finchina")
    stock_list = ["000001.SZ", "000002.SZ"]
    date_list = ("20200101", "20201231")
    factor_list1 = ['turn', 'swing',]
    data = sd.get_factor_price_daily(stock_list, date_list, factor_list1, fill_na=True).reset_index()
    data['Datetime'] = pd.to_datetime(data['mddate'], format='%Y%m%d')
    data.reset_index()
    data = data.rename(columns={'stock': 'Symbol'})
    data.set_index(["Datetime", "Symbol"])

    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20200101 000000000", end_date="20201231 000000000")
    ####################################################################

    # 加载数据到回测框架
    brain.add_feeds(datanames=["000001.SZ", "000002.SZ"], time_frame="K_DAY", instrument_type="STOCK")
    ####################################################################

    # 加载自定义因子数据到框架
    brain.add_cache_factor_df(data, "K_DAY")
    ####################################################################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyFactorExample)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    brain.generate_report(plot=True, plotname="StrategyCustomFactor")
    ####################################################################

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())


if __name__ == '__main__':
    main()
