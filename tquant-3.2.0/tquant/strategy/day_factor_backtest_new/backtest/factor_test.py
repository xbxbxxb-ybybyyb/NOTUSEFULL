import matplotlib

matplotlib.use('Agg')
import os
import pandas as pd
import numpy as np
import tquant.strategy.day_factor_backtest_new.util.dt as tdt
from tquant.strategy.day_factor_backtest_new.util.utility import pprint
from tquant.strategy.day_factor_backtest_new.IO.IO import str_date_parser
from tquant.strategy.day_factor_backtest_new.index_calc.regression_index_calc import regression_analysis
from tquant.strategy.day_factor_backtest_new.index_calc.statistical_index_calc import turnover_calc, \
    factor_distribution, factor_score_correlation_calc, summary_table, collinear_test
from tquant.strategy.day_factor_backtest_new.index_calc.evaluative_index_calc import alpha_decay_test, calc_factor_ic, \
    calc_ic_stats, calc_ic_duration_test, calc_ic_by_industry, get_prod_ret
from tquant.strategy.day_factor_backtest_new.data.data_preprocess import standard_process, regression_ols
from tquant.strategy.day_factor_backtest_new.data.data_manager import DataManager
from tquant.strategy.day_factor_backtest_new.index_calc.return_index_calc import compute_sampling_ret_stat, \
    compute_calmar_ratio_half_year
from tquant.strategy.day_factor_backtest_new.index_calc.industry_index_calc import calc_hhi
from tquant.strategy.day_factor_backtest_new.index_calc.segment_index_calc import find_er_ls_col, segment_test, \
    segment_performance_measure, compute_top_excess_return, segment_test_by_industry, calc_segment_rank
from collections import OrderedDict
from tquant.strategy.day_factor_backtest_new.util.naming_config import *
from tquant import tq_logger
from tquant import BasicData, StockData

universe_dict = {'sz50': 'index_50', 'hs300': 'index_300', 'zz500': 'index_500',
                 'zz800': 'index_800', 'zz1000': 'index_1000',
                 'risk_universe': 'risk_universe',
                 'alpha_universe': 'alpha_universe'}
benchmark_set = ['zz500', 'sz50', 'hs300', 'zz800', 'zz1000']  # ,'wind_alla'] , 'zz800'
prev_len = 20  # for holding period return
corr_len = 60  # style correlation


class SingleFactorTest:
    """
    easy backtest: no factor neutralization, standardization, fillTS, etc...
    """

    def __init__(self, start_date=20160101, end_date=20181231, holding_period=5, benchmark='zz500',
                 universe='alpha_universe', segment_number=15, neutral_list=['Size', 'Industry'], fillna=False,
                 easy_test=False, seg_by_industry=False, seg_benchmark=None, provided_data=None, robust_segment=False,
                 transaction_cost=0.0013, industry_type='CITIC_I', interest_type='SIMPLE', seg_ic=0.5,
                 ic_type='score_weighted', compare_style='Size', ret_price='close', ret_shift=False, median=True,
                 standard=True, neutralize=True):
        self.start_date = str_date_parser(start_date)
        self.end_date = str_date_parser(end_date)
        self.start_date_str = start_date
        self.end_date_str = end_date
        self.holding_period = holding_period
        self.benchmark = benchmark.lower()
        self.universe = universe.lower()
        self.segment_number = segment_number
        self.seg_benchmark = seg_benchmark if seg_benchmark is not None else self.benchmark
        self.neutral_list = list(neutral_list)
        self.fillna = fillna
        self.easy_test = easy_test
        self.neutralize = neutralize
        self.robust_segment = robust_segment
        self.seg_by_industry = seg_by_industry
        self.transaction_cost = transaction_cost if transaction_cost != 0 else None
        self.industry_type = industry_type
        self.interest_type = interest_type
        self.seg_ic = seg_ic
        self.ic_type = ic_type
        self.compare_style = compare_style
        self.ret_price = ret_price
        self.ret_shift = ret_shift
        self.factor_data = None
        self.bd = BasicData()
        self.sd = StockData()
        self.date = self.bd.get_trading_day(end_date, -5)[-1]
        self.stock_list = self.sd.get_plate_info('MARKET', self.date, 'ALLA_HIS')['stock'].tolist()
        self.date_list = self.bd.get_trading_day(str(start_date), str(end_date))
        self.excess_return_dict = {}
        self.median = median
        self.standard = standard

        self.logger = tq_logger

        # stage variables
        self.name = None
        self.standardized_data = None
        self.neutralized_data = None
        self.base_data = dict()
        self._data = dict()  # new factor backtest would aligned to this variable

        self.prev_start_date = max(tdt.get_trading_day_offset(self.start_date, -prev_len)[0], pd.Timestamp(20090105))
        self.bmk_map = 'open' if self.ret_price == 'open' else 'close'
        self.bmk_name = 'bmk_price_{0}_{1}'.format(self.benchmark, self.bmk_map)
        self.price_name = '{0}_adj'.format(self.ret_price)
        self.hpr_name = 'hpr_{0}_{1}'.format(self.holding_period, self.ret_price)

        if self.holding_period == 1:
            self.ret_shift = True

        if provided_data is not None:
            # check data 
            provide_date_list = provided_data['close_adj'].index.tolist()
            sdate_p, edate_p = provide_date_list[0], provide_date_list[-1]
            if sdate_p <= self.start_date and edate_p >= self.end_date:
                self.base_data = provided_data
            else:
                print('provide data wrong - check date')
                print('backtest range: %s - %s \n provide range: %s - %s'
                      % (str(self.start_date), str(self.end_date), str(sdate_p), str(edate_p)))
                raise Exception
        else:
            self.load_data()
            # pd.to_pickle(self.base_data,"data_dict_alpha_universe.pkl")
            # self.base_data = pd.read_pickle("data_dict_alpha_universe.pkl")

        self.ret_handle()  # process return

    @property
    def data(self):
        return self._data

    def ret_handle(self):
        pprint('Process holding period return & benchmark')

        shift_str = '_shift' if self.ret_shift else ''
        self.bmk_use = self.bmk_name + shift_str  # 下一个交易日的benchmark数据
        self.price_use = self.price_name + shift_str
        self.hpr_use = self.hpr_name + shift_str
        self.base_data[self.hpr_name] = self.base_data[self.price_name].shift(-1 * self.holding_period) / \
                                        self.base_data[self.price_name] - 1
        self.base_data[self.hpr_name][~self.base_data['stock_filter_' + str(self.universe)]] = np.nan

        # self.bmk_name: bmk_price_alpha_universe_close
        # 此分支不走
        # if self.bmk_name not in list(self.base_data.keys()):
        #     pprint('Reload bechmark price')
        #     if self.benchmark in universe_set and self.benchmark == self.universe:
        #         # daily return average - return2price - dummy price
        #         stk_ret = self.base_data[self.price_name] / self.base_data[self.price_name].shift(1) - 1  # fix
        #         universe_ret = stk_ret[self.base_data['stock_filter_' + str(self.universe)].reindex(index=stk_ret.index,
        #                                                                                             columns=stk_ret.columns).fillna(
        #             value=False)].mean(axis=1)
        #         benchmark_price = (universe_ret + 1).cumprod()  # benchmark为股票池每天的平均收益
        #     else:
        #         pass
        #         # if self.benchmark in benchmark_set:
        #         #     h5_index = IO.read_data([self.prev_start_date, self.end_date], bmk_map[self.ret_price],
        #         #                             ftype=FType.MD, dtype=DType.INDEX, dsource=DSource.WIND)
        #         #     benchmark_price = h5_index.unstack()[bmk_map[self.ret_price]][index_lookup[self.benchmark]]#股价？收益率？
        #         # else:
        #         #     print('benchmark wrong: %s' % (self.benchmark))
        #         #     raise Exception
        #     self.base_data[self.bmk_name] = benchmark_price

        if self.ret_shift:
            self.base_data[self.price_use] = self.base_data[self.price_name].shift(-1)
            self.base_data[self.hpr_use] = self.base_data[self.hpr_name].shift(-1)
            self.base_data[self.bmk_use] = self.base_data[self.bmk_name].shift(-1)

    def load_data(self):
        dm = DataManager(start_date=self.start_date_str, end_date=self.end_date_str, price_use=self.ret_price,
                         universe=self.universe, holding_period=self.holding_period, ret_shift=self.ret_shift,
                         ic_type=self.ic_type, industry_type=self.industry_type, benchmark=self.benchmark)

        data_dict = dict()
        pprint('Loading data: %s - %s' % (self.start_date, self.end_date))

        pprint('Getting stock filter data')
        data_dict['stock_filter_' + str(self.universe)] = dm.get_stock_filter_data()

        pprint('Getting return data')
        # md_list = ['close', 'adjfactor', 'open', 'vwap']
        # md_dict = {s: IO.read_data([self.prev_start_date, self.end_date], [s], ftype=FType.MD, dsource=DSource.WIND)[
        #    s].unstack() for s in md_list}
        md_dict = {}
        # SJL
        self.logger.debug(
            "prev_start_date {} and end_date {} and stock numbers {}".format(self.prev_start_date.strftime("%Y%m%d"),
                                                                             self.end_date.strftime("%Y%m%d"),
                                                                             len(self.stock_list)))

        data_dict['%s_adj' % self.ret_price] = dm.get_price_use_data()

        pprint('Getting benchmark data')

        data_dict[self.bmk_name] = dm.get_benchmark_data()
        self.logger.debug("{0}的benchmark_price为：{1}".format(self.benchmark, data_dict[self.bmk_name]))
        # SJL
        pprint('Getting style and industry data')
        # # load basic data regardless easy backtest
        # style_dict = {}
        # style_list = IO.get_available_cols(ftype=FType.RISK, dsource=DSource.STYLEFACTOR)
        #
        # for s in style_list:
        #     style_dict[s] = IO.read_data([self.start_date, self.end_date], ftype=FType.RISK,
        #                                  dsource=DSource.STYLEFACTOR, columns=[s], max_workers=1)[s].unstack()
        # data_dict['neutral_dict'] = {item: style_dict[item] for item in list(set(self.neutral_list + ['Industry']))}
        # data_dict['style_dict'] = style_dict
        #
        # pprint('Getting industry by user defined type')
        # user_industry = IO.read_data([self.start_date, self.end_date], columns=self.industry_type,
        #                              dsource=DSource.WIND, ftype=FType.INDUSTRY)
        # data_dict['user_industry'] = user_industry[self.industry_type].unstack()

        data_dict['user_industry'] = dm.get_industry_data()

        # bie barra因子暂不上线
        # data_dict['style_dict'] = tmp_dict['style_dict']
        # data_dict['neutral_dict'] = tmp_dict['neutral_dict']

        # 跟入参neutral_list有关，风格因子
        data_dict['neutral_dict'] = {}
        data_dict['neutral_dict']['Size'] = dm.get_size_data()
        data_dict['neutral_dict']['Industry'] = data_dict['user_industry']

        pprint('Getting industry weight data')
        # normalized to 1.0
        # 行业权重归一化，行业权重等于行业内股票市值和的权重
        data_dict['industry_weight_' + self.seg_benchmark] = dm.get_industry_weight_data()
        stock_weight = dm.get_stock_weight_data()
        data_dict['stock_weight'] = stock_weight[stock_weight.columns[0]].unstack()
        benchmark_price = data_dict[self.bmk_name]
        # bie 基准昨日收益率
        day_benchmark_ret_series = benchmark_price / benchmark_price.shift(1) - 1
        day_benchmark_ret_series.replace([np.inf, -np.inf], 0.0, inplace=True)  # 收益率为inf时替换为0
        self.day_benchmark_ret = day_benchmark_ret_series.loc[pd.Timestamp(self.date)]
        self.logger.debug("计算基准昨日收益率为：{0}".format(self.day_benchmark_ret))
        # 基准上周收益率
        week_benchmark_ret_series = benchmark_price / benchmark_price.shift(5) - 1
        week_benchmark_ret_series.replace([np.inf, -np.inf], 0.0, inplace=True)
        self.week_benchmark_ret = week_benchmark_ret_series.loc[pd.Timestamp(self.date)]
        self.logger.debug("计算基准上周收益率为：{0}".format(self.week_benchmark_ret))
        # 基准上月收益率
        month_benchmark_ret_series = benchmark_price / benchmark_price.shift(21) - 1
        month_benchmark_ret_series.replace([np.inf, -np.inf], 0.0, inplace=True)
        self.month_benchmark_ret = month_benchmark_ret_series.loc[pd.Timestamp(self.date)]
        self.logger.debug("计算基准上月收益率：{0}".format(self.month_benchmark_ret))
        self.base_data = data_dict

    def shoot(self, result_folder, module):
        # do something useful
        pprint('* Factor backtest - %s *' % (self.name))
        output_folder = os.path.join(result_folder, self.name + '/')
        self.pickle_name = os.path.join(output_folder, 'FactorBacktest_' + str(self.name) + '.pkl')

        if not os.path.exists(output_folder):
            pprint("Output location: " + output_folder)
            os.makedirs(output_folder)

        if not self.easy_test:
            # 做了数据清洗：中位数过滤，(x-均值)/标准差
            self.data['factor_data'], self.standardized_data = \
                standard_process(factor_data=self.data['factor_data'],
                                 stock_filter_df=self.data['stock_filter_' + str(self.universe)],
                                 stock_industry_df=self.data['neutral_dict']['Industry'],
                                 fillna=self.fillna, median=self.median, standard=self.standard,
                                 boxskew=False)
            # pprint('Collinear backtest')
            # factor_corr =  collinear_test(standardized_data=self.standardized_data, neutral_dict=self.data['neutral_dict'])
            pprint('Regression analysis')
            # regression_output = regression_analysis(standardized_data=self.standardized_data,
            #                                         neutral_dict_df=self.data['neutral_dict'],
            #                                         holding_period_ret=self.data[self.hpr_use],
            #                                         ic_type=sellf.ic_type)#bie 去掉
            # regression_stats = self.regression_stats_process(regression_output, neutral_list=self.neutral_list,
            #                                                  name=self.name)#bie 去掉
            # ic_ts_combined['IC Neutralized'] = regression_output['IC']#bie 去掉
            if self.neutralize:
                self.neutralized_data, r2, _, _ = regression_ols(self.standardized_data,
                                                                 self.data['neutral_dict'])
                factor_data = self.neutralized_data
            else:
                factor_data = self.standardized_data
            # _, _, beta, tstats = regression_ols(self.data[self.hpr_use], {'resid': self.neutralized_data})

            # factor_data = self.neutralized_data  # 从regression_analysis中获取行业中性化数据
        else:
            factor_data = self.data['factor_data']

        # ic_ts_combined['IC_top_quantile'] = quantile_ic(factor_data, self.data[self.hpr_use],1 - 1/self.segment_number, 1)

        if not self.easy_test:
            pass
            # correlation with style factors
            # bie barra因子暂不上线
            # pprint('Collinear backtest')
            # style_list = list(self.data['style_dict'].keys())
            #
            # style_list.sort()
            # style_corr_pd = calc_corr(factor_data, self.data['style_dict'])[style_list]

            # pprint('Style correlation backtest')
            # ic_ts_style = calc_ic_dict(self.data['style_dict'], self.data[self.hpr_use], ic_type=self.ic_type)
            # ic_style_corr = calc_ts_corr(ic_ts_combined['IC Original'], ic_ts_style, roll_win=corr_len)[style_list]

        if not self.easy_test:
            pass
            # output_dict['factor_corr'] = factor_corr
            # output_dict['regression_output'] = regression_output
            # output_dict['regression_stats'] = regression_stats

            # bie barra因子暂不上线
            # output_dict['style_corr'] = style_corr_pd
            # output_dict['ic_style_corr'] = ic_style_corr

        pprint('============Start Backtest Analysis:{}==========.'.format(module))
        self.output_dict = {}
        if not module:
            module = 'complete'
        if not isinstance(module, str):
            raise Exception("请输入正确格式的module,目前仅支持")
        if module == "basic":
            comment = ['basic']
        elif module == "basic_stability":
            comment = ['basic', 'stability']
        elif module == "basic_segment":
            comment = ['basic', 'segment']
        elif module == "basic_seg_stab":
            comment = ['basic', 'segment', 'stability']
        elif module == "industry":
            comment = ['basic', 'segment', 'industry']
        elif module == "complete":
            comment = ['basic', 'segment', 'industry', 'stability']
        else:
            raise Exception("目前仅支持'basic', 'segment','basic_stability', 'basic_seg_stab' ,'industry', 'complete'四种格式的回测报告，暂不支持{}".format(module))

        if 'basic' in comment:
            # calculate average turnover
            pprint("Calc Average Turnover")
            # 计算因子值隔天从后10%变成前90%或从前90%变成10%转换
            self.avg_turnover = round(turnover_calc(self.factor_data), 5)
            self.logger.debug("avg_turnover: {0}".format(self.avg_turnover))

            # 因子回测评价的基本信息汇总
            pprint("Calc Summary Info")
            sum_df = summary_table(factor_data=self.data['factor_data'], factor_name=self.name,
                                   universe=self.universe, holding_period=self.holding_period,
                                   avg_turnover=self.avg_turnover, benchmark=self.benchmark,
                                   segment_number=self.segment_number, standard=self.standard,
                                   median=self.median, fillna=self.fillna, seg_by_industry=self.seg_by_industry,
                                   transaction_cost=self.transaction_cost, industry_type=self.industry_type,
                                   interest_type=self.interest_type, ic_type=self.ic_type,
                                   compare_style=self.compare_style, ret_price=self.ret_price,
                                   ret_shift=self.ret_shift)

            self.logger.debug("因子评价基本信息汇总：\n{0}".format(sum_df))
            pprint("Calc Distribution Info")
            factor_coverage_ts = pd.DataFrame([np.isfinite(self.data['factor_data']).sum(axis=1)],
                                              index=['Stock Number']).T  # 每日有值股票数汇总
            factor_dist = factor_distribution(factor_data=self.data['factor_data'],
                                              stock_filter_df=self.data['stock_filter_' + str(self.universe)])

            pprint('Calc Auto correlation and IC')
            factor_auto_correlation = factor_score_correlation_calc(factor_data)  # Pearson和Spearman
            ic_decay, alpha_cumsum = alpha_decay_test(factor_data,
                                                      holding_period_return=self.data[self.hpr_use])  # alpha_cumsum未用到
            self.logger.debug("ic_decay:\n{0}".format(ic_decay))
            ic_duration = calc_ic_duration_test(factor_data, price_use_data=self.data[self.price_use],
                                                ic_type=self.ic_type)  # 因子值与过去5天，3天，未来3天，5天的收益率的相关性
            self.logger.debug("ic_duration:\n{0}".format(ic_duration))

            # bie barra因子暂不上线
            # ic_contextual_ts = calc_context_ic(factor_data, self.data[self.price_use], self.holding_period,
            #                                    self.data['style_dict'], seg_ic=self.seg_ic, add_own=True)
            # ic_contextual_stats = calc_ic_stats(ic_contextual_ts)
            # 计算 标准化后的因子数据与复权的ret_price的增长率的相关性
            ic_ts_combined = pd.DataFrame()

            ic_ts_combined['IC Original'] = self.data['factor_data'].corrwith(self.data[self.hpr_use], axis=1)

            ic_ts_combined['IC Score Weighted'] = calc_factor_ic(factor_data, self.data[self.hpr_use],
                                                                 ic_type='score_weighted')  # sjl统一ic类型
            ic_stats = calc_ic_stats(ic_ts_combined)
            self.logger.debug("ic_stats:\n{0}".format(ic_stats))
            # bie 历史IC平均值
            self.IC = ic_stats.loc['IC Mean', 'IC Original']
            self.IR = ic_stats.loc['ICIR', 'IC Original']

            self.output_dict.update({
                'summary_info': sum_df,
                'distribution': factor_dist,
                'stock_count': factor_coverage_ts,
                'factor_auto_correlation': factor_auto_correlation,
                'ic_stats': ic_stats,
                'ic_ts_combined': ic_ts_combined,
                'ic_decay': ic_decay,
                'alpha_cumsum': alpha_cumsum,
                'ic_duration': ic_duration,
            })

        if 'segment' in comment:
            pprint('Segment analysis')
            _ = segment_test(factor_data, self.data[self.price_use], self.holding_period,
                             self.data[self.bmk_use], self.segment_number,
                             handle_return_outlier=self.robust_segment, transaction_cost=self.transaction_cost)
            if not self.transaction_cost:
                seg_return = _
                self.output_dict.update({
                    'seg_return': seg_return
                })
            else:
                seg_return, seg_return_after_cost = _[0], _[1]
                self.output_dict.update({
                    'seg_return': seg_return_after_cost,
                })
            # 为前端展示提供指标
            self.get_new_target(self.output_dict)

        if 'industry' in comment:
            pprint('Segment analysis by industry')
            stk_weight = None if self.benchmark in ['alpha_universe', 'risk_universe'] else self.data['stock_weight']
            seg_tmp = segment_test_by_industry(factor_data, self.data[self.price_use], self.holding_period,
                                               self.data[self.bmk_use], self.segment_number,
                                               self.data['neutral_dict']['Industry'],
                                               self.data['industry_weight_' + self.seg_benchmark],
                                               transaction_cost=self.transaction_cost,
                                               return_industry=self.seg_by_industry,
                                               stock_weight=stk_weight)

            if self.transaction_cost is None:
                seg_return, seg_return_each_industry = seg_tmp[0], seg_tmp[1]
                self.output_dict.update({
                    'seg_return': seg_return,
                    'seg_return_each_industry': seg_return_each_industry
                })
            else:
                seg_return, seg_return_after_cost, seg_return_each_industry, segret_by_ind_after_cost = \
                    seg_tmp[0], seg_tmp[1], seg_tmp[2], seg_tmp[3]
                self.output_dict.update({
                    'seg_return': seg_return,
                    'seg_return_each_industry': segret_by_ind_after_cost
                })
            # 为前端展示提供指标
            self.get_new_target(self.output_dict)

        if 'segment' in comment:
            pprint('Segment analysis')
            from functools import partial
            calc_seg_measure = partial(segment_performance_measure, interest_type=self.interest_type)

            # # TODO：seg_by_industry为True时将seg_return值覆盖，仅max_quantile值后续用到，待优化分支
            # ls_col, max_quantile, min_quantile = find_er_ls_col(
            #     seg_return)  # check max_quantile for segment by industry usage

            seg_return = self.output_dict['seg_return'].copy()
            use_ind = np.isfinite(seg_return).sum(axis=1) > 2
            seg_return_stat_year = seg_return.loc[use_ind].groupby(seg_return.loc[use_ind].index.year).apply(
                calc_seg_measure)
            self.logger.debug("seg_return_stat_year:\n{0}".format(seg_return_stat_year))
            pprint('Segment Performance Measure ({})'.format(self.compare_style))
            seg_return_stat = segment_performance_measure(seg_return, self.interest_type)
            self.logger.debug("seg_return_stat:\n{0}".format(seg_return_stat))
            pprint("Calc Segment Rank")
            market_rank = calc_segment_rank(seg_return=seg_return, holding_period_ret=self.data[self.hpr_use],
                                            holding_period=self.holding_period, segment_number=self.segment_number)

            self.output_dict.update({
                'seg_return_stat_year': seg_return_stat_year,  # 年化Sharp，年化收益率
                'seg_return_stat': seg_return_stat,
                'market_rank': market_rank
            })
            if self.factor_data.shape[0] > 250:
                _ = segment_test(self.data['neutral_dict'][self.compare_style], self.data[self.price_use],
                                 self.holding_period,
                                 self.data[self.bmk_use], self.segment_number,
                                 handle_return_outlier=self.robust_segment, transaction_cost=self.transaction_cost)
                if self.transaction_cost:
                    seg_return_fac, seg_return_after_cost_fac = _[0], _[1]
                    self.output_dict.update({
                        'seg_return_fac': seg_return_after_cost_fac
                    })
                else:
                    seg_return_fac = _
                    self.output_dict.update({
                        'seg_return_fac': seg_return_fac
                    })

        if 'industry' in comment:
            pprint('Calc IC by industry')
            ic_ind_pd = calc_ic_by_industry(factor_data, self.data[self.hpr_use], self.data['user_industry'],
                                            self.ic_type)

            if self.industry_type == 'CITIC_I':
                ind_map = CITIC_I_mapper

            elif self.industry_type == 'KNN_I':
                ind_map = KNN_I_mapper
            else:
                ind_map = None
            ic_ind_pd = ic_ind_pd.rename(columns=ind_map) if ind_map is not None else ic_ind_pd

            pprint('Calc Seg Return by industry')
            # SJL 无须指定max_quantile

            # SJL 若按行业分层，则seg_return代表行业加权权重，而seg_return_ew代表无行业加权的分层。
            seg_return_each_industry = self.output_dict['seg_return_each_industry'].copy()
            seg_return_each_industry_stat_dict = {}
            from functools import partial
            calc_seg_measure = partial(segment_performance_measure, interest_type=self.interest_type)
            ind_list = list(set(seg_return_each_industry.index.get_level_values(level=1)))
            for i in ind_list:
                try:
                    seg_return_each_industry_stat_dict.update(
                        {i: calc_seg_measure(seg_return_each_industry.xs(i, level=1))})
                except:
                    continue
            seg_return_each_industry_stat = pd.concat(seg_return_each_industry_stat_dict, axis=0)
            seg_return_each_industry_stat.index.names = ['Industry', 'Segment']
            self.output_dict.update({
                'seg_return_each_industry_stat': seg_return_each_industry_stat

            })
            # bie calc_seg_measure是segment_performance_measure函数固定了interest_type参数的对象，所以只能传入该函数的第一个参数
            # seg_return_each_industry_stat_dict = {i: calc_seg_measure(seg_return_each_industry.xs(i, level=1),
            #                                                           self.interest_type) for i in ind_list}

            # calc industry concentration
            pprint('Calc Industry Concentration')
            ind_col = [i for i in seg_return_each_industry.columns if i.find('Index') > 0][0]
            ind_excess_ret = seg_return_each_industry[ind_col].unstack()
            industry_concentration = calc_hhi(ind_excess_ret, positive_only=True)  # 产业集中度指标，各行业收益归一化后求平方和

            self.output_dict.update({
                'ic_by_industry': ic_ind_pd,
                'industry_concentration': industry_concentration
            })

            if self.factor_data.shape[0] > 250:
                stk_weight = None if self.benchmark in ['alpha_universe', 'risk_universe'] else self.data[
                    'stock_weight']
                seg_tmp_fac = segment_test_by_industry(self.data['neutral_dict'][self.compare_style],
                                                       self.data[self.price_use], self.holding_period,
                                                       self.data[self.bmk_use], self.segment_number,
                                                       self.data['neutral_dict']['Industry'],
                                                       self.data['industry_weight_' + self.seg_benchmark],
                                                       transaction_cost=self.transaction_cost,
                                                       return_industry=self.seg_by_industry,
                                                       stock_weight=stk_weight)
                if self.transaction_cost is None:
                    seg_return_fac, _ = seg_tmp_fac[0], seg_tmp_fac[1]  # seg_return vs seg_resutn_fac
                    self.output_dict.update({
                        'seg_return_fac': seg_return_fac
                    })
                else:
                    seg_return_fac, seg_return_after_cost_fac, _, _ = seg_tmp_fac[0], seg_tmp_fac[1], seg_tmp_fac[2], \
                                                                      seg_tmp_fac[3]
                    self.output_dict.update({
                        'seg_return_after_cost_fac': seg_return_after_cost_fac
                    })
        if "stability" in comment:
            pprint("Calc Sampling Ret Stat")
            excess_return = compute_top_excess_return(factor_data=self.data['factor_data'],
                                                      neutralized_data=self.neutralized_data,
                                                      standardized_data=self.standardized_data,
                                                      stock_close_pd=self.data[self.price_use],
                                                      benchmark_price_ps=self.data[self.bmk_use],
                                                      holding_period=self.holding_period,
                                                      transaction_cost=self.transaction_cost,
                                                      robust_segment=self.robust_segment)

            sample_stat = compute_sampling_ret_stat(excess_return)

            self.output_dict.update({
                'sample_bin_ret_mean': sample_stat[0],
                'sample_bins_ret_stat': sample_stat[1],
                'Calmar_half_year': compute_calmar_ratio_half_year(excess_return),
            })
            if self.factor_data.shape[0] > 250:
                self.output_dict.update({
                    'sample_std2ret': sample_stat[3],
                    'sample_bins_ret_diff2ret': sample_stat[2]
                })

    # 为前端展示指标用
    def get_new_target(self, output_dict: object) -> object:
        import collections
        show_dict = collections.OrderedDict()
        seg_return = output_dict['seg_return'].copy()
        show_dict['收益分析'] = seg_return
        sum_df = output_dict['summary_info']
        interest_type = sum_df['Settings2'].values[3]
        tr_list = ['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']
        show_dict_stat = {i: segment_performance_measure(show_dict[i], interest_type) for i in show_dict}
        seg_ret_sum_stats = pd.concat([show_dict_stat[i].iloc[-1] for i in show_dict_stat], axis=1).T
        seg_ret_sum_stats.index = list(show_dict.keys())
        seg_ret_sum_stats = seg_ret_sum_stats[tr_list]
        # 新增kafka输出指标 ['Return(Ann.)', 'Vol(Ann.)', 'Sharpe', 'MDD', 'HitRate']
        self.excess_return_dict['annReturn'] = seg_ret_sum_stats.iloc[0]['Return(Ann.)']
        self.excess_return_dict['annVol'] = seg_ret_sum_stats.iloc[0]['Vol(Ann.)']
        self.excess_return_dict['sharpe'] = seg_ret_sum_stats.iloc[0]['Sharpe']
        self.excess_return_dict['mdd'] = seg_ret_sum_stats.iloc[0]['MDD']
        self.excess_return_dict['hitRate'] = seg_ret_sum_stats.iloc[0]['HitRate']

        if int(self.holding_period) == 1:
            if self.ret_shift:
                pre_day = self.bd.get_trading_day(self.date, -5)[-3]
            else:
                pre_day = self.bd.get_trading_day(self.date, -5)[-2]
            try:
                # seg_return_after_cost
                day_ret_series = seg_return.loc[pd.Timestamp(pre_day)]
                self.day_segent_num = day_ret_series.idxmax()
                self.excess_return_dict['day_ret'] = day_ret_series.loc[self.day_segent_num]
            except:
                self.excess_return_dict['day_ret'] = ''
        else:
            self.excess_return_dict['day_ret'] = ''

        # 最近一周收益率
        if int(self.holding_period) < 5:
            pre_5_day = self.bd.get_trading_day(self.date, -5)[0]
        else:
            pre_5_day = self.bd.get_trading_day(self.date, -self.holding_period - 1)[0]
        try:
            week_ret_df = seg_return.loc[pd.Timestamp(pre_5_day):pd.Timestamp(self.date), :].copy()
            week_ret_df = get_prod_ret(week_ret_df)
            week_ret_series = week_ret_df.loc['prod'].copy()
            self.week_segent_num = week_ret_series.idxmax()
            self.excess_return_dict['week_ret'] = week_ret_series.loc[self.week_segent_num] - 1
        except:
            self.excess_return_dict['week_ret'] = ''
        # 最近一个月收益率
        if int(self.holding_period) < 21:
            pre_21_day = self.bd.get_trading_day(self.date, -21)[0]
        else:
            pre_21_day = self.bd.get_trading_day(self.date, -self.holding_period - 1)[0]
        month_ret_df = seg_return.loc[pd.Timestamp(pre_21_day):pd.Timestamp(self.date), :].copy()
        month_ret_df = get_prod_ret(month_ret_df)
        month_ret_series = month_ret_df.loc['prod'].copy()
        self.month_segent_num = month_ret_series.idxmax()
        self.excess_return_dict['month_ret'] = month_ret_series.loc[self.month_segent_num] - 1
