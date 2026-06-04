# -*- coding: utf-8 -*-
import time
from xbrain import XBrain
import xbrain as xb
from talib import SMA
from xbrain.strategy_base import StrategyBase


# ======================================================================================================

class StrategyExample(StrategyBase):  # 策略类需继承 StrategyBase 基类

    # 策略涉及的参数在 params 中定义，通过 self.params.p1 访问
    params = (
        ('period', 10),  # sma10窗口
        ('stoploss', 0.05),  # 止损比例
        ('takeprofit', 0.05),  # 止盈比例
        ('opencashpercent', 0.5)  # 开仓比例
    )

    def __init__(self):
        self.close = self.datas[0].close
        self.open = self.datas[0].open

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

        instrument = self.datas[0].get_data_name()  # 标的
        sma_df = self.get_past_feed_price_df(instrument, 10)[instrument]  # 标的行情数据
        sma10 = SMA(sma_df['open'].values, timeperiod=10)  # sma
        cash = self.get_cash()  # 可用现金

        # 数据情况
        # self.log('收盘价 {}, {} --- sma {} --- 当前仓位 {}'.format(self.close[-1], self.close[0], sma10[-2:], pos_size))

        # 开空和开多单独运行
        # ===================================================
        # 开多
        # 如果无持仓，收盘价站上SMA10，金叉时开仓买入
        # if pos_size == 0 and self.close[0] > sma10[-1] and self.close[-1] <= sma10[-2]:
        #     self.buy(value=self.params.opencashpercent * cash)
        #     self.log('开仓：价格{}， 金额{}'.format(self.close[0], self.params.opencashpercent * cash))
        #     return

        # ===================================================

        # 开空
        # 如果无持仓，收盘价低于SMA10，死叉时开仓卖出
        if pos_size == 0 and self.open[0] < sma10[-1] and self.open[-1] >= sma10[-2]:
            print(sma_df[['open', 'close']][-2:])
            self.sell(value=self.params.opencashpercent * cash)
            self.log('开仓：价格{}， 金额{}'.format(self.open[0], self.params.opencashpercent * cash))
            return
        # ===================================================

        # 平仓
        # 如果有持仓，则计算盈亏情况，决定是否止盈止损
        # 止损
        if pos.closeable_amount() != 0 and self.open[0] <= pos_cost * (1 - self.params.stoploss):
            self.order_target_size(self.datas[0], target=0)
            self.log('平仓：成本{}, 数量{}'.format(pos_cost, pos_size))
            return

        # 止盈
        if pos.closeable_amount() != 0 and self.open[0] >= pos_cost * (1 + self.params.takeprofit):
            self.order_target_size(self.datas[0], target=0)
            self.log('平仓：成本{}, 数量{}'.format(pos_cost, pos_size))
            return

        # 持仓超过 250 分钟，则清仓
        if pos_size != 0 and self.count_bars_since_trade_open(self.datas[0]) > 250:
            print(sma_df[['open', 'close']][-2:])
            self.order_target_size(self.datas[0], target=0)
            self.log('平仓：成本{}, 数量{}'.format(pos_cost, pos_size))
            return

    def stop(self):
        self.log('End of backtest. Final value: {}'.format(self.get_value()))


# ======================================================================================================

def main():
    t1 = time.time()

    # 创建回测框架 XBrain 实例
    brain = XBrain(
        start_date="20210101 000000000",
        end_date="20210110 150000000",
        init_amount=2000000,
        commission=0.00025,  # 手续费
        margin_multi=1,  # 保证金倍率，仅期货品种适用，实际保证金比例为品种最低要求保证金比率（margin） * 保证金倍率。
        slippage_multi=0,  # 滑点倍率，实际滑点为品种价格最小变动单位（slippage） * 滑点倍率。
        live=False
    )
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    brain.add_feeds(
        datanames="IC00.CF",  # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="K_1MIN",  # 回测频度
        instrument_type='FUTURE',  # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )

    ####################################################################

    # # 加载平台行情基准数据
    # brain.add_feed_benchmark(
    #     dataname="IC00.CF",  # 基准标的代码
    #     time_frame="K_1MIN",  # 回测频度，枚举变量，可选有 'K_1MIN', 'K_DAY', 'TICK'
    #     instrument_type='FUTURE',  # 标的品种，枚举变量，可选有 STOCK, FUTURE
    # )

    ####################################################################

    # 设置撮合模式
    brain.set_fill_method(fill_price='THIS_OPEN')

    ####################################################################
    t2 = time.time()

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyExample)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    # param:
    # - plot: 是否绘图，True 绘制，False 不绘图
    # - plotname: 绘图名称
    brain.generate_report(plot=True, plotname='StrategyFutureSMA')
    ####################################################################

    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())
    # trade_summary.to_pickle("trade_summary.pkl")
    # trade_records.to_pickle("trade_records.pkl")
    print(trade_summary)
    print(trade_records)

    t3 = time.time()
    print('加载数据耗时：{}'.format(round(t2 - t1)))
    print('回测总耗时：{}'.format(round(t3 - t1)))


if __name__ == '__main__':
    main()

    # 注：任务运行结束后可能会出现以下异常信息，并不会影响运行结果，可以忽略。
    # Error in sys.excepthook:
    #
    # Original
    # exception
    # was:

    # 回测报告：
    # ================================================================================
    # Final Portfolio Value: 1722449.96
    # StrategyProfitRate   : -0.13877502000000064
    # AnnualProfitRate     : -0.9994631195945272
    # SharpeRatio          : -3.0616957195754995
    # MaxDrawDown          : 0.0992151857538933
    # MaxDrawDownFrom      : 2021-01-04
    # MaxDrawDownTo        : 2021-01-08
    # WinLostRatio         : 0.0
    # WinRate              : 0.0
    # ================================================================================
