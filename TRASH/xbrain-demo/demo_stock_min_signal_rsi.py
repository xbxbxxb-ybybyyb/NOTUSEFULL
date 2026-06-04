from xbrain.strategy_base import StrategyBase
import xbrain as xb
from xbrain import XBrain
import numpy as np, pandas as pd
import talib, time
from tquant.basic_data import BasicData
from tquant.stock_data import StockData


class StrategyExample(StrategyBase):
    params = (
        ('stock_num', 3),  # 最大持仓标的数量
    )

    def __init__(self):
        self.buy_list = []

        self.count = 0
        self.pool = ['300058.SZ', '000725.SZ', '300416.SZ', '603899.SH', '002594.SZ', '300529.SZ',
                     '601012.SH', '000661.SZ', '600763.SH', '300601.SZ', '300347.SZ', '300014.SZ',
                     '300661.SZ', '603589.SH', '603708.SH', '002714.SZ', '601888.SH', '000895.SZ',
                     '002456.SZ', '002351.SZ', '002959.SZ', '002901.SZ', '600660.SH', '300768.SZ',
                     '002821.SZ', '600276.SH', '600196.SH', '002371.SZ', '300595.SZ', '300750.SZ',
                     '600309.SH', '002352.SZ', '300357.SZ', '300009.SZ', '300702.SZ', '002595.SZ',
                     '300036.SZ', '300037.SZ', '002643.SZ', '002916.SZ', '601222.SH']

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def prenext(self):
        self.log("Current index: {}. Preparing for calculations.".format(len(self)))

    def next(self):
        pass

    def next_open(self):
        # 计算rsi调用add_feed数据，调整回测起始时间
        self.count += 1
        if self.count <= 100:
            return
        else:
            self.get_RSI_signal()
            self.orderStock()

    # ----计算股票池中每只股票的买卖信号，加入买卖股票列表中-------------------
    def get_RSI_signal(self):
        rsi_code = []
        buys = []
        sells = []
        buy_flag = 0
        pool = self.pool

        for stockcode in pool:
            prices = self.get_past_feed_price_df([stockcode], 60)
            # 注意：RSI函数使用的price必须是narray
            rsi = talib.RSI(prices[stockcode]['close'].values, timeperiod=6)[-1]
            rsi = int(rsi)

            # 形成买卖股票list
            if rsi < 25:
                rsi_code.append((rsi, stockcode))
                buy_flag = 1
            elif rsi > 85:
                sells.append(stockcode)

        if buy_flag == 1:
            rsi_code.sort(key=lambda x: x[0])
            buys = np.array(rsi_code)
            self.buy_list = list(buys[:, 1])
        else:
            self.buy_list = []

        self.sell_list = sells
        # self.log('buy_list: ' + str(self.buy_list))

    def orderStock(self):
        buys = self.buy_list
        sells = self.sell_list

        # 持仓标的
        positions_open = self.get_open_position().keys()

        # 卖出
        for stock, position in self.get_open_position().items():
            if stock in sells:
                data = self.get_data_by_name(stock)
                if position.closeable_amount() > 0:
                    self.closeout(data)
                    self.log('sell all:', stock)
                if stock not in self.pool:
                    self.closeout(data)
                    self.log('sell all:', stock)

        # 买入
        for stock in buys:
            if stock not in positions_open:
                available_cash = self.get_cash()
                if (self.p.stock_num - len(positions_open)) > 0:
                    data = self.get_data_by_name(stock)
                    buy_value = available_cash / (self.p.stock_num - len(positions_open))
                    self.buy(data, value=buy_value)
                    self.log('buy:' + stock + ' ' + str(buy_value))


def main():
    brain = XBrain(
        stocklike=True,
        start_date='20200101 000000000',
        end_date='20200114 235959000',
        init_amount=300000,
        commission=0.0003,
        live=False
    )
    ####################################################################
    pool = ['300058.SZ', '000725.SZ', '300416.SZ', '603899.SH', '002594.SZ', '300529.SZ',
            '601012.SH', '000661.SZ', '600763.SH', '300601.SZ', '300347.SZ', '300014.SZ',
            '300661.SZ', '603589.SH', '603708.SH', '002714.SZ', '601888.SH', '000895.SZ',
            '002456.SZ', '002351.SZ', '002959.SZ', '002901.SZ', '600660.SH', '300768.SZ',
            '002821.SZ', '600276.SH', '600196.SH', '002371.SZ', '300595.SZ', '300750.SZ',
            '600309.SH', '002352.SZ', '300357.SZ', '300009.SZ', '300702.SZ', '002595.SZ',
            '300036.SZ', '300037.SZ', '002643.SZ', '002916.SZ', '601222.SH']

    # 设置底仓
    # sd = StockData()
    # for stock in pool:
    #     df = sd.get_stock_kline(stock, '20200102 093000000', '20200102 093000000')
    #     data = data.append(df)
    # data = data[['HTSCSecurityID','ClosePx']].rename(columns={'HTSCSecurityID':'stock', 'ClosePx':'close'}).set_index('stock')
    # for stock in pool:
    #     brain.add_initial_position(stock, 1000, data.loc[stock,'close'])

    brain.set_fill_method(fill_price='THIS_OPEN')
    brain.add_feeds(
        datanames=pool,                            # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame='K_1MIN',                       # 回测频度
        instrument_type='STOCK',                   # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )

    ####################################################################
    brain.add_feed_benchmark(
        dataname='000300.SH',                      # 标的名称，需符合数据科学量化研究平台标的命名规范
        time_frame="K_1MIN",                       # 回测频度
        instrument_type='STOCK',                   # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )
    ####################################################################

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyExample)
    ####################################################################
    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告
    brain.generate_report(plot=False, plotname='StrategySignalRSI')
    # ####################################################################
    #
    # 获取Analyzers分析的结果
    # return: trade_summary 回测的整体评价， trade_records逐笔订单信息， daily_pnl为每天收益
    trade_summary, trade_records, daily_pnl = brain.get_analyzer_result()
    print(trade_summary.head())
    print(trade_records.head())
    print(daily_pnl.head())


if __name__ == '__main__':
    main()