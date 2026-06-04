# -*- coding: utf-8 -*-

from xbrain import XBrain
from tquant import IndexData
import math
import pandas as pd
from xbrain.strategy_base import StrategyBase
from datetime import datetime, timedelta
from tquant import StockData
from talib import MA
from xquant.factordata import FactorData
import xbrain as xb
from xbrain.indicators.xqindicator import XqIndicator


# 基本面选股策略


def calc_momentum(price, N):
    mom = price / price.shift(N) - 1
    return mom


def calc_vol_ratio(vol, N1, N2):
    return MA(vol.values, N1) / MA(vol.values, N2)


def get_qtr_date(cur_dt):
    # qtr_list = ['0331', '0630', '0930', '1231']
    cur_year = cur_dt[:4]
    cur_month_date = cur_dt[4:8]
    if '0331' <= cur_month_date < '0630':
        qtr_month_date = '0331'
        qtr_year = cur_year
    elif '0630' <= cur_month_date < '0930':
        qtr_month_date = '0630'
        qtr_year = cur_year
    elif '0930' <= cur_month_date < '1231':
        qtr_month_date = '0930'
        qtr_year = cur_year
    else:
        qtr_month_date = '1231'
        qtr_year = str(int(cur_year) - 1)
    return qtr_year + qtr_month_date


def calc_cashtostdebt_factor(dt, cashtostdebt, dataname):
    result = []
    for d in dt:
        dt_0 = xb.num2dt(d).strftime('%Y%m%d')
        index = (get_qtr_date(dt_0), dataname)
        val = cashtostdebt[index]['cashtostdebt']
        # val = cashtostdebt.loc[[index], :]['cashtostdebt'].values[0]
        result.append(val)
    return result


class MomentumFactor(XqIndicator):
    lines = ('momentum',)

    params = (
        ('N', 3),
    )

    def __init__(self):
        self._tafunc = calc_momentum
        self._lookback = self.params.N


class VolumeFactor(XqIndicator):
    lines = ('volume',)

    params = (
        ('N1', 3),
        ('N2', 20),
    )

    def __init__(self):
        self._tafunc = calc_vol_ratio
        self._lookback = max(self.params.N1, self.params.N2)


class CashFlowFactor(XqIndicator):
    lines = ('cash_flow',)

    params = (
        ('cashtostdebt', None),
        ('dataname', None),
    )

    def __init__(self):
        if self.params.cashtostdebt is None:
            fd = FactorData()
            dates = [y + i for y in ['2019', '2020'] for i in ['0331', '0630', '0930', '1231']]
            self.params.cashtostdebt = fd.get_factor_value(
                'Basic_factor', stock=[], mddate=dates, factor_names=['cashtostdebt']
            )
        if self.params.dataname is None:
            raise Exception('Please provide data name.')

        self._tafunc = calc_cashtostdebt_factor
        self._lookback = 0


def map_values_to_range_with_fixed_step(values, min_val, max_val, step, inverse=False):
    if inverse:
        values *= -1.0
    if values.min() == values.max():
        return pd.Series([0.5 * (min_val + max_val)] * len(values))
    scale = (max_val - min_val) / (values.max() - values.min())
    mapped = (values - values.min()) * scale + min_val
    mapped = (mapped + step * 1e-10) // step * step
    return mapped


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

        sd = StockData(data_source="finchina")

        cashtostdebt_df = pd.DataFrame()
        dates = [y + i for y in ['2019', '2020'] for i in
                 ['0331', '0630', '0930', '1231']]
        # 获取19，20年每个季度全市场可交易股票
        for date in dates:
            date_time = datetime.strptime(date, "%Y%m%d")
            week_day = date_time.weekday()
            stock_day = date
            if week_day == 5:
                stock_day = (date_time + timedelta(-1)).strftime('%Y%m%d')
            elif week_day == 6:
                stock_day = (date_time + timedelta(-2)).strftime('%Y%m%d')
            stock_df = sd.get_plate_info('MARKET', stock_day, 'ALLA')
            stocks = list(stock_df['stock'])
            if not stocks:
                continue
            c_df = sd.get_factor_financial_analysis(stocks, [date], factor_list='cashtostdebt', fill_na=True)
            cashtostdebt_df = cashtostdebt_df.append(c_df)

        # 将 pandas DataFrame 转换成 dict，加速后续取数据操作
        cashtostdebt_dict = cashtostdebt_df.to_dict(orient='index')

        for d in self.datas:
            # mem动量指标
            self.momentum_20[d.get_data_name()] = MomentumFactor(d.close, N=20)
            self.momentum_3[d.get_data_name()] = MomentumFactor(d.close, N=3)
            self.volume[d.get_data_name()] = VolumeFactor(d.close, N1=3, N2=20)
            # 现金流指标
            self.cf[d.get_data_name()] = CashFlowFactor(
                d.datetime, cashtostdebt=cashtostdebt_dict, dataname=d.get_data_name()
            )

    def next(self):
        datas = [d for d in self.datas if d.is_ready()]
        df = pd.DataFrame({'stock': [d.get_data_name() for d in datas]})
        df['mom_20'] = [self.momentum_20[d.get_data_name()].momentum[0] for d in datas]
        df['mom_3'] = [self.momentum_3[d.get_data_name()].momentum[0] for d in datas]
        df['vol'] = [self.volume[d.get_data_name()].volume[0] for d in datas]
        df['cf'] = [self.cf[d.get_data_name()].cash_flow[0] for d in datas]

        if df[['mom_20', 'mom_3', 'vol']].isnull().any().any():
            return
        df.fillna(0, inplace=True)
        df['mom_score'] = map_values_to_range_with_fixed_step(df['mom_20'], 0, 5, 0.2, True) + \
                          map_values_to_range_with_fixed_step(df['mom_3'], 0, 5, 0.2, False)
        df['volume_score'] = map_values_to_range_with_fixed_step(df['vol'], 0, 10, 0.2, False)
        df['cf_score'] = map_values_to_range_with_fixed_step(df['cf'], 0, 10, 0.2, False)
        df['total_score'] = df['mom_score'] + df['volume_score'] + df['cf_score']
        df = df.sort_values(by=['total_score'], ascending=[False])

        pos_stock = [d.get_data_name() for d in self.datas if self.get_position(d)]

        if not pos_stock or (pos_stock and len(self) - self.last_rebalance_day > self.params.rebalance_period):
            # 筛选前一百只股票
            to_rebalance = df.iloc[:self.params.K, :]
            to_closeout = [stock for stock in pos_stock if stock not in to_rebalance['stock'].values]
            self.log('To close: {}'.format(to_closeout))
            for stock in to_closeout:
                if self.get_position_by_name(stock).size > 0:
                    self.closeout(self.get_data_by_name(stock))

            # 均分当前现金
            amount_per_stock = self.get_value() * (1 - self.params.cash_reserve) / to_rebalance.shape[0]
            self.log('Amount per stock: {}'.format(amount_per_stock))
            for index, row in to_rebalance.iterrows():  # 买入/调整调仓标的的持仓
                stock = row['stock']
                d = self.get_data_by_name(stock)
                self.buy(data=d, value=amount_per_stock) # 买入目标仓位
                self.log('To rebalance to {} shares'.format(stock))
                # try:
                #     rebalance_shares = amount_per_stock / d.close[0]  # 获取当日收盘价，计算买入股数
                # except ZeroDivisionError:
                #     rebalance_shares = 0
                # rebalance_shares = math.floor(rebalance_shares // 100) * 100  # 股数化零为整百
                # self.log('To rebalance to {}: {} shares'.format(stock, rebalance_shares))
                # self.order_target_size(d, rebalance_shares)  # 下单买入到目标仓位

            self.last_rebalance_day = len(self)



def main():
    # 创建回测框架 XBrain 实例
    brain = XBrain(start_date="20200107 000000000", end_date="20201231 235959000", live=False)
    ####################################################################

    # 加载回测期内的标的数据到回测框架
    ind = IndexData()
    stock_list = ind.get_index_info('20200612', 'HS300', 0)['stock'].tolist()

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