# 计算一个因子一天的回测指标 入库（17张表）其中15张每个入库三条记录，剩下两张各入库一条记录
import ray
import itertools
from tquant.strategy.market_factor_backtest import MarketFactorBacktest, Month_return, top_tail_factors, data_to_mysql
from tquant import StockData, BasicData
from tquant.strategy.day_factor_backtest.backtest.utility import align_data_inner
sd = StockData()
bd = BasicData()
import pandas as pd
import numpy as np
import itertools

transaction_cost_list = [0, 0.0013, 0.0023]
stock_pool_list = ['alpha_universe', 'hs300', 'zz500', 'zz800', 'zz1000']
backtest_period_list = ['3m', '1y', '3y']


def backtest_factor_by_params_his(factor_df, start_date, end_date, factor_name):
    params_combine = list(itertools.product(transaction_cost_list, stock_pool_list, backtest_period_list))
    date_list = bd.get_trading_day(start_date, end_date)
    ray.init(num_cpus=8)
    tasks_stats = [
        backtest_factor_stats_by_param_his.remote(factor_df, date_list=date_list, factor_name=factor_name,
                                                  seg_benchmark=universe, benchmark=universe, universe=universe,
                                                  transaction_cost=transaction_cost, backtest_period=backtest_period)
        for
        transaction_cost, universe, backtest_period in params_combine]
    ray.get(tasks_stats)

    # 计算收益指标并入库
    tasks_monthret = [
        backtest_factor_monthret_by_param_his.remote(date_list=date_list,
                                                     transaction_cost=transaction_cost,
                                                     stock_pool=stock_pool, factor_name=factor_name) for
        transaction_cost, stock_pool, backtest_period in params_combine]

    ray.get(tasks_monthret)
    # 计算top20 tail20
    ray.shutdown()
    backtest_factor_top_tail_by_param_his(date_list=date_list, factor_df=factor_df, factor_name=factor_name)


def backtest_factor_top_tail_by_param_his(date_list, factor_df, factor_name):
    for date in date_list:
        factor_data_copy = factor_df[factor_df.index.get_level_values(0).isin([date])]
        top_tail_factors(mddate=date, factor_data=factor_data_copy, factor_name=factor_name)
    return


@ray.remote
def backtest_factor_stats_by_param_his(factor_df, date_list, factor_name, seg_benchmark, benchmark, universe,
                                       transaction_cost, backtest_period):
    factor_df = factor_df[~factor_df.index.get_level_values(0).isin([date_list[-1]])]
    stock_list = sd.get_plate_info('MARKET', date_list[-1], 'ALLA_HIS')['stock'].tolist()
    benchmark_price_ps, stock_close_pd, stock_filter = get_price_use_data(stock_list=stock_list,
                                                                          date_list=date_list,
                                                                          seg_benchmark=seg_benchmark,
                                                                          benchmark=benchmark,
                                                                          universe=universe)
    # 提取因子值，因子值是mddate和trd_days_1两天数据。计算分层收益考虑成本时用到两天因子值计算换手率
    factor_df.index.names = ['mddate', 'stock']
    factor_df.reset_index(inplace=True)
    factor_df.loc[:, 'mddate'] = factor_df.loc[:, 'mddate'].apply(pd.Timestamp)
    factor_df.set_index(['mddate', 'stock'], inplace=True)
    factor_df = factor_df[factor_name].unstack()
    factor_df[stock_filter == False] = np.nan  # 获取股票池标的，过滤停牌和涨跌停
    factor_df = factor_df.dropna(how='all', axis=1)
    data_dict = {"stock_close_pd": stock_close_pd, "benchmark_price_ps": benchmark_price_ps, "factor_df":factor_df}
    data_dict = align_data_inner(data_dict)
    stock_close_pd = data_dict["stock_close_pd"]
    benchmark_price_ps = data_dict["benchmark_price_ps"]
    factor_df = data_dict["factor_df"]

    for i in range(2, len(date_list)):
        entrydate = date_list[i]
        middate = date_list[i - 1]
        mddate = date_list[i - 2]
        factor_df_copy = factor_df[factor_df.index.get_level_values(0).isin([mddate, middate])]
        benchmark_price_ps_copy = benchmark_price_ps[
            benchmark_price_ps.index.get_level_values(0).isin([mddate, middate, entrydate])]
        stock_close_pd_copy = stock_close_pd[
            stock_close_pd.index.get_level_values(0).isin([mddate, middate, entrydate])]
        instance = MarketFactorBacktest(entrydate=entrydate, mddate=mddate, middate=middate, backtest_period=backtest_period,
                                        factor_data=factor_df_copy,
                                        universe=universe, factor_name=factor_name,
                                        filter=True, transaction_cost=transaction_cost,
                                        stock_close_pd=stock_close_pd_copy,
                                        benchmark_price_ps=benchmark_price_ps_copy)
        instance.calc_ic_daily()
        instance.seg_test()
        instance.seg_performance_measure()
        instance.data_to_mysql()
    return


@ray.remote
def backtest_factor_monthret_by_param_his(date_list, transaction_cost, stock_pool, factor_name):
    for i in range(2, len(date_list)):
        mddate = date_list[i - 2]
        instance = Month_return(mddate=mddate, universe=stock_pool,
                                transaction_cost=transaction_cost, factor_name=factor_name)
        instance.month_ret()
        instance.data_to_mysql()
    return


def get_price_use_data(stock_list, date_list, seg_benchmark, benchmark, universe):
    data_dict = {}
    universe_set = {'sz50': 'index_50', 'hs300': 'index_300', 'zz500': 'index_500', 'zz800': 'index_800',
                    'zz1000': 'index_1000', 'risk_universe': 'risk_universe',
                    'alpha_universe': 'alpha_universe'}
    index_lookup = {'zz500': '000905.SH', 'hs300': '000300.SH', 'zz800': '000906.SH', 'zz1000': '000852.SH'}
    if seg_benchmark in ['hs300', 'zz500', 'sh50', 'zz800', 'zz1000', 'sz50']:
        if seg_benchmark == 'sz50':
            seg_benchmark = 'sh50'
        eval_factors = [universe_set[universe], 'filter_stpt', 'CITIC_I'] + [
            'index_weight_' + seg_benchmark]
    else:
        eval_factors = [universe_set[universe], 'filter_stpt', 'CITIC_I']
    evaluation_df = sd.get_factor_evaluation(stock_list, date_list, eval_factors)
    if universe in universe_set.keys():

        h5_filter = evaluation_df.loc[:, [universe_set[universe], 'filter_stpt']]
    else:
        h5_filter = evaluation_df.loc[:, ['filter_stpt']]
    for f in h5_filter.columns:
        if f in ['risk_universe', 'alpha_universe', 'filter_stpt', 'filter_suspend', 'listing_1yr',
                 'over_half_for_half_year', 'index_50', 'index_300', 'index_500', 'index_800', 'index_1000']:
            h5_filter[f].fillna(value=0, inplace=True)
            h5_filter[f] = h5_filter[f].astype(int).astype(bool)
    h5_filter.reset_index(inplace=True)
    h5_filter.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
    h5_filter.set_index(["dt", "Ticker"], inplace=True)
    h5_filter = h5_filter.fillna(value=False)
    # 对self.universe的股票进行stpt过滤
    if universe in universe_set.keys():
        compound_filter = h5_filter[universe_set[universe]] & h5_filter['filter_stpt']
    else:
        compound_filter = h5_filter['filter_stpt']

    stock_filter = compound_filter.unstack().fillna(value=False)
    stock_filter.index = pd.DatetimeIndex(stock_filter.index)
    data_dict['stock_filter_' + str(universe)] = stock_filter

    md_dict = {}
    factors = ['close', 'adjfactor']
    factors_df = sd.get_factor_price_daily(stock_list, date_list, factors, sort_option=False,
                                           fill_na=False)
    for fac in factors:
        sub_df = factors_df.loc[:, fac].unstack()
        sub_df.replace(0.0, np.nan, inplace=True)
        sub_df.fillna(method='ffill', inplace=True)
        sub_df.index.name = 'dt'
        sub_df.index = pd.DatetimeIndex(sub_df.index)
        sub_df = sub_df.reindex(index=stock_filter.index, columns=stock_filter.columns)
        md_dict[fac] = sub_df
    md_dict['close_adj'] = md_dict['close'] * md_dict['adjfactor']
    md_dict['hpr_1_close_shift'] = md_dict['close_adj'].shift(-2) / md_dict['close_adj'].shift(
        -1) - 1

    if benchmark == 'alpha_universe':
        # 计算基准
        stk_ret = md_dict['close_adj'] / md_dict['close_adj'].shift(1) - 1  # T-1日收益率作为T日行情
        stk_ret.replace([np.inf, -np.inf], 0.0, inplace=True)
        # 市场每日平均收益
        universe_ret = stk_ret[
            data_dict['stock_filter_' + universe].reindex(index=stk_ret.index,
                                                          columns=stk_ret.columns).fillna(
                value=False)].mean(axis=1)
        universe_ret.iloc[0] = 0.0
        benchmark_price_ps = (universe_ret + 1).cumprod()  # 市场每日累计收益
    elif benchmark in index_lookup:
        benchmark_price_ps = sd.get_factor_price_daily(index_lookup[benchmark], date_list, 'close')
        benchmark_price_ps.reset_index(inplace=True)
        benchmark_price_ps.rename(columns={'mddate': 'dt', 'stock': 'Ticker'}, inplace=True)
        benchmark_price_ps['dt'] = benchmark_price_ps['dt'].apply(pd.Timestamp)
        benchmark_price_ps.set_index(['dt', 'Ticker'], inplace=True)
        benchmark_price_ps = benchmark_price_ps.unstack()['close'][index_lookup[benchmark]]

        # 因子值、收盘价、基准
    stock_close_pd = md_dict['close_adj'].shift(-1)
    benchmark_price_ps = benchmark_price_ps.shift(-1)
    return benchmark_price_ps, stock_close_pd, stock_filter


if __name__ == "__main__":
    # 使用场景1： 对单个平台因子进行补数
    from tquant import StockData

    sd = StockData()
    start_date = '20190101'
    end_date = '20200101'
    factor_name = 'close'
    stock_list = sd.get_plate_info("MARKET", end_date, "ALLA_HIS")['stock'].to_list()
    factor_df = \
        sd.get_factor_price_daily(trading_codes=stock_list, date_list=(start_date, end_date),
                                  factor_list=[factor_name])[
            factor_name].unstack()  # 截面因子的形式
    backtest_factor_by_params_his(factor_df, start_date, end_date)

    # 使用场景2： 对单个平台因子进行每日更新
    from tquant import StockData

    sd = StockData()
    mddate = '20191101'
    stock_list = sd.get_plate_info("MARKET", end_date, "ALLA_HIS")['stock'].to_list()
    factor_df = \
        sd.get_factor_price_daily(trading_codes=stock_list, date_list=[mddate],
                                  factor_list=[factor_name])  # multiindex的形式
    backtest_factor_by_params(factor_df, mddate)

    # 使用场景3: 对单个系统因子进行补数
    # 真正使用是在web_entry/web_calculation_release.py

    # 使用场景4：对单个系统因子进行每日更新
    # 使用脚本：web_entry/web_backtest_tiny_release.py
