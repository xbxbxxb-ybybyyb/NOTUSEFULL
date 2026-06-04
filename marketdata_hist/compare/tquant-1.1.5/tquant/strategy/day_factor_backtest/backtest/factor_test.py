import matplotlib
matplotlib.use('Agg')
import os
import pandas as pd
import numpy as np
import scipy.stats as sps
import tquant.strategy.day_factor_backtest.utility.dt as tdt
from tquant.strategy.day_factor_backtest.backtest.utility import *
from tquant.strategy.day_factor_backtest.backtest.segment_test import segment_test,segment_performance_measure,segment_test_by_industry
from collections import OrderedDict
from tquant.strategy.day_factor_backtest.backtest.naming_config import *
from tquant import tq_logger
from tquant import BasicData
from tquant import StockData

universe_set = ['index_50', 'index_300', 'index_500', 'risk_universe', 'alpha_universe']#, 'index_800'
universe_dict = {'sz50':'index_50', 'hs300':'index_300', 'zz500':'index_500', 'risk_universe':'risk_universe','alpha_universe':'alpha_universe'}
index_lookup = {'zz500': '000905.SH', 'sz50': '000016.SH', 'hs300': '000300.SH',
                'wind_alla': '881001.WI'}# 'zz800': '000906.SH',
benchmark_set = ['zz500', 'sz50', 'hs300']  # ,'wind_alla'] , 'zz800'
bmk_map = {'close':'close','open':'open'}#sjl 暂不支持vwap
prev_len = 20  # for holding period return
corr_len = 60  # style correlation


class SingleFactorTest:
    """
    easy backtest: no factor neutralization, standardization, fillTS, etc...
    """

    def __init__(self, start_date=20160101, end_date=20181231, holding_period=5, benchmark='zz500',
                 universe='alpha_universe',
                 segment_number=15, neutral_list=['Size', 'Industry'], fillna=False, easy_test=False,
                 seg_by_industry=False, seg_benchmark=None, provided_data=None, robust_segment=False,
                 transaction_cost=0.0013, industry_type='CITIC_I', interest_type='SIMPLE', seg_ic=0.5,
                 ic_type='score_weighted', compare_style='Size', ret_price='close', ret_shift=True,
                 median=True, standard=True):
        if int(end_date) > 20190630:
            raise Exception('end_date should not exceed 20190630')

        self.start_date = str_date_parser(start_date)
        self.end_date = str_date_parser(end_date)
        self.start_date_str = start_date
        self.end_date_str = end_date
        self.holding_period = holding_period
        self.benchmark = benchmark
        self.universe = universe_dict.get(universe)
        self.segment_number = segment_number
        self.seg_benchmark = seg_benchmark if seg_benchmark is not None else self.benchmark
        self.neutral_list = list(neutral_list)
        self.fillna = fillna
        self.easy_test = easy_test
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
        if len(self.date_list) < 250:
            raise Exception("tradingday: date num less than 250 !")

        self.median = median
        self.standard = standard

        # stage variables
        self.name = None
        self.standardized_data = None
        self.neutralized_data = None
        self.base_data = dict()
        self._data = dict()  # new factor backtest would aligned to this variable

        self.prev_start_date = max(tdt.get_trading_day_offset(self.start_date, -prev_len)[0], pd.Timestamp(20090105))
        self.bmk_map = 'open' if self.ret_price == 'open' else 'close'
        self.bmk_name = 'bmk_price_%s_%s' % (self.benchmark, self.bmk_map)
        self.price_name = '%s_adj' % (self.ret_price)
        self.hpr_name = 'hpr_%d_%s' % (self.holding_period, self.ret_price)

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
            pd.to_pickle(self.base_data,"data_dict_alpha_universe.pkl")
            self.base_data = pd.read_pickle("data_dict_alpha_universe.pkl")
        self.ret_handle()  # process return

    @property
    def data(self):
        return self._data

    def ret_handle(self):
        pprint('Process holding period return & benchmark')

        shift_str = '_shift' if self.ret_shift else ''
        self.bmk_use = self.bmk_name + shift_str#下一个交易日的benchmark数据
        self.price_use = self.price_name + shift_str
        self.hpr_use = self.hpr_name + shift_str

        self.base_data[self.hpr_name] = self.base_data[self.price_name].shift(-1 * self.holding_period) / \
                                        self.base_data[self.price_name] - 1
        self.base_data[self.hpr_name][~self.base_data['stock_filter_' + str(self.universe)]] = np.nan
        
        #self.bmk_name: bmk_price_alpha_universe_close
        # 此分支不走
        if self.bmk_name not in list(self.base_data.keys()):
            pprint('Reload bechmark price')
            if self.benchmark in universe_set and self.benchmark == self.universe:
                # daily return average - return2price - dummy price
                stk_ret = self.base_data[self.price_name] / self.base_data[self.price_name].shift(1) - 1  # fix
                universe_ret = stk_ret[self.base_data['stock_filter_' + str(self.universe)].reindex(index=stk_ret.index,
                                                                                                    columns=stk_ret.columns).fillna(
                    value=False)].mean(axis=1)
                benchmark_price = (universe_ret + 1).cumprod()#benchmark为股票池每天的平均收益
            else:
                if self.benchmark in benchmark_set:
                    h5_index = IO.read_data([self.prev_start_date, self.end_date], bmk_map[self.ret_price],
                                            ftype=FType.MD, dtype=DType.INDEX, dsource=DSource.WIND)
                    benchmark_price = h5_index.unstack()[bmk_map[self.ret_price]][index_lookup[self.benchmark]]#股价？收益率？
                else:
                    print('benchmark wrong: %s' % (self.benchmark))
                    raise Exception
            self.base_data[self.bmk_name] = benchmark_price

        if self.ret_shift:
            self.base_data[self.price_use] = self.base_data[self.price_name].shift(-1)
            self.base_data[self.hpr_use] = self.base_data[self.hpr_name].shift(-1)
            self.base_data[self.bmk_use] = self.base_data[self.bmk_name].shift(-1)

    def load_data(self):
        data_dict = dict()
        pprint('Loading data: %s - %s' % (self.start_date, self.end_date))

        pprint('Getting return data')
        md_list = ['close', 'adjfactor', 'open', 'vwap']
        #md_dict = {s: IO.read_data([self.prev_start_date, self.end_date], [s], ftype=FType.MD, dsource=DSource.WIND)[
        #    s].unstack() for s in md_list}
        md_dict = {}
        #SJL
        tq_logger.debug("prev_start_date {} and end_date {} and stock numbers {}".format(self.prev_start_date.strftime("%Y%m%d"),
                       self.end_date.strftime("%Y%m%d"), len(self.stock_list)))
        for fac in md_list:
            sub_df = self.sd.get_factor_price_daily(self.stock_list, self.date_list,[fac], fill_na=True).iloc[:,0].unstack()
            sub_df.replace(0.0, np.nan, inplace = True)
            sub_df.fillna(method = 'ffill', inplace = True)
            sub_df.index.name = 'dt'
            sub_df.index = pd.DatetimeIndex(sub_df.index)
            md_dict[fac] = sub_df

        for p in ['close', 'open', 'vwap']:
            md_dict['%s_adj' % (p)] = md_dict[p] * md_dict['adjfactor']
            # 3个因子的复权
            data_dict['%s_adj' % (p)] = md_dict['%s_adj' % (p)]

        pprint('Getting stock filter data')
        if self.universe in universe_set:
            h5_filter = self.sd.get_factor_evaluation(self.stock_list, (self.start_date_str, self.end_date_str), [self.universe, 'filter_stpt'])
        else:
            h5_filter = self.sd.get_factor_evaluation(self.stock_list, (self.start_date_str, self.end_date_str),['filter_stpt'])
        for f in h5_filter.columns:
            if f in ['risk_universe', 'alpha_universe', 'filter_stpt', 'filter_suspend', 'listing_1yr',
                     'over_half_for_half_year', 'index_50', 'index_300', 'index_500']:
                h5_filter[f] = h5_filter[f].astype(int).astype(bool)
        h5_filter.reset_index(inplace=True)
        h5_filter.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
        h5_filter['dt'] = h5_filter['dt'].apply(pd.Timestamp)
        h5_filter.set_index(["dt", "Ticker"], inplace=True)
        h5_filter = h5_filter.fillna(value=False)

        # 对self.universe的股票进行stpt过滤
        if self.universe in universe_set:
            compound_filter = h5_filter[self.universe] & h5_filter['filter_stpt']
        else:
            compound_filter = h5_filter['filter_stpt']

        stock_filter = compound_filter.unstack().fillna(value=False)
        data_dict['stock_filter_' + str(self.universe)] = stock_filter

        pprint('Getting benchmark data')

        if self.benchmark in universe_set and self.benchmark == self.universe:
            # daily return average - return2price - dummy price
            # self.price_name的增长率
            stk_ret = data_dict[self.price_name] / data_dict[self.price_name].shift(1) - 1  # fix
            stk_ret.replace([np.inf, -np.inf], 0.0, inplace = True)#bug修复，收益率为inf时替换为0
            universe_ret = stk_ret[
                stock_filter.reindex(index=stk_ret.index, columns=stk_ret.columns).fillna(value=False)].mean(axis=1)#市场每日平均收益
            benchmark_price = (universe_ret + 1).cumprod()#市场每日累计收益
        else:
            # bie 切换数据源
            index_list = ['000300.SH', '000905.SH', '000016.SH']
            prev_date = self.prev_start_date.strftime('%Y%m%d')
            e_date = self.end_date.strftime('%Y%m%d')
            index_price = self.sd.get_factor_price_daily(index_list,(prev_date, e_date),['close'], fill_na=True)
            index_price.reset_index(inplace=True)
            index_price.rename(columns={'mddate': 'dt', 'stock': 'Ticker'}, inplace=True)
            index_price['dt'] = index_price['dt'].apply(pd.Timestamp)
            index_price.set_index(['dt', 'Ticker'], inplace=True)
            benchmark_price = index_price.unstack()['close'][index_lookup[self.benchmark]]
        data_dict[self.bmk_name] = benchmark_price

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

        user_industry = self.sd.get_factor_evaluation(self.stock_list, (self.start_date_str, self.end_date_str), [self.industry_type])
        user_industry.reset_index(inplace=True)
        user_industry.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
        user_industry['dt'] = user_industry['dt'].apply(pd.Timestamp)
        user_industry.set_index(["dt", "Ticker"], inplace=True)
        data_dict['user_industry'] = user_industry[self.industry_type].unstack()

        # bie barra因子暂不上线
        # data_dict['style_dict'] = tmp_dict['style_dict']
        # data_dict['neutral_dict'] = tmp_dict['neutral_dict']

        data_dict['neutral_dict'] = {}
        mkt_cap_data = self.sd.get_factor_valuation_metrics(self.stock_list, (self.start_date_str, self.end_date_str), ['mkt_cap_ard'])
        mkt_cap_data.reset_index(inplace=True)
        mkt_cap_data['mddate'] = mkt_cap_data['mddate'].apply(pd.Timestamp)
        mkt_cap_data.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
        mkt_cap_data.set_index(["dt", "Ticker"], inplace=True)
        mkt_cap_ard = mkt_cap_data['mkt_cap_ard'].unstack()
        lncap = np.log(mkt_cap_ard)
        Size = norm_winsor(lncap, bound=5)
        #跟neutral_list有关
        data_dict['neutral_dict']['Size'] = Size
        data_dict['neutral_dict']['Industry'] = data_dict['user_industry']


        pprint('Getting industry weight data')
        # assert self.seg_benchmark in ['hs300', 'zz500', 'sh50', 'alla']
        if self.seg_benchmark in ['hs300', 'zz500', 'sh50']:
            stock_weight = self.sd.get_factor_evaluation(self.stock_list, (self.start_date_str, self.end_date_str),
                                                      ['index_weight_' + self.seg_benchmark])
            stock_weight.reset_index(inplace=True)
            stock_weight.rename(columns={"mddate": "dt", "stock": "Ticker"}, inplace=True)
            stock_weight['dt'] = stock_weight['dt'].apply(pd.Timestamp)
            stock_weight.set_index(["dt", "Ticker"], inplace=True)
            stock_weight.columns = ['stock_weight']
        else:
            # mkt_cap_ard = IO.read_data([self.start_date, self.end_date], columns=['mkt_cap_ard'],
            #                            ftype=FType.MD, dsource=DSource.WIND)['mkt_cap_ard'].unstack()
            #sjl a按市值占全市场市场的比率，计算权重
            #TODO： 小bug，退市票需要去掉之后，再计算市值
            mkt_cap_ard = self.sd.get_factor_valuation_metrics(self.stock_list, self.date_list, ['mkt_cap_ard'], fill_na=True).iloc[:,0].unstack()
            mkt_cap_ard.index = pd.DatetimeIndex(mkt_cap_ard.index)
            mkt_cap_ard = mkt_cap_ard.reindex(index=stock_filter.index, columns=stock_filter.columns)
            mkt_cap_ard[~stock_filter] = np.nan
            mkt_cap_ard_MI = mkt_cap_ard.stack()
            stock_weight = pd.DataFrame(mkt_cap_ard_MI / mkt_cap_ard_MI.groupby('dt').sum())
            stock_weight.columns = ['stock_weight']
        _stock_industry = pd.DataFrame(data_dict['neutral_dict']['Industry'].stack(), columns=['Industry'])
        #计算行业内股票权重，每个行业权重未股票权重加和。stock_weight是全市场票的市值加权。
        weight_grouped = pd.concat([_stock_industry, stock_weight], axis=1).groupby(['dt', 'Industry'])
        industry_weight = weight_grouped['stock_weight'].sum()
        # normalized to 1.0
        #行业权重归一化
        data_dict['industry_weight_' + self.seg_benchmark] = industry_weight / industry_weight.groupby('dt').sum()
        data_dict['stock_weight'] = stock_weight[stock_weight.columns[0]].unstack()
        self.base_data = data_dict

    # def cleansing(self, boxskew=False):
    #     #没有调用
    #     pprint('Data cleansing')
    #     if self.fillna:
    #         self.standardized_data = standard_process(self.data['factor_data'], boxskew=boxskew,
    #                                                   stock_filter=self.data['stock_filter_' + str(self.universe)],
    #                                                   stock_industry=self.data['neutral_dict']['Industry'])
    #     else:
    #         self.standardized_data = standard_process(self.data['factor_data'], boxskew=boxskew)

    def standard_process(self, boxskew=False):
        pprint('Data cleaning')
        if self.fillna:
            #缺失值用行业中位数填充
            pprint('Fillna by industry')
            self.data['factor_data'] = factor_fillna_industry(self.data['factor_data'],
                                   stock_filter=self.data['stock_filter_' + str(self.universe)],
                                   stock_industry=self.data['neutral_dict']['Industry'])

        if boxskew:
            pprint('BoxSkewPlot processing')
            self.standardized_data = BoxSkewPlot(self.data['factor_data'])
        else:
            self.standardized_data = self.data['factor_data']

        pprint('Norm winsor processing')
        if self.median:
            bound = 3
            winsor = False
            factor_pd = self.standardized_data.copy()
            self.standardized_data = median_filter(factor_pd, mad=bound, winsor=winsor, inplace=True)
        if self.standard:
            std_ts = self.standardized_data.std(axis=1, ddof=0)
            std_ts.loc[std_ts == 0] = 1
            self.standardized_data = self.standardized_data.subtract(self.standardized_data.mean(axis=1), axis=0).divide(std_ts, axis=0)

        pprint('Norm winsor processing')
        #SJL 继续保留去极值
        self.standardized_data = norm_winsor(self.standardized_data)

    def factor_fillna_ts(self, window_number):
        self._data['factor_data'] = self._data['factor_data'].rolling(window=window_number, min_periods=1).mean()

    def regression_analysis(self):
        """
        VIF = 1 / (1-R2)
        0 < VIF < 10, no collinearity；10 ≤ VIF < 100, middle state, VIF ≥ 100, strong collinearity
        OLS 1: F(factor_to_be_test) = F(Style) * Beta(Style) + X(Industry) * Beta(Industry) + Resid
        OLS 2: R(stock_return) = Resid * Beta(Resid) + ~Resid
        output: ols2.tstat, ols2.beta, VIF, IC
        """
        #用neutral_list中的数据做了回归预测
        self.neutralized_data, r2, _, _ = regression_ols(self.standardized_data, self.data['neutral_dict'])
        _, _, beta, tstats = regression_ols(self.data[self.hpr_use], {'resid': self.neutralized_data})
        r2 = pd.DataFrame(r2)
        vif = 1 / (1 - r2[r2 < 1])
        IC = calc_factor_ic(self.neutralized_data, self.data[self.hpr_use], ic_type=self.ic_type)
        output_pd = pd.concat([tstats[['resid']], beta[['resid']], r2, vif, IC], axis=1)
        output_pd.columns = ['T-stat', 'Beta', 'Rsq', 'VIF', 'IC']
        return output_pd

    def regression_stats_process(self, output_pd):

        ttest, factor_beta, rsq, vif, IC = output_pd['T-stat'], output_pd['Beta'], output_pd['Rsq'], output_pd['VIF'], \
                                           output_pd['IC']
        ttest_avg = ttest.mean()
        ttest_abs_avg = ttest.abs().mean()
        ttestg2pct = (ttest > 2).sum() / len(ttest) if len(ttest) > 0 else np.nan
        ttest_sharpe = ttest_avg / ttest.std() if ttest.std() != 0 else np.nan
        factor_beta_mean = factor_beta.mean()
        factor_beta_t = sps.ttest_1samp(factor_beta.dropna(), popmean=0).statistic
        IC_avg = IC.mean()
        IC_std = IC.std()
        IR = IC_avg / IC_std if IC_std != 0 else np.nan
        IC_pos = (IC > 0).sum() / len(IC) if len(IC) != 0 else np.nan
        IC_absg5bp = (IC.abs() > 0.05).sum() / len(IC) if len(IC) != 0 else np.nan
        vif_avg = vif.mean()
        rsq_avg = rsq.mean()
        reg_dict = OrderedDict([
            ('| T-stat | avg', ttest_abs_avg),
            ('T-stat > 2 in %', ttestg2pct),
            ('T-stat (avg / std)', ttest_sharpe),
            ('Beta', factor_beta_mean),
            ('Beta T-Value', factor_beta_t),
            ('IC avg', IC_avg),
            ('IC std', IC_std),
            ('ICIR', IR),
            ('IC > 0 in %', IC_pos),
            ('| IC | > 0.05 in %', IC_absg5bp),
            ('VIF', vif_avg),
            ('R2 (Explained by %s)' % ' , '.join(list(set(self.neutral_list + ['Industry']))), rsq_avg)])

        regstat = pd.DataFrame(reg_dict, index=[self.name]).T
        return regstat

    def factor_score_correlation(self, factor_pd):
        """
        correlation_type = 'spearman','pearson'
        """
        factor_auto_correlation = pd.DataFrame()
        factor_auto_correlation['Pearson Linear ' + str(self.holding_period) + ' Days'] = factor_pd.corrwith(
            factor_pd.shift(self.holding_period), axis=1)
        factor_rank = factor_pd.rank(axis=1)
        factor_auto_correlation['Spearman Rank ' + str(self.holding_period) + ' Days'] = factor_rank.corrwith(
            factor_rank.shift(self.holding_period), axis=1)
        return factor_auto_correlation

    def factor_distribution_calc(self):
        factor_np = self.data['factor_data'].values.flatten()
        factor_val = factor_np[np.isfinite(factor_np)]
        factor_min = np.min(factor_val)
        factor_max = np.max(factor_val)
        factor_mean = np.mean(factor_val)
        factor_median = np.median(factor_val)
        factor_std = np.std(factor_val)
        factor_skew = sps.skew(factor_val)#偏度
        factor_kurtosis = sps.kurtosis(factor_val)#峰度
        factor_complete = len(factor_val) / self.data['stock_filter_' + str(self.universe)].sum().sum()
        colname = ['Skew', 'Kurtosis', 'Complete%', 'Median', 'Mean', 'Max', 'Min', 'Std']
        factor_dist = pd.DataFrame([factor_skew, factor_kurtosis, factor_complete,
                                    factor_median, factor_mean, factor_max, factor_min, factor_std], index=colname)
        return factor_dist

    def collinear_test(self):
        factor_corr = {}
        for item in self.data['neutral_dict']:
            factor_corr[item] = self.standardized_data.corrwith(self.data['neutral_dict'][item], axis=1)
        factor_corr = pd.DataFrame.from_dict(factor_corr, orient='index').T
        return factor_corr

    def alpha_decay_test(self, factor_data, max_lag=5, ic_type='original'):
        """
        max_lag: (int) number of holding period after factor data was observed
        Correlation: IC(T), Return(T+1:T+1+Holding_Period)
        Correlation for all days
        """
        total_rebal = int(factor_data.shape[0] / self.holding_period)
        max_lag = total_rebal if max_lag > total_rebal else max_lag  # control for input error
        lag_list = [i * self.holding_period for i in range(max_lag)]
        IC_ts = np.empty([len(factor_data), len(lag_list)])
        for i in range(len(lag_list)):
            lag_ret = self.data[self.hpr_use].shift(-1 * lag_list[i])#逐个holding_period计算收益率
            IC_ts[:, i] = calc_factor_ic(factor_data, lag_ret, self.ic_type)
        ic_decay = pd.DataFrame(np.nanmean(IC_ts, axis=0), index=lag_list, columns=['IC Decay'])#随着时间推移后的IC
        alpha_ts = calc_factor_ic(factor_data, self.data[self.hpr_use], self.ic_type) * \
                   self.data[self.hpr_use].std(axis=1) / self.holding_period
        alpha_cumsum = pd.DataFrame(alpha_ts.cumsum(), columns=['Alpha (IC*Dispersion)'])#？
        return ic_decay, alpha_cumsum

    def summary_table(self):
        factor_date_list = self.data['factor_data'].index.tolist()
        start_date = factor_date_list[0].strftime("%Y-%m-%d")
        end_date = factor_date_list[-1].strftime("%Y-%m-%d")
        test_date = start_date + ' - ' + end_date
        universe = 'A Shares' if self.universe is None else self.universe
        date_num, stock_num = self.data['factor_data'].shape
        sum_index = ['Factor Name', 'Test Period', 'Stock Universe', 'Stock Count', 'Date Count', 'Holding Period',
                     'Average Turnover']
        sum_val_str = [str(i) for i in
                       [self.name, test_date, universe.replace('_', ' '), stock_num, date_num, self.holding_period, self.avg_turnover]]
        sum_df = pd.DataFrame(sum_val_str, index=sum_index)
        sum_df.columns = ['Basic Info']
        sft_setting = pd.DataFrame([['Benchmark', 'Segment Number', 'Standard', 'median_winsor','Fillna By Industry',  # 'easy_test',
                                      'Seg by Industry', 'Transaction Cost'],
                                    [self.benchmark, self.segment_number, self.standard, self.median, self.fillna,
                                     self.seg_by_industry, self.transaction_cost]],
                                   columns=sum_index, index=[' ', 'Settings']).T#sjl，'Robust Segment'已去除，分层时去除异常点
        sft_setting2 = pd.DataFrame([['Industry Type' ,'IC Type', 'Compare Style', 'Interest Type',
                                      'Ret Price', 'Ret Shift', ''],
                                     [self.industry_type ,self.ic_type, self.compare_style, self.interest_type,
                                      self.ret_price, self.ret_shift]],
                                    columns=sum_index, index=[' ', 'Settings2']).T#sjl，self.easy_test去除，替换为industry_type，因子中性化所选行业
        sum_df = pd.concat([sum_df, sft_setting, sft_setting2], axis=1)
        return sum_df

    @staticmethod
    def save_to_h5(df, name, save_path):
        """save dataframe matrix to multiindex h5"""
        h5_name = os.path.join(save_path, name + '.h5')
        data_MI = df.stack().reset_index()
        data_MI.columns = ['dt', 'Ticker', name]
        data_MI.Ticker = data_MI.Ticker.astype('object')
        data_MI = data_MI.set_index(['dt', 'Ticker'])
        os.remove(h5_name) if os.path.exists(h5_name) else None
        # IO.pd_hdf5_writer(data_MI, h5_name, dataset=name)


    def calc_ic_duration_test(self, factor_data):
        duration_list = [-5, -3, -1, 1, 3, 5, 10, 20]  # , 40, 60, 80, 100, 120]
        ret_dict = {}
        for i in duration_list:
            if i < 0:
                # calculate gain
                ret_dict[i] = self.data[self.price_use] / self.data[self.price_use].shift(-1 * i) - 1
            if i > 0:
                # calculate return
                ret_dict[i] = self.data[self.price_use].shift(-1 * i) / self.data[self.price_use] - 1
        ic_ts = pd.DataFrame()
        for i in duration_list:
            ic_ts[i] = calc_factor_ic(factor_data, ret_dict[i], self.ic_type)
        lag_list_name = [str(i) + 'd' for i in duration_list]
        ic_duration = pd.DataFrame(np.nanmean(ic_ts, axis=0), index=lag_list_name, columns=['IC Decay'])
        return ic_duration

    @staticmethod
    def calc_ic_stats(ic_ts):
        ic_ts = ic_ts.dropna()
        icir = ic_ts.mean() / ic_ts.std()
        hit_rate = (ic_ts > 0).sum() / len(ic_ts)
        ic_stats = pd.DataFrame([ic_ts.mean(), ic_ts.std(), icir, hit_rate])
        ic_stats.index = ['IC Mean', 'IC Std', 'ICIR', 'Hit Rate']
        return ic_stats


    def calc_segment_rank(self, seg_return):
        self.data['holding_period_ret_daily'] = (self.data[self.hpr_use] + 1) ** (1 / self.holding_period) - 1
        name_pool = ['Q' + str(self.segment_number - i) for i in range(int(self.segment_number))]
        _ = seg_return[[name_pool[0], name_pool[-1]]].mean()
        max_quantile, min_quantile = _.idxmax(), _.idxmin()
        market_rank = calc_market_rank(seg_return.dropna()[max_quantile], self.data['holding_period_ret_daily'])
        return market_rank

    def shoot(self, result_folder):
        # do something useful
        pprint('* Factor backtest - %s *' % (self.name))
        output_folder = os.path.join(result_folder, self.name + '/')
        self.excel_name = os.path.join(output_folder, 'FactorBacktest_' + str(self.name) + '.xlsx')
        self.pickle_name = os.path.join(output_folder, 'FactorBacktest_' + str(self.name) + '.pkl')

        # calculate average turnover
        # 计算因子值隔天从后10%变成前90%或从前90%变成10%转换
        self.avg_turnover = round(get_turnover(self.factor_data), 5)

        # 因子回测评价的基本信息汇总
        sum_df = self.summary_table()#概览
        factor_coverage_ts = pd.DataFrame([np.isfinite(self.data['factor_data']).sum(axis=1)], index=['Stock Number']).T#每日有值股票数汇总
        factor_dist = self.factor_distribution_calc()

        # self.factor_fillna_ts(self.holding_period)
        ic_ts_combined = pd.DataFrame()

        from functools import partial
        calc_seg_measure = partial(segment_performance_measure, interest_type=self.interest_type)

        if not os.path.exists(output_folder):
            pprint("Output location: " + output_folder)
            os.makedirs(output_folder)

        if not self.easy_test:
            # 做了数据清洗：中位数过滤，(x-均值)/标准差
            self.standard_process()
            # pprint('Collinear backtest')
            # factor_corr = self.collinear_test()
            pprint('Regression analysis')
            # regression_output = self.regression_analysis()#bie 去掉
            # regression_stats = self.regression_stats_process(regression_output)#bie 去掉
            # ic_ts_combined['IC Neutralized'] = regression_output['IC']#bie 去掉

            self.neutralized_data, r2, _, _ = regression_ols(self.standardized_data, self.data['neutral_dict'])
            # _, _, beta, tstats = regression_ols(self.data[self.hpr_use], {'resid': self.neutralized_data})

            factor_data = self.neutralized_data#从regression_analysis中获取行业中性化数据
        else:
            factor_data = self.data['factor_data']

        # ic_ts_combined['IC_top_quantile'] = quantile_ic(factor_data, self.data[self.hpr_use],1 - 1/self.segment_number, 1)

        pprint('Auto correlation and IC tests')
        factor_auto_correlation = self.factor_score_correlation(factor_data)
        ic_decay, alpha_cumsum = self.alpha_decay_test(factor_data)
        ic_duration = self.calc_ic_duration_test(factor_data)

        pprint('Calc conextual IC')
        # bie barra因子暂不上线
        # ic_contextual_ts = calc_context_ic(factor_data, self.data[self.price_use], self.holding_period,
        #                                    self.data['style_dict'], seg_ic=self.seg_ic, add_own=True)
        # ic_contextual_stats = self.calc_ic_stats(ic_contextual_ts)

        # 计算 标准化后的因子数据与复权的ret_price的增长率的相关性
        ic_ts_combined['IC Original'] = self.data['factor_data'].corrwith(self.data[self.hpr_use], axis=1)
        ic_ts_combined['IC Score Weighted'] = calc_factor_ic(factor_data, self.data[self.hpr_use],
                                                           ic_type = 'score_weighted')#sjl统一ic类型
        ic_stats = self.calc_ic_stats(ic_ts_combined)

        if not self.easy_test:
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

        pprint('Segment analysis')

        _ = segment_test(factor_data, self.data[self.price_use], self.holding_period,
                         self.data[self.bmk_use], self.segment_number,
                         handle_return_outlier=self.robust_segment, transaction_cost=self.transaction_cost)
        if self.transaction_cost is None:
            seg_return = _
        else:
            seg_return, seg_return_after_cost = _[0], _[1]

        #TODO：seg_by_industry为True时将seg_return值覆盖，仅max_quantile值后续用到，待优化分支
        ls_col, max_quantile, min_quantile = find_er_ls_col(seg_return)  # check max_quantile for segment by industry usage

        if self.seg_by_industry:
            stk_weight = None if self.benchmark in ['alpha_universe', 'risk_universe'] else self.data['stock_weight']
            seg_tmp = segment_test_by_industry(factor_data, self.data[self.price_use], self.holding_period,
                                               self.data[self.bmk_use], self.segment_number,
                                               self.data['neutral_dict']['Industry'],
                                               self.data['industry_weight_' + self.seg_benchmark],
                                               transaction_cost=self.transaction_cost,
                                               return_industry=self.seg_by_industry,
                                               stock_weight=stk_weight, max_quantile=max_quantile)
            if self.transaction_cost is None:
                seg_return, seg_return_each_industry = seg_tmp[0], seg_tmp[1]
            else:
                # seg_return is replace by with industry weight seg method
                seg_return_ew, seg_return_ew_after_cost = seg_return.copy(), seg_return_after_cost.copy()
                seg_return, seg_return_after_cost, seg_return_each_industry, segret_by_ind_after_cost = \
                    seg_tmp[0], seg_tmp[1], seg_tmp[2], seg_tmp[3]

            seg_return_each_industry = seg_return_each_industry.rename(
                index=ind_map) if ind_map is not None else seg_return_each_industry
            ind_list = list(set(seg_return_each_industry.index.get_level_values(level=1)))
            # bie calc_seg_measure是segment_performance_measure函数固定了interest_type参数的对象，所以只能传入该函数的第一个参数
            # seg_return_each_industry_stat_dict = {i: calc_seg_measure(seg_return_each_industry.xs(i, level=1),
            #                                                           self.interest_type) for i in ind_list}
            seg_return_each_industry_stat_dict = {i: calc_seg_measure(seg_return_each_industry.xs(i, level=1)) for i in ind_list}
            seg_return_each_industry_stat = pd.concat(seg_return_each_industry_stat_dict, axis=0)
            seg_return_each_industry_stat.index.names = ['Industry', 'Segment']

            # calc industry concentration
            pprint('Calc Industry Concentration')
            ind_col = [i for i in seg_return_each_industry.columns if i.find('Index') > 0][0]
            ind_excess_ret = seg_return_each_industry[ind_col].unstack()
            industry_concentration = calc_hhi(ind_excess_ret, positive_only=True)

        if self.compare_style is not None:
            pprint('Compare %s Factor: Segment analysis' % (self.compare_style))
            _ = segment_test(self.data['neutral_dict'][self.compare_style], self.data[self.price_use],
                             self.holding_period,
                             self.data[self.bmk_use], self.segment_number,
                             handle_return_outlier=self.robust_segment, transaction_cost=self.transaction_cost)
            if self.transaction_cost is None:
                seg_return_fac = _
            else:
                seg_return_fac, seg_return_after_cost_fac = _[0], _[1]
            if self.seg_by_industry:
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
                    seg_return_fac, seg_return_each_industry_fac = seg_tmp_fac[0], seg_tmp_fac[1]
                else:
                    # seg_return is replace by with industry weight seg method
                    # seg_return_ew_fac,seg_return_ew_after_cost_fac = seg_return_fac.copy(),seg_return_after_cost_fac.copy()
                    seg_return_fac, seg_return_after_cost_fac, seg_return_each_industry_fac, segret_by_ind_after_cost_fac = \
                        seg_tmp_fac[0], seg_tmp_fac[1], seg_tmp_fac[2], seg_tmp_fac[3]

                # no sign control - assume small size yield positive return 

        seg_return_stat = segment_performance_measure(seg_return, self.interest_type)
        use_ind = np.isfinite(seg_return).sum(axis=1) > 2
        seg_return_stat_year = seg_return.loc[use_ind].groupby(seg_return.loc[use_ind].index.year).apply(
            calc_seg_measure)


        market_rank = self.calc_segment_rank(seg_return)

        pprint('Saving results to excel')
        output_dict = {'summary_info': sum_df,
                       'distribution': factor_dist,
                       'stock_count': factor_coverage_ts,
                       'seg_return': seg_return,
                       'seg_return_stat': seg_return_stat,
                       'seg_return_stat_year': seg_return_stat_year,#年化Sharp，年化收益率
                       'factor_auto_correlation': factor_auto_correlation,
                       'ic_ts_combined': ic_ts_combined,
                       'ic_stats': ic_stats,
                       # 'ic_contextual_ts': ic_contextual_ts, # bie barra因子暂不上线
                       # 'ic_contextual_stats': ic_contextual_stats, # bie barra因子暂不上线
                       'ic_decay': ic_decay,
                       'alpha_cumsum': alpha_cumsum,
                       'ic_duration': ic_duration,
                       'market_rank': market_rank}

        if self.seg_by_industry:
            output_dict['seg_return_ew'] = seg_return_ew
            output_dict['seg_return_each_industry_stat'] = seg_return_each_industry_stat
            output_dict['seg_return_each_industry'] = seg_return_each_industry
            output_dict['industry_concentration'] = industry_concentration
            if self.transaction_cost is not None:
                segret_by_ind_after_cost = segret_by_ind_after_cost.rename(
                    index=ind_map) if ind_map is not None else seg_return_each_industry
                ind_list = list(set(segret_by_ind_after_cost.index.get_level_values(level=1)))
                seg_return_each_industry_stat_dict_after_cost = {
                    i: segment_performance_measure(segret_by_ind_after_cost.xs(i, level=1), self.interest_type) for i in
                    ind_list}#key为行业，value为分层评价指标dataframe
                segret_by_ind_stat_after_cost = pd.concat(seg_return_each_industry_stat_dict_after_cost, axis=0)
                segret_by_ind_stat_after_cost.index.names = ['Industry', 'Segment']
                output_dict['seg_return_ew_after_cost'] = seg_return_ew_after_cost#ew表示不区分行业的分层收益，保存下来之后被seg_return被行业加权的分层收益替换掉
                output_dict['segret_by_ind_stat_after_cost'] = segret_by_ind_stat_after_cost#表示行业分层评价指标，索引为行业与分层明细，列为详细评价指标
                output_dict['segret_by_ind_after_cost'] = segret_by_ind_after_cost#表示行业分层评价收益，索引为行业与日期，列为收益率

        if not self.easy_test:
            # output_dict['factor_corr'] = factor_corr
            # output_dict['regression_output'] = regression_output
            # output_dict['regression_stats'] = regression_stats
            output_dict['ic_by_industry'] = ic_ind_pd
            # bie barra因子暂不上线
            # output_dict['style_corr'] = style_corr_pd
            # output_dict['ic_style_corr'] = ic_style_corr

        if self.transaction_cost is not None:
            seg_return_after_cost_stat = segment_performance_measure(seg_return_after_cost, self.interest_type)
            use_ind = np.isfinite(seg_return_after_cost).sum(axis=1) > 2

            seg_return_year_after_cost_stat = seg_return_after_cost.loc[use_ind].groupby(
                seg_return_after_cost.loc[use_ind].index.year).apply(calc_seg_measure)
            output_dict['seg_return_after_cost'] = seg_return_after_cost
            output_dict['seg_return_after_cost_stat'] = seg_return_after_cost_stat
            output_dict['seg_return_year_after_cost_stat'] = seg_return_year_after_cost_stat

        if self.compare_style is not None:
            output_dict['seg_return_fac'] = seg_return_fac
            if self.transaction_cost is not None:
                output_dict['seg_return_after_cost_fac'] = seg_return_after_cost_fac

        self.output_dict = output_dict


