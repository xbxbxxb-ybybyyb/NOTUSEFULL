import time
import datetime as dt
from xfactor.test.symbol_team.Utils.HelperFunctions import fast_long_short_nav, nav_series_annually_stat, \
    calc_group_rank, compress_intraday_index_to_daily, get_intraday_moment_df, intraday_equally_wt_fast_nav, \
    factor_distribution_calc2, factor_neutralizer, outlier_filter, z_score_standardizer, \
    fillna_with_industry_median_new, factor_neutralizer_new
from xfactor.test.test_data_loader import fix_inlib_factors_path
# from matplotlib.pylab import *
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import matplotlib.pyplot as plt

from xfactor.test.symbol_team.FactorTest.LogicTestBase import LogicExcessKlineBase
import xfactor.test.symbol_team.DataAPI.DataToolkit as Dtk
from xfactor.test.symbol_team.FactorTest.config_for_test import get_thresholds_for_indicators
from dateutil.relativedelta import relativedelta
from collections import Counter
from itertools import product
import pandas as pd
from copy import deepcopy
import numpy as np
from multiprocessing import Pool
import uuid
import os


class SingleFactorTest(object):
    def __init__(self, factor_name, factor_value_dict, start_date, end_date, execute_cpu_num=1):
        self.factor_name = factor_name
        query_trade_date_list = Dtk.get_trading_day(start_date, end_date)
        self.factor_name = factor_name
        self.start_date_orignal = query_trade_date_list[0]
        self.start_date = query_trade_date_list[0]
        self.end_date = query_trade_date_list[-1]
        self.complete_stock_list = Dtk.get_complete_stock_list()
        self.factor_value_dict = factor_value_dict
        self.data_buffer = None
        self.holding_period = 1
        self.universe = 'alpha_universe'
        self.intraday_price_type = 'twap_30_5'
        self.time_intervals = [1000, 1030, 1100, 1300, 1330, 1400, 1430]
        self.end_date_IS = end_date
        firstdate_of_the_last_halfyear_IS = dt.datetime.strptime(str(end_date), '%Y%m%d') - relativedelta(
            months=6)
        self.firstdate_of_the_last_halfyear_IS = int(dt.datetime.strftime(firstdate_of_the_last_halfyear_IS, "%Y%m%d"))
        self.exempt_dates = [['20200203', '20200204'], ['20160104', '20160108']]
        self.thresholds_for_test = get_thresholds_for_indicators()
        self.load_factors_min_em_return()
        self.single_step_for_em_calc = 100
        self.execute_cpu_num = execute_cpu_num
        self.max_correlation_threshold = 0.65
        self.report_address = '/tmp/'
        self.report_timestamp = dt.datetime.now()
        self.factor_distribution_dct = {}
        self.factors_ic_dict = {}
        pass

    def load_data_buffer(self):
        volume_df = Dtk.get_panel_daily_pv_df(self.complete_stock_list, Dtk.get_n_days_off(self.start_date, -3)[0],
                                              self.end_date, "volume")
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
        daily_stock_universe_df = Dtk.get_panel_daily_info(self.complete_stock_list,
                                                           Dtk.get_n_days_off(self.start_date, -3)[0],
                                                           self.end_date, info_type=self.universe,
                                                           output_index_type='timestamp')
        stock_universe_df = daily_stock_universe_df.shift(1).loc[self.start_date:]
        data_buffer = {
            'volume': volume_df,
            'industry': industry_df,
            'mkt_cap_ard': mkt_cap_ard_df,
            'stock_universe': stock_universe_df
        }
        self.data_buffer = data_buffer

    def load_label(self):
        label_dct = {}
        for intraday_price_moment in self.time_intervals:
            stock_universe_df = self.data_buffer['stock_universe'].copy()
            valid_end_date = Dtk.get_n_days_off(self.end_date, self.holding_period + 1)[-1]

            # 先获取日内频的twap价格，再从中抽取时刻等于self.intraday_price_moment的价格，再将index转化为日频的
            intraday_buy_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, self.start_date,
                                                                 valid_end_date,
                                                                 pv_type='interval_buy_' + self.intraday_price_type,
                                                                 adj_type='FORWARD')
            intraday_buy_price_df = get_intraday_moment_df(intraday_buy_price_df,
                                                           int(intraday_price_moment) * 100)
            intraday_buy_price_df_with_daily_index = compress_intraday_index_to_daily(intraday_buy_price_df, False)
            intraday_sell_price_df = Dtk.get_panel_interval_pv_df(self.complete_stock_list, self.start_date,
                                                                  valid_end_date,
                                                                  pv_type='interval_' + self.intraday_price_type,
                                                                  adj_type='FORWARD')
            intraday_sell_price_df = get_intraday_moment_df(intraday_sell_price_df, int(intraday_price_moment) * 100)
            intraday_sell_price_df_with_daily_index = compress_intraday_index_to_daily(intraday_sell_price_df, False)

            return_rate_df = intraday_sell_price_df_with_daily_index.shift(
                -self.holding_period) / intraday_buy_price_df_with_daily_index - 1
            # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
            intraday_return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
            label_data = intraday_return_rate_df * stock_universe_df / stock_universe_df
            label_dct.update({intraday_price_moment: label_data})
            print('Loading daily label for IC calculation:{}'.format(intraday_price_moment))
        self.label_dct = label_dct

    # 载入库内要求相关性的因子的分钟超额序列
    def load_factors_min_em_return(self):
        # 保存库内因子信息文件
        factors_inlib_dict = pd.read_pickle(fix_inlib_factors_path)
        all_factors_passed = []
        for singletime in self.time_intervals:
            factors_inlib_thetime = factors_inlib_dict[str(singletime)]  # 时间点对应的value
            factors_inlib_thetime = factors_inlib_thetime['isInLib'][factors_inlib_thetime['isInLib'] == 1]
            factors_inlib_thetime_inem = factors_inlib_thetime.index.tolist()
            all_factors_passed.extend(factors_inlib_thetime_inem)
        logic_of_all_factors = [i[8:] for i in all_factors_passed]
        count_of_passedtimes = Counter(logic_of_all_factors)
        count_of_passedtimes_series = pd.Series(count_of_passedtimes)
        factors_passed_alltimes = count_of_passedtimes_series[
            count_of_passedtimes_series == len(self.time_intervals)].index.tolist()

        # 根据有效的因子列表获取超额收益
        data = Dtk.get_factor_excess_ret_kline(self.start_date, self.end_date, factors_passed_alltimes)
        self.hedged_df = data

    # 多时点的因子值预处理，分别涉及各时点因子值的去异常值、标准化和中性化，并根据样本内的icmean进行因子值调整
    def factor_processing(self):
        valid_start_date = Dtk.get_n_days_off(self.start_date, -2)[0]
        label_dict = deepcopy(self.label_dct)
        data_buffer = deepcopy(self.data_buffer)
        volume_df, industry_df, mkt_cap_ard_df, stock_universe_df = data_buffer['volume'], data_buffer['industry'], \
                                                                    data_buffer['mkt_cap_ard'], data_buffer[
                                                                        'stock_universe']
        factor_value_dict = self.factor_value_dict
        std_factor_value_dict = {}
        factors_ic_dict = {}
        for singletime in self.time_intervals:
            original_factor_data_singletime = factor_value_dict['Fix{}_{}'.format(singletime, self.factor_name)]
            original_factor_data_singletime.index = [int(i) for i in original_factor_data_singletime.index]
            original_factor_data_singletime = original_factor_data_singletime.loc[valid_start_date:self.end_date]
            factor_data1 = Dtk.convert_df_index_type(original_factor_data_singletime, 'date_int', 'timestamp')
            volume_df = volume_df.reindex(factor_data1.index)
            industry_df = industry_df.reindex(factor_data1.index)
            mkt_cap_ard_df = mkt_cap_ard_df.reindex(factor_data1.index)
            stock_universe_df = stock_universe_df.reindex(factor_data1.index)
            factor_data1 = factor_data1.reindex(columns=self.complete_stock_list)
            factor_data1 = factor_data1 * volume_df / volume_df  # 将停牌股票的因子值置为nan
            index2 = factor_data1.index
            factor_data1 = outlier_filter(factor_data1, method="MAD", parameter=10)  # 因子去除极值
            index3 = factor_data1.index
            factor_data1 = fillna_with_industry_median_new(factor_data1, industry_df)
            factor_data1 = factor_data1.reindex(index3)
            factor_data1 = factor_neutralizer_new(factor_data1, industry_df, mkt_cap_ard_df)
            factor_data1 = z_score_standardizer(factor_data1)  # 因子标准化
            factor_data1 = factor_data1.reindex(index2)
            factor_data1 = factor_data1 * stock_universe_df / stock_universe_df
            label_singletime = label_dict[singletime]
            label_singletime = label_singletime.reindex(index=factor_data1.index, columns=factor_data1.columns)
            factor_ic_singletime = self.get_corr(factor_data1, label_singletime, axis=1)
            factor_ic_singletime = Dtk.convert_df_index_type(factor_ic_singletime.to_frame(), 'timestamp',
                                                             'date_int').iloc[:, 0].loc[
                                   self.start_date:self.end_date_IS]
            if factor_ic_singletime.mean() < 0:
                factor_data1 = pd.DataFrame(-factor_data1.values, index=factor_data1.index,
                                            columns=factor_data1.columns)
            factor_data1 = Dtk.convert_df_index_type(factor_data1, 'timestamp', 'date_int')
            factor_data1 = factor_data1.reindex(columns=self.complete_stock_list)
            std_factor_value_dict.update({singletime: factor_data1})
            factors_ic_dict.update({singletime: factor_ic_singletime})
        self.std_factor_value_dict = std_factor_value_dict
        self.factors_ic_dict = factors_ic_dict

    @staticmethod
    def calculated_factor_em(obj, factor_value_dict):
        sek = obj
        temp = sek.calculate_excess_ret_kline(factor_value_dict)
        return temp

    @staticmethod
    def get_em_for_singletask(std_factor_value_dict, singletask, tasks):
        ticktime, sub_dates_in_task = singletask[0], singletask[1]
        sub_start_date, sub_end_date = sub_dates_in_task[0], sub_dates_in_task[-1]
        valid_sub_start_date = Dtk.get_n_days_off(sub_start_date, -2)[0]
        std_factor_value = std_factor_value_dict[ticktime].loc[valid_sub_start_date:sub_end_date]
        factor_dict_for_task = {ticktime: std_factor_value}
        sek = LogicExcessKlineBase(start_date=sub_start_date, end_date=sub_end_date,
                                   factor_value_dict=factor_dict_for_task)
        res_singletask = sek.calculate_excess_ret()
        pct = (tasks.index(singletask) + 1) / len(tasks)
        print(pct)
        return res_singletask

    # 计算因子逻辑的分钟超额收益
    def get_factors_em(self):
        def split_calc_datetime_into_group(start_date, end_date, max_date_num_per_task):
            # 按照天数将需要计算的时间段进行分组，例如，每100个交易日分一组
            group = []
            calc_datetime_list = Dtk.get_trading_day(start_date, end_date)
            size = len(calc_datetime_list)
            from_index = 0
            while from_index < size:
                group.append(calc_datetime_list[from_index: min(size, from_index + max_date_num_per_task)])
                from_index += max_date_num_per_task
            return group

        trading_date_groups = split_calc_datetime_into_group(self.start_date, self.end_date,
                                                             self.single_step_for_em_calc)
        factors_times = list(self.std_factor_value_dict.keys())
        tasks = list(product(factors_times, trading_date_groups))
        res_dict = dict(zip(self.time_intervals, [[] for i in self.time_intervals]))
        calc_num = self.execute_cpu_num
        result = []
        pool = Pool(calc_num)
        for singletask in tasks:
            result.append(
                pool.apply_async(func=self.get_em_for_singletask, args=(self.std_factor_value_dict, singletask, tasks)))
        result = [task_id.get() for task_id in result]
        pool.close()
        pool.join()
        for singleresult in result:
            for ticktime in singleresult:
                singleresult_singletime = singleresult[ticktime]
                res_dict[ticktime].append(singleresult_singletime)
        for ticktime in res_dict:
            res_dict[ticktime] = pd.concat(res_dict[ticktime]).sort_index()

        for single_exempt_date_pair in self.exempt_dates:
            sub_start_date, sub_end_date = single_exempt_date_pair[0], single_exempt_date_pair[1]
            for ticktime in res_dict:
                res_dict[ticktime].loc[sub_start_date:sub_end_date] = 0
        res_df = pd.DataFrame(res_dict)
        res = res_df.mean(axis=1)
        return res

    # 进行样本内的指标计算和测试
    def get_test_result_IS(self, ret_min):
        ret_min = ret_min.loc[str(self.start_date):str(self.end_date_IS)]
        ret_min_cumsum = ret_min.cumsum()
        repair_df = self.get_repare_time(ret_min_cumsum)
        ret_min_mean = ret_min.rolling(242 * 120, min_periods=242 * 120).mean() * 242 * 240
        ret_min_std = ret_min.rolling(242 * 120, min_periods=242 * 120).std() * np.sqrt(242 * 240)
        sr_min_insample = ret_min_mean / ret_min_std
        sr_min_insample.dropna(axis=0, how='all', inplace=True)
        indicators = {
            'insample_ret_anual': ret_min.loc[:str(self.end_date_IS)].mean() * 242 * 240,
            'insample_rolling_sr_mean': sr_min_insample.mean(),
            'insample_rolling_sr_std': sr_min_insample.std(),
            'insample_sr_sr': sr_min_insample.mean() / sr_min_insample.std(),
            'insample_max_repair_days': repair_df.max() / 242,
            'decay_rate_of_last_halfyear_sr': self.get_sr(
                ret_min.loc[str(self.firstdate_of_the_last_halfyear_IS):str(self.end_date_IS)]) / self.get_sr(
                ret_min.loc[:str(self.end_date_IS)]),
        }
        sub_testresult_IS = {}
        negative_effect_indicators = ['insample_rolling_sr_std', 'insample_max_repair_days']
        for singleindcator in indicators:
            if singleindcator in negative_effect_indicators:
                sub_testresult_IS.update(
                    {singleindcator: indicators[singleindcator] < self.thresholds_for_test[singleindcator]})
            else:
                sub_testresult_IS.update(
                    {singleindcator: indicators[singleindcator] > self.thresholds_for_test[singleindcator]})
        sub_testresult_IS_series = pd.Series(sub_testresult_IS)
        return sub_testresult_IS_series.sum() >= sub_testresult_IS_series.shape[0]

    def em_plot(self, min_em, uuid):
        plot_root = self.report_address + 'imag_{}_{}'.format(self.factor_name, uuid)
        if os.path.exists(plot_root) == False:
            os.mkdir(plot_root)
        temp = min_em.copy()
        related_years = sorted(list(set([i.year for i in temp.index.tolist()])))
        years_to_draw = []
        for singleyear in related_years:
            substartdate = singleyear * 10000 + 101
            subenddate = singleyear * 10000 + 1231
            subcompletedates = Dtk.get_trading_day(substartdate, subenddate)
            subcompletedates = [i for i in subcompletedates if i not in self.exempt_dates]
            subdatesindata = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in temp.index.tolist() if
                              int(dt.datetime.strftime(i, '%Y%m%d')) in subcompletedates]
            if subdatesindata[0] == subcompletedates[0]:
                years_to_draw.append(singleyear)
        if len(years_to_draw) > 0:
            for singleyear in years_to_draw:
                substartdate = singleyear * 10000 + 101
                subenddate = singleyear * 10000 + 1231
                substartdate_str = str(substartdate)
                subenddate_str = str(subenddate)
                sub_em = min_em.loc[substartdate_str:subenddate_str]
                sub_nav = sub_em.cumsum()
                sub_nav_values = sub_nav.values
                plt.plot(sub_nav_values, label=str(singleyear))
            plt.xlabel('time')
            plt.ylabel('excess_mean')
            plt.title(self.factor_name)
            plt.axhline(y=0, ls=":", c="gray")  # 添加水平直线
            plt.legend()
            plt.savefig('{}/{}.jpg'.format(plot_root, self.factor_name))
            plt.close()

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
        keys = list(self.factor_distribution_dct['rawfactor_distribution'].index)
        result.append([' ', 'Factor Raw', 'Factor Neutralized'])
        for item in keys:
            result.append(
                [item,
                 round(self.factor_distribution_dct['rawfactor_distribution'].loc[item], 5),
                 round(self.factor_distribution_dct['neuedfactor_distribution'].loc[item], 5)])
        return result

    def _dic2list_ic(self):
        result = []
        keys = list(self.ic_stats_dct['neued'].index)
        result.append([' ', 'Factor Neutralized'])
        for item in keys:
            result.append([item, round(self.ic_stats_dct['neued'].loc[item], 5)])
        return result

    def __pdf_output(self, min_em):
        uuid0 = str(uuid.uuid1())
        self.em_plot(min_em, uuid0)
        img_path = self.report_address + 'imag_{}_{}/{}.jpg'.format(self.factor_name, uuid0, self.factor_name)
        abs_address = self.report_address

        doc = SimpleDocTemplate(
            abs_address + 'FactorBacktest_' + self.factor_name + '_' + str(
                self.report_timestamp.strftime("%Y%m%d_%H%M%S")) + '.pdf', rightMargin=40, leftMargin=20, topMargin=50,
            bottomMargin=20)
        style_type = getSampleStyleSheet()
        style_type.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        story = []
        story.append(Paragraph(self.factor_name + ' test', style_type['Title']))
        story.append(Spacer(1, 24))
        text_data = '<font size=9.5>%s</font>' % time.ctime()
        text_data = 'Report date : ' + text_data
        story.append(Paragraph(text_data, style_type['Normal']))
        story.append(Spacer(1, 24))
        text_data = 'Factor Information'
        story.append(Paragraph(text_data, style_type['Justify']))
        story.append(Spacer(1, 12))
        dic = {
            'Factor_Name': self.factor_name,
            'Test_Period': str(self.start_date_orignal) + ' --> ' + str(self.end_date),
            'Stock Universe': self.universe,
            'Date Count': Dtk.get_trading_day(self.start_date_orignal, self.end_date).__len__(),
        }
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

        text_data = 'Cumulative excess return of each year'
        story.append(Paragraph(text_data, style_type['Justify']))
        story.append(Spacer(1, 24))
        im = Image(img_path, 6.5 * inch, 3.125 * inch)
        story.append(im)
        doc.build(story)
        pass

    def corr_old_factors(self, min_em, start_date, end_date):
        # 计算与已入库所有因子的相关性
        factorsinlib_minem = self.hedged_df.loc[str(start_date):str(end_date)]
        corr_series = factorsinlib_minem.loc[str(start_date):str(end_date)].corrwith(
            min_em.loc[str(start_date):str(end_date)])
        corr_series_abs = corr_series.abs()
        return corr_series_abs

    # 测试因子的相关性
    def func_check_corr(self, min_em):
        max_corr_series = self.corr_old_factors(min_em, self.start_date, self.end_date_IS)
        max_correlation_threshold = self.max_correlation_threshold
        corrfactorspk_result = 0
        if max_corr_series.max() < max_correlation_threshold:
            unqualified_corr_factors = []
        else:
            unqualified_corr_factors = max_corr_series[max_corr_series >= max_correlation_threshold].index.tolist()
        unqualified_corr_factors = list(set(unqualified_corr_factors))
        corrflag = unqualified_corr_factors.__len__() == 0
        return (corrflag, corrfactorspk_result)

    @staticmethod
    def get_sr(item):
        sr = item.mean() * (242 * 240) / (item.std() * np.sqrt(242 * 240))
        return sr

    @staticmethod
    def get_repare_time(ret_cumsum):
        ret_cumsum_copy = ret_cumsum.copy()
        ret_cummax = ret_cumsum.cummax()
        not_greater_than_pre_max = ((ret_cumsum_copy - ret_cummax) < 0)
        not_greater_than_pre_max_cumsum = not_greater_than_pre_max.cumsum()
        a = not_greater_than_pre_max_cumsum.copy()
        b = a.copy()
        b[not_greater_than_pre_max] = np.nan
        b.fillna(method='ffill', inplace=True)
        ans = a - b
        return ans

    @staticmethod
    def get_corr(x, y, axis=0, method='pearson'):
        x = x.copy()
        y = y.copy()
        if axis == 1:
            x = x.T
            y = y.T
        elif axis == 0:
            pass
        else:
            raise Exception('wrong axis input')

        if method == 'spearman':
            x = x.rank(axis=0)
            y = y.rank(axis=0)
        elif method == 'pearson':
            pass
        else:
            raise Exception('wrong method input')
        # 转换成数组
        columns_bcp = x.columns.tolist()
        x = x.values
        y = y.values
        common_nan = (np.isnan(x) == True) | (np.isnan(y) == True)

        x[common_nan] = np.nan
        y[common_nan] = np.nan
        a = x - np.nanmean(x, axis=0)
        b = y - np.nanmean(y, axis=0)
        c = np.nanmean(a * b, axis=0) / (np.nanstd(a, axis=0, ddof=0) * np.nanstd(b, axis=0, ddof=0))
        return pd.Series(c, index=columns_bcp)

    # 获取因子的原始值分布和中性化后值的分布
    def get_factors_distribution(self):
        ## 原始值分布
        rawfactor_distributions_dct = {}
        for singletime in self.time_intervals:
            factor_value_singletime = self.factor_value_dict['Fix{}_{}'.format(singletime, self.factor_name)]
            rawfactor_distribution_singletime = factor_distribution_calc2(factor_value_singletime)
            rawfactor_distributions_dct.update({singletime: rawfactor_distribution_singletime['factor_distribution']})
        rawfactor_distribution = pd.DataFrame(rawfactor_distributions_dct).mean(axis=1)
        ## 中性化值分布
        neuedfactor_distributions_dct = {}
        for singletime in self.time_intervals:
            neuedfactor_singletime = self.std_factor_value_dict[singletime]
            neuedfactor_distribution_singletime = factor_distribution_calc2(neuedfactor_singletime)
            neuedfactor_distributions_dct.update(
                {singletime: neuedfactor_distribution_singletime['factor_distribution']})
        neuedfactor_distribution = pd.DataFrame(neuedfactor_distributions_dct).mean(axis=1)
        self.factor_distribution_dct = {
            'rawfactor_distribution': rawfactor_distribution,
            'neuedfactor_distribution': neuedfactor_distribution
        }

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

    # 获取因子IC时序的分布特征
    def get_factors_IC_stat(self):
        icstats_times = {}
        for singletime in self.time_intervals:
            factoric_singletime = self.factors_ic_dict[singletime]
            ic_stat_singletime = self.ic_stat_calc(factoric_singletime, 'IC')
            icstats_times.update({singletime: ic_stat_singletime['IC']})

        icstats = pd.DataFrame(icstats_times).mean(axis=1)
        self.ic_stats_dct = {
            'neued': icstats
        }

    def launch_test(self):
        self.load_data_buffer()
        self.load_label()
        self.factor_processing()
        # self.get_factors_distribution()
        # self.get_factors_IC_stat()
        min_em = self.get_factors_em()
        qualifiedflag_IS = self.get_test_result_IS(min_em)
        corrflag, corrfactorspk_result = self.func_check_corr(min_em)
        # self.__pdf_output(min_em)
        flag = qualifiedflag_IS * corrflag
        # print("Generating pdf report...")
        for_reason = {
            'qualifiedflag_IS': qualifiedflag_IS,
            'corrflag': corrflag

        }
        return {"factor": self.factor_name, "flag": flag, "reason": for_reason, "team": "stock_trade"}
