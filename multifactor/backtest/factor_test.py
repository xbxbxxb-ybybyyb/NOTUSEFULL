import matplotlib
matplotlib.use('Agg')
import os
import pandas as pd
import numpy as np
import scipy.stats as sps
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import multifactor.utility.dt as tdt
from multifactor.backtest.report_generator import generate_pdf
from multifactor.backtest.utility import *
import multifactor.utility.common as ut 
from collections import OrderedDict
from multifactor.backtest.naming_config import *

universe_set = ['index_50', 'index_300', 'index_500', 'index_800','risk_universe', 'alpha_universe']
index_lookup = {'zz500': '000905.SH', 'zz800': '000906.SH', 'sz50': '000016.SH', 'hs300': '000300.SH',
                'wind_alla': '881001.WI'}
benchmark_set = ['zz500','zz800','sz50','hs300']#,'wind_alla']
#bmk_map = {'close':'close','open':'open','vwap':'close'}
prev_len = 20 # for holding period return 
corr_len = 60 # style correlation

class SingleFactorTest:
    """
    easy test: no factor neutralization, standardization, fillTS, etc...
    """
    def __init__(self, start_date, end_date, holding_period=5, benchmark='zz500', universe='alpha_universe',
                 segment_number=15, neutral_list=['Size', 'Industry'], fillna=False, easy_test=False,
                 seg_by_industry=False, seg_benchmark=None, provided_data=None, robust_segment=False,
                 transaction_cost=0.002, industry_type='CITIC_I', interest_type='SIMPLE',seg_ic=0.5,
                 ic_type = 'score_weighted',compare_style='Size',ret_price='close',ret_shift=True):

        self.start_date = IO.str_date_parser(start_date)
        self.end_date = IO.str_date_parser(end_date)
        self.holding_period = holding_period
        self.benchmark = benchmark
        self.universe = universe
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
 
        # stage variables
        self.name = None
        self.standardized_data = None
        self.neutralized_data = None
        self.base_data = dict()
        self._data = dict()  # new factor test would aligned to this variable

        self.prev_start_date = max(tdt.get_trading_day_offset(self.start_date, -prev_len)[0], pd.Timestamp(20090105))
        bmk_map = 'open' if self.ret_price == 'open' else 'close'
        self.bmk_name = 'bmk_price_%s_%s'%(self.benchmark,bmk_map)
        self.price_name = '%s_adj'%(self.ret_price)
        self.hpr_name = 'hpr_%d_%s'%(self.holding_period,self.ret_price)

        if self.holding_period == 1:
            self.ret_shift = True

        if provided_data is not None:
            # check data 
            provide_date_list = provided_data['close_adj'].index.tolist()
            sdate_p,edate_p = provide_date_list[0],provide_date_list[-1]
            if sdate_p<= self.start_date and edate_p>=self.end_date:
                self.base_data = provided_data
            else:
                print ('provide data wrong - check date')
                print ('test range: %s - %s \n provide range: %s - %s'
                       %(str(self.start_date),str(self.end_date),str(sdate_p),str(edate_p)))
                raise Exception
        else:
            self.load_data()
        self.ret_handle() # process return 
        
        
        
    @property
    def data(self):
        return self._data
    
    def ret_handle(self):
        pprint('Process holding period return & benchmark')

        shift_str = '_shift' if self.ret_shift else ''
        self.bmk_use = self.bmk_name + shift_str
        self.price_use = self.price_name + shift_str
        self.hpr_use = self.hpr_name + shift_str

        self.base_data[self.hpr_name] = self.base_data[self.price_name].shift(-1*self.holding_period)/self.base_data[self.price_name] - 1
        self.base_data[self.hpr_name][~self.base_data['stock_filter_'+str(self.universe)]] = np.nan

        if self.bmk_name not in list(self.base_data.keys()):
            pprint('Reload bechmark price')
            if self.benchmark in universe_set and self.benchmark == self.universe:
                # daily return average - return2price - dummy price
                stk_ret = self.base_data[self.price_name]/self.base_data[self.price_name].shift(1) - 1 #fix
                universe_ret = stk_ret[self.base_data['stock_filter_'+str(self.universe)].reindex(index=stk_ret.index,
                                                      columns=stk_ret.columns).fillna(value=False)].mean(axis=1)
                benchmark_price = (universe_ret+1).cumprod()
            else:
                if self.benchmark in benchmark_set:           
                    h5_index = IO.read_data([self.prev_start_date, self.end_date], bmk_map[self.ret_price], ftype=FType.MD, dtype=DType.INDEX, dsource=DSource.WIND)
                    benchmark_price = h5_index.unstack()[bmk_map[self.ret_price]][index_lookup[self.benchmark]]
                else:
                    print ('benchmark wrong: %s'%(self.benchmark))
                    raise Exception
            self.base_data[self.bmk_name] = benchmark_price

        if self.ret_shift:
            self.base_data[self.price_use] = self.base_data[self.price_name].shift(-1)
            self.base_data[self.hpr_use] = self.base_data[self.hpr_name].shift(-1)
            self.base_data[self.bmk_use] = self.base_data[self.bmk_name].shift(-1)
                                               
    def load_factor(self, factor_data, name='test_factor'):
        assert np.any([isinstance(factor_data, _type) for _type in [pd.Series, pd.DataFrame]])
        data_dict = self.base_data.copy()
        self.name = name
        if isinstance(factor_data, pd.Series):
            factor_data = factor_data.unstack()
        elif isinstance(factor_data, pd.DataFrame):
            if len(factor_data.columns) == 1:
                factor_data = factor_data[factor_data.columns[0]].unstack()
        factor_data = factor_data.sort_index()
        pprint('Filter factor by universe')
        data_dict['factor_data'] = factor_data.reindex(columns=data_dict['stock_filter_'+str(self.universe)].columns)
        # replace inf, -inf by nan
        data_dict['factor_data'][~np.isfinite(data_dict['factor_data'])] = np.nan

        pprint('Align factor with base data')
        data_dict = align_data_inner(data_dict)
        data_dict['factor_data'][data_dict['stock_filter_'+str(self.universe)]==False] = np.nan
        data_dict['factor_data'] = data_dict['factor_data'].dropna(how='all', axis=1)
        data_dict = align_data_inner(data_dict) 
        self._data = data_dict
        self.standardized_data = None
        self.neutralized_data = None

    def load_data(self):
        data_dict = dict()
        pprint('Loading data: %s - %s'%(self.start_date,self.end_date))

        pprint('Getting return data')
        md_list = ['close','adjfactor','open','vwap']
        md_dict = {s:IO.read_data([self.prev_start_date, self.end_date],[s],ftype=FType.MD, dsource=DSource.WIND)[s].unstack() for s in md_list}
        for p in ['close','open','vwap']:
            md_dict['%s_adj'%(p)] = md_dict[p] * md_dict['adjfactor']
            data_dict['%s_adj'%(p)] = md_dict['%s_adj'%(p)]

        pprint('Getting stock filter data')

        if self.universe in universe_set:
            h5_filter = IO.read_data([self.start_date, self.end_date], columns=[self.universe, 'filter_stpt'],
                                      ftype=FType.UNIV, dsource=DSource.OPTM)
            pprint('Getting universe data: ' + self.universe.lower())
            h5_filter = h5_filter.fillna(value=False)
            compound_filter = h5_filter[self.universe] & h5_filter['filter_stpt']
        else:
            h5_filter = IO.read_data([self.start_date, self.end_date], columns='filter_stpt', ftype=FType.UNIV, dsource=DSource.OPTM)
            compound_filter = h5_filter['filter_stpt']
        stock_filter = compound_filter.unstack().fillna(value=False)
        data_dict['stock_filter_'+str(self.universe)] = stock_filter

        pprint('Getting benchmark data')
        if self.benchmark in universe_set and self.benchmark == self.universe:
            # daily return average - return2price - dummy price
            stk_ret = data_dict[self.price_name]/data_dict[self.price_name].shift(1) - 1 #fix
            universe_ret = stk_ret[stock_filter.reindex(index=stk_ret.index,columns=stk_ret.columns).fillna(value=False)].mean(axis=1)
            benchmark_price = (universe_ret+1).cumprod()
        else:
            index_price = IO.read_data([self.prev_start_date, self.end_date], ftype=FType.MD, dtype=DType.INDEX, dsource=DSource.WIND)
            benchmark_price = index_price.unstack()['close'][index_lookup[self.benchmark]]
        data_dict[self.bmk_name] = benchmark_price

        pprint('Getting style and industry data')
        # load basic data regardless easy test
        style_dict = {}
        style_list = IO.get_available_cols(ftype=FType.RISK,dsource=DSource.STYLEFACTOR)
        for s in style_list:
            style_dict[s] = IO.read_data([self.start_date, self.end_date],ftype=FType.RISK,
                                           dsource=DSource.STYLEFACTOR,columns=[s],max_workers=1)[s].unstack()
        data_dict['neutral_dict'] = {item:style_dict[item] for item in list(set(self.neutral_list + ['Industry']))}
        data_dict['style_dict'] = style_dict
        
        pprint('Getting industry by user defined type')
        user_industry = IO.read_data([self.start_date, self.end_date], columns=self.industry_type,
                                      dsource=DSource.WIND, ftype=FType.INDUSTRY)
        data_dict['user_industry'] = user_industry[self.industry_type].unstack()
        
        pprint('Getting industry weight data')
        #assert self.seg_benchmark in ['hs300', 'zz500', 'sh50', 'alla']
        if self.seg_benchmark in ['hs300','zz500','sh50']:
            stock_weight = IO.read_data([self.start_date, self.end_date], columns='index_weight_'+self.seg_benchmark,
                                         dsource=DSource.OPTM, ftype=FType.UNIV)
            stock_weight.columns= ['stock_weight']
        else:
            mkt_cap_ard = IO.read_data([self.start_date, self.end_date], columns=['mkt_cap_ard'],
                                           ftype=FType.MD, dsource=DSource.WIND)['mkt_cap_ard'].unstack()
            mkt_cap_ard = mkt_cap_ard.reindex(index=stock_filter.index,columns=stock_filter.columns)
            mkt_cap_ard[~stock_filter] = np.nan
            mkt_cap_ard_MI = mkt_cap_ard.stack()
            stock_weight = pd.DataFrame(mkt_cap_ard_MI / mkt_cap_ard_MI.groupby('dt').sum())
            stock_weight.columns= ['stock_weight']
        _stock_industry = pd.DataFrame(data_dict['neutral_dict']['Industry'].stack(), columns=['Industry'])
        weight_grouped = pd.concat([_stock_industry, stock_weight], axis=1).groupby(['dt', 'Industry'])
        industry_weight = weight_grouped['stock_weight'].sum()
        # normalized to 1.0
        data_dict['industry_weight_'+self.seg_benchmark] = industry_weight / industry_weight.groupby('dt').sum()
        data_dict['stock_weight'] = stock_weight[stock_weight.columns[0]].unstack()
        self.base_data = data_dict
    
    def cleansing(self, boxskew=False):
        pprint('Data cleansing')
        if self.fillna:
            self.standardized_data = standard_process(self.data['factor_data'], boxskew=boxskew,
                                                      stock_filter=self.data['stock_filter_'+str(self.universe)],
                                                      stock_industry=self.data['neutral_dict']['Industry'])
        else:
            self.standardized_data = standard_process(self.data['factor_data'], boxskew=boxskew)
                 
    def standard_process(self, boxskew=False):
        pprint('Data cleaning')
        if boxskew:
            pprint('BoxSkewPlot processing')
            self.standardized_data = BoxSkewPlot(self.data['factor_data'])
        else:
            self.standardized_data = self.data['factor_data']
        if self.fillna:
            pprint('Fillna by industry')
            factor_fillna_industry(self.data['factor_data'], stock_filter=self.data['stock_filter_'+str(self.universe)],
                                   stock_industry=self.data['neutral_dict']['Industry'])
            
        pprint('Norm winsor processing')
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
        self.neutralized_data, r2, _, _ = regression_ols(self.standardized_data, self.data['neutral_dict'])
        _, _, beta, tstats = regression_ols(self.data[self.hpr_use], {'resid': self.neutralized_data})
        r2 = pd.DataFrame(r2)
        vif = 1 / (1 - r2[r2 < 1])
        IC = calc_factor_ic(self.neutralized_data,self.data[self.hpr_use],ic_type=self.ic_type)
        output_pd = pd.concat([tstats[['resid']], beta[['resid']], r2, vif, IC], axis=1)
        output_pd.columns = ['T-stat', 'Beta', 'Rsq', 'VIF', 'IC']
        return output_pd

    
    def regression_stats_process(self, output_pd):
           
        ttest, factor_beta, rsq, vif, IC = output_pd['T-stat'], output_pd['Beta'], output_pd['Rsq'], output_pd['VIF'], output_pd['IC']
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
        factor_skew = sps.skew(factor_val)
        factor_kurtosis = sps.kurtosis(factor_val)
        factor_complete = len(factor_val) / self.data['stock_filter_'+str(self.universe)].sum().sum()
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

    def alpha_decay_test(self, factor_data, max_lag=5,ic_type='original'):
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
            lag_ret = self.data[self.hpr_use].shift(-1 * lag_list[i])
            IC_ts[:, i] = calc_factor_ic(factor_data,lag_ret,self.ic_type)
        ic_decay = pd.DataFrame(np.nanmean(IC_ts, axis=0), index=lag_list, columns=['IC Decay'])
        alpha_ts = calc_factor_ic(factor_data,self.data[self.hpr_use],self.ic_type) * \
                   self.data[self.hpr_use].std(axis=1) / self.holding_period
        alpha_cumsum = pd.DataFrame(alpha_ts.cumsum(), columns=['Alpha (IC*Dispersion)'])
        return ic_decay, alpha_cumsum

    def summary_table(self):
        factor_date_list = self.data['factor_data'].index.tolist()
        start_date = factor_date_list[0].strftime("%Y-%m-%d")
        end_date = factor_date_list[-1].strftime("%Y-%m-%d")
        test_date = start_date + ' - ' + end_date
        universe = 'A Shares' if self.universe is None else self.universe
        date_num, stock_num = self.data['factor_data'].shape
        sum_index = ['Factor Name', 'Test Period','Stock Universe', 'Stock Count', 'Date Count', 'Holding Period']
        sum_val_str = [str(i) for i in [self.name, test_date, universe.replace('_', ' '), stock_num, date_num, self.holding_period]]
        sum_df = pd.DataFrame(sum_val_str, index=sum_index)
        sum_df.columns = ['Basic Info']
        sft_setting = pd.DataFrame([['Benchmark', 'Segment Number', 'Fillna', #'easy_test',
                                     'Robust Segment', 'Seg by Industry', 'Transaction Cost'],
                                    [self.benchmark, self.segment_number, self.fillna,
                                     self.robust_segment, self.seg_by_industry, self.transaction_cost]],
                                     columns=sum_index, index=[' ', 'Settings']).T
        sft_setting2 = pd.DataFrame([['Easy Test','IC Type', 'Compare Style', 'Interest Type',
                                      'Ret Price','Ret Shift'],
                                    [self.easy_test, self.ic_type, self.compare_style,self.interest_type,self.ret_price,self.ret_shift]],
                                     columns=sum_index, index=[' ', 'Settings2']).T
        sum_df = pd.concat([sum_df, sft_setting,sft_setting2], axis=1)
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
        IO.pd_hdf5_writer(data_MI, h5_name, dataset=name)

    def factor_coverage(self):
        date_num, stock_num = self.data['factor_data'].shape
        stock_ts = pd.DataFrame([np.isfinite(self.data['factor_data']).sum(axis=1)], index=['Stock Number']).T
        return stock_ts

    def calc_ic_duration_test(self, factor_data):
        duration_list = [-5, -3, -1, 1, 3, 5, 10, 20]#, 40, 60, 80, 100, 120]
        ret_dict = {}
        for i in duration_list:
            if i < 0:
                # calculate gain
                ret_dict[i] = self.data[self.price_use] / self.data[self.price_use].shift(-1*i) - 1
            if i > 0:
                # calculate return
                ret_dict[i] = self.data[self.price_use].shift(-1*i) / self.data[self.price_use] - 1
        ic_ts = pd.DataFrame()
        for i in duration_list:
            ic_ts[i] = calc_factor_ic(factor_data,ret_dict[i],self.ic_type)
        lag_list_name = [str(i)+'d' for i in duration_list]
        ic_duration = pd.DataFrame(np.nanmean(ic_ts, axis=0), index=lag_list_name, columns=['IC Decay'])
        return ic_duration
    
    @staticmethod
    def calc_ic_stats(ic_ts):
        ic_ts = ic_ts.dropna()
        icir = ic_ts.mean() / ic_ts.std()
        hit_rate = (ic_ts>0).sum()/len(ic_ts)
        ic_stats = pd.DataFrame([ic_ts.mean(), ic_ts.std(), icir, hit_rate])
        ic_stats.index = ['IC Mean', 'IC Std', 'ICIR','Hit Rate']
        return ic_stats

    def calc_segment_rank(self,seg_return):
        self.data['holding_period_ret_daily'] = (self.data[self.hpr_use] + 1) ** (1 / self.holding_period) - 1
        name_pool = ['Q' + str(self.segment_number - i) for i in range(int(self.segment_number))]
        _ = seg_return[[name_pool[0], name_pool[-1]]].mean()
        max_quantile, min_quantile = _.idxmax(), _.idxmin()
        market_rank = calc_market_rank(seg_return.dropna()[max_quantile],self.data['holding_period_ret_daily'])
        return market_rank

    def shoot(self, result_folder):
        # do something useful
        pprint('* Factor test - %s *'%(self.name))
        output_folder = os.path.join(result_folder, self.name+'/')
        self.excel_name = os.path.join(output_folder, 'FactorBacktest_'+str(self.name)+'.xlsx')
        self.pickle_name = os.path.join(output_folder, 'FactorBacktest_'+str(self.name)+'.pkl')

        sum_df = self.summary_table()
        factor_coverage_ts = self.factor_coverage()
        factor_dist = self.factor_distribution_calc()

        # self.factor_fillna_ts(self.holding_period)
        ic_ts_combined = pd.DataFrame()
        ic_ts_combined['IC Original'] = self.data['factor_data'].corrwith(self.data[self.hpr_use], axis=1)

        from functools import partial
        calc_seg_measure = partial(segment_performance_measure, interest_type=self.interest_type)

        if not os.path.exists(output_folder):
            pprint("Output location: " + output_folder)
            os.makedirs(output_folder)

        if not self.easy_test:
            self.standard_process()
            #pprint('Collinear test')
            #factor_corr = self.collinear_test()
            pprint('Regression analysis')
            regression_output = self.regression_analysis()
            regression_stats = self.regression_stats_process(regression_output)
            ic_ts_combined['IC Neutralized'] = regression_output['IC']
            """
            if save2h5:
                pprint('Saving neutralized results to H5')
                self.save_to_h5(self.standardized_data, self.name+'_standardized', result_folder)
                self.save_to_h5(self.neutralized_data, self.name+'_neutralized', result_folder)
            """
            factor_data = self.neutralized_data
        else:
            factor_data = self.data['factor_data']

        #ic_ts_combined['IC_top_quantile'] = quantile_ic(factor_data, self.data[self.hpr_use],1 - 1/self.segment_number, 1)
        
        pprint('Auto correlation and IC tests')
        factor_auto_correlation = self.factor_score_correlation(factor_data)
        ic_decay, alpha_cumsum = self.alpha_decay_test(factor_data)
        ic_duration =  self.calc_ic_duration_test(factor_data)


        pprint('Calc conextual IC')
        ic_contextual_ts = calc_context_ic(factor_data,self.data[self.price_use],self.holding_period,self.data['style_dict'],seg_ic=self.seg_ic,add_own=True)
        ic_ts_combined['IC Score Weighted'] = calc_factor_ic(factor_data,self.data[self.hpr_use],ic_type='score_weighted')
        ic_contextual_stats = self.calc_ic_stats(ic_contextual_ts)
        ic_stats = self.calc_ic_stats(ic_ts_combined)


        if not self.easy_test:
            pprint('Calc IC by industry')
            ic_ind_pd = calc_ic_by_industry(factor_data, self.data[self.hpr_use],self.data['user_industry'],self.ic_type)

            if self.industry_type == 'CITIC_I':
                ind_map = CITIC_I_mapper
                                 
            elif self.industry_type == 'KNN_I':
                ind_map = KNN_I_mapper
            else:
                ind_map = None
            ic_ind_pd = ic_ind_pd.rename(columns=ind_map) if ind_map is not None else ic_ind_pd
            # correlation with style factors
            pprint('Collinear test')
            style_list = list(self.data['style_dict'].keys())
            style_list.sort()
            style_corr_pd = calc_corr(factor_data, self.data['style_dict'])[style_list]
            
            pprint('Style correlation test')
            #ic_ts_style = calc_ic_dict(self.data['style_dict'],self.data[self.hpr_use])
            ic_ts_style = calc_ic_dict(self.data['style_dict'],self.data[self.hpr_use],ic_type=self.ic_type)
            ic_style_corr = calc_ts_corr(ic_ts_combined['IC Original'],ic_ts_style,roll_win=corr_len)[style_list]
            
        pprint('Segment analysis')
        
        _ = segment_test(factor_data, self.data[self.price_use], self.holding_period,
                          self.data[self.bmk_use], self.segment_number,
                          handle_return_outlier=self.robust_segment,transaction_cost=self.transaction_cost)
        if self.transaction_cost is None:
            seg_return = _
        else:
            seg_return, seg_return_after_cost = _[0],_[1]
            
        ls_col,max_quantile,min_quantile = find_er_ls_col(seg_return) # check max_quantile for segment by industry usage
            
        if self.seg_by_industry:
            stk_weight = None if self.benchmark in ['alpha_universe','risk_universe'] else self.data['stock_weight']
            seg_tmp = segment_test_by_industry(factor_data, self.data[self.price_use], self.holding_period,
                                               self.data[self.bmk_use], self.segment_number,
                                               self.data['neutral_dict']['Industry'],
                                               self.data['industry_weight_'+self.seg_benchmark],
                                               transaction_cost=self.transaction_cost,
                                               return_industry=self.seg_by_industry,
                                               stock_weight=stk_weight,max_quantile=max_quantile)
            if self.transaction_cost is None:
                seg_return,seg_return_each_industry = seg_tmp[0],seg_tmp[1]
            else:
                # seg_return is replace by with industry weight seg method
                seg_return_ew,seg_return_ew_after_cost = seg_return.copy(),seg_return_after_cost.copy()
                seg_return,seg_return_after_cost,seg_return_each_industry,segret_by_ind_after_cost =\
                seg_tmp[0],seg_tmp[1],seg_tmp[2],seg_tmp[3]
              
            seg_return_each_industry = seg_return_each_industry.rename(index=ind_map) if ind_map is not None else seg_return_each_industry
            ind_list = list(set(seg_return_each_industry.index.get_level_values(level=1)))
            seg_return_each_industry_stat_dict = {i:calc_seg_measure(seg_return_each_industry.xs(i,level=1),
                                                                                self.interest_type) for i in ind_list}
            seg_return_each_industry_stat = pd.concat(seg_return_each_industry_stat_dict,axis=0)
            seg_return_each_industry_stat.index.names = ['Industry','Segment']

            # calc industry concentration
            pprint('Calc Industry Concentration')
            ind_col = [i for i in seg_return_each_industry.columns if i.find('Index')>0][0]
            ind_excess_ret = seg_return_each_industry[ind_col].unstack()
            industry_concentration = calc_hhi(ind_excess_ret,positive_only=True)

        if self.compare_style is not None:
            pprint('Compare %s Factor: Segment analysis'%(self.compare_style))
            _ = segment_test(self.data['neutral_dict'][self.compare_style], self.data[self.price_use], self.holding_period,
                                      self.data[self.bmk_use], self.segment_number,
                                      handle_return_outlier=self.robust_segment,transaction_cost=self.transaction_cost)
            if self.transaction_cost is None:
                seg_return_fac = _
            else:
                seg_return_fac, seg_return_after_cost_fac = _[0],_[1]
            if self.seg_by_industry:
                stk_weight = None if self.benchmark in ['alpha_universe','risk_universe'] else self.data['stock_weight']
                seg_tmp_fac = segment_test_by_industry(self.data['neutral_dict'][self.compare_style], self.data[self.price_use], self.holding_period,
                                                       self.data[self.bmk_use], self.segment_number,
                                                       self.data['neutral_dict']['Industry'],
                                                       self.data['industry_weight_'+self.seg_benchmark],
                                                       transaction_cost=self.transaction_cost,
                                                       return_industry=self.seg_by_industry,
                                                       stock_weight=stk_weight)
                if self.transaction_cost is None:
                    seg_return_fac,seg_return_each_industry_fac = seg_tmp_fac[0],seg_tmp_fac[1]
                else:
                    # seg_return is replace by with industry weight seg method
                    #seg_return_ew_fac,seg_return_ew_after_cost_fac = seg_return_fac.copy(),seg_return_after_cost_fac.copy()
                    seg_return_fac,seg_return_after_cost_fac,seg_return_each_industry_fac,segret_by_ind_after_cost_fac =\
                    seg_tmp_fac[0],seg_tmp_fac[1],seg_tmp_fac[2],seg_tmp_fac[3]
                
                # no sign control - assume small size yield positive return 
                
        seg_return_stat = segment_performance_measure(seg_return,self.interest_type)
        use_ind = np.isfinite(seg_return).sum(axis=1)>2
        seg_return_stat_year = seg_return.loc[use_ind].groupby(seg_return.loc[use_ind].index.year).apply(calc_seg_measure)
        
        # segret_30 with/without t_cost only save one 
        _ = segment_test(factor_data, self.data[self.price_use], self.holding_period,
                                                   self.data[self.bmk_use], 30,
                                                   transaction_cost=self.transaction_cost,
                                                   handle_return_outlier=self.robust_segment, return_bucket_ic=True)
        if self.transaction_cost is None:
            seg_return_30, bucket_ic_30 = _[0],_[1]
        else:
            seg_return_30, bucket_ic_30 = _[1],_[2]
            # seg 30 only one copy 
        seg_return_30_stat = segment_performance_measure(seg_return_30,self.interest_type)
        use_ind = np.isfinite(seg_return_30).sum(axis=1)>2
        seg_return_30_stat_year = seg_return_30.loc[use_ind].groupby(seg_return_30.loc[use_ind].index.year).apply(calc_seg_measure)
        
        market_rank = self.calc_segment_rank(seg_return)
            
        pprint('Saving results to excel')
        output_dict = {'summary_info': sum_df,
                       'distribution': factor_dist,
                       'stock_count': factor_coverage_ts,
                       'seg_return':seg_return,
                       'seg_return_stat': seg_return_stat,
                       'seg_return_stat_year': seg_return_stat_year,
                       'seg_return_30': seg_return_30,
                       'bucket_ic_30': bucket_ic_30,
                       'seg_return_30_stat': seg_return_30_stat,
                       'seg_return_30_stat_year': seg_return_30_stat_year,
                       'factor_auto_correlation': factor_auto_correlation,
                       'ic_ts_combined': ic_ts_combined,
                       'ic_stats': ic_stats,
                       'ic_contextual_ts':ic_contextual_ts,
                       'ic_contextual_stats':ic_contextual_stats,
                       'ic_decay': ic_decay,
                       'alpha_cumsum': alpha_cumsum,
                       'ic_duration': ic_duration,
                       'market_rank':market_rank}

        if self.seg_by_industry:
            output_dict['seg_return_ew'] = seg_return_ew
            output_dict['seg_return_each_industry_stat'] = seg_return_each_industry_stat
            output_dict['seg_return_each_industry'] = seg_return_each_industry
            output_dict['industry_concentration'] = industry_concentration
            if self.transaction_cost is not None:
                segret_by_ind_after_cost = segret_by_ind_after_cost.rename(index=ind_map) if ind_map is not None else seg_return_each_industry
                ind_list = list(set(segret_by_ind_after_cost.index.get_level_values(level=1)))
                seg_return_each_industry_stat_dict_after_cost = {i:segment_performance_measure(segret_by_ind_after_cost.xs(i,level=1),self.interest_type) for i in ind_list}
                segret_by_ind_stat_after_cost = pd.concat(seg_return_each_industry_stat_dict_after_cost,axis=0)
                segret_by_ind_stat_after_cost.index.names = ['Industry','Segment']
                output_dict['seg_return_ew_after_cost'] = seg_return_ew_after_cost
                output_dict['segret_by_ind_stat_after_cost'] = segret_by_ind_stat_after_cost
                output_dict['segret_by_ind_after_cost'] = segret_by_ind_after_cost
                
        if not self.easy_test:
            #output_dict['factor_corr'] = factor_corr
            output_dict['regression_output'] = regression_output
            output_dict['regression_stats'] = regression_stats
            output_dict['ic_by_industry'] = ic_ind_pd
            output_dict['ic_by_industry'] = ic_ind_pd
            output_dict['style_corr'] = style_corr_pd
            output_dict['ic_style_corr'] = ic_style_corr
            
        if self.transaction_cost is not None:
            seg_return_after_cost_stat = segment_performance_measure(seg_return_after_cost,self.interest_type)
            use_ind = np.isfinite(seg_return_after_cost).sum(axis=1)>2
            
            seg_return_year_after_cost_stat = seg_return_after_cost.loc[use_ind].groupby(seg_return_after_cost.loc[use_ind].index.year).apply(calc_seg_measure)
            output_dict['seg_return_after_cost'] = seg_return_after_cost
            output_dict['seg_return_after_cost_stat'] = seg_return_after_cost_stat
            output_dict['seg_return_year_after_cost_stat'] = seg_return_year_after_cost_stat

        if self.compare_style is not None:
            output_dict['seg_return_fac'] = seg_return_fac
            if self.transaction_cost is not None:
                output_dict['seg_return_after_cost_fac'] = seg_return_after_cost_fac

        excel_saver(output_dict, self.excel_name)
        save_pickle(output_dict, self.pickle_name)
        pprint('Generating pdf report')
        generate_pdf(self.pickle_name)
        
        pprint('* Finished - %s *'%(self.name))



"""

from multifactor.IO import IO
from multifactor.IO.IO_enums import *
from multifactor.backtest.utility import read_pickle
from multifactor.backtest.factor_test import SingleFactorTest

if __name__ == '__main__':
    base_data = read_pickle(r'A:\zhisj\data\quant_data\factor_test_hpr_10.pkl')
    sdate,edate = 20090101,20181019
    fac_path = r'A:\zhisj\factor\pv\minute\volume\minute_b24_comb_nis.h5'
    sft = SingleFactorTest(sdate, edate, universe='alpha_universe', robust_segment=True,
                           seg_by_industry=False, fillna=False, provided_data=base_data, easy_test=False, transaction_cost=0.004)
    #save_pickle(sft.base_data,r'A:\zhisj\data\quant_data\factor_test_hpr_10.pkl')
    test_fct = IO.read_data([sdate, edate], alt=fac_path)
    sft.load_factor(test_fct,name ='minute_b24_comb_nis')
    sft.shoot()
"""