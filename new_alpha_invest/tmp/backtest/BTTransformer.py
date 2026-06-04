# -*- coding: utf-8 -*-
from xbrain import XBrain
import pandas as pd
from xbrain.strategy_base import StrategyBase
from datetime import datetime, timedelta
from xquant.factordata import FactorData
import xbrain as xb

# 策略逻辑类，
class StrategyMultifactors(StrategyBase):
    params = (
        ('K', 100),
        ('cash_reserve', 0.1),  # 每次换仓，保留一定比例的现金，不 allin
        ('rebalance_period', 1),
    )

    def __init__(self):
        self.last_rebalance_day = 0
        self.momentum_20 = {}
        self.momentum_3 = {}
        self.volume = {}
        self.cf = {}

    def next(self):
       pass


def main():
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20200107 000000000", end_date="20201231 235959000", live=False)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    fa = FactorData()
    stock_list = fa.hset('20200612', 'HS300', 0)['stock'].tolist()

    brain.add_feeds(
        datanames=stock_list,                         # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame='K_DAY',                           # 回测频度
        instrument_type='STOCK',                      # 标的品种，枚举变量，可选有 STOCK, FUTURE
        method=True                                   # 后复权，仅日频股票数据有复权价格
    )
    ####################################################################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyMultifactors)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    brain.generate_report(plot = True, plotname="StrategyAlpha")
    ####################################################################

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息，daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())


if __name__ == '__main__':
    main()


    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 1046441.69
    # StrategyProfitRate       : 0.04644169224704919
    # AnnualProfitRate         : 0.048819579380159794
    # SharpeRatio              : 0.18505091084106257
    # MaxDrawDown              : 0.16231469647986604
    # MaxDrawDownFrom          : 2020-02-25
    # MaxDrawDownTo            : 2020-04-28
    # WinLostRatio             : 1.8681679205484982
    # WinRate                  : 0.36847710330138445
    # ================================================================================