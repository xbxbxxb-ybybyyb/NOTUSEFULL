"""
Update on 2019/9/12
@ author: 015616
功能：日内因子的检测 （只能实现日内！！！）
      检测按twap价格
      计算ICIR的时候考虑了股票的涨跌停和停牌情况
      计算top组收益的时候也考虑了买卖情况
"""

import matplotlib

matplotlib.use('Agg')  # Generate images without having a window appear; must be imported before pylab is imported
from ..DataAPI import DataToolkit as Dtk
import pandas as pd
from matplotlib.pylab import *
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt
import datetime as dt
import numpy as np
import os
import json
from fix_factor_backtest.backtest.test_data_loader import get_top_group_nav_data
from fix_factor_backtest.backtest.Utils.HelperFunctions import fast_long_short_nav, \
    nav_series_annually_stat, \
    calc_group_rank, compress_intraday_index_to_daily, get_intraday_moment_df, intraday_equally_wt_fast_nav, \
    factor_distribution_calc2, factor_neutralizer, outlier_filter, z_score_standardizer, fillna_with_industry_median_new\
    , factor_neutralizer_new
from fix_factor_backtest.backtest.Utils.PlotFunctions import plot_group_bar2, plot_series, plot_one_series, \
    plot_boxplot
import uuid


class SingleFactorTest:
    def __init__(self, factor_name, factor_value, start_date, end_date, check_date_list, report_address,
                 holding_period=1, group_num=10, intraday_price_type='twap_30_5', universe='alpha_universe',
                 neutral_factor_set=None, outlier_filtering_method="MAD", stock_cost_rate=0.0004):
        if int(end_date) > 20200630:
            raise Exception('end_date should not exceed 20190630')
        # 初始设置
        if neutral_factor_set is None:
            neutral_factor_set = {'size', 'industry3'}
        query_trade_date_list = Dtk.get_trading_day(start_date, end_date)
        self.factor_name = factor_name
        self.start_date_orignal = query_trade_date_list[0]
        self.start_date = query_trade_date_list[0]
        self.end_date = query_trade_date_list[-1]
        self.check_date_list = check_date_list
        self.holding_period = holding_period
        self.intraday_price_type = intraday_price_type
        self.intraday_price_moment = factor_name[3:7]
        self.universe = universe
        self.group_num = group_num
        self.neutral_factor_set = neutral_factor_set
        self.stock_cost_rate = stock_cost_rate
        self.outlier_filter_method = outlier_filtering_method
        self.benchmark_list = ["000300.SH", "000905.SH"]
        self.report_address = report_address
        if not os.path.exists(self.report_address):
            os.makedirs(self.report_address)

        # 中间变量和最终结果
        self.complete_stock_list = Dtk.get_complete_stock_list()
        self.original_factor_data_df = factor_value.reindex(self.complete_stock_list, axis=1)
        self.factor_data_df = None
        self.neutralized_factor_data_df = None
        # 选取昨日alpha_universe
        valid_start_date = Dtk.get_n_days_off(self.start_date, -2)[0]
        daily_stock_universe_df = Dtk.get_panel_daily_info(self.complete_stock_list, valid_start_date,
                                                           self.end_date, info_type=self.universe,
                                                           output_index_type='timestamp')
        self.stock_universe_df = daily_stock_universe_df.shift(1).iloc[1:].copy()

        volume_df = Dtk.get_panel_daily_pv_df(self.complete_stock_list, self.start_date, self.end_date, "volume")
        self.suspend_filter = Dtk.convert_df_index_type(volume_df, 'date_int', 'timestamp')

        self.label_data = None
        self.factor_raw_test_report = {}
        self.factor_test_report = {}
        self.factor_neutralized_test_report = {}
        self.group_nav_list = []  # 快速分组测试（不对冲）每组的回测净值
        self.group_total_annualized_return_dict = {}  # 快速分组测试（不对冲）每组的年化收益
        self.daily_return_median = pd.DataFrame()
        self.daily_return_mean = pd.DataFrame()
        # Top组相对基准的超额收益净值(nav)序列，有4个key: "000300.SH" , "000905.SH", "MktMean"和"MktMedian"
        self.top_group_hedge_nav_dict = {}
        self.top_group_excess_return_each_year = {}  # Top组相对基准每年的超额收益
        self.top_group_excess_return_each_month = {}  # Top组相对基准每月的超额收益
        self.top_group_monthly_winning_pct_stat = {}  # Top组相对基准超额收益月胜率统计，4个key
        self.top_group_daily_winning_pct_stat = {}  # Top组相对基准超额收益日胜率统计，4个key
        self.long_short_nav = None  # Long-short净值
        self.long_short_return_each_year = {}  # 每年Long-short的收益率
        self.report_timestamp = dt.datetime.now()
        self.top_group_avg_turnover_rate = None  # top组日均换手率
        self.factor_stat_output = {}  # 最终结果放在里面
        self.each_year_group_return_dict = {}  # 分组测试每年的收益率
        self.group_return_rank_coef = {}  # 分组测试收益率与组号的相关性
        self.corr_information = {}  # 储存与现在因子的相关性信息
        # self.size_analysis_result = None  # 因子市值分析结果
        self.check_date_if_qualified = {}
        self.daily_top_group_stock_list = {}  # 存储每日top组股票池
        self.long_short_return_each_year_daily = {}  # 每年Long-short的日均收益率
        self.topgroup_ret_exceed_mean = {}  # top组超额收益率，相对市场均值
        self.conditions = {}
        self.hedged_df = get_top_group_nav_data(self.factor_name)

    def load_label(self):
        valid_end_date = Dtk.get_n_days_off(self.end_date, self.holding_period + 1)[-1]
        #SJL twap暂时不支持，用vwap代替
        data_df_deal_price = Dtk.get_panel_daily_pv_df(self.complete_stock_list, self.start_date, valid_end_date,
                                                       pv_type='vwap', adj_type='FORWARD')
        daily_return_df = data_df_deal_price / data_df_deal_price.shift(self.holding_period) - 1
        stock_universe_df = Dtk.convert_df_index_type(self.stock_universe_df, 'timestamp', 'date_int')
        daily_return_df_filtered = daily_return_df.mul(stock_universe_df).div(stock_universe_df)
        self.daily_return_median = daily_return_df_filtered.median(axis=1)
        self.daily_return_mean = daily_return_df_filtered.mean(axis=1)

        # 先获取日内频的twap价格，再从中抽取时刻等于self.intraday_price_moment的价格，再将index转化为日频的
        intraday_buy_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, self.start_date,
                                                             valid_end_date,
                                                             pv_type='interval_buy_' + self.intraday_price_type,
                                                             adj_type='FORWARD')
        intraday_buy_price_df = get_intraday_moment_df(intraday_buy_price_df,
                                                       int(self.intraday_price_moment) * 100)
        intraday_buy_price_df_with_daily_index = compress_intraday_index_to_daily(intraday_buy_price_df, False)
        intraday_sell_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, self.start_date,
                                                              valid_end_date,
                                                              pv_type='interval_' + self.intraday_price_type,
                                                              adj_type='FORWARD')
        intraday_sell_price_df = get_intraday_moment_df(intraday_sell_price_df, int(self.intraday_price_moment) * 100)
        intraday_sell_price_df_with_daily_index = compress_intraday_index_to_daily(intraday_sell_price_df, False)

        return_rate_df = intraday_sell_price_df_with_daily_index.shift(
            -self.holding_period) / intraday_buy_price_df_with_daily_index - 1
        # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
        intraday_return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        self.label_data = intraday_return_rate_df * self.stock_universe_df / self.stock_universe_df

    @staticmethod
    def ic_stat_calc(ic_array, ic_name):
        ic_array = ic_array.dropna()
        ic_mean = np.mean(ic_array)
        ic_std = np.std(ic_array)
        icir = ic_mean / ic_std * np.sqrt(244)
        abs_ic = np.abs(ic_array)
        ic_greater_than_0p02_pct = abs_ic[abs_ic > 0.02].__len__() / abs_ic.__len__()

        def autocorr(x, t=1):
            return np.corrcoef(x[0:len(x) - t], x[t:len(x)])[0, 1]

        ic_auto_corr_1 = autocorr(ic_array.values, 1)
        ic_auto_corr_2 = autocorr(ic_array.values, 2)
        ic_auto_corr_3 = autocorr(ic_array.values, 3)

        ic_df = ic_array.to_frame()
        cumsum_ic_df = ic_df.cumsum()
        cumsum_ic_df = Dtk.convert_df_index_type(cumsum_ic_df, 'timestamp', 'date_int')

        index_date = list(cumsum_ic_df.index)
        date_year_list = [i // 10000 for i in index_date]
        year_list = list(set(date_year_list))
        year_list.sort()
        year_begin_idx = {}  # 记录每年首日在index_date中的位置索引
        year_idx = 0
        year_begin_idx.update({year_list[year_idx]: 0})
        year_end_idx = {}  # 记录每年末日在index_date中的位置索引
        for j, i_date in enumerate(date_year_list):
            if date_year_list[j] > year_list[year_idx]:
                year_end_idx.update({year_list[year_idx]: j - 1})
                year_idx += 1
                year_begin_idx.update({year_list[year_idx]: j})
            if j == date_year_list.__len__() - 1:
                year_end_idx.update({year_list[year_idx]: j})
        year_dates_count = {}  # 记录回测期间每年的交易日天数
        for i_year in year_begin_idx.keys():
            year_dates_count.update({i_year: year_end_idx[i_year] - year_begin_idx[i_year] + 1})
        ic_each_year = {}
        if year_dates_count[year_list[0]] < 30:  # 如果第1年的交易日小于30天，那么第1年的IC就没有计算的必要
            for j, i_year in enumerate(year_begin_idx.keys()):
                if j > 0:
                    ic_each_year.update({"IC_mean" + str(i_year): ((cumsum_ic_df.iloc[year_end_idx[i_year]] -
                                                                    cumsum_ic_df.iloc[year_end_idx[i_year - 1]]) /
                                                                   year_dates_count[i_year]).values[0]})
        else:
            for j, i_year in enumerate(year_begin_idx.keys()):
                if j == 0:
                    ic_each_year.update({"IC_mean" + str(i_year): ((cumsum_ic_df.iloc[year_end_idx[i_year]] -
                                                                    cumsum_ic_df.iloc[year_begin_idx[i_year]]) /
                                                                   year_dates_count[i_year]).values[0]})
                else:
                    ic_each_year.update({"IC_mean" + str(i_year): ((cumsum_ic_df.iloc[year_end_idx[i_year]] -
                                                                    cumsum_ic_df.iloc[year_end_idx[i_year - 1]]) /
                                                                   year_dates_count[i_year]).values[0]})

        ic_stat_value_list = [ic_mean, ic_std, icir, ic_greater_than_0p02_pct, ic_auto_corr_1, ic_auto_corr_2,
                              ic_auto_corr_3]
        for ic_mean_key in ic_each_year.keys():
            ic_stat_value_list.append(ic_each_year[ic_mean_key])
        ic_stat_df_index_list = ['IC_mean', 'IC_std', 'ICIR', '|IC|>0.02_pct', 'IC_AutoCorr_1', 'IC_AutoCorr_2',
                                 'IC_AutoCorr_3']
        for ic_mean_key in ic_each_year.keys():
            ic_stat_df_index_list.append(ic_mean_key)
        ic_stat_df = pd.DataFrame(ic_stat_value_list, index=ic_stat_df_index_list, columns=[ic_name])
        return ic_stat_df

    def corr_old_factors(self, start_date, end_date):
        # 计算与已入库所有因子的相关性
        if self.hedged_df is None:
            return pd.Series(np.array(0))
        corr_series = self.hedged_df.loc[start_date:end_date].corrwith(
            self.topgroup_ret_exceed_mean['exceed_mean'].loc[start_date:end_date])
        corr_series_abs = corr_series.abs()
        return corr_series_abs

    def __other_performance_stat(self):
        result = list()
        result.append([' ', 'Stat'])
        result.append(['Top Group Average Turnover Rate', round(self.top_group_avg_turnover_rate, 4)])
        for i_key in self.group_return_rank_coef.keys():
            result.append(["GroupRank_" + str(i_key), round(self.group_return_rank_coef[i_key], 4)])
        for i_key in self.long_short_return_each_year.keys():
            result.append([i_key, round(self.long_short_return_each_year[i_key], 4)])
        for i_key in self.top_group_excess_return_each_year.keys():
            result.append([i_key, round(self.top_group_excess_return_each_year[i_key], 4)])
        for i_key in self.top_group_monthly_winning_pct_stat.keys():
            result.append(["MonthlyWinningPct_" + str(i_key),
                           round(self.top_group_monthly_winning_pct_stat[i_key], 4)])

        return result

    def func_check_qualified(self, check_date):
        # 检查因子在check_date往前回溯2年，是否满足入库标准
        check_date_year, check_date_monthday = divmod(check_date, 10000)
        if check_date_monthday == 1231:
            test_start_day = (check_date_year - 1) * 10000 + 101
        elif check_date_monthday == 630:
            test_start_day = (check_date_year - 2) * 10000 + 701
        else:
            raise Exception('check date is not half-year end or year-end.')
        test_date_list = Dtk.get_trading_day(test_start_day, check_date)
        test_start_day = test_date_list[0]
        test_mid_day = test_date_list[int(test_date_list.__len__() / 2)]
        test_end_day = Dtk.get_n_days_off(test_date_list[-1], -3)[0]
        test_start_day_timestamp = Dtk.convert_date_or_time_int_to_datetime(test_start_day).timestamp()
        test_mid_day_timestamp = Dtk.convert_date_or_time_int_to_datetime(test_mid_day).timestamp()
        test_end_day_timestamp = Dtk.convert_date_or_time_int_to_datetime(test_end_day).timestamp()

        # 判断因子是否满足入库标准
        abs_icir_threshold = 1.5

        mkt_median_return_threshold = 0.1
        long_short_return_threshold = 0
        # avg_turnover_threshold = 0.9
        return_exceed_mean_threshold = 0
        max_correlation_threshold = 0.65
        similarity_threshold = 0.4
        universe_coverage_mean_threshold = 0.8

        def func_same_sign(*args):
            first_value = args[0]
            for value in args:
                if value * first_value < 0:
                    return False
            return True

        ic_series = self.factor_neutralized_test_report['IC_series'].loc[
                    test_start_day_timestamp: test_end_day_timestamp]
        ic_series = ic_series.dropna()
        ic_1st_year = ic_series.loc[0: test_mid_day_timestamp].mean()
        ic_2nd_year = ic_series.loc[test_mid_day_timestamp + 1:].mean()
        # 第一、第二年的因子横截面IC同向
        condition1 = func_same_sign(ic_1st_year, ic_2nd_year)
        # if not condition1:
        #     print(check_date, 'IC different sign', ic_1st_year, ic_2nd_year)

        group_return_list_1st_year = []
        group_return_list_2nd_year = []
        for j, i_group in enumerate(self.group_nav_list):
            group_return_list_1st_year.append(
                self.group_nav_list[j].loc[test_mid_day] - self.group_nav_list[j].loc[test_start_day])
            group_return_list_2nd_year.append(
                self.group_nav_list[j].loc[test_end_day] - self.group_nav_list[j].loc[test_mid_day])
        group_return_coef1 = calc_group_rank(group_return_list_1st_year)
        group_return_coef2 = calc_group_rank(group_return_list_2nd_year)
        # 第一、第二年的收益序列E与原始排序F的秩相关系数同向
        condition2 = func_same_sign(group_return_coef1, group_return_coef2)
        # if not condition2:
        #     print(check_date, 'Group return different sign', group_return_coef1, group_return_coef2)

        icir = ic_series.mean() / ic_series.std() * np.sqrt(244)
        # 两年度的年化ICIR绝对值大于阈值1.5
        condition3 = abs(icir) > abs_icir_threshold
        # if not condition3:
        #     print(check_date, 'The absolute value of ICIR is', abs(icir), 'less than ', abs_icir_threshold)

        # top_group_hedged_nav_1st_year = self.top_group_hedge_nav_dict['MktMedian'].loc[
        #                                 test_start_day: test_mid_day].fillna(method='ffill')
        # top_group_hedged_return_1st_year = top_group_hedged_nav_1st_year.iloc[-1] - top_group_hedged_nav_1st_year.iloc[
        #     0]
        # top_group_hedged_nav_2nd_year = self.top_group_hedge_nav_dict['MktMedian'].loc[
        #                                 test_mid_day: test_end_day].fillna(method='ffill')
        # top_group_hedged_return_2nd_year = top_group_hedged_nav_2nd_year.iloc[-1] - top_group_hedged_nav_2nd_year.iloc[
        #     0]
        # condition4 = (top_group_hedged_return_1st_year > mkt_median_return_threshold) and \
        #              (top_group_hedged_return_2nd_year > mkt_median_return_threshold)
        # if not condition4:
        #     print(check_date, 'Top group hedged return of 1st, 2nd year and MktMedian return threshold are',
        #           top_group_hedged_nav_1st_year, top_group_hedged_nav_2nd_year, mkt_median_return_threshold)
        condition4 = (self.topgroup_ret_exceed_mean['exceed_mean'].loc[
                      test_start_day:test_end_day].mean() > return_exceed_mean_threshold)
        long_short_nav_1st_year = self.long_short_nav.loc[test_start_day: test_mid_day].fillna(method='ffill')
        long_short_return_1st_year = long_short_nav_1st_year.iloc[-1] - long_short_nav_1st_year.iloc[0]
        long_short_nav_2nd_year = self.long_short_nav.loc[test_mid_day: test_end_day].fillna(method='ffill')
        long_short_return_2nd_year = long_short_nav_2nd_year.iloc[-1] - long_short_nav_2nd_year.iloc[0]
        condition5 = (long_short_return_1st_year > long_short_return_threshold) and \
                     (long_short_return_2nd_year > long_short_return_threshold)

        condition6 = (self.factor_test_report["Universe_coverage_mean"] >= universe_coverage_mean_threshold)
        # 和已入库的因子比较：1). Top组股票池相似度 2). Top组收益率相似度 当满足（股票池相似度>=0.4 并且 收益率>=0.8）这个条件的时候不能入库
        max_corr_series = self.corr_old_factors(test_start_day, test_end_day)
        # 如果top组的超额收益已经满足相关性要求则不需要再测试top组的重合度，若两项条件均不满足则把相关性和相似度高的股票输出
        if max_corr_series.max() < max_correlation_threshold:
            unqualified_corr_factors = []
        else:
            unqualified_corr_factors = max_corr_series[max_corr_series > max_correlation_threshold].index.tolist()

        exceed_ret_series = self.topgroup_ret_exceed_mean['exceed_mean'].loc[test_start_day:test_end_day]
        exceed_ret_series = exceed_ret_series.dropna()
        temp_mean = exceed_ret_series.mean()
        temp_std = exceed_ret_series.std()
        z_value = temp_mean / (temp_std / np.sqrt(len(exceed_ret_series)))
        condition7 = (z_value > 1.96)
        # if not condition7:
        #     print('t_test failed')

        self.conditions.update({str(check_date) + "-qualified": {
            'condition1': str(condition1),
            'condition2': str(condition2),
            'condition3': str(condition3),
            'condition4': str(condition4),
            'condition5': str(condition5),
            'condition6': str(condition6),
            'condition7': str(condition7),
        }})
        if all([condition1, condition2, condition3, condition4, condition5, condition6, condition7]):
            self.check_date_if_qualified.update({str(check_date) + "-qualified": True})
        else:
            self.check_date_if_qualified.update({str(check_date) + "-qualified": False})

        unqualified_corr_factors = list(set(unqualified_corr_factors))
        self.check_date_if_qualified.update(
            {str(check_date) + '_unqualified_correlation_factors': unqualified_corr_factors})

    def __fast_group_test(self, group_num=10, test_factor=..., position_window=1, stock_cost_ratio=0):
        """极速分层测试：不做行业中性，不对冲，但是考虑了买卖的可行性（停牌不可以买卖， 涨停不可以买、跌停不可以卖）"""
        test_factor2 = Dtk.convert_df_index_type(test_factor, 'timestamp', 'date_int')
        group_set = []
        for j, i_date in enumerate(list(test_factor2.index)):
            if j % position_window == 0:
                factor0 = test_factor2.loc[i_date]
                factor0 = factor0.sort_values()
                factor0 = factor0.dropna()
                num_stock = factor0.shape[0]
                stock_num_each_group = np.floor(num_stock / group_num)
                for i_group in range(group_num):
                    code_selected = list(factor0.index[int(stock_num_each_group * i_group):int(
                        stock_num_each_group * i_group + stock_num_each_group)])
                    if code_selected.__len__() > 0:
                        if group_set.__len__() < group_num:
                            group_set.append({i_date: code_selected})
                        else:
                            group_set[i_group].update({i_date: code_selected})
        # group_set是一个list, 长度等于group_num，其每个元素是一组的分组信息
        # group_set中的值（单组分组信息）是字典，字典的key是换仓日（例如20150105），value是对应日的股票列表
        intraday_buyable_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, list(test_factor2.index)[0],
                                                           list(test_factor2.index)[-1],
                                                           pv_type='interval_buyable_volume' +
                                                                   self.intraday_price_type[4:],
                                                           adj_type='FORWARD')
        intraday_buyable_df = intraday_buyable_df.fillna(0)
        intraday_buyable_df = get_intraday_moment_df(intraday_buyable_df,
                                                     int(self.intraday_price_moment) * 100)
        intraday_buyable_df = compress_intraday_index_to_daily(intraday_buyable_df, False)
        intraday_sellable_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, list(test_factor2.index)[0],
                                                            list(test_factor2.index)[-1],
                                                            pv_type='interval_sellable_volume' +
                                                                    self.intraday_price_type[4:],
                                                            adj_type='FORWARD')
        intraday_sellable_df = intraday_sellable_df.fillna(0)
        intraday_sellable_df = get_intraday_moment_df(intraday_sellable_df, int(self.intraday_price_moment) * 100)
        intraday_sellable_df = compress_intraday_index_to_daily(intraday_sellable_df, False)

        buy_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, list(test_factor2.index)[0],
                                                    list(test_factor2.index)[-1],
                                                    'interval_buy_' + self.intraday_price_type,
                                                    adj_type='FORWARD')
        buy_price_df = get_intraday_moment_df(buy_price_df, int(self.intraday_price_moment) * 100)
        buy_price_df = compress_intraday_index_to_daily(buy_price_df, False)

        sell_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, list(test_factor2.index)[0],
                                                     list(test_factor2.index)[-1],
                                                     'interval_sell_' + self.intraday_price_type,
                                                     adj_type='FORWARD')
        sell_price_df = get_intraday_moment_df(sell_price_df, int(self.intraday_price_moment) * 100)
        sell_price_df = compress_intraday_index_to_daily(sell_price_df, False)

        close_price_df = Dtk.get_panel_daily_pv_df(self.complete_stock_list, list(test_factor2.index)[0],
                                                   list(test_factor2.index)[-1], "close", "FORWARD")
        trading_day_list = list(test_factor2.index)

        if self.factor_neutralized_test_report["IC_cumsum"].mean() < 0:
            top_group_idx = 0
        else:
            top_group_idx = self.group_num - 1
        for j, group in enumerate(group_set):
            temp_ans_list = intraday_equally_wt_fast_nav(group, trading_day_list, buy_price_df, sell_price_df,
                                                         close_price_df,
                                                         intraday_buyable_df, intraday_sellable_df, stock_cost_ratio)
            i_group_nav, i_group_annualized_return, factor_turnover_rate = temp_ans_list
            self.group_nav_list.append(i_group_nav)
            if j == top_group_idx:
                self.top_group_avg_turnover_rate = factor_turnover_rate
            if j <= 8:
                self.group_total_annualized_return_dict.update({"Group" + str(0) + str(j + 1):
                                                                    i_group_annualized_return})
            else:
                self.group_total_annualized_return_dict.update({"Group" + str(j + 1): i_group_annualized_return})
        if self.group_nav_list[0].values[-1] > self.group_nav_list[-1].values[-1]:
            self.daily_top_group_stock_list = group_set[0]
            top_group_nav = self.group_nav_list[0]
            bottom_group_nav = self.group_nav_list[-1]
        else:
            self.daily_top_group_stock_list = group_set[-1]
            top_group_nav = self.group_nav_list[-1]
            bottom_group_nav = self.group_nav_list[0]
        group_return_each_year_list = []
        # 将分组测试中，每组的nav计算每年的收益率
        for j, i_group_nav in enumerate(self.group_nav_list):
            if j <= 8:
                return_each_year_all = nav_series_annually_stat(i_group_nav, "Group" + "0" + str(j + 1))
            else:
                return_each_year_all = nav_series_annually_stat(i_group_nav, "Group" + str(j + 1))
            return_each_year, return_each_year_daily = return_each_year_all
            group_return_each_year_list.append(return_each_year)
        year_list = []
        for item in list(group_return_each_year_list[0].keys()):
            year_list.append(item[0:4])
        for i_year in year_list:
            temp_list = []
            for j_group in range(self.group_num):
                if j_group <= 8:
                    temp_list.append(group_return_each_year_list[j_group][i_year + "-Group0" + str(j_group + 1)])
                else:
                    temp_list.append(group_return_each_year_list[j_group][i_year + "-Group" + str(j_group + 1)])
            self.each_year_group_return_dict.update({i_year: temp_list})

        for year in self.each_year_group_return_dict.keys():
            group_rank = calc_group_rank(self.each_year_group_return_dict[year])
            self.group_return_rank_coef.update({year: group_rank})  # 计算每年分组测试、每组收益率排序的rank相关系数

        for hedge_index in self.benchmark_list:
            hedged_nav_series, hedge_index_annualized_return = \
                self.__fast_group_hedge_nav(top_group_nav, hedge_index)
            top_group_excess_return_each_year, _ = nav_series_annually_stat(hedged_nav_series, hedge_index)
            self.top_group_excess_return_each_year.update(top_group_excess_return_each_year)
            self.top_group_hedge_nav_dict.update({hedge_index: hedged_nav_series})
            self.group_total_annualized_return_dict.update({hedge_index: hedge_index_annualized_return})
            daily_index = list(hedged_nav_series.index)
            monthly_index = Dtk.get_trading_day(daily_index[0], daily_index[-1], 'M')
            if daily_index[0] < monthly_index[0]:
                monthly_index_1 = [daily_index[0]]
                monthly_index_1.extend(monthly_index)
            else:
                monthly_index_1 = monthly_index
            hedged_nav_series_monthly = hedged_nav_series.reindex(monthly_index_1)
            hedged_return_each_month_series = hedged_nav_series_monthly - hedged_nav_series_monthly.shift(1)
            hedged_return_each_month_series.iloc[0] = hedged_nav_series_monthly.iloc[0] - 1
            # 将月度超额收益降序排列，一般列首>0、列尾<=0，逐个循环，可计算月度超额收益>0的月数
            hedged_monthly_return_descending_list = list(hedged_return_each_month_series)
            hedged_monthly_return_descending_list.sort(reverse=True)
            if hedged_monthly_return_descending_list[0] > 0 >= hedged_monthly_return_descending_list[-1]:
                for i in range(hedged_monthly_return_descending_list.__len__()):
                    if hedged_monthly_return_descending_list[i] * hedged_monthly_return_descending_list[i + 1] <= 0:
                        break
                monthly_alpha_winning_pct = (i + 1) / hedged_monthly_return_descending_list.__len__()
            elif hedged_monthly_return_descending_list[-1] > 0:
                monthly_alpha_winning_pct = 1
            else:
                monthly_alpha_winning_pct = 0
            self.top_group_monthly_winning_pct_stat.update({hedge_index: monthly_alpha_winning_pct})
            for date_return in hedged_return_each_month_series.iteritems():
                dict_key = str(date_return[0])[0:6] + "-" + str(hedge_index)
                self.top_group_excess_return_each_month.update({dict_key: date_return[1]})
        long_short_nav_series, long_short_annualized_return = fast_long_short_nav(top_group_nav, bottom_group_nav)
        long_short_return_each_year, long_short_return_each_year_daily = nav_series_annually_stat(long_short_nav_series,
                                                                                                  "LongShort")
        self.long_short_nav = long_short_nav_series
        self.long_short_return_each_year = long_short_return_each_year
        self.long_short_return_each_year_daily = long_short_return_each_year_daily

    def __fast_group_hedge_nav(self, nav_series, hedge_index):
        pct_chg_list = nav_series.diff()
        pct_chg_list = pct_chg_list.replace({np.nan: 0})
        if hedge_index == "MktMedian":
            self.daily_return_median = self.daily_return_median.reindex(nav_series.index)
            hedge_index_pct_chg = self.daily_return_median
        elif hedge_index == "MktMean":
            self.daily_return_mean = self.daily_return_mean.reindex(nav_series.index)
            hedge_index_pct_chg = self.daily_return_mean
        else:
            hedge_index_close = Dtk.get_panel_daily_pv_df([hedge_index], self.start_date, self.end_date, 'close')
            hedge_index_pct_chg = hedge_index_close / hedge_index_close.shift(1) - 1
            hedge_index_pct_chg = hedge_index_pct_chg[hedge_index]
        hedge_index_pct_chg.iloc[0] = 0.0
        daily_alpha = pct_chg_list - hedge_index_pct_chg
        daily_alpha.iloc[0] = 0.0
        hedged_nav = np.cumsum(daily_alpha) + 1
        hedged_nav = pd.Series(hedged_nav, index=nav_series.index)
        hedge_index_annualized_return = np.cumsum(hedge_index_pct_chg.values)[-1] / (
                hedge_index_pct_chg.__len__() / 244)
        return hedged_nav, hedge_index_annualized_return

    #####################################################################
    # -------------------- 以下是生成pdf报告的代码 -------------------- #
    def __pdf_output(self):
        uuid0 = str(uuid.uuid1())
        abs_address = self.report_address
        if not os.path.exists(abs_address):
            os.makedirs(abs_address)
        if not os.path.exists(abs_address + self.factor_name[8:]):
            os.makedirs(abs_address + self.factor_name[8:])
        doc = SimpleDocTemplate(
            abs_address + self.factor_name[8:] + '/FactorBacktest_' + self.factor_name + '_' + str(
                self.report_timestamp.strftime("%Y%m%d_%H%M%S")) + '.pdf', rightMargin=40, leftMargin=20, topMargin=50,
            bottomMargin=20)
        story = []
        style_type = getSampleStyleSheet()
        style_type.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        story.append(Paragraph(self.factor_name + ' backtest', style_type['Title']))
        story.append(Spacer(1, 24))
        text_data = '<font size=9.5>%s</font>' % time.ctime()
        text_data = 'Report date : ' + text_data
        story.append(Paragraph(text_data, style_type['Normal']))
        story.append(Spacer(1, 48))
        text_data = 'Factor Information'
        story.append(Paragraph(text_data, style_type['Justify']))
        story.append(Spacer(1, 12))
        dic = {
            'Factor_Name': self.factor_name,
            'Test_Period': str(self.start_date_orignal) + ' --> ' + str(self.end_date),
            'Stock Universe': self.universe,
            'Date Count': Dtk.get_trading_day(self.start_date_orignal, self.end_date).__len__(),
            'Holding Period': self.holding_period,
            'Neutral Factors': self.neutral_factor_set,
            'Outlier Filter': self.outlier_filter_method,
            'Daily Price Type': self.intraday_price_type,
            'Intraday Price Type(if used)': self.intraday_price_type,
            'Stock Cost Rate': self.stock_cost_rate,
            'Top Group Average Turnover Rate': self.top_group_avg_turnover_rate
        }
        dic.update(self.check_date_if_qualified)
        for i_key in self.long_short_return_each_year_daily.keys():
            dic.update({i_key: self.long_short_return_each_year_daily[i_key]})
        long_short_daily_return = (self.long_short_nav.iloc[-1] - self.long_short_nav.iloc[0]) / len(
            self.long_short_nav)
        long_short_daily_return = "%.2f%%" % (long_short_daily_return * 100)
        dic.update({'Alltime-LongShort-daily': long_short_daily_return})
        for item in dic.keys():
            story.append(Paragraph(item.rjust(20) + ' : ' + str(dic[item]), style_type['Normal']))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 24))
        story.append(Paragraph('Factor Distribution:', style_type['Justify']))
        story.append(Spacer(1, 6))
        data = self._dic2list()
        tb = self._table_model(data)
        story.append(tb)
        story.append(Spacer(1, 24))
        story.append(Paragraph('IC Statistics:', style_type['Justify']))
        data = self._dic2list_ic()
        tb = self._table_model(data)
        story.append(tb)
        story.append(Spacer(1, 24))

        story.append(Spacer(1, 24))
        boxplot_pic_name = uuid0 + "boxplot.png"
        inputs = [self.factor_raw_test_report['factor_data'], self.factor_test_report['factor_data'],
                  self.factor_neutralized_test_report['factor_data']]
        iboxplot_pic = plot_boxplot(inputs, boxplot_pic_name, self.report_address)
        story.append(iboxplot_pic)

        story.append(Spacer(1, 24))
        ic_cumsum_pic_name = uuid0 + "ic_cumsum.png"
        series_input = [self.factor_test_report['IC_cumsum'], self.factor_neutralized_test_report['IC_cumsum']]
        ic_cum_pic = plot_series(series_input, ['factor', 'factor_n'], 'IC_cumsum', 'IC_cumsum',
                                 ic_cumsum_pic_name, self.report_address)
        story.append(ic_cum_pic)

        story.append(Spacer(1, 24))
        ic_rolling_pic_name = uuid0 + "ic_rolling.png"
        series_input = [self.factor_test_report['IC_rolling'], self.factor_neutralized_test_report['IC_rolling']]
        ic_rolling_pic = plot_series(series_input, ['factor', 'factor_n'], 'IC_rolling', 'IC_rolling',
                                     ic_rolling_pic_name, self.report_address)
        story.append(ic_rolling_pic)

        story.append(Spacer(1, 24))
        universe_coverage_pic_name = uuid0 + 'universe_coverage.png'
        series_input = [self.factor_test_report['Universe_coverage_series'],
                        self.factor_neutralized_test_report['Universe_coverage_series']]
        universe_coverage_pic = plot_series(series_input, ['factor', 'factor_n'],
                                            'Factor_coverage_ratio_in_universe',
                                            'Factor_coverage_ratio_in_stock_universe', universe_coverage_pic_name,
                                            self.report_address)
        story.append(universe_coverage_pic)

        story.append(Spacer(1, 24))
        group_test_nav_pic_name = uuid0 + "group_nav.png"
        group_test_nav_pic = self._draw_group_nav(group_test_nav_pic_name)
        story.append(group_test_nav_pic)

        story.append(Spacer(1, 24))
        top_group_hedged_pic_name = uuid0 + 'top_group_hedged_nav.png'
        df_0 = self.top_group_hedge_nav_dict["000300.SH"].to_frame()
        df_1 = self.top_group_hedge_nav_dict["000905.SH"].to_frame()
        df_0 = Dtk.convert_df_index_type(df_0, 'date_int', 'timestamp')
        df_1 = Dtk.convert_df_index_type(df_1, 'date_int', 'timestamp')
        series_0 = df_0[0]
        series_1 = df_1[0]
        series_input = [series_0, series_1]
        top_group_hedged_nav_pic = plot_series(series_input, ["hedged_000300", "hedged_000905"],
                                               'top_group_hedged_nav', 'Top_group_hedged_nav',
                                               top_group_hedged_pic_name, self.report_address, 'upper left')
        story.append(top_group_hedged_nav_pic)

        story.append(Spacer(1, 24))
        group_annualized_return_pic_name = uuid0 + "group_annualized_return.png"
        group_annualized_return_pic = self.__plot_group_annualized_bar(group_annualized_return_pic_name)
        story.append(group_annualized_return_pic)

        story.append(Spacer(1, 24))
        long_short_pic_name = uuid0 + "Long_short_nav.png"
        long_short_df = self.long_short_nav.to_frame()
        long_short_df = Dtk.convert_df_index_type(long_short_df, 'date_int', 'timestamp')
        long_short_nav_series = long_short_df[0]
        long_short_nav_pic = plot_one_series(long_short_nav_series, "long_short_nav", "long_short_nav",
                                             "Long_short_nav", long_short_pic_name, self.report_address)
        story.append(long_short_nav_pic)

        group_pic = None
        story.append(Spacer(1, 24))
        for i_year in self.each_year_group_return_dict.keys():
            i_pic_name = uuid0 + "Group_return" + i_year + ".png"
            group_pic = plot_group_bar2(self.each_year_group_return_dict[i_year], i_year, i_pic_name,
                                        self.report_address)
            story.append(group_pic)
            story.append(Spacer(1, 24))

        doc.build(story)
        del ic_cum_pic, ic_rolling_pic, group_test_nav_pic, universe_coverage_pic, top_group_hedged_nav_pic, \
            group_annualized_return_pic, long_short_nav_pic, group_pic
        os.remove(os.path.join(self.report_address, boxplot_pic_name))
        os.remove(os.path.join(self.report_address, ic_cumsum_pic_name))
        os.remove(os.path.join(self.report_address, ic_rolling_pic_name))
        os.remove(os.path.join(self.report_address, group_test_nav_pic_name))
        os.remove(os.path.join(self.report_address, universe_coverage_pic_name))
        os.remove(os.path.join(self.report_address, top_group_hedged_pic_name))
        os.remove(os.path.join(self.report_address, group_annualized_return_pic_name))
        os.remove(os.path.join(self.report_address, long_short_pic_name))
        for i_year in self.each_year_group_return_dict.keys():
            i_pic_name = uuid0 + "Group_return" + i_year + ".png"
            os.remove(os.path.join(self.report_address, i_pic_name))

    @staticmethod
    def _table_model(data):
        width = 5.2
        col_widths = (width / len(data[0])) * inch
        dis_list = []
        for x in data:
            dis_list.append(x)
        component_table = Table(dis_list, colWidths=col_widths)
        return component_table

    def _dic2list(self):
        result = []
        keys = list(self.factor_neutralized_test_report['factor_distribution'].index)
        result.append([' ', 'Factor Raw', 'Factor', 'Factor Neutralized'])
        for item in keys:
            result.append(
                [item,
                 round(self.factor_raw_test_report['factor_distribution'].loc[item, 'factor_distribution'], 5),
                 round(self.factor_test_report['factor_distribution'].loc[item, 'factor_distribution'], 5),
                 round(self.factor_neutralized_test_report['factor_distribution'].loc[item, 'factor_distribution'], 5)])
        return result

    def _dic2list_ic(self):
        result = []
        keys = list(self.factor_neutralized_test_report['IC_stat'].index)
        result.append([' ', 'Factor Raw', 'Factor', 'Factor Neutralized'])
        for item in keys:
            result.append([item, round(self.factor_raw_test_report['IC_stat'].loc[item, 'IC'], 5),
                           round(self.factor_test_report['IC_stat'].loc[item, 'IC'], 5),
                           round(self.factor_neutralized_test_report['IC_stat'].loc[item, 'IC_of_factor_neutralized'],
                                 5)])
        return result

    def _draw_group_nav(self, pic_name):
        time_stamp_list = self.group_nav_list[0].index
        index = []
        index_number = []
        x_number = []
        for i, time_stamp in enumerate(time_stamp_list):
            x_number.append(i)
            if i % int(time_stamp_list.__len__() / 6) == 0:
                index_number.append(i)
                index.append(str(time_stamp))
        x_number = np.array(x_number)
        plt.figure(figsize=(6, 2), dpi=300)
        for i in range(self.group_num):
            plt.plot(x_number, self.group_nav_list[i].values, linewidth=0.4, label=str(i))
        plt.xticks(index_number, index, fontsize=5, rotation=0)
        plt.ylabel('group_nav', fontsize=5)
        plt.yticks(fontsize=5)
        plt.title('group_nav', fontsize=5)
        if self.group_num <= 10:
            plt.legend(loc='lower left', fontsize=5)
        else:
            plt.legend(loc='lower left', fontsize=3)
        file_name = os.path.join(self.report_address, pic_name)
        plt.savefig(file_name, format='png')
        im = Image(file_name, 9 * inch, 3 * inch)
        return im

    def __plot_group_annualized_bar(self, pic_name):
        def autolabel(rects):  # 为柱状图标上数字
            for i_rect in rects:
                height = i_rect.get_height()
                if height >= 0:
                    plt.text(i_rect.get_x(), 1.03 * height, '%.4f' % float(height), fontsize=3)
                else:
                    plt.text(i_rect.get_x(), 0.97 * height, '%.4f' % float(height), fontsize=3)

        plt.figure(figsize=(6, 2), dpi=300)
        rect = plt.bar(np.arange(self.group_num + self.benchmark_list.__len__()),
                       [self.group_total_annualized_return_dict[group] for group in
                        self.group_total_annualized_return_dict.keys()])
        plt.xticks(np.arange(self.group_num + self.benchmark_list.__len__()),
                   list(self.group_total_annualized_return_dict.keys()), fontsize=3, rotation=30)
        plt.yticks(fontsize=5)
        plt.title("Group annualized return", fontsize=5)
        autolabel(rect)
        file_name = os.path.join(self.report_address, pic_name)
        plt.savefig(file_name, format='png')
        im = Image(file_name, 9 * inch, 3 * inch)
        return im

    # -------------------- 以上是生成pdf报告的代码 -------------------- #
    #####################################################################

    def __json_output(self):
        self.factor_stat_output.update({"Factor_name": self.factor_name, "Test_period_start": self.start_date_orignal,
                                        "Test_period_end": self.end_date, "Stock_universe": self.universe,
                                        "Date_count": Dtk.get_trading_day(self.start_date_orignal,
                                                                          self.end_date).__len__(),
                                        "Holding_period": self.holding_period,
                                        "Neutral_factors": list(self.neutral_factor_set),
                                        "Group_number": self.group_num, "Label_type": self.intraday_price_type,
                                        "Universe_coverage_mean": self.factor_test_report[
                                            "Universe_coverage_mean"],
                                        "Universe_coverage_min": self.factor_test_report[
                                            "Universe_coverage_min"],
                                        "Not_enough_coverage_dates": self.factor_test_report[
                                            "Not_enough_coverage_dates"],
                                        "Stock_cost_rate": self.stock_cost_rate,
                                        "Top_group_avg_turnover_rate": self.top_group_avg_turnover_rate,
                                        })

        flag = [x for x in self.check_date_if_qualified.values() if x == False]
        not_null_list = [x for x in self.check_date_if_qualified.values() if isinstance(x, list) and len(x) > 0]

        if len(flag) <= 2 and len(not_null_list) <= 2:
            criterion = True
        else:
            criterion = False

        self.factor_stat_output.update(self.check_date_if_qualified)
        for ic_stat_item in list(self.factor_neutralized_test_report['IC_stat'].index):
            self.factor_stat_output.update(
                {ic_stat_item: self.factor_neutralized_test_report['IC_stat'].loc[ic_stat_item][0]})
        for i_key in self.long_short_return_each_year_daily.keys():
            self.factor_stat_output.update({i_key: self.long_short_return_each_year_daily[i_key]})
        long_short_daily_return = (self.long_short_nav.iloc[-1] - self.long_short_nav.iloc[0]) / len(
            self.long_short_nav)
        long_short_daily_return = "%.2f%%" % (long_short_daily_return * 100)
        self.factor_stat_output.update({'Alltime-LongShort-daily': long_short_daily_return})
        for rank_year in list(self.group_return_rank_coef.keys()):
            self.factor_stat_output.update({'GroupRank_' + rank_year: self.group_return_rank_coef[rank_year]})
        for i_benchmark in self.top_group_monthly_winning_pct_stat.keys():
            self.factor_stat_output.update(
                {str('MonthlyWinningPct_' + i_benchmark): self.top_group_monthly_winning_pct_stat[i_benchmark]})
        self.factor_stat_output.update(self.top_group_excess_return_each_year)
        self.factor_stat_output.update(self.long_short_return_each_year)
        self.factor_stat_output.update(self.top_group_excess_return_each_month)
        abs_address = self.report_address
        if not os.path.exists(abs_address):
            os.makedirs(abs_address)
        if not os.path.exists(abs_address + self.factor_name[8:]):
            os.makedirs(abs_address + self.factor_name[8:])
        json_file = open(abs_address + self.factor_name[8:] + '/FactorBacktest_' + self.factor_name + '_' + str(
            self.report_timestamp.strftime("%Y%m%d_%H%M%S")) + '.json', 'w')
        json_file.write(json.dumps(self.factor_stat_output))
        json_file.close()
        return criterion

    # def __json_conditions_output(self):
    #     abs_address = self.report_address
    #     if not os.path.exists(abs_address):
    #         os.makedirs(abs_address)
    #     json_file = open(abs_address + 'conditionsisqualified_ ' + self.factor_name + '_' + str(
    #         self.report_timestamp.strftime("%Y%m%d_%H%M%S")) + '.json', 'w')
    #     json_file.write(json.dumps(self.conditions))
    #     json_file.close()
    #     pass

    def load_price_label(self, intraday_price_moment):
        valid_end_date = Dtk.get_n_days_off(self.end_date, 2)[-1]
        intraday_buy_price_df = Dtk.get_panel_interval_pv_df( self.complete_stock_list, self.start_date,
                                                             valid_end_date, pv_type='interval_buy_twap_30_5',
                                                             adj_type='FORWARD')
        intraday_buy_price_df = get_intraday_moment_df(intraday_buy_price_df,
                                                       int(intraday_price_moment) * 100)
        intraday_buy_price_df_with_daily_index = compress_intraday_index_to_daily(intraday_buy_price_df, False)
        intraday_sell_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, self.start_date,
                                                              valid_end_date, pv_type='interval_twap_30_5',
                                                              adj_type='FORWARD')
        intraday_sell_price_df = get_intraday_moment_df(intraday_sell_price_df, int(intraday_price_moment) * 100)
        intraday_sell_price_df_with_daily_index = compress_intraday_index_to_daily(intraday_sell_price_df, False)

        valid_start_date = Dtk.get_n_days_off(self.start_date, -2)[0]
        valid_end_date = Dtk.get_n_days_off(self.end_date, 2)[-1]
        daily_stock_universe_df = Dtk.get_panel_daily_info(self.complete_stock_list, valid_start_date,
                                                           valid_end_date, info_type=self.universe,
                                                           output_index_type='date_int')
        stock_universe_df = daily_stock_universe_df.shift(1).iloc[1:].copy()

        return_rate_df = intraday_sell_price_df_with_daily_index.shift(-1) / intraday_buy_price_df_with_daily_index - 1
        return_rate_df = return_rate_df * stock_universe_df / stock_universe_df
        return_rate_df = return_rate_df.loc[self.start_date:self.end_date]
        markt_mean_df = return_rate_df.mean(axis=1)

        # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
        # intraday_return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')

        return return_rate_df, markt_mean_df

    def TopGroup_DailyRetExceedMean(self, group_test_factor_data, cost_ratio = 0):
        # group_test_factor_data = group_test_factor_data * self.stock_universe_df/self.stock_universe_df
        df_int = Dtk.convert_df_index_type(group_test_factor_data, 'timestamp', 'date_int')
        return_rate_df, markt_mean_df = self.load_price_label(self.intraday_price_moment)
        ic_series = Dtk.convert_df_index_type(pd.DataFrame(self.factor_neutralized_test_report['IC_series']), 'timestamp', 'date_int')
        if ic_series.loc[20160101:20181231,:].mean().values <0:
            df_int = -df_int
        df_infer_rank = df_int.rank(axis=1, ascending=True, pct=True)
        sign = df_infer_rank.values >= 0.9
        df_infer_select = df_infer_rank * sign / sign

        #筛选出每天的top组
        stock_selec_dic = {}
        for date in df_int.index.tolist():
            date_stock_series = df_infer_select.loc[date].dropna()
            date_stoc_list = date_stock_series.index.tolist()
            stock_selec_dic.update({date: date_stoc_list})

        return_value_exceed_mean_series = pd.Series(index=df_int.index.tolist()[0:-1])
        for date in df_int.index.tolist()[0:-1]:
            tomorrow_date = Dtk.get_n_days_off(date, 2)[-1]
            out_stock = []  # 在第二天会调掉的股票
            in_stock = []  # 在第二天不会调掉的股票
            for it in stock_selec_dic[date]:
                if it not in stock_selec_dic[tomorrow_date]:
                    out_stock.append(it)
                else:
                    in_stock.append(it)

            return_out = (1 - cost_ratio) * return_rate_df.loc[date, out_stock] - cost_ratio
            return_in = return_rate_df.loc[date, in_stock]
            return_value = (return_out.sum() + return_in.sum()) / (len(return_out.dropna()) + len(return_in.dropna()))

            return_value_exceed_mean = return_value - markt_mean_df.loc[date]
            return_value_exceed_mean_series[date] = return_value_exceed_mean

        self.topgroup_ret_exceed_mean.update({'exceed_mean': return_value_exceed_mean_series})
    def launch_test(self):
        # stock_universe_df是一个矩阵，值为1或0，如某只股票在某日在股票池内则值为1、否则为0
        self.load_label()

        # 以下计算因子的IC
        # factor_data_df 乘以 stock_universe_df 再除以 stock_universe_df，就会把不在股票池内的因子值调整为nan
        factor_data = compress_intraday_index_to_daily(self.original_factor_data_df, index_type_timestamp=True)
        factor_data = factor_data.astype(float64)
        factor_data = factor_data * self.stock_universe_df / self.stock_universe_df
        factor_isnan = np.isnan(factor_data)
        factor_coverage = factor_data.shape[1] - np.sum(factor_isnan, axis=1)
        universe_coverage_ratio = factor_coverage / np.sum(self.stock_universe_df, axis=1)  # 因子在universe的覆盖度
        universe_coverage_ratio = universe_coverage_ratio.replace(np.nan, 0)
        not_enough_coverage_series = universe_coverage_ratio[universe_coverage_ratio < 0.1]
        not_enough_coverage_date_list = []
        for date in list(not_enough_coverage_series.index):
            not_enough_coverage_date_list.append(int(dt.datetime.fromtimestamp(date).strftime("%Y%m%d")))
        self.factor_test_report.update({"Universe_coverage_series": universe_coverage_ratio})
        self.factor_test_report.update({"Universe_coverage_mean": np.mean(universe_coverage_ratio)})
        self.factor_test_report.update({"Universe_coverage_min": np.min(universe_coverage_ratio)})
        self.factor_test_report.update({"Not_enough_coverage_dates": not_enough_coverage_date_list})

        factor_data = factor_data * self.suspend_filter / self.suspend_filter
        # clean_factor_data = factor_data * self.limite_status / self.limite_status

        self.factor_raw_test_report.update({'factor_data': factor_data})
        factor_raw_distribution = factor_distribution_calc2(factor_data)
        # print(factor_raw_distribution)
        self.factor_raw_test_report.update({'factor_distribution': factor_raw_distribution})
        self.label_data = self.label_data.reindex(factor_data.index)
        ic_series = factor_data.corrwith(self.label_data, axis=1)
        ic_stat = self.ic_stat_calc(ic_series, 'IC')
        # print(ic_stat)
        ic_rolling_window = max([3, self.holding_period])
        ic_rolling = ic_series.rolling(ic_rolling_window).mean()
        ic_cumsum = ic_series.cumsum()
        self.factor_raw_test_report.update({'IC_series': ic_series})
        self.factor_raw_test_report.update({'IC_stat': ic_stat})
        self.factor_raw_test_report.update({'IC_rolling': ic_rolling})
        self.factor_raw_test_report.update({'IC_cumsum': ic_cumsum})
        index1 = factor_data.index
        factor_data = outlier_filter(factor_data, self.outlier_filter_method)  # 因子去除极值
        factor_data = z_score_standardizer(factor_data)  # 因子标准化
        factor_data = factor_data.reindex(index=index1)
        self.factor_data_df = factor_data
        self.factor_test_report.update({'factor_data': factor_data})
        factor_distribution = factor_distribution_calc2(factor_data)
        # print(factor_distribution)  # 这些打印的部分，后续会改成输出到报告
        self.factor_test_report.update({'factor_distribution': factor_distribution})
        # 因为计算因子时会删去部分天（例如2016年1月熔断的2天），label也要将这些天删去
        self.label_data = self.label_data.reindex(factor_data.index)
        ic_series = factor_data.corrwith(self.label_data, axis=1)
        ic_stat = self.ic_stat_calc(ic_series, 'IC')
        # print(ic_stat)
        ic_rolling_window = max([3, self.holding_period])
        ic_rolling = ic_series.rolling(ic_rolling_window).mean()
        ic_cumsum = ic_series.cumsum()
        self.factor_test_report.update({'IC_series': ic_series})
        self.factor_test_report.update({'IC_stat': ic_stat})
        self.factor_test_report.update({'IC_rolling': ic_rolling})
        self.factor_test_report.update({'IC_cumsum': ic_cumsum})

        # 与预处理保持一致
        volume_df = Dtk.get_panel_daily_pv_df(self.complete_stock_list, self.start_date, self.end_date, "volume")
        volume_df = Dtk.convert_df_index_type(volume_df, 'date_int', 'timestamp')
        industry_df = Dtk.get_panel_daily_info(self.complete_stock_list, Dtk.get_n_days_off(self.start_date, -3)[0],
                                               self.end_date,
                                               'industry3')
        industry_df = industry_df.shift(1)
        industry_df = Dtk.convert_df_index_type(industry_df, 'date_int', 'timestamp')
        mkt_cap_ard_df = Dtk.get_panel_daily_info(self.complete_stock_list, Dtk.get_n_days_off(self.start_date, -3)[0],
                                                  self.end_date,
                                                  'mkt_cap_ard', 'timestamp')
        mkt_cap_ard_df = np.log(mkt_cap_ard_df)
        mkt_cap_ard_df = mkt_cap_ard_df.shift(1)

        factor_data1 = compress_intraday_index_to_daily(self.original_factor_data_df, index_type_timestamp=True)
        factor_data1 = factor_data1 * volume_df / volume_df  # 将停牌股票的因子值置为nan
        # index1 = self.original_factor_data_df.index
        index2 = factor_data1.index
        factor_data1 = outlier_filter(factor_data1, method="MAD", parameter=10)  # 因子去除极值
        index3 = factor_data1.index
        factor_data1 = fillna_with_industry_median_new(factor_data1, industry_df)
        factor_data1 = factor_data1.reindex(index3)
        factor_data1 = factor_neutralizer_new(factor_data1, industry_df, mkt_cap_ard_df)
        factor_data1 = z_score_standardizer(factor_data1)  # 因子标准化
        factor_data1 = factor_data1.reindex(index2)
        # factor_data1.index = index1
        factor_data_neutralized = factor_data1
        # 因子中性化（将self.neutral_factor_set对原因子回归，以残差作为新的因子值）
        # 日内中性化时需要用前一天的行业、市值
        # factor_data_neutralized = factor_neutralizer(factor_data, self.start_date, self.end_date,
        #                                              self.neutral_factor_set, neutral_regressor_backward_shift=True)
        # factor_data_neutralized = factor_neutralizer2(self.limite_status,
        #                                               factor_data, self.start_date, self.end_date,
        #                                               self.neutral_factor_set, neutral_regressor_backward_shift=True)
        temp_factor_data_neutralized = factor_data_neutralized * self.stock_universe_df / self.stock_universe_df
        factor_data_neutralized_isnan = np.isnan(temp_factor_data_neutralized)
        factor_neu_coverage = temp_factor_data_neutralized.shape[1] - np.sum(factor_data_neutralized_isnan, axis=1)

        # 中性化因子在universe的覆盖度
        neu_universe_coverage_ratio = factor_neu_coverage / np.sum(self.stock_universe_df, axis=1)
        neu_universe_coverage_ratio = neu_universe_coverage_ratio.replace(np.nan, 0)
        neu_not_enough_coverage_series = neu_universe_coverage_ratio[neu_universe_coverage_ratio < 0.1]
        neu_not_enough_coverage_date_list = []
        for date in list(neu_not_enough_coverage_series.index):
            neu_not_enough_coverage_date_list.append(int(dt.datetime.fromtimestamp(date).strftime("%Y%m%d")))
        self.factor_neutralized_test_report.update({"Universe_coverage_series": neu_universe_coverage_ratio})
        self.factor_neutralized_test_report.update({"Universe_coverage_mean": np.mean(neu_universe_coverage_ratio)})
        self.factor_neutralized_test_report.update({"Universe_coverage_min": np.min(neu_universe_coverage_ratio)})
        self.factor_neutralized_test_report.update({"Not_enough_coverage_dates": neu_not_enough_coverage_date_list})
        self.factor_neutralized_test_report.update({"factor_data": factor_data_neutralized})
        self.neutralized_factor_data_df = factor_data_neutralized
        factor_distribution = factor_distribution_calc2(factor_data_neutralized)
        # print(factor_distribution)
        self.factor_neutralized_test_report.update({'factor_distribution': factor_distribution})
        ic_series = factor_data_neutralized.corrwith(self.label_data, axis=1)
        ic_series.sort_index(inplace=True)
        ic_stat = self.ic_stat_calc(ic_series, 'IC_of_factor_neutralized')
        # print(ic_stat)
        ic_rolling = ic_series.rolling(ic_rolling_window).mean()
        ic_cumsum = ic_series.cumsum()
        self.factor_neutralized_test_report.update({'IC_series': ic_series})
        self.factor_neutralized_test_report.update({'IC_stat': ic_stat})
        self.factor_neutralized_test_report.update({'IC_rolling': ic_rolling})
        self.factor_neutralized_test_report.update({'IC_cumsum': ic_cumsum})

        # 在前面计算IC时，删去了部分全市场都为nan时的日期，但分组测试时要补回来
        factor_data = compress_intraday_index_to_daily(self.original_factor_data_df, index_type_timestamp=True)
        factor_data = factor_data.astype(float64)
        factor_index = factor_data.index
        group_test_factor_data = self.factor_neutralized_test_report["factor_data"].reindex(factor_index)
        # print("Running fast group test...")
        group_test_factor_data = group_test_factor_data * self.stock_universe_df / self.stock_universe_df
        self.TopGroup_DailyRetExceedMean(group_test_factor_data)
        self.__fast_group_test(group_num=self.group_num, test_factor=group_test_factor_data,
                               position_window=self.holding_period, stock_cost_ratio=self.stock_cost_rate)
        # print("Fast group test finished.")
        for check_date in self.check_date_list:
            self.func_check_qualified(check_date)
        flag = self.__json_output()

        # 计算相关性
        hedged_nav_series = self.top_group_hedge_nav_dict['000905.SH']  # 000905.SH 中证500指数

        print("Generating pdf report...")
        self.__pdf_output()
        # print("Pdf report generated. Single factor backtest for", self.factor_name, "finished.")
        return {"factor": self.factor_name, "flag": flag, "reason": self.check_date_if_qualified, "team": "stock_trade"}
