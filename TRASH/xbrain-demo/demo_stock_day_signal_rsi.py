from xbrain import XBrain
from xbrain.strategy_base import StrategyBase
import xbrain as xb
import numpy as np, pandas as pd
import talib, time
from tquant.basic_data import BasicData
from tquant.stock_data import StockData


# 演示依据RSI相对强弱指标，在自定义股票池中进行选股买卖操作
# 依据RSI指标按日调仓，RSI>85超买逃顶，RSI<25超卖抄底，策略年化收益：190%


class StrategyExample(StrategyBase):
    params = (
        ('stock_num', 3),  # 最大持仓标的数量
    )

    def __init__(self):
        self.bd = BasicData()
        self.sd = StockData()
        self.buy_list = []
        # 获取回测区间
        start_date, end_date = self.get_backtest_period()
        start_date, end_date = start_date.strftime('%Y%m%d'), end_date.strftime('%Y%m%d')
        self.trd_day_separate = self.bd.get_trading_day(start_date, 62)[-1]
        # 获取回测标的池
        self.pool = self.get_backtest_securities_dict()['STOCK']
        # 通过Tquant SDK获取涨跌停数据
        self.maxupordown = self.sd.get_factor_price_daily(self.pool, (start_date, end_date), ['maxupordown'])

    def start(self):
        self.log("Current index: {}. Let's ROCK!".format(len(self)))

    def prenext(self):
        self.log("Current index: {}. Preparing for calculations.".format(len(self)))

    def next(self):
        # ----计算股票池中每只股票的买卖信号，加入买卖股票列表中-------------------
        self.get_RSI_signal()
        # ----执行买卖逻辑-------------------
        self.orderStock()

    def get_RSI_signal(self):
        rsi_code = []
        buys = []
        sells = []
        buy_flag = 0
        dt = self.data.datetime.datetime(0).strftime('%Y%m%d')
        trd_days = self.bd.get_trading_day(dt, -63)[:-1]

        #删选当天可交易的股票池
        pool = self.sd.stock_filter(self.pool, trd_days[-1], "SUSPEND")["stock"].tolist()
        # 计算RSI指标，若框架加载的数据指标周期不满足RSI计算则通过量化平台获取close值计算，若满足则使用框架数据进行计算
        for stockcode in pool:
            if dt < self.trd_day_separate:
                prices = self.sd.get_factor_price_daily(stockcode, trd_days, ['close_badj']).rename(
                    columns={'close_badj': 'close'})
            else:
                prices = self.get_past_feed_price_df(datanames=[stockcode], lagged_bar=62)[:-1]
            # 获取历史dataframe数据计算RSI指标，注意：RSI函数使用的price必须是narray
            rsi = talib.RSI(prices['close'].values, timeperiod=6)[-1]
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
        dt = self.data.datetime.datetime(0).strftime('%Y%m%d')
        buys = self.buy_list
        sells = self.sell_list

        # 下单后立即成交，通过 get_open_position 获取的当前持仓也立即变化
        # 卖出
        for stock, position in self.get_open_position().items():
            if stock in sells:
                data = self.get_data_by_name(stock)
                if self.maxupordown.loc[dt].loc[stock]['maxupordown'] == 1:  # 涨停不卖
                    continue
                elif position.closeable_amount() > 0:
                    self.closeout(data)
                    self.log('sell all:', stock)
                if stock not in self.pool:
                    self.closeout(data)
                    self.log('sell all:', stock)

        # 买入
        for stock in buys:
            if stock not in self.get_open_position().keys():
                available_cash = self.get_cash()
                if (self.p.stock_num - len(self.get_open_position().keys())) > 0:
                    if self.maxupordown.loc[dt].loc[stock]['maxupordown'] == -1:  # 跌停不买
                        continue
                    else:
                        data = self.get_data_by_name(stock)
                        buy_value = available_cash / (self.p.stock_num - len(self.get_open_position().keys()))
                        print('可用资金 {}， 最大持仓数量 {}， 当前持仓数量 {}'
                              .format(available_cash, self.p.stock_num, len(self.get_open_position().keys())))
                        self.buy(data, value=buy_value)
                        self.log('buy:' + stock + ' ' + str(buy_value))


def main():
    start_date = '20200101'
    end_date = '20200914'
    brain = XBrain(
        stocklike=True,
        start_date=start_date + ' 000000000',
        end_date=end_date + ' 235959000',
        init_amount=300000,
        commission=0.0003,
        live=False
    )
    ####################################################################
    stock_pool = ['300058.SZ', '000725.SZ', '300416.SZ', '603899.SH', '002594.SZ', '300529.SZ',
                  '601012.SH', '000661.SZ', '600763.SH', '300601.SZ', '300347.SZ', '300014.SZ',
                  '300661.SZ', '603589.SH', '603708.SH', '002714.SZ', '601888.SH', '000895.SZ',
                  '002456.SZ', '002351.SZ', '002959.SZ', '002901.SZ', '600660.SH', '300768.SZ',
                  '002821.SZ', '600276.SH', '600196.SH', '002371.SZ', '300595.SZ', '300750.SZ',
                  '600309.SH', '002352.SZ', '300357.SZ', '300009.SZ', '300702.SZ', '002595.SZ',
                  '300036.SZ', '300037.SZ', '002643.SZ', '002916.SZ', '601222.SH']

    brain.set_fill_method(fill_price='THIS_OPEN')

    # 加载回测期内的标的数据到回测框架
    # method=True，后复权仅日频股票数据有复权价格
    brain.add_feeds(datanames=stock_pool, time_frame='K_DAY', instrument_type='STOCK', method=True)

    brain.add_feed_benchmark(
        dataname='000300.SH',  # 标的名称，需符合数据科学量化研究平台标的命名规范，此处使用 IF 主力合约
        time_frame="K_DAY",  # 回测频度
        instrument_type='STOCK',  # 标的品种，枚举变量，可选有 STOCK, FUTURE
    )

    # 加载策略到回测框架，此处策略类是用户需要重点关注，并实现的
    brain.add_strategy(StrategyExample)
    ####################################################################

    # 运行回测
    brain.backtest_run()
    ####################################################################

    # 生成回测报告文件
    brain.generate_report(plot=True, plotname='StrategySignalRSI')
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

    # 回测结果：
    # ================================================================================
    # Final Portfolio Value    : 617878.26
    # StrategyProfitRate       : 1.0595941900259427
    # AnnualProfitRate         : 1.9001140345904655
    # BenchmarkProfitRate      : 0.128526372932239
    # BenchmarkAnnualProfitRate: 0.1984337362794042
    # SharpeRatio              : 3.390216794555208
    # MaxDrawDown              : 0.18591635646185428
    # MaxDrawDownFrom          : 2020-08-03
    # MaxDrawDownTo            : 2020-09-10
    # WinLostRatio             : 0
    # WinRate                  : 1.0
    # ================================================================================