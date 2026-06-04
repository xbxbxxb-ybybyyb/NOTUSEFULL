# -*- coding: utf-8 -*-
"""
Created on Thu Oct 18 14:56:56 2018
@author: 013150
"""
from version_control import version_number
import pandas as pd
import numpy as np

if version_number == 0:
    from xquant.backtest.Strategy import Strategy
    from xquant.backtest.data_util import fill_na
    from xquant.backtest.date_util import get_warehouse_transfer_day
    from xquant.factor import FactorData
else:
    from xquant.strategy.backtest.Strategy import Strategy
    from xquant.strategy.backtest.data_util import fill_na
    from xquant.strategy.backtest.date_util import get_warehouse_transfer_day
    from xquant.thirdpartydata.factor import FactorData

np.random.seed(3000)



def get_factor(tradingDays, universe, position_bases, flag="xquant"):
    """
    获取因子数据
    """
    if flag == "xquant":
        fa = FactorData(timeout=10)
        close_data = fa.getSimpleFactorData(["open"], tradingDays, universe)
        close_data = close_data.fillna(method="ffill")
        close_data = close_data.fillna(method="backfill")  # 以下一个有效值填充nan值
        close_data.index = [int(t) for t in close_data.index]
        close_data = fill_na(close_data, position_bases, tradingDays[0])
        return close_data.reindex(columns=universe)
    elif flag == "local":
        if position_bases:
            close_data = pd.read_csv("close_data.csv", index_col=0)
        else:
            close_data = pd.read_csv("close_data.csv", index_col=0)
        close_data = close_data.fillna(method="ffill")
        close_data = close_data.fillna(method="backfill")  # 以下一个有效值填充nan值
        close_data.index = [int(t) for t in close_data.index]
        close_data = fill_na(close_data, position_bases, tradingDays[0])
        return close_data.loc[:, universe], close_data.columns.tolist()


class MyStrategy(Strategy):
    def __init__(self):
        # 父类初始化
        super().__init__()
        # 回测开始日期
        self.start = "20180302"
        # 回测结束日期
        self.end = "20180712"
        # 日线行情或分钟线行情
        self.freq = "d"
        # 调仓间隔的事件
        self.refresh_rate = 3

        # 证券池
        self.universe = ['000001.SZ', '000002.SZ', '000004.SZ']
        # 基准
        self.benchmark = ["000300.SH"]
        # 账户名称
        self.account_name = 'act3'
        # 资金
        self.capital_base = 200000
        # 初始持仓信息
        # self.position_base = {'000002.SZ': 1000}
        self.position_base = {}
        # 初始持仓成本
        # self.cost_base = {'000002.SZ': 3}
        self.cost_base = {}
        # 账户佣金
        self.acount_commission = self.Commission(buycost=0.001, sellcost=0.002, unit='perValue')
        # 账户滑点
        self.account_slippage = self.Slippage(value=0.0, unit='perValue')

    def initialize(self, context):
        '''
        策略执行前初始化，只调用一次
        '''
        context.history.current_price_his = get_factor(context.tradingDays,
                                                       self.universe + self.benchmark,
                                                       self.position_base, flag="xquant")
        context.history.current_price_his = context.history.current_price_his.loc[context.tradingDays]
        # 获取回测区间股票和指数的收盘价
        context.get_account(self.account_name).print_accounts(
            context.history.current_price_his.loc[int(context.current_date)])

    def handle_data(self, context, flag="xquant"):
        '''
        执行策略，每个换仓日调用一次
        '''
        # 获取行情数据
        if flag == "xquant":
            fa = FactorData(timeout=60 * 3)
            self.universe = list(fa.stockFilter(context.current_date, 1, self.universe)[str(context.current_date)])
        elif flag == "local":
            if self.position_base:
                self.universe = ['000001.SZ']
            else:
                pass
        re = context.history.current_price_his.loc[context.previous_date:context.current_date].reindex(
            columns=self.universe)
        # 选股
        stock_code = self.universe[np.random.randint(len(self.universe))]
        stock_positions = context.get_account(self.account_name).get_positions()
        stock_amount = 0
        if stock_positions.get(stock_code) != None:
            s_pos = stock_positions[stock_code]
            stock_amount = s_pos.get_available_amount()

        # 下单
        close_price = re.loc[context.current_date, stock_code]

        if stock_amount > 0:
            direction = np.random.choice([-1, 1], 1)[0]  # 买卖方向
            if direction < 0:
                order_amount = -int(min(np.random.rand(), 0.5) * stock_amount / 100) * 100  # 下单股数,随机买卖
            else:
                order_amount = int(stock_amount / 100) * 100
            context.get_account(self.account_name). \
                order(stock_code, order_amount, close_price, context)
        else:
            context.get_account(self.account_name). \
                order(stock_code, 1000, close_price, context)

    def print_ratio(self, history, start_date, end_date):
        pass

    def post_trading_day(self, context):
        '''
        策略盘后处理逻辑，如当日交易总结，预计算因子等
        '''
        target_term = get_warehouse_transfer_day(self.start, self.end, self.refresh_rate)
        start_date = target_term[0]
        end_date = target_term[-1]
        # 计算评价指标
        self.print_ratio(context.history, start_date, end_date)
