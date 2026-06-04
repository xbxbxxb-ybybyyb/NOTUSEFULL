"""
BARRA STYLE FACTOR
Barra China Equity Model (CNE6) Empirical Notes - July 2018

long term reversal: neutralized to momentum
residual vol: neutralized to size / beta 
"""

from Wind.utils import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import datetime as dt
from Wind.risk_utility import *
import logging
from functools import partial
import os
from log import Log
import time
import gc
logger = Log("Barra_risk")


class UpdateBarraRisk:
    def __init__(self, sdate, edate, operation='append', universe='alpha_universe', benchmark = 'zz500', 
                            root_path='/app/data/wdb_h5/WIND_TEST',parallel=True,md_path=None,fdd_path=None,sql_config=None):
        self.sdate = sdate
        self.edate = edate
        self.operation = operation
        if operation in ['append', 'create']:
            if operation == 'create':
                self.append_mode = None
                self.from_scratch = True
            else:
                self.append_mode = True
                self.from_scratch = False
        else:
            raise AssertionError
        self.check_date_complete = False if self.operation =='create' else True
        self.parallel = parallel
        self.cdate_list = get_trading_date_range(self.sdate, self.edate)
        self.universe = universe
        current_time = dt.datetime.now().strftime('%Y%m%d_%H%M%S')

        if benchmark not in ['zz500','hs300','zz800']:
            raise AssertionError
        else:
            self.benchmark = benchmark
        self.risk_univ_name = 'risk_universe'
        self.industry_name = 'CITIC_I'
        #self.day_num = 1200
        #self.fdd_lookback_qtr = 12

        self.day_num = 600
        self.fdd_lookback_qtr = 8
        self.fdd_min_pct = 0.5
        self.md_min_pct = 0.5
        self.sdate_prev = get_prev_sdate(self.sdate,self.day_num,sql_config)
        # self.sdate_prev = get_trading_day_offset(self.sdate, -self.day_num)[0]
        self.qtr_list = get_qtr_list(self.sdate_prev, self.edate, num_qtr=self.fdd_lookback_qtr) 
        self.sdate_qtr, self.edate_qtr = self.qtr_list[0], self.qtr_list[-1]
                
        # built params
        self.mkttype = MktType.CHINA
        self.dtype = DType.STOCK
        self.ftype = FType.RISK
        self.dfreq = DFreq.DAILY
        # self.dsource = DSource.STYLEFACTOR2
        #mkttype, dtype, ftype, dfreq, dsource, dtable

        # path 
        self.root_path = root_path
        self.process_path = os.path.join(root_path,'RISK_CHINA_STOCK_DAILY_STYLEFACTOR','LOCAL_DATA','LOG','STYLE')
        if md_path is None:
            self.md_path = os.path.join(self.process_path,'base_data','md_%s_%s.pkl'%(self.sdate,self.edate))
        else:
            self.md_path = md_path
        if fdd_path is None:
            self.fdd_path = os.path.join(self.process_path,'base_data','fdd_%s_%s.pkl'%(self.sdate,self.edate))
        else:
            self.fdd_path = fdd_path

        self.log_name = os.path.join(self.process_path, 'log', 'barra_risk_%s.log' % (current_time))

        self.style_path = "/app/data/wdb_h5/WIND_TEST/RISK_CHINA_STOCK_DAILY_STYLEFACTOR/RISK_CHINA_STOCK_DAILY_STYLEFACTOR.h5"

        self.descriptor_path = "/app/data/wdb_h5/WIND_TEST/RISK_CHINA_STOCK_DAILY_DESCRIPTOR/RISK_CHINA_STOCK_DAILY_DESCRIPTOR.h5"


        for i in [self.root_path,self.style_path,self.descriptor_path,self.log_name,self.fdd_path,self.md_path]:
            path = os.path.dirname(i)
            if not os.path.exists(path):
                os.makedirs(path)


        logger.info('*** BARRA RISK UPDATE : %s - %s (%s days) ***'%(self.sdate,self.edate,len(self.cdate_list)))
        # stage variable
        self.data = None  # dictionary of DataFrames for MD
        self.boilerplate = None
        self.fdd = {}
        self.fdd_lists = None  # named list dictionary for FDD
        # save tank
        self.raw = {} # raw descriptor
        self.descriptor = {} # process descriptor
        self.style = {}  # raw - processed style       

    def load_basic_data(self):
        # load data with long look back days
        logger.info('* Loading Basic Data: %s - %s *' % (self.sdate_prev, self.edate))
        tic = time.time()
        risk_univ_name = self.risk_univ_name #'risk_universe'
        industry_name = self.industry_name #'CITIC_I'
        
        sdate_prev = self.sdate_prev
        edate = self.edate

        # load data with long look back days
        logger.info('* Loading Basic Data: %s - %s *' % (sdate_prev, edate))
        logger.info('Getting market data')
        md_list = ['close', 'total_shares', 'adjfactor', 'turn', 'mkt_cap_ard']
        
        alt_mdstock = "/app/data/wdb_h5/WIND_TEST/MD_CHINA_STOCK_DAILY_WIND/MD_CHINA_STOCK_DAILY_WIND.h5"
        h5_data = read_data([sdate_prev, edate], columns=md_list,alt=alt_mdstock)
        h5_data['close_adj'] = h5_data['close'] * h5_data['adjfactor']
        dat = {k:h5_data[k].unstack() for k in h5_data}
        dat['stock_return'] = dat['close_adj'] / dat['close_adj'].shift(1) - 1
        boilerplate = dat['close_adj']

        logger.info('Getting universe data')
        
        alt_univ = "/app/data/wdb_h5/WIND_TEST/UNIV_CHINA_STOCK_DAILY_OPTM/UNIV_CHINA_STOCK_DAILY_OPTM.h5"
        universe_pd = read_data([sdate_prev, edate], columns=self.universe,alt=alt_univ)
        universe_pd = universe_pd[universe_pd.columns[0]].unstack().reindex(index=boilerplate.index,
                                                                            columns=boilerplate.columns).fillna(False)
        universe_return_weighted = (dat['stock_return'] * universe_pd * dat['mkt_cap_ard']).divide(
                                   (dat['mkt_cap_ard'] * universe_pd).sum(axis=1), axis=0).sum(axis=1)
        dat['universe_return_weighted'] = universe_return_weighted.reindex(index=boilerplate.index)

        # make up real boilerplate
        dates_index = [item for item in get_trading_date_range(self.sdate, self.edate) if item in boilerplate.index]
        self.boilerplate = boilerplate.reindex(index=dates_index)  # placeholder for newly generated factors
        self.iter_num = len(self.boilerplate.index)
        
        # load data with normal start and end dates
        logger.info('Getting risk universe data')
        risk_univ = read_data([self.sdate_prev, self.edate], columns=[risk_univ_name], alt=alt_univ)
        dat['risk_univ'] = risk_univ.unstack()[risk_univ_name]
        dat['risk_univ'] = dat['risk_univ'].reindex(index=self.boilerplate.index, columns=self.boilerplate.columns).fillna(False)

        logger.info('Getting industry data')
        
        alt_industry = "/app/data/wdb_h5/WIND_TEST/INDUSTRY_CHINA_STOCK_DAILY_WIND/INDUSTRY_CHINA_STOCK_DAILY_WIND.h5"
        h5_ind = read_data([self.sdate_prev, self.edate], columns=[industry_name],alt=alt_industry)
        dat['industry'] = h5_ind[h5_ind.columns[0]].unstack()
        dat['industry'] = dat['industry'].reindex(index=self.boilerplate.index, columns=self.boilerplate.columns)

        logger.info('Getting benchmark data')
        index_lookup = {'zz500': '000905.SH', 'zz800': '000906.SH', 'sz50': '000016.SH', 'hs300': '000300.SH'}
        
        alt_mdindex = "/app/data/wdb_h5/WIND_TEST/MD_CHINA_INDEX_DAILY_WIND/MD_CHINA_INDEX_DAILY_WIND.h5"
        h5_index = read_data([self.sdate_prev, self.edate], 'close', alt=alt_mdindex)
        benchmark_price = h5_index.unstack()['close'][index_lookup[self.benchmark]]
        dat['bmk_ret'] = benchmark_price/benchmark_price.shift(1) - 1
        dat['bmk_ret_log'] = np.log(benchmark_price/benchmark_price.shift(1))
        
        dat['excess_return'] = dat['stock_return'].subtract(dat['bmk_ret'],axis=0)
        dat['universe_excess_return_weighted'] = dat['universe_return_weighted'] - dat['bmk_ret']
        
        dat['stock_return_log'] = np.log(dat['close_adj']/dat['close_adj'].shift(1))
        dat['excess_return_log'] = dat['stock_return_log'].subtract(dat['bmk_ret_log'],axis=0)
        
        self.data = align_data_outer(dat)
        self.data['risk_univ'] = self.data['risk_univ'].reindex(index=self.boilerplate.index,columns=self.boilerplate.columns)
        self.data['industry'] = self.data['industry'].reindex(index=self.boilerplate.index,columns=self.boilerplate.columns)
        self.data['risk_univ'] = self.data['risk_univ'].fillna(value=False)

        # save_pickle(self.data,self.md_path)
        toc = time.time()
        logger.info('* Load Basic data Done %s*'%(print_time(toc,tic)))

    # load fdd data
    def load_fdd_data(self):
        logger.info('* Loading FDD Data: %s - %s *'%(self.sdate_qtr, self.edate_qtr))
        tic = time.time()
        sdate_dummy,edate_dummy = 20000101,20990101    
        statement_type = 408001000
        qfa_type = 408002000
        
        logger.info('Loading FDD Data: %s - %s'%(self.sdate_qtr, self.edate_qtr))
    
        logger.info('Getting backfill prep data')
        prep_data = get_backfill_prep(self.sdate_prev, self.edate)

        # path_dict = get_wind_path()
        total_shares = self.data['total_shares']
        alt_AShareDividend = "/app/data/wdb_h5/WIND_TEST/AShareDividend/AShareDividend.h5"
        data_dividend = read_data([sdate_dummy,edate_dummy],alt=alt_AShareDividend)
        if data_dividend['S_DIV_PROGRESS'].dtype == 'object':
            data_dividend["S_DIV_PROGRESS"] = data_dividend["S_DIV_PROGRESS"].apply(pd.to_numeric)
        data_dividend = data_dividend[data_dividend['S_DIV_PROGRESS']==3]
        data_dividend['dividend_amount'] = data_dividend['CASH_DVD_PER_SH_PRE_TAX'] * data_dividend[
            'S_DIV_BASESHARE'] * 1e4


        # input data list         
        balance_list_accural = ['TOT_ASSETS','TOT_LIAB','TOT_CUR_ASSETS','TOT_CUR_LIAB','MONETARY_CAP','NON_CUR_LIAB_DUE_WITHIN_1Y','TAXES_SURCHARGES_PAYABLE']
        income_list_accural = ['LESS_IMPAIR_LOSS_ASSETS','TOT_OPER_REV','OPER_REV','NET_PROFIT_INCL_MIN_INT_INC']
        balance_list_noa_equity = ['TOT_SHRHLDR_EQY_INCL_MIN_INT']
        balance_list_noa_financial_asset = ['MONETARY_CAP','TRADABLE_FIN_ASSETS','FIN_ASSETS_AVAIL_FOR_SALE',
                                            'HELD_TO_MTY_INVEST','INVEST_REAL_ESTATE','TIME_DEPOSITS','OTH_ASSETS','LONG_TERM_REC']
        balance_list_noa_financial_obligation = ['ST_BORROW','TRADABLE_FIN_LIAB','NOTES_PAYABLE','NON_CUR_LIAB_DUE_WITHIN_1Y','LT_BORROW','BONDS_PAYABLE']
        balance_list_noa = balance_list_noa_equity + balance_list_noa_financial_asset + balance_list_noa_financial_obligation
        # AShareIncome
        income_list_noa = ['NET_PROFIT_INCL_MIN_INT_INC','LESS_FIN_EXP','NET_INT_INC']
        # AShareFinancialIndicator
        ind_list_noa = ['S_FA_EXTRAORDINARY']
        balance_list_cxgro = ['FIX_ASSETS']
        eod_derive_list = ['S_VAL_PE_TTM','S_VAL_PCF_OCFTTM']
        ttm_list = ['S_FA_EBIT_TTM','NET_PROFIT_TTM','NET_CASH_FLOWS_OPER_ACT_TTM','S_FA_INVESTCASHFLOW_TTM',
                    'TOT_OPER_REV_TTM', 'S_FA_GC_TTM', 'S_FA_GROSSPROFITMARGIN_TTM', 'S_FA_ROA_TTM']
        
        cashflow_list = ['NET_CASH_FLOWS_OPER_ACT']

        balance_list = list(set(balance_list_accural + balance_list_noa + balance_list_cxgro))
        income_list = list(set(income_list_accural + income_list_noa))
        ind_list = ind_list_noa
        
        sdate_qtr, edate_qtr = self.sdate_qtr, self.edate_qtr

        logger.info('Getting fdd table data')
        # eod daily - no need for getting prev data
        
        alt_AShareEODDerivativeIndicator = "/app/data/wdb_h5/WIND_TEST/AShareEODDerivativeIndicator/AShareEODDerivativeIndicator.h5"
        data_eod_derive = read_data([self.sdate, self.edate], columns=eod_derive_list,alt=alt_AShareEODDerivativeIndicator)
        alt_AShareBalanceSheet = "/app/data/wdb_h5/WIND_TEST/AShareBalanceSheet/AShareBalanceSheet.h5"
        data_balance_full = read_data([sdate_qtr, edate_qtr], columns=balance_list+['STATEMENT_TYPE'],alt=alt_AShareBalanceSheet)
        if data_balance_full["STATEMENT_TYPE"].dtype == 'object':
            data_balance_full["STATEMENT_TYPE"] = data_balance_full["STATEMENT_TYPE"].apply(pd.to_numeric)
        alt_AShareIncome = "/app/data/wdb_h5/WIND_TEST/AShareIncome/AShareIncome.h5"
        data_income_full = read_data([sdate_qtr, edate_qtr], columns=income_list+['STATEMENT_TYPE'], alt=alt_AShareIncome)

        if data_income_full["STATEMENT_TYPE"].dtype == 'object':
            data_income_full["STATEMENT_TYPE"] = data_income_full["STATEMENT_TYPE"].apply(pd.to_numeric)
        alt_AShareFinancialIndicator =  "/app/data/wdb_h5/WIND_TEST/AShareFinancialIndicator/AShareFinancialIndicator.h5"
        data_fin_ind = read_data([sdate_qtr, edate_qtr], columns=ind_list, alt=alt_AShareFinancialIndicator)
        alt_AShareTTMHis = "/app/data/wdb_h5/WIND_TEST/AShareTTMHis/AShareTTMHis.h5"
        data_ttm = read_data([sdate_qtr, edate_qtr], columns=ttm_list, alt=alt_AShareTTMHis)

        alt_AShareCashFlow = "/app/data/wdb_h5/WIND_TEST/AShareCashFlow/AShareCashFlow.h5"
        data_cashflow_full = read_data([sdate_qtr, edate_qtr], columns=cashflow_list+['STATEMENT_TYPE','ANN_DT'], alt=alt_AShareCashFlow)
        if data_cashflow_full["STATEMENT_TYPE"].dtype == 'object':
            data_cashflow_full["STATEMENT_TYPE"] = data_cashflow_full["STATEMENT_TYPE"].apply(pd.to_numeric)
        data_cashflow_full = data_cashflow_full.sort_values('ANN_DT')
        data_cashflow_full = data_cashflow_full.reset_index().drop_duplicates(subset=['dt','Ticker','STATEMENT_TYPE'], keep='last').set_index(['dt','Ticker'])
        
        data_balance = data_balance_full[data_balance_full['STATEMENT_TYPE']==statement_type].drop('STATEMENT_TYPE', axis=1)
        data_income = data_income_full[data_income_full['STATEMENT_TYPE']==statement_type].drop('STATEMENT_TYPE', axis=1)
        data_cashflow = data_cashflow_full[data_cashflow_full['STATEMENT_TYPE']==statement_type].drop('STATEMENT_TYPE', axis=1)

        data_income_qfa = data_income_full[data_income_full['STATEMENT_TYPE']==qfa_type].drop('STATEMENT_TYPE', axis=1)
        # 防止数据库有重复数据录入
        data_income_qfa.drop_duplicates(subset=None,keep='first',inplace=True)
        data_income_qfa.columns = [item + '_QFA' for item in data_income_qfa.columns]
        data_cashflow_qfa = data_cashflow_full[data_cashflow_full['STATEMENT_TYPE']==qfa_type].drop('STATEMENT_TYPE', axis=1)
        data_cashflow_qfa.columns = [item + '_QFA' for item in data_cashflow_qfa.columns]

        fdd_data_qtr_mi = {'data_eod_derive':data_eod_derive,'data_balance':data_balance,'data_income':data_income,
                       'data_cashflow':data_cashflow,'data_income_qfa':data_income_qfa,'data_cashflow_qfa':data_cashflow_qfa,
                       'data_fin_ind':data_fin_ind,'data_ttm':data_ttm}

        fdd_data_qtr_dict = {c:fdd_data_qtr_mi[k][c].unstack() for k in fdd_data_qtr_mi for c in fdd_data_qtr_mi[k]}

        data_eod_derive_dict = {k:data_eod_derive[k].unstack() for k in data_eod_derive}
        fdd_daily_data_dict = data_eod_derive_dict
        orig_table = {'data_dividend':data_dividend}

        self.fdd_lists = {'balance_list_noa_equity': balance_list_noa_equity,
                          'balance_list_noa_financial_asset': balance_list_noa_financial_asset,
                          'balance_list_noa_financial_obligation': balance_list_noa_financial_obligation,
                          'income_list_noa': income_list_noa,
                          'ind_list_noa': ind_list_noa}
        
        self.fdd = {'qtr':fdd_data_qtr_dict,'daily':fdd_daily_data_dict,
                    'qtr_mi':fdd_data_qtr_mi,'prep_data':prep_data,
                    'orig_table':orig_table}
        # save_pickle是与read_data配合使用的，read_data暂不需要
        # save_pickle(self.fdd,self.fdd_path)
        toc = time.time()
        logger.info('* Load FDD Data Done %s*'%(print_time(toc,tic)))
        return
        
    def read_data(self):
        logger.info('* Read Data From Existing Pickle *')
        logger.info('MD data: %s'%(self.md_path))
        logger.info('FDD data: %s'%(self.fdd_path))

        self.data = read_pickle(self.md_path)
        self.fdd = read_pickle(self.fdd_path)
        
        boilerplate = self.data['close_adj']
        full_date_list = [item for item in get_trading_date_range2(self.sdate, self.edate)]
        dates_index = [item for item in get_trading_date_range2(self.sdate, self.edate) if item in boilerplate.index]
        lack_list = list(set(full_date_list) - set(dates_index))
        lack_list.sort()
        if len(lack_list)>0:
            logger.error('* read data wrong: lack - %s*'%(str(lack_list)))
            raise Exception
        self.boilerplate = boilerplate.reindex(index=dates_index)  # placeholder for newly generated factors
        self.iter_num = len(self.boilerplate.index)

        balance_list_accural = ['TOT_ASSETS','TOT_LIAB','TOT_CUR_ASSETS','TOT_CUR_LIAB','MONETARY_CAP','NON_CUR_LIAB_DUE_WITHIN_1Y','TAXES_SURCHARGES_PAYABLE']
        income_list_accural = ['LESS_IMPAIR_LOSS_ASSETS','TOT_OPER_REV','OPER_REV','NET_PROFIT_INCL_MIN_INT_INC']
        balance_list_noa_equity = ['TOT_SHRHLDR_EQY_INCL_MIN_INT']
        balance_list_noa_financial_asset = ['MONETARY_CAP','TRADABLE_FIN_ASSETS','FIN_ASSETS_AVAIL_FOR_SALE',
                                            'HELD_TO_MTY_INVEST','INVEST_REAL_ESTATE','TIME_DEPOSITS','OTH_ASSETS','LONG_TERM_REC']
        balance_list_noa_financial_obligation = ['ST_BORROW','TRADABLE_FIN_LIAB','NOTES_PAYABLE','NON_CUR_LIAB_DUE_WITHIN_1Y','LT_BORROW','BONDS_PAYABLE']
        balance_list_noa = balance_list_noa_equity + balance_list_noa_financial_asset + balance_list_noa_financial_obligation
        # AShareIncome
        income_list_noa = ['NET_PROFIT_INCL_MIN_INT_INC','LESS_FIN_EXP','NET_INT_INC']
        # AShareFinancialIndicator
        ind_list_noa = ['S_FA_EXTRAORDINARY']
        balance_list_cxgro = ['FIX_ASSETS']
        eod_derive_list = ['S_VAL_PE_TTM','S_VAL_PCF_OCFTTM']
        ttm_list = ['S_FA_EBIT_TTM','NET_PROFIT_TTM','NET_CASH_FLOWS_OPER_ACT_TTM','S_FA_INVESTCASHFLOW_TTM',
                    'TOT_OPER_REV_TTM', 'S_FA_GC_TTM', 'S_FA_GROSSPROFITMARGIN_TTM', 'S_FA_ROA_TTM']
        
        cashflow_list = ['NET_CASH_FLOWS_OPER_ACT']

        self.fdd_lists = {'balance_list_noa_equity': balance_list_noa_equity,
                          'balance_list_noa_financial_asset': balance_list_noa_financial_asset,
                          'balance_list_noa_financial_obligation': balance_list_noa_financial_obligation,
                          'income_list_noa': income_list_noa,
                          'ind_list_noa': ind_list_noa}
        
        logger.info('* Read Data Done *')
        return 
    
        
    def baseline_process(self, pd_raw):
        # instead of inner join factor to make with base factors
        # factor DataFrame should be reindexed to base factors
        pd_raw = pd_raw.reindex(index = self.boilerplate.index, columns=self.boilerplate.columns)
        date_lack = list(set(self.boilerplate.index) - set(pd_raw.dropna(axis=0,how='all').index))
        date_lack.sort()
        if len(date_lack)>0:
            if self.operation == 'append':
                logger.warning('data empty for one day')
                raise Exception
            else:
                logger.warning('data not exist for %d days: %s - %s'%(len(date_lack),date_lack[0],date_lack[-1]))
    
        stk_filter = self.data['risk_univ'].reindex(index=pd_raw.index) if self.operation == 'create' else self.data['risk_univ']
        stk_industry = self.data['industry'].reindex(index=pd_raw.index) if self.operation == 'create' else self.data['industry']
        return standard_process(pd_raw, stock_filter=stk_filter, stock_industry=stk_industry,
                                winsor=True, weight=None)
    
    def backfiller(self,qtr_pd):
        backfill_qtr = partial(backfill_master, sdate=self.sdate_prev, edate=self.edate, prep_data=self.fdd['prep_data'])
        return backfill_qtr(qtr_pd)

    def boilerplate_pd(self, np_raw):
        assert isinstance(np_raw, np.ndarray)
        row_num_np,col_num_np = np_raw.shape
        row_num_bp,col_num_bp = len(self.boilerplate.index),len(self.boilerplate.columns)
        if row_num_np!=row_num_bp or col_num_np!=col_num_bp:
            logger.info('boilerplate_pd: dimension not matching')
            raise Exception
        return pd.DataFrame(np_raw, index=self.boilerplate.index, columns=self.boilerplate.columns)
    
    """Beta and Hsigma"""
    def risk_beta(self, half_life=252, look_back_days=504, smooth_num=4,ma_alpha=11,lag_alpha=11):
        logger.info('Update Risk Factor: Market Beta & Residual Volatility')
        take_idx = self.iter_num + look_back_days + ma_alpha + lag_alpha + 1
        if len(self.data['excess_return']) < take_idx:
            logger.warning('beta: data not enough')
            raise Exception
        excess_ret_stk = self.data['excess_return']
        excess_ret_uni = self.data['universe_return_weighted'].subtract(self.data['bmk_ret'],axis=0)
        
        er_stk_roll_mat = excess_ret_stk.rolling(smooth_num,min_periods=int(smooth_num/2)).mean().values
        er_uni_roll_mat = excess_ret_uni.rolling(smooth_num,min_periods=int(smooth_num/2)).mean().values.reshape(-1, 1)
        
        res_vol, rsquared, beta, tvalues = rolling_ts_regression(er_uni_roll_mat[-take_idx:, :],
                                                                 er_stk_roll_mat[-take_idx:, :],
                                                                 look_back_days=look_back_days,
                                                                 half_life=half_life, 
                                                                 x_type='macro',
                                                                 ufunc=np.nanstd,
                                                                 parallel=self.parallel)
        hbeta = self.boilerplate_pd(beta[-self.iter_num:, :, 1])
        hsigma = self.boilerplate_pd(res_vol[-self.iter_num:, :])
        halpha_non_lagged = pd.DataFrame(beta[-self.iter_num - ma_alpha - lag_alpha:, :, 0])
        halpha = self.boilerplate_pd(halpha_non_lagged.rolling(ma_alpha,int(ma_alpha*0.5)).mean().shift(lag_alpha).iloc[-self.iter_num:].values)
        self.raw.update({'hbeta':hbeta,'hsigma':hsigma,'halpha':halpha})

    
    """Value: Book to Price"""

    def risk_book_to_price(self):
        # book_to_price = (TOT_ASSETS - TOT_LIAB) / mkt_cap_ard
        logger.info('Update Risk Factor: Value')
        btop = self.backfiller(self.fdd['qtr']['TOT_ASSETS'] - self.fdd['qtr']['TOT_LIAB']) / self.data['mkt_cap_ard']
        self.raw.update({'btop':btop})

    """Dividend Yield"""

    def risk_dividend_yield(self):
        logger.info('Update Risk Factor: Dividend Yield')
        dtop = calc_dividend_yield(self.sdate,self.edate,self.fdd['orig_table']['data_dividend'],
                                                self.data['risk_univ'],self.data['mkt_cap_ard'])
        self.raw.update({'dtop':dtop})
                        
    """Earnings Quality"""

    def risk_earnings_quality(self):
        """accurals
        Aggregate Accruals = NOAt – NOA t-1
        Where Net Operating Assets (NOA) =
        (Total Assets – Cash) – (Total Liabilities – Total Debt)
        Accruals Ratio = (NOAt – NOA t-1)/ ((NOAt + NOA t-1)/2)

        应计量是指盈利中未收到现金的部分，由流动资产、流动负债、折旧三部分组成。
        流动资产部分指剔除现金或现金等价物增加额后的企业流动资产变化；
        流动负债部分是剔除距到期日不足一年的长期贷款与应付税额变化后的流动负债变化；
        折旧部分即折旧与摊销。
        CA就是流动资产 Cash就是现金等价物 CL是流动负债 STD是距离到期日不足一年的贷款 TP是应付税款 Dep是折旧

        Accordingly, the accrual component of earnings is computed using
        information from the balance sheet and income statement, as is common in the earnings
        management literature (Dechow et al. 1995):
        Accruals = (ACA - ACash) - (ACL -ASTD - ATP) - Dep
        where ACA = change in current assets (Compustat item 4),
        ACash = change in cashlcash equivalents (Compustat item l),   - bs: MONETARY_CAP
        ACL = change in current liabilities (Compustat item 5),
        ASTD = change in debt included in current liabilities (Compustat item 34),
        ATP = change in income taxes payable (Compustat item 71), and
        Dep = depreciation and amortization expense (Compustat item 14).

        cash - MONETARY_CAP
        curent_liability - TOT_CUR_LIAB
        debt - NON_CUR_LIAB_DUE_WITHIN_1Y
        tax - TAXES_SURCHARGES_PAYABLE
        dep: DEPR_FA_COGA_DPBA + AMORT_INTANG_ASSETS + AMORT_LT_DEFERRED_EXP

        Aggregate Accruals = Nit – (CFOt + CFIt)
        Again, the measurement can be standardized by taking the average net operating assets for the period to compare across companies.
        Accruals Ratio = Nit – (CFOt + CFIt)/ (NOAt + NOA t-1)/2
        """
        
        logger.info('Update Risk Factor: Earnings Quality')
        """ NOA: net operating asset """
        equity = self.fdd['qtr_mi']['data_balance'][self.fdd_lists['balance_list_noa_equity']].sum(axis=1)
        financial_obligation = self.fdd['qtr_mi']['data_balance'][self.fdd_lists['balance_list_noa_financial_obligation']].sum(axis=1)
        financial_asset = self.fdd['qtr_mi']['data_balance'][self.fdd_lists['balance_list_noa_financial_asset']].sum(axis=1)
        net_operating_asset_qtr = (equity + financial_obligation - financial_asset).unstack()
        total_assets_qtr = self.fdd['qtr']['TOT_ASSETS']
        
        accruals_balance_sheet_qtr =  -(net_operating_asset_qtr - net_operating_asset_qtr.shift(1)) /((total_assets_qtr + total_assets_qtr.shift(1)) / 2)

        net_income_qtr = self.fdd['qtr']['NET_PROFIT_TTM']
        cfo_qtr = self.fdd['qtr']['NET_CASH_FLOWS_OPER_ACT_TTM']
        cfi_qtr = self.fdd['qtr']['S_FA_INVESTCASHFLOW_TTM']
        accrual_cashflow_qtr = (net_income_qtr - (cfo_qtr + cfi_qtr))/((total_assets_qtr + total_assets_qtr.shift(1))/2)

        accruals_balance_sheet = self.backfiller(accruals_balance_sheet_qtr)
        accrual_cashflow = self.backfiller(accrual_cashflow_qtr)

        self.raw.update({'abs':accruals_balance_sheet,'acf':accrual_cashflow})
                        
        #return accruals_balance_sheet, accrual_cashflow

    """Earnings Variability"""

    def risk_earnings_variability(self):
        logger.info('Update Risk Factor: Earnings Variability')
        lookback_qtr = self.fdd_lookback_qtr
        min_periods = int(self.fdd_lookback_qtr * self.fdd_min_pct)

        sale_qtr = self.fdd['qtr']['TOT_OPER_REV_QFA']
        net_income_qfa = self.fdd['qtr']['NET_PROFIT_INCL_MIN_INT_INC_QFA']
        cashflow_qfa = self.fdd['qtr']['NET_CASH_FLOWS_OPER_ACT_QFA']

        vsal_qtr = sale_qtr.rolling(lookback_qtr, min_periods).std() / sale_qtr.rolling(lookback_qtr, min_periods).mean()
        vern_qtr = net_income_qfa.rolling(lookback_qtr, min_periods).std() / net_income_qfa.rolling(lookback_qtr, min_periods).mean()
        vflo_qtr = cashflow_qfa.rolling(lookback_qtr, min_periods).std() / net_income_qfa.rolling(lookback_qtr, min_periods).mean()

        vsal = self.backfiller(vsal_qtr)
        vern = self.backfiller(vern_qtr)
        vflo = self.backfiller(vflo_qtr)
        
        self.raw.update({'vsal':vsal,'vern':vern,'vflo':vflo})
                
    """Earnings Yield"""

    def risk_earnings_yield(self):
        """
        EPFWD - Predicted earnings-to-price ratio
        CETOP - Cash earnings-to-price ratio
        ETOP  - Trailing earnings-to-price ratio
        """
        logger.info('Update Risk Factor: Earnings Yield')

        cetop = self.fdd['daily']['S_VAL_PCF_OCFTTM']
        etop = self.fdd['daily']['S_VAL_PE_TTM']
        ebit_daily = self.backfiller(self.fdd['qtr']['S_FA_EBIT_TTM'])
        ev_daily = self.data['mkt_cap_ard']
        em = ebit_daily / ev_daily
        self.raw.update({'cetop':cetop,'etop':etop,'em':em})
        
    """Growth"""

    def risk_growth(self):
        """
        SGRO  - Sales growth (trailing five years)
        EGRO  - Earnings growth (trailing five years)
        EGRLF - Long-term predicted earnings growth
        EGRSF - Short-term predicted earnings growth
        """
        lookback_qtr = self.fdd_lookback_qtr
        min_periods = int(self.fdd_lookback_qtr * self.fdd_min_pct)

        total_shares = self.data['total_shares']
        logger.info('Update Risk Factor: Growth')
        earning_ttm_qtr = self.fdd['qtr']['NET_PROFIT_TTM']
        sales_qtr = self.fdd['qtr']['TOT_OPER_REV']
        shares_qtr = get_qtr_end_data(total_shares)
        
        eps_qtr = earning_ttm_qtr/shares_qtr
        sps_qtr = sales_qtr/shares_qtr
        
        egro_qtr = eps_qtr.rolling(lookback_qtr,min_periods).apply(get_growth_rate)
        sgro_qtr = sps_qtr.rolling(lookback_qtr,min_periods).apply(get_growth_rate)

        egro = self.backfiller(egro_qtr)
        sgro = self.backfiller(sgro_qtr)
        self.raw.update({'egro':egro,'sgro':sgro})
        
    """Investment Quality"""

    def risk_investment_quality(self):
        logger.info('Update Risk Factor: Investment Quality')
        lookback_qtr = self.fdd_lookback_qtr
        min_periods = int(self.fdd_lookback_qtr * self.fdd_min_pct)
        
        total_assets_qtr = self.fdd['qtr']['TOT_ASSETS']
        ppe_qtr = self.fdd['qtr']['FIX_ASSETS']
        depreciation_qfa = self.fdd['qtr']['LESS_IMPAIR_LOSS_ASSETS_QFA']
        capex_qtr = (ppe_qtr - ppe_qtr.shift(1) + depreciation_qfa)#/total_assets_qtr

        share_ots_daily = self.data['total_shares'] #'FLOAT_A_SHR_TODAY'
        share_ots_qtr = get_qtr_end_data(share_ots_daily)

        agro_qtr = -1 * total_assets_qtr.rolling(lookback_qtr,min_periods).apply(get_growth_rate)
        igro_qtr = -1 * share_ots_qtr.rolling(lookback_qtr,min_periods).apply(get_growth_rate)
        cxgro_qtr = -1* capex_qtr.rolling(lookback_qtr,min_periods).apply(get_growth_rate)

        agro = self.backfiller(agro_qtr)
        igro = self.backfiller(igro_qtr)
        cxgro = self.backfiller(cxgro_qtr)        
        self.raw.update({'agro':agro,'igro':igro,'cxgro':cxgro})
        
    """Leverage"""

    def risk_leverage(self):
        """
        Leverage  = MLEV + DTOA + BLEV
        Note: book value of preferred equity is rare in China
        MLEV (Market Leverage) = (ME + LD) / ME
        DTOA (Debt to Assets)  = tot_liab / TOT_ASSETS
        BLEV (Book Leverage)  = (BE + PE + LD) / BE
        note: BE could be tot_shrhldr_eqy_excl_min_int from wind
        """
        logger.info('Update Risk Factor: Leverage')
        book_value_qtr = self.fdd['qtr']['TOT_SHRHLDR_EQY_INCL_MIN_INT']
        long_term_debt_qtr = self.fdd['qtr']['NON_CUR_LIAB_DUE_WITHIN_1Y']
        mkt_cap_ard = self.data['mkt_cap_ard']
        total_liab_qtr = self.fdd['qtr']['TOT_LIAB']
        total_assets_qtr = self.fdd['qtr']['TOT_ASSETS']
        long_term_debt = self.backfiller(long_term_debt_qtr)
        
        blev_qtr = (book_value_qtr + long_term_debt_qtr) / book_value_qtr
        dtoa_qtr = total_liab_qtr / total_assets_qtr

        mlev = (mkt_cap_ard + long_term_debt) / mkt_cap_ard
        blev = self.backfiller(blev_qtr)
        dtoa = self.backfiller(dtoa_qtr)
        
        self.raw.update({'mlev':mlev,'blev':blev,'dtoa':dtoa})
        

    """Liquidity"""
    def risk_liquidity(self, window=21, look_back_terms=12):
        logger.info('Update Risk Factor: Liquidity')
        min_pct = self.md_min_pct
        turn = self.data['turn']
        turn[turn==0] = np.nan
        turn[~np.isfinite(turn)] = np.nan
        date_num, stock_num = turn.shape
        if date_num < window * look_back_terms + self.iter_num - 1:
            logger.warning('stock return date number less than required')
            raise AssertionError
        X = turn.iloc[-window*look_back_terms-self.iter_num+1:, :]
        stom = np.log(X.rolling(window=window, min_periods=int(window*min_pct)).mean())
        stoq = np.log(X.rolling(window=int(window*look_back_terms/4), min_periods=int(window*look_back_terms/4*min_pct)).mean())
        stoa = np.log(X.rolling(window=window*look_back_terms, min_periods=int(window*look_back_terms*min_pct)).mean())
        avtr = EWMA(X, window*look_back_terms, int(window*look_back_terms/4),ufunc='sum')
        
        self.raw.update({'stom':stom,'stoq':stoq,'stoa':stoa,'avtr':avtr})
    
    
    """Long Term Reversal"""

    def risk_long_term_reversal(self, look_back_days=252, smooth_num=4, ma_window=11):
        logger.info('Update Risk Factor: Long Term Reversal')
        """look_back_days=1040, half_life=260, smooth_num=4, ma_window=11, lag=273
        """
        min_pct = self.md_min_pct
        half_life= int(np.floor(look_back_days/4))
        lag = int(np.floor(look_back_days/4))
        min_num = look_back_days + lag + smooth_num + ma_window + self.iter_num + 1
        if len(self.data['excess_return']) < min_num:
            logger.warning('risk: long term reversal - data not enough')
            raise Exception
        
        idx = int(look_back_days + ma_window + lag + self.iter_num+1)
        ltrstr_non_lagged = EWMA(self.data['excess_return_log'].iloc[-idx:,:], look_back_days, half_life, ufunc='sum')
        ltrstr = - ltrstr_non_lagged.rolling(ma_window, min_periods=int(ma_window*min_pct)).mean().shift(lag)

        excess_ret_stk = self.data['excess_return'] 
        excess_ret_uni = self.data['universe_return_weighted'].subtract(self.data['bmk_ret'],axis=0)
        
        er_stk_roll_mat = excess_ret_stk.rolling(smooth_num,min_periods=int(smooth_num*min_pct)).mean().values
        er_uni_roll_mat = excess_ret_uni.rolling(smooth_num,min_periods=int(smooth_num*min_pct)).mean().values.reshape(-1, 1)
        
        # for shift lag number -- pre sliced 
        take_idx = look_back_days + ma_window + lag + self.iter_num + 1
        end_idx = lag # for less calculation
        res_vol, rsquared, beta, tvalues = rolling_ts_regression(er_uni_roll_mat[-take_idx:-end_idx, :],
                                                                 er_stk_roll_mat[-take_idx:-end_idx, :],
                                                                 look_back_days=look_back_days,
                                                                 half_life=half_life, 
                                                                 x_type='macro',
                                                                 ufunc=np.nanstd,
                                                                 parallel=self.parallel)

        lthalpha_raw = pd.DataFrame(beta[:, :, 0]).rolling(ma_window, min_periods=int(ma_window/2)).mean().iloc[-self.iter_num:, :].values
        lthalpha = - self.boilerplate_pd(lthalpha_raw)
        self.raw.update({'ltrstr':ltrstr,'lthalpha':lthalpha})

    """Mid Capitalization"""

    def risk_mid_cap(self):
        logger.info('Update Risk Factor: Mid Capitalization')
        mkt_cap_ard = self.data['mkt_cap_ard']
        univ = self.data['risk_univ']
        mkt_cap_ard[~univ] = np.nan # filter for not in universe
        size = norm_winsor(np.log(mkt_cap_ard),universe=self.data['risk_univ'])
        size_cube = norm_winsor(size ** 3,universe=self.data['risk_univ'])
        # WLS
        midcap, _, _, _ = regression_ols(y = size_cube, x={'size': size},weight=mkt_cap_ard)
        self.raw.update({'midcap':midcap})


    """Momentum"""


    def risk_momentum(self, look_back_days=252, ma_window=11, lag=11, half_life=126):
        logger.info('Update Risk Factor: Momentum')
        idx = look_back_days + self.iter_num + ma_window + lag + 1
        if len(self.data['excess_return_log'])<idx:
            raise Exception
        rstr_non_lagged = EWMA(self.data['excess_return_log'].iloc[-idx:], look_back_days, half_life)
        rstr = rstr_non_lagged.rolling(ma_window, min_periods=int(ma_window/2)).mean().shift(lag)
        # halpha - computed in hbeta
        self.raw.update({'rstr':rstr})

    """Profitability"""
    def risk_profitability(self):
        logger.info('Update Risk Factor: Profitability')
        
        sales_ttm_qtr = self.fdd['qtr']['TOT_OPER_REV_TTM']
        cogs_ttm_qtr = self.fdd['qtr']['S_FA_GC_TTM']
        total_assets_qtr = self.fdd['qtr']['TOT_ASSETS']
        #gross_profit_margin_qtr = (sales_ttm_qtr - cogs_ttm_qtr)/sales_ttm_qtr
        #roa_qtr = self.fdd['qtr']['net_profit_ttm'] / total_assets_qtr

        ato_qtr = sales_ttm_qtr/total_assets_qtr
        gp_qtr = (sales_ttm_qtr - cogs_ttm_qtr)/total_assets_qtr
        gpm_qtr = self.fdd['qtr']['S_FA_GROSSPROFITMARGIN_TTM']
        roa_qtr = self.fdd['qtr']['S_FA_ROA_TTM']

        ato = self.backfiller(ato_qtr)
        gp = self.backfiller(gp_qtr)
        gpm = self.backfiller(gpm_qtr)
        roa = self.backfiller(roa_qtr)
        self.raw.update({'ato':ato,'gp':gp,'gpm':gpm,'roa':roa})
        
    """Volatility"""
    def risk_residual_volatility(self, half_life=42, look_back_days=252):
        logger.info('Update Risk Factor: Residual Volatility')
        idx = look_back_days + self.iter_num + 1
        dastd = EWMA(self.data['excess_return'].iloc[-idx:,:], look_back_days, half_life, ufunc='std',min_pct=self.md_min_pct)
        cmra = self.data['excess_return_log'].iloc[-idx:,:].rolling(look_back_days, 
                                                                    min_periods=int(look_back_days*self.md_min_pct)).apply(
                                                                    lambda x: np.max(np.cumsum(x)) - np.min(np.cumsum(x)))
        self.raw.update({'dastd':dastd,'cmra':cmra})

    """Size"""

    def risk_size(self):
        logger.info('Update Risk Factor: Size')
        mkt_cap_ard = self.data['mkt_cap_ard']
        lncap = np.log(mkt_cap_ard)
        self.raw.update({'lncap':lncap})

    def risk_industry(self):
        self.style.update({'industry':self.data['industry']})

    def update_descriptor(self):
        logger.info('*'*40)
        logger.info('* Update Descriptor *')
        tic = time.time()

        self.risk_beta()
        self.risk_book_to_price()
        self.risk_dividend_yield()
        self.risk_earnings_quality()
        self.risk_earnings_variability()
        self.risk_earnings_yield()
        self.risk_growth()
        self.risk_investment_quality()
        self.risk_leverage()
        self.risk_liquidity()
        self.risk_long_term_reversal()
        self.risk_mid_cap()
        self.risk_momentum()
        self.risk_profitability()
        self.risk_residual_volatility()
        self.risk_size()
        
        logger.info('Process Descriptor')
        des_list = list(self.raw.keys())
        des_num = len(des_list)
        
        if self.parallel:
            raw_dict = multiprocess_wrapper(func=standard_process,iter_list=self.raw,collect_output=True,
                                            stock_filter=self.data['risk_univ'], stock_industry=self.data['industry'],
                                            date_complete=self.check_date_complete)
            self.descriptor = raw_dict
        else:
            for des in self.raw:
                logger.info('%d/%d - %s'%(des_list.index(des)+1,des_num,des))
                #self.descriptor[des] = self.baseline_process(self.raw[des])
                self.descriptor[des] = standard_process(self.raw[des],stock_filter=self.data['risk_univ'], 
                                                        stock_industry=self.data['industry'],date_complete=self.check_date_complete)
        toc = time.time()
        logger.info('* Descriptor Process Done %s*'%(print_time(toc,tic)))
        return 


    def update_style(self):        
        logger.info('*'*40)
        logger.info('* Update Style *')
        tic = time.time()
        self.style['Beta'] = self.descriptor['hbeta']
        
        self.style['BookToPrice'] = self.descriptor['btop']
        
        self.style['DividendYield'] = self.descriptor['dtop']
        
        self.style['EarningsQuality'] = self.descriptor['abs'] + self.descriptor['acf']
        
        self.style['EarningsVariability'] = self.descriptor['vsal'] + self.descriptor['vern'] + self.descriptor['vflo']
        
        self.style['EarningsYield'] = self.descriptor['cetop'] + self.descriptor['etop'] + self.descriptor['em']
        
        self.style['Growth'] = self.descriptor['egro'] + self.descriptor['sgro']
        
        self.style['InvestmentQuality'] = self.descriptor['agro'] + self.descriptor['igro'] + self.descriptor['cxgro']
        
        self.style['Leverage'] = self.descriptor['mlev'] + self.descriptor['blev'] + self.descriptor['dtoa']
        
        self.style['Liquidity'] = self.descriptor['stom'] + self.descriptor['stoq'] + self.descriptor['stoa'] + self.descriptor['avtr'] 
        
        self.style['LongTermReversal'] = self.descriptor['ltrstr'] + self.descriptor['lthalpha']
        
        self.style['MidCapitalization'] = self.descriptor['midcap']
        
        self.style['Momentum'] = self.descriptor['rstr'] + self.descriptor['halpha']
        
        self.style['Profitability'] = self.descriptor['ato'] + self.descriptor['gp'] + self.descriptor['gpm'] + self.descriptor['roa']
        
        self.style['ResidualVolatility'] = self.descriptor['hsigma'] + self.descriptor['dastd'] + self.descriptor['cmra']
        
        self.style['Size'] = self.descriptor['lncap']

        logger.info('Process Style')
        
        #sepcial_list = ['LongTermReversal']
        style_list = list(self.style.keys())
        style_num = len(style_list)

        if self.parallel:
            style_dict = multiprocess_wrapper(func=standard_process,iter_list=self.style,collect_output=True,
                                              stock_filter=self.data['risk_univ'], stock_industry=self.data['industry'],
                                              date_complete=self.check_date_complete)
            self.style = style_dict
        else:
            for s in self.style:
                logger.info('%d/%d - %s'%(style_list.index(s)+1,style_num,s))
                #self.style[s] = self.baseline_process(self.style[s])
                self.style[s] = standard_process(self.style[s],stock_filter=self.data['risk_univ'], 
                                                 stock_industry=self.data['industry'],
                                                 date_complete=self.check_date_complete)
            
        LongTermReversal, _, _, _ = regression_ols(y=self.style['LongTermReversal'], x={'Momentum': self.style['Momentum']})
        
        ResidualVolatility, _, _, _ = regression_ols(y=self.style['ResidualVolatility'], x={'Size': self.style['Size'],'Beta':self.style['Beta']})
            
        self.style['LongTermReversal'] = standard_process(LongTermReversal,stock_filter=self.data['risk_univ'], 
                                                          stock_industry=self.data['industry'],
                                                          date_complete=self.check_date_complete)
        
        self.style['ResidualVolatility'] = standard_process(ResidualVolatility,stock_filter=self.data['risk_univ'], 
                                                            stock_industry=self.data['industry'],
                                                            date_complete=self.check_date_complete)
 
        self.risk_industry()
        toc = time.time()
        logger.info('* Update Style Done %s*'%(print_time(toc,tic)))
        return 


    def save_factor(self):
        logger.info('*'*40)
        logger.info('* Save Factor *')
        tic = time.time()
        logger.info('Save Descriptor to : %s'%(self.descriptor_path))
        save_factor_tank(self.descriptor,self.descriptor_path,self.append_mode,self.from_scratch,self.cdate_list)
        
        logger.info('Save Style to : %s'%(self.style_path))
        save_factor_tank(self.style,self.style_path,self.append_mode,self.from_scratch,self.cdate_list)
        toc = time.time()
        logger.info('* Save Factor Done - %s *'%(print_time(toc,tic)))
        
        """
        IO.hdf5_node_remover(self.descriptor_path,dataset=des)
        IO.hdf5_node_remover(self.style_path,dataset=s)
        IO.pd_hdf5_writer(self.style['DividendYield'].stack(),self.style_path,dataset=s)        
        IO.pd_hdf5_writer(self.descriptor['dtop'].stack(),self.descriptor_path,dataset=des)        
        """
        return 
    
    def launch(self):
        """raw_tank
                -> filter/norm_winsor/fill_industry
           descriptor_tank
                -> combine/neutral/norm_winsor
            style_tank
                -> save
        """
        tic = time.time()
        
        self.update_descriptor()
        self.update_style()
        self.save_factor()        
        
        toc = time.time()
        logger.info('*** BARRA Risk Update Done - %s ***'%(print_time(toc,tic)))
        
        return

    def load_data(self):
        logger.info('*'*40)
        logger.info('* Prep Data: %s - %s *'%(self.sdate_prev, self.edate))
        tic = time.time()

        self.load_basic_data()
        self.load_fdd_data()    

        toc = time.time()
        logger.info('* Prep Data Done %s *'%(print_time(toc,tic)))
    

def execute(date,sql_config):
    # sdate,edate,cdate_list = check_update_date()
    sdate = edate = date
    self = UpdateBarraRisk(sdate, edate,sql_config=sql_config)
    self.load_data()
    self.launch()


      
        
       

