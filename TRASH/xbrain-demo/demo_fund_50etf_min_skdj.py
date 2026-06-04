# -*- coding: utf-8 -*-

from xbrain import XBrain
import xbrain as xb
from xbrain.strategy_base import StrategyBase
import pandas as pd
import talib

# 演示自定义SKDJ指标，并在自定义添加的50etf分钟频数据中进行回测使用
# g使用et_past_feed_price_df接口获取回测原始dataframe数据，并计算SKDJ指标
# SKDJ指标公式计算如下

def LLV(df, N):
    return pd.Series.rolling(df,N).min()

def HHV(df, N):
    return pd.Series.rolling(df,N).max()

def EMA(df, N):
    return pd.Series.ewm(df, span=N, min_periods=N-1, adjust=True).mean()

def MA(DF, N):
    return pd.Series.rolling(DF, N).mean()

def SKDJ(df,N,M):
    CLOSE = df['close']
    LOWV = LLV(df['low'], N)
    HIGHV = HHV(df['high'], N)
    RSV = EMA((CLOSE - LOWV) / (HIGHV - LOWV) * 100, M)
    K = EMA(RSV, M)
    D = MA(K, M)
    DICT = {'SKDJ_K': K, 'SKDJ_D': D}
    VAR = pd.DataFrame(DICT)
    return VAR


class StrategySKDJ(StrategyBase): # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('tradesize', 3000),                   # 每笔交易股数
    )

    def __init__(self):
        self.skdj_k = []
        self.skdj_d = []

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def next(self):
        if len(self) < 120:
            return

        # 获取回测数据并计算指标
        data = self.get_past_feed_price_df("510050.SH", 120)["510050.SH"]
        skdj = SKDJ(data, 60, 30)
        skdj_k = skdj.iloc[-1, :].SKDJ_K
        skdj_d = skdj.iloc[-1, :].SKDJ_D
        self.skdj_k.append(skdj_k)
        self.skdj_d.append(skdj_d)
        if len(self.skdj_k)<2:
            return

        # 1.指标>80 时，回档机率大；指标<20 时，反弹机率大；
        # 2.K在20左右向上交叉D时，视为买进信号；
        # 3.K在80左右向下交叉D时，视为卖出信号；
        pos = self.get_position(self.datas[0])
        if pos.size == 0 and self.skdj_k[-2] <= 25 and self.skdj_k[-1]>25:
            self.buy(data=self.datas[0], size=self.params.tradesize)
            return

        if pos.closeable_amount() > 0 and self.skdj_k[-1] > 80 and self.skdj_k[-2] <=80:
            self.closeout(data=self.datas[0])
            return

    def stop(self):
        pos = self.get_position(self.datas[0])
        print(pos.closeable_amount())
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


if __name__ == '__main__':
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20200331 000000000", end_date="20200830 235959000", live=False, commission=0.0)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    load_self_data = True
    if load_self_data:
        data = pd.read_pickle("50etf_1.pkl").reset_index()
        data = data[['MDDate', 'MDTime', 'OpenPx', 'HighPx', 'LowPx', 'ClosePx', 'TotalVolumeTrade']]
        data.columns = ['MDDate', 'MDTime', 'Open', 'High', 'Low', 'Close', 'Volume']
        data['Datetime'] = data.apply(lambda x: x['MDDate'] + ' ' + x['MDTime'], axis=1)
        data = data[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
        data['Datetime'] = pd.to_datetime(data['Datetime'], format='%Y%m%d %H%M%S%f')
        brain.add_data(df=data, dataname="510050.SH", time_frame='K_1MIN', instrument_type='FUND')
    else:
        data = brain.add_feeds(datanames="510050.SH", time_frame='K_1MIN', instrument_type='FUND')

    ####################################################################

    # 设置撮合模式
    # THIS_CLOSE为当前bar的close价为目标撮合价格，并在当前bar以当前bar的close价格尝试撮合成交
    brain.set_fill_method(fill_price='THIS_CLOSE', fill_method='PERCENT')

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategySKDJ)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot=True, plotname="StrategySKDJ")

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())

    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 998820.29
    # StrategyProfitRate       : -0.0011797050000003084
    # AnnualProfitRate         : -0.0037582510771128064
    # SharpeRatio              : -23.68423781623521
    # MaxDrawDown              : 0.0018467690966114036
    # MaxDrawDownFrom          : 2020-01-02
    # MaxDrawDownTo            : 2020-03-16
    # WinLostRatio             : 0.4587543523470229
    # WinRate                  : 0.5294117647058824
    # ================================================================================