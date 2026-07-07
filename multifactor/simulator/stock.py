__author__ = "Software Authors: Xu Deyuan"
__copyright__ = "Copyright (C) 2019 HTSC"
__license__ = "Private"
__version__ = "1.0.3"
import configparser
import multifactor.IO.IO as IO
from multifactor.IO.IO_enums import*
import multifactor.utility.dt as tdt
import numpy as np
import pandas as pd
from multifactor.optimizer.cvx_optimizer import CvxOptimizer
import queue
import threading
import logging
import os
from multifactor.simulator.stock_reporter import report_generator
import shelve
import collections
import warnings
import re
import traceback
import sys
def vec_normalize(vec,norm=1):
    _vec=np.fabs(np.array(vec)).reshape(-1)
    _sum=_vec[~np.isnan(_vec)].sum()
    if _sum!=1 and _sum!=0:
        _vec=_vec*norm/_sum
        _vec=[i*abs(j)/j if j!=0 else 0 for i,j in zip(_vec,vec)]
        if type(vec)==np.ndarray:
            return np.array(_vec)
        elif type(vec)==list:
            return _vec
        elif type(vec)==pd.Series:
            return pd.Series(_vec,index=vec.index)
        else:
            raise AssertionError
    else:
        return vec
class Trader:
    def __init__(self):
        self._start_date=None
        self._end_date=None
        self._trade_cycle=None
        self._trade_days_offset=None
        self._benchmark=None
        self._hedge_ratio=None
        self._stock_trade_fee_in=None
        self._stock_trade_fee_out=None
        self._fts_trade_fee_in=None
        self._fts_trade_fee_out=None
        self._init_capital=None
        self._const_capital=None
        self._fts_leverage=None
        self._stock_leverage=None
        self._md_mtx=None
        self._fts_mtx=None
        self._mu_mtx=None
        self._alpha_wt_dic=None
        self._cov_mtx=None
        self._fct_expo_mtx=None
        self._ind_detail_ps=None
        self._idiosyn_mtx=None
        self._ind_weight_ps=None
        self._bench_fct_exp_ps=None
        self._bench_stock_weights_ps=None
        self._risk_aversion_coeff=None
        self._trans_cost_eta=None
        self._trans_penalty_coeff=None
        self._turnover_lim=None
        self._wt_low_lim=None
        self._wt_high_lim=None
        self._fine_tune_huge_stock_weight=None
        self._fund_leverage=None
        self._style_lims_dic=None
        self._ind_dev_value=None
        self._ind_weight_pct_lim=None
        self._ind_ctl_lst=None
        self._no_entry_lst=None
        self._must_in_dic=None
        self._wt_filter_lim=None
        self._buy_price_ref=None
        self._sell_price_ref=None
        self._trans_amt_ratio_lim=None
        self._susp_days_threshold=None
        self.conf_str=None
        self.fts_buy_ref='close'
        self.fts_sell_ref='close'
        self.daily_opt=None
        self.error_flag=False
        self.output_path=None
        self.md_func=None
        self.opt_func=None
        self.poke_func=None
        self.mu_ps=None
        self.stock_account_dic=dict()
        self.futures_account_dic=dict()
        self.stock_account_type_dic=dict()
        self.stock_bank=None
        self.futures_bank=None
        self.stock_tear_sheet_lst=list()
        self.fts_tear_sheet_lst=list()
        self.orders=queue.Queue()
        self.feedback=queue.Queue()
        self.orders_todo=queue.Queue()
        self.pending_stock_set_dic=dict()
        self.cv=threading.Condition()
        self.ts=None
        self.prev_ts=None
        self.stock_turnover_value_dic=dict()
        self.partial_done_set_dic=dict()
        self.stock_value_todo_ps=None
        self.transaction_days=None
        self.executor_active=None
        self.trans_bank_transfer=None
        self.verbose=False
        self.solver=None
        self.logger=None
        self.logger_mode='a'
        self.daily_stock_rtn_dic=dict()
        self.daily_stock_pnl_dic=dict()
        self.daily_stock_adjusted_close_price_dic=dict()
        self.daily_futures_close_price_dic=dict()
        self.daily_bench_stock_weights_dic=dict()
        self.daily_stock_industry_dic=dict()
        self.daily_rtn_sum_dic=dict()
        self.daily_wt_dic=dict()
        self.daily_stock_dic=dict()
        self.daily_stock_sum_dic=dict()
        self.daily_fts_dic=dict()
        self.daily_fts_sum_dic=dict()
        self.daily_cash_dic=dict()
        self.daily_net_dic=dict()
        self.daily_turnover_dic=dict()
        self.wt_target_dic=dict()
        self.trans_fct_expo_dic=dict()
        self.trans_cost_dic=dict()
    @property
    def start_date(self):
        return self._start_date
    @property
    def end_date(self):
        return self._end_date
    @property
    def trade_cycle(self):
        return self._trade_cycle
    @property
    def trade_days_offset(self):
        return self._trade_days_offset
    @property
    def benchmark(self):
        return self._benchmark
    @property
    def hedge_ratio(self):
        return self._hedge_ratio
    @property
    def stock_trade_fee_in(self):
        return self._stock_trade_fee_in
    @property
    def stock_trade_fee_out(self):
        return self._stock_trade_fee_out
    @property
    def fts_trade_fee_in(self):
        return self._fts_trade_fee_in
    @property
    def fts_trade_fee_out(self):
        return self._fts_trade_fee_out
    @property
    def init_capital(self):
        return self._init_capital
    @property
    def const_capital(self):
        return self._const_capital
    @property
    def stock_leverage(self):
        return self._stock_leverage
    @property
    def fts_leverage(self):
        return self._fts_leverage
    @property
    def md_mtx(self):
        return self._md_mtx
    @property
    def fts_mtx(self):
        return self._fts_mtx
    @property
    def mu_mtx(self):
        return self._mu_mtx
    @property
    def bench_fct_exp_ps(self):
        return self._bench_fct_exp_ps
    @property
    def bench_stock_weights_ps(self):
        return self._bench_stock_weights_ps
    @property
    def alpha_wt_dic(self):
        return self._alpha_wt_dic
    @property
    def cov_mtx(self):
        return self._cov_mtx
    @property
    def fct_expo_mtx(self):
        return self._fct_expo_mtx
    @property
    def ind_detail_ps(self):
        return self._ind_detail_ps
    @property
    def idiosyn_mtx(self):
        return self._idiosyn_mtx
    @property
    def ind_weight_ps(self):
        return self._ind_weight_ps
    @property
    def risk_aversion_coeff(self):
        return self._risk_aversion_coeff
    @property
    def trans_cost_eta(self):
        return self._trans_cost_eta
    @property
    def trans_penalty_coeff(self):
        return self._trans_penalty_coeff
    @property
    def turnover_lim(self):
        return self._turnover_lim
    @property
    def wt_low_lim(self):
        return self._wt_low_lim
    @property
    def wt_high_lim(self):
        return self._wt_high_lim
    @property
    def fund_leverage(self):
        return self._fund_leverage
    @property
    def fine_tune_huge_stock_weight(self):
        return self._fine_tune_huge_stock_weight
    @property
    def style_lims_dic(self):
        return self._style_lims_dic
    @property
    def ind_dev_value(self):
        return self._ind_dev_value
    @property
    def ind_weight_pct_lim(self):
        return self._ind_weight_pct_lim
    @property
    def ind_ctl_lst(self):
        return self._ind_ctl_lst
    @property
    def no_entry_lst(self):
        return self._no_entry_lst
    @property
    def must_in_dic(self):
        return self._must_in_dic
    @property
    def reserved_dic(self):
        must_in_dic=self.must_in_dic.copy()if self.must_in_dic is not None else dict()
        return must_in_dic
    @property
    def wt_filter_lim(self):
        return self._wt_filter_lim
    @property
    def buy_price_ref(self):
        return self._buy_price_ref
    @property
    def sell_price_ref(self):
        return self._sell_price_ref
    @property
    def trans_amt_ratio_lim(self):
        return self._trans_amt_ratio_lim
    @property
    def susp_days_threshold(self):
        return self._susp_days_threshold
    def stash(self,filename):
        with shelve.open(filename,'n')as db:
            just_a_dick=dict()
            for attr in self.__dict__:
                if not callable(getattr(self,attr))and not attr.startswith('__')and type(getattr(self,attr))not                        in[threading.Condition,logging.Logger]:
                    if type(getattr(self,attr))is not queue.Queue:
                        just_a_dick[attr]=getattr(self,attr)
                    else:
                        just_a_dick[attr]=getattr(self,attr).queue
            db['money']=just_a_dick
    def unstash(self,filename):
        with shelve.open(os.path.join(self.output_path,filename),'r')as db:
            just_a_dick=db['money']
            for attr in just_a_dick:
                if type(just_a_dick[attr])is not collections.deque:
                    self.__dict__[attr]=just_a_dick[attr]
                else:
                    self.__dict__[attr].queue=just_a_dick[attr]
    def oxidant(self,conf_path,start_date=None,end_date=None,stash=None):
        config=configparser.ConfigParser(allow_no_value=True)
        config.optionxform=str
        with open(conf_path,'r')as conf:
            config.read_file(conf)
            if start_date is not None:
                self._start_date=IO.str_date_parser(start_date)
            else:
                self._start_date=IO.str_date_parser(config['GENERAL']['Start Date'])
            if end_date is not None:
                self._end_date=IO.str_date_parser(end_date)
            else:
                self._end_date=IO.str_date_parser(config['GENERAL']['End Date'])
            self.output_path=config.get('GENERAL','Output Path',fallback='./')
            self.logger=logging.getLogger('Trader')
            self.logger.setLevel(getattr(logging,config['GENERAL']['Logger Level'].upper()))
            try:
                file_handler=logging.FileHandler(os.path.join(self.output_path,config['GENERAL']['Logger File']),mode=self.logger_mode)
            except FileNotFoundError:
                os.makedirs(self.output_path)
                file_handler=logging.FileHandler(os.path.join(self.output_path,config['GENERAL']['Logger File']),mode=self.logger_mode)
            file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(file_handler)
            if stash is not None:
                self.unstash(stash)
                self._start_date=tdt.get_trading_day_offset(self.ts,1,dfreq=DFreq.DAILY)[0]
                self._end_date=IO.str_date_parser(end_date)
                stash_warning_str='\nWARNING: actual config may vary from above since restart is engaged.\n'
                if stash_warning_str not in self.conf_str:
                    self.conf_str=self.conf_str+stash_warning_str
                self.logger.info('stash restored')
                return
            self.logger.info('begin to parse config file')
            if config['GENERAL']['Trade Cycle']in['WEEKLY','DAILY','MONTHLY','BIWEEKLY']:
                self._trade_cycle=config['GENERAL']['Trade Cycle']
            else:
                try:
                    self._trade_cycle=int(config['GENERAL']['Trade Cycle'])
                except ValueError:
                    AssertionError
            self._trade_days_offset=int(config['GENERAL']['Trade Days Offset'])
            if config['GENERAL']['Benchmark']in['HS300','ZZ500','SZ50']:
                self._benchmark=config['GENERAL']['Benchmark']
            else:
                raise AssertionError
            self._hedge_ratio=float(config['GENERAL']['Hedge Ratio'])
            self._stock_leverage=float(config['GENERAL']['Stock Leverage'])
            self._fts_leverage=float(config['GENERAL']['Futures Leverage'])
            self._stock_trade_fee_in=float(config['GENERAL']['Stock Trade Buy Fee'])
            self._stock_trade_fee_out=float(config['GENERAL']['Stock Trade Sell Fee'])
            self._fts_trade_fee_in=float(config['GENERAL']['Futures Trade Buy Fee'])
            self._fts_trade_fee_out=float(config['GENERAL']['Futures Trade Sell Fee'])
            if config['GENERAL']['Interest Type']=='SIMPLE':
                self._const_capital=float(config['GENERAL']['Initial Capital'])
            elif config['GENERAL']['Interest Type']=='ACCUMULATIVE':
                self._init_capital=float(config['GENERAL']['Initial Capital'])
            else:
                raise AssertionError
            self.daily_opt=config['GENERAL'].getboolean('Daily Optimization')
            tmp_dic=dict()
            for key in config['ALPHA WEIGHTS']:
                tmp_dic[key]=float(config['ALPHA WEIGHTS'][key])
            if len(tmp_dic)>0:
                self._alpha_wt_dic=tmp_dic
            else:
                raise AssertionError
            self._risk_aversion_coeff=float(config['OPTIMIZER PARAMETERS']['Risk Aversion Coefficient'])
            self._trans_cost_eta=float(config['OPTIMIZER PARAMETERS']['Turnover Penalty Power'])
            self._trans_penalty_coeff=float(config['OPTIMIZER PARAMETERS']['Turnover Penalty Coefficient'])
            self._turnover_lim=float(config['OPTIMIZER PARAMETERS']['Turnover Hard Limit'])
            self._wt_low_lim=float(config['OPTIMIZER PARAMETERS']['Stock Minimum Weight'])
            self._wt_high_lim=float(config['OPTIMIZER PARAMETERS']['Stock Maximum Weight'])
            self._fund_leverage=float(config['OPTIMIZER PARAMETERS']['Leverage Ratio'])
            self._fine_tune_huge_stock_weight=config.getboolean('OPTIMIZER PARAMETERS','Fine Tune Huge Stock Weight',fallback=True)
            try:
                tmp_dic=dict()
                for key in config['STYLE FACTOR CONTROL']:
                    tmp_dic[key]=[float(item)for item in config['STYLE FACTOR CONTROL'][key].split(',')]
                if len(tmp_dic)>0:
                    self._style_lims_dic=tmp_dic
            except KeyError:
                pass
            self._ind_dev_value=config.getfloat('INDUSTRY CONTROL','Benchmark Deviation',fallback=None)
            self._ind_weight_pct_lim=config.getfloat('INDUSTRY CONTROL','Weight Percentage On Watch',fallback=None)
            try:
                if config['INDUSTRY CONTROL']['Restrict to Benchmark']is not None:
                    if len(config['INDUSTRY CONTROL']['Restrict to Benchmark'])>0:
                        self._ind_ctl_lst=config['INDUSTRY CONTROL']['Restrict to Benchmark'].split()
            except KeyError:
                pass
            try:
                if config['OPTIMIZER PARAMETERS']['Stock Blacklist']is not None:
                    if len(config['OPTIMIZER PARAMETERS']['Stock Blacklist'])>0:
                        self._no_entry_lst=config['OPTIMIZER PARAMETERS']['Stock Blacklist'].split()
            except KeyError:
                pass
            try:
                tmp_dic=dict()
                for key in config['STOCK WHITELIST']:
                    tmp_dic[key]=float(config['STOCK WHITELIST'][key])
                if len(tmp_dic)>0:
                    self._must_in_dic=tmp_dic
            except(KeyError,TypeError):
                pass
            self._wt_filter_lim=float(config['TRANSACTIONAL PARAMETERS']['Stock Weight Threshold'])
            self._trans_amt_ratio_lim=float(config['TRANSACTIONAL PARAMETERS']['Maximum Buyable Ratio'])
            self._susp_days_threshold=int(config['TRANSACTIONAL PARAMETERS']['Suspension Days to Exclude'])
            self._buy_price_ref=config['TRANSACTIONAL PARAMETERS']['Buy Price Kind']
            self._sell_price_ref=config['TRANSACTIONAL PARAMETERS']['Sell Price Kind']
            if self.init_capital is not None:
                self.stock_bank=Bank(self.init_capital/(1+self.hedge_ratio))
                self.futures_bank=Bank(self.init_capital*self.hedge_ratio/(1+self.hedge_ratio))
            else:
                self.stock_bank=Bank(self.const_capital/(1+self.hedge_ratio))
                self.futures_bank=Bank(self.const_capital*self.hedge_ratio/(1+self.hedge_ratio))
            self.futures_account_dic={self.benchmark:Account(self.benchmark,self.fts_trade_fee_in,self.fts_trade_fee_out,self.fts_leverage*self.fund_leverage,self.futures_bank)}
            self.logger.info('end parsing config file')
        with open(conf_path,'r')as conf:
            self.conf_str=conf.read()
    def trade_days(self,offset=0):
        end_date=self.end_date+pd.Timedelta(days=100)
        start_date=self.start_date-pd.Timedelta(days=100)
        if self.trade_cycle=='DAILY':
            days=tdt.get_trading_date_range(start_date,end_date,dfreq=DFreq.DAILY)
        elif self.trade_cycle=='WEEKLY':
            days=tdt.get_trading_date_range(start_date,end_date,dfreq=DFreq.WEEKLY)
        elif self.trade_cycle=='MONTHLY':
            days=tdt.get_trading_date_range(start_date,end_date,dfreq=DFreq.MONTHLY)
        elif self.trade_cycle=='BIWEEKLY':
            days=tdt.get_trading_date_range(start_date,end_date,dfreq=DFreq.WEEKLY)
            days=days[::2]
        elif isinstance(self.trade_cycle,int):
            days=tdt.get_trading_date_range(start_date,end_date,dfreq=DFreq.DAILY)
            days=days[::self.trade_cycle]
        else:
            raise AssertionError
        if offset!=0:
            days=[tdt.get_trading_day_offset(day,offset,dfreq=DFreq.DAILY)[0]for day in days]
        return days
    def deoxidant(self,mu_mtx=None,cov_mtx=None,fct_expo_mtx=None,idiosyn_mtx=None,ind_weight_ps=None,bench_fct_exp_ps=None,control_lst=None,bench_stock_weights_ps=None,**kwargs):
        assert mu_mtx is not None
        if bench_stock_weights_ps is not None:
            self._bench_stock_weights_ps=bench_stock_weights_ps
        if fct_expo_mtx is not None and ind_weight_ps is not None:
            ind_order_lst=[item for item in fct_expo_mtx.columns if item in ind_weight_ps.index]
            self._ind_weight_ps=ind_weight_ps.reindex(ind_order_lst)
            self._ind_detail_ps=fct_expo_mtx[ind_order_lst].idxmax(axis=1)
        else:
            self._ind_weight_ps=None
        if control_lst is None:
            control_lst=[]
        else:
            control_lst=list(control_lst.copy())
        if self.no_entry_lst is not None:
            control_lst=list(set(control_lst).union(self.no_entry_lst))
        stock_pool=set(mu_mtx.index)
        if cov_mtx is not None:
            stock_pool=stock_pool.intersection(cov_mtx.index)
        stock_pool=stock_pool.intersection(fct_expo_mtx.index)if fct_expo_mtx is not None else stock_pool
        stock_pool=stock_pool.intersection(idiosyn_mtx.index)if idiosyn_mtx is not None else stock_pool
        stock_pool=stock_pool.difference(control_lst)
        stock_pool=stock_pool.union(self.reserved_dic.keys())
        self.logger.info('stock pool num: %d'%len(stock_pool))
        self._mu_mtx=mu_mtx.reindex(sorted(stock_pool)).fillna(0)
        self._fct_expo_mtx=fct_expo_mtx.reindex(self.mu_mtx.index).fillna(0)if fct_expo_mtx is not None else None
        if cov_mtx is not None:
            self._cov_mtx=cov_mtx.reindex(index=self.mu_mtx.index,columns=self.mu_mtx.index)
        else:
            self._cov_mtx=None
        if idiosyn_mtx is not None:
            self._idiosyn_mtx=idiosyn_mtx.reindex(index=self.mu_mtx.index,columns=self.mu_mtx.index).fillna(0)
        if fct_expo_mtx is not None and bench_fct_exp_ps is not None:
            self._bench_fct_exp_ps=bench_fct_exp_ps.reindex(self.fct_expo_mtx.columns).fillna(0)
    def md_slicer(self,func,ts):
        self._md_mtx=None
        self._fts_mtx=None
        self._md_mtx,self._fts_mtx=func(ts)
    def opt_slicer(self,func,ts,control_lst=None):
        self._mu_mtx=None
        self._cov_mtx=None
        self._fct_expo_mtx=None
        self._idiosyn_mtx=None
        self._ind_weight_ps=None
        self._bench_fct_exp_ps=None
        self._bench_stock_weights_ps=None
        self.deoxidant(**func(ts,self.benchmark),control_lst=control_lst)
    def optimize(self):
        reserved_ps=pd.Series(self.reserved_dic)
        THRESHOLD_LIM=100
        trial_counter=0
        TRIAL_MAX_NUM=6
        while trial_counter<TRIAL_MAX_NUM:
            trial_counter+=1
            relax_coeff=1+(trial_counter-1)/(TRIAL_MAX_NUM-1)
            opt=CvxOptimizer()
            opt.solver=self.solver
            opt.verbose=self.verbose
            if self.idiosyn_mtx is not None:
                opt.idiosyn_mtx=np.array(self.idiosyn_mtx)
            if self.fct_expo_mtx is not None:
                opt.fct_expo_mtx=np.array(self.fct_expo_mtx)
            if self.cov_mtx is not None:
                opt.cov_mtx=np.array(self.cov_mtx)
            ps_alpha=pd.Series(self.alpha_wt_dic)
            assert self.mu_mtx is not None
            self.mu_ps=self.mu_mtx.reindex(columns=ps_alpha.index).dot(ps_alpha)
            if len(self.mu_ps)==0:
                self.logger.warning('empty alpha data given, return empty portfolio series')
                return reserved_ps
            opt.mu_vec=np.array(self.mu_ps)
            opt.bench_vec=np.array(self.bench_stock_weights_ps.reindex(self.mu_ps,fill_value=0))
            opt.eta=self.trans_cost_eta
            opt.penalty_coeff=self.trans_penalty_coeff
            opt.risk_aversion=self.risk_aversion_coeff
            wt_low_lims_ps=pd.Series(self.wt_low_lim,index=self.mu_mtx.index)
            wt_high_lims_ps=pd.Series(self.wt_high_lim,index=self.mu_mtx.index)
            prev_weight=pd.Series(self.get_stock_balances(self.stock_account_dic.keys(),weight=True,dictionary=True,status='~Pending',signed_book_value=True))
            opt.w0=prev_weight.reindex(index=self.mu_mtx.index).fillna(0).tolist()
            ind_on_watch_ps=None
            if self.ind_weight_pct_lim is not None:
                assert self.fct_expo_mtx is not None and self.ind_weight_ps is not None
                assert self.ind_dev_value is not None
                ind_on_watch_ps=self.ind_weight_ps.sort_values().cumsum()
                ind_on_watch_ps=self.ind_weight_ps.reindex(ind_on_watch_ps.loc[ind_on_watch_ps>=1-self.ind_weight_pct_lim/100].index)
            if self.fine_tune_huge_stock_weight:
                for item in self.bench_stock_weights_ps.index:
                    if item not in self.mu_mtx.index:
                        continue
                    wt_high_lims_ps.loc[item]=self.bench_stock_weights_ps.loc[item]+self.wt_high_lim
                    wt_low_lims_ps.loc[item]=max(0,self.bench_stock_weights_ps.loc[item]-self.wt_high_lim)
            else:
                if self.ind_weight_pct_lim is not None or self.ind_dev_value is not None:
                    ind_stock_num_ps=self.fct_expo_mtx.sum().reindex(self.ind_weight_ps.index)
                    ind_min_wt_ps=self.ind_weight_ps.divide(ind_stock_num_ps)
                    ind_min_wt_ps=ind_min_wt_ps.multiply(5*relax_coeff)
                    ind_min_wt_ps=ind_min_wt_ps.loc[ind_min_wt_ps>=self.wt_high_lim]
                    if self.ind_weight_pct_lim is not None:
                        ind_min_wt_ps=ind_min_wt_ps.reindex(ind_on_watch_ps.index).dropna()
                    for item in ind_min_wt_ps.index:
                        ind_ps=self.fct_expo_mtx[item]
                        ind_ps=ind_ps.loc[ind_ps!=0]
                        wt_high_lims_ps.loc[ind_ps.index]=ind_min_wt_ps[item]
            wt_low_lims_ps.loc[reserved_ps.index]=reserved_ps-1e-5
            wt_high_lims_ps.loc[reserved_ps.index]=reserved_ps+1e-5
            CvxOptimizer.wt_low_lims_ps=np.array(wt_low_lims_ps)
            CvxOptimizer.wt_high_lims_ps=np.array(wt_high_lims_ps)
            opt.add_rule('wt_low_lim','self.w >= CvxOptimizer.wt_low_lims_ps')
            opt.add_rule('wt_high_lim','self.w <= CvxOptimizer.wt_high_lims_ps')
            opt.add_rule('wt_sum','cvx.norm(self.w, 1) <= 1')
            # print(prev_weight)
            if prev_weight.abs().sum()!=0:
                opt.add_rule('turn_over_lim','cvx.norm(self.w - self.w0, 1) / 2 <= %s'%(self.turnover_lim*relax_coeff))
            if self.fct_expo_mtx is not None:
                fct_expo_cols=self.fct_expo_mtx.columns
                fct_low_lims_ps=pd.Series(-THRESHOLD_LIM,index=fct_expo_cols)
                fct_high_lims_ps=pd.Series(THRESHOLD_LIM,index=fct_expo_cols)
                if self.style_lims_dic is not None:
                    for style in self.style_lims_dic:
                        style_lims=np.array(self.style_lims_dic[style])
                        fct_low_lims_ps.loc[style],fct_high_lims_ps.loc[style]=(style_lims-style_lims.mean())*relax_coeff+style_lims.mean()
                if self.ind_dev_value is not None:
                    if self.ind_ctl_lst is not None:
                        assert ind_on_watch_ps is None
                        controlled_inds=self.ind_ctl_lst
                    elif ind_on_watch_ps is not None:
                        controlled_inds=list(ind_on_watch_ps.index)
                    else:
                        controlled_inds=list(self.ind_weight_ps.index)
                    fct_low_lims_ps.loc[controlled_inds]=-abs(self.ind_dev_value)*relax_coeff
                    fct_high_lims_ps.loc[controlled_inds]=abs(self.ind_dev_value)*relax_coeff
                if self.bench_fct_exp_ps is not None:
                    fct_low_lims_ps=fct_low_lims_ps+self.bench_fct_exp_ps
                    fct_high_lims_ps=fct_high_lims_ps+self.bench_fct_exp_ps
                ind_nums=self.fct_expo_mtx.sum(axis=0)
                if len(ind_nums.loc[ind_nums==0])>0:
                    self.logger.warning('%s not full, check alpha input or style factors'%', '.join(map(str,ind_nums.loc[ind_nums==0.0].index.tolist())))
                CvxOptimizer.fct_low_lims_ps=np.array(fct_low_lims_ps)
                CvxOptimizer.fct_high_lims_ps=np.array(fct_high_lims_ps)
                opt.add_rule('style_low_lim_vec','self.fct_expo_mtx.T * self.w >= CvxOptimizer.fct_low_lims_ps')
                opt.add_rule('style_high_lim_vec','self.fct_expo_mtx.T * self.w <= CvxOptimizer.fct_high_lims_ps')
            opt.check_run()
            try:
                opt.run()
                if 'optimal' in opt.status or 'optimal'.upper()in opt.status:
                    self.logger.info('[%s] %s optimization finished with status %s %s'%(trial_counter,opt.solver,opt.status,self.ts))
                    return pd.Series(np.array(opt.w.value).reshape(-1),index=self.mu_mtx.index)
                else:
                    self.logger.warning('[%s] %s optimization finished with status %s %s'%(trial_counter,opt.solver,opt.status,self.ts))
            except Exception as _exp:
                self.logger.warning('[%s] %s optimization failed %s: %s'%(trial_counter,opt.solver,self.ts,_exp))
        raise StopIteration
    def get_stock_balances(self,account_lst,weight=False,dictionary=False,ref='book_value',status=None,signed_book_value=False):
        balances=[]
        candidates=[]
        status_func=lambda x:x
        if status is not None and '~' in status:
            status_func=lambda x:not x
            status=status.replace('~','').strip()
        for stock in account_lst:
            try:
                value=getattr(self.stock_account_dic[stock],ref)
            except KeyError:
                try:
                    self.stock_account_dic[stock]=Account(stock,self.stock_trade_fee_in,self.stock_trade_fee_out,self.stock_leverage*self.fund_leverage,self.stock_bank)
                except TypeError:
                    self.stock_account_dic={stock:Account(stock,self.stock_trade_fee_in,self.stock_trade_fee_out,self.stock_leverage*self.fund_leverage,self.stock_bank)}
                finally:
                    value=getattr(self.stock_account_dic[stock],ref)
            if status is not None:
                if status_func(self.stock_account_dic[stock].status!=status):
                    continue
                else:
                    candidates.append(stock)
            else:
                candidates.append(stock)
            if ref=='book_value' and signed_book_value:
                if self.stock_account_dic[stock].long_amount-self.stock_account_dic[stock].short_amount>=0:
                    balances.append(value)
                else:
                    balances.append(-value)
            else:
                balances.append(value)
        if weight:
            total_balance=sum([abs(item)for item in balances])
            if total_balance==0:
                balances=[0 for item in balances]
            else:
                balances=[item/total_balance for item in balances]
        if dictionary:
            return dict(zip(candidates,balances))
        else:
            return balances
    def get_futures_balances(self,account_lst,weight=False,dictionary=False,ref='book_value',status=None,signed_book_value=False):
        balances=[]
        candidates=[]
        status_func=lambda x:x
        if status is not None and '~' in status:
            status_func=lambda x:not x
            status=status.replace('~','').strip()
        for futures in account_lst:
            try:
                value=getattr(self.futures_account_dic[futures],ref)
            except KeyError:
                try:
                    self.futures_account_dic[futures]=Account(futures,self.fts_trade_fee_in,self.fts_trade_fee_out,self.fts_leverage*self.fund_leverage,self.futures_bank)
                except TypeError:
                    self.futures_account_dic={futures:Account(futures,self.fts_trade_fee_in,self.fts_trade_fee_out,self.fts_leverage*self.fund_leverage,self.futures_bank)}
                finally:
                    value=getattr(self.futures_account_dic[futures],ref)
            if status is not None:
                if status_func(self.futures_account_dic[futures].status!=status):
                    continue
                else:
                    candidates.append(futures)
            else:
                candidates.append(futures)
            if ref=='book_value' and signed_book_value:
                if self.futures_account_dic[futures].long_amount-self.futures_account_dic[futures].short_amount>=0:
                    balances.append(value)
                else:
                    balances.append(-value)
            else:
                balances.append(value)
        if weight:
            total_balance=sum([abs(item)for item in balances])
            if total_balance==0:
                balances=[0 for item in balances]
            else:
                balances=[item/total_balance for item in balances]
        if dictionary:
            return dict(zip(candidates,balances))
        else:
            return balances
    def account_updater(self,ref,action=False):
        if ref=='close' and action and self.ts not in self.pending_stock_set_dic:
            self.pending_stock_set_dic[self.ts]=set()
        for stock,account in self.stock_account_dic.items():
            if account.status=='Normal' and max(account.long_amount,account.short_amount)==0:
                account.adjfactor=None
                continue
            volume,adjfactor,ref_price=self.md_mtx.loc[stock,['volume','adjfactor',ref]]
            if account.adjfactor is None:
                account.adjfactor=adjfactor
            else:
                adj_ratio=adjfactor/account.adjfactor
                if adj_ratio!=1:
                    if np.isnan(adj_ratio):
                        adj_ratio=1
                    account.amount_touch(adj_ratio)
                    account.adjfactor=adjfactor
            if volume!=0:
                account.susp_days=0
                try:
                    prev_price=account.book_value/(account.long_amount+account.short_amount)
                except(FloatingPointError,ZeroDivisionError):
                    prev_price=0
                pct_chg=(ref_price-prev_price)/prev_price*100 if prev_price!=0 else 0
                pct_chg=0 if np.isnan(pct_chg)else pct_chg
                account.touch(pct_chg)
                if account.status=='Pending' and ref=='close' and action:
                    if account.book_value!=0:
                        self.logger.warning('%s added to pending list %s'%(stock,self.ts))
                        self.pending_stock_set_dic[self.ts].add(stock)
                        if account.long_amount!=0:
                            self.orders_todo.put(Event(account,account.long_amount,self.ts,account.long_close),block=True)
                        if account.short_amount!=0:
                            self.orders_todo.put(Event(account,account.short_amount,self.ts,account.short_close),block=True)
                    else:
                        account.status='Normal'
                if account.status=='Partial Done' and ref=='close' and action:
                    account.status='Normal'
            else:
                if ref=='close' and action:
                    account.susp_days+=1
                    if stock not in self.reserved_dic and(account.susp_days>=self.susp_days_threshold or account.status=='Pending'):
                        self.logger.warning('%s added to pending list %s'%(stock,self.ts))
                        self.pending_stock_set_dic[self.ts].add(stock)
                        if account.long_amount!=0:
                            self.orders_todo.put(Event(account,account.long_amount,self.ts,account.long_close),block=True)
                        if account.short_amount!=0:
                            self.orders_todo.put(Event(account,account.short_amount,self.ts,account.short_close),block=True)
                        account.status='Pending'
        for futures,account in self.futures_account_dic.items():
            try:
                prev_price=account.book_value/(account.long_amount+account.short_amount)
            except(FloatingPointError,ZeroDivisionError):
                prev_price=0
            ref_price=self.fts_mtx.loc[futures,'close']
            pct_chg=(ref_price-prev_price)/prev_price*100 if prev_price!=0 else 0
            account.touch(pct_chg)
    def poke(self,tomorrow=False):
        if tomorrow:
            ts=tdt.get_trading_day_offset(self.ts,1,dfreq=DFreq.DAILY)[0]
            prev_ts=self.ts
        else:
            ts=self.ts
            prev_ts=self.prev_ts
        self.logger.info('retrieving optimization data %s'%ts)
        if prev_ts is not None:
            self.opt_slicer(self.opt_func,ts,control_lst=self.pending_stock_set_dic[prev_ts])
        else:
            self.opt_slicer(self.opt_func,ts)
        self.logger.info('optimization initiated %s'%ts)
        optimal_wt=self.optimize()
        optimal_portion=optimal_wt.abs().sum()
        optimal_portion=optimal_portion if optimal_portion<=1 else 1
        optimal_wt=vec_normalize(optimal_wt.loc[optimal_wt.abs()>abs(self.wt_filter_lim)],optimal_portion)
        self.wt_target_dic[ts]=optimal_wt.sort_index()
    def navigator(self,ts):
        self.logger.info('retrieving market data %s'%ts)
        self.md_slicer(self.md_func,ts)
        self.prev_ts=self.ts
        self.ts=ts
        self.trans_bank_transfer=0
        if self.daily_opt or self.ts in self.transaction_days:
            if self.poke_func is not None:
                self.logger.info('third party optimization function triggered %s'%self.ts)
                custom_target_weight=self.poke_func(self.ts)
            else:
                self.poke()
            self.logger.info('target weight calculated %s'%self.ts)
        with self.cv:
            if not self.orders_todo.empty():
                self.logger.info('daily chores to clear pending stocks %s'%ts)
                self.account_updater(self.sell_price_ref)
                self.chores()
            if self.ts in self.transaction_days:
                self.logger.info('transaction day in process %s'%ts)
                self.account_updater(self.sell_price_ref)
                self.logger.info('rebalance stock & futures banks to prepare for transactions %s'%ts)
                prev_stock_net_value=sum(self.get_stock_balances(self.stock_account_dic.keys(),ref='value',status='~Pending'))
                prev_fts_net_value=sum(self.get_futures_balances(self.futures_account_dic,ref='value',status='~Pending'))
                prev_cash_value=self.futures_bank.value+self.stock_bank.value
                prev_net_value=prev_stock_net_value+prev_fts_net_value+prev_cash_value
                if self.const_capital is not None:
                    self.trans_bank_transfer=prev_net_value-self.const_capital
                    if self.trans_bank_transfer>0:
                        self.stock_bank.withdraw(self.trans_bank_transfer)
                    else:
                        self.stock_bank.deposit(-self.trans_bank_transfer)
                    prev_net_value=self.const_capital
                next_stock_side_value=prev_net_value/(1+self.hedge_ratio)
                bank_transfer=prev_stock_net_value+self.stock_bank.value-next_stock_side_value
                if bank_transfer>0:
                    self.stock_bank.withdraw(bank_transfer)
                    self.futures_bank.deposit(bank_transfer)
                else:
                    self.stock_bank.deposit(-bank_transfer)
                    self.futures_bank.withdraw(-bank_transfer)
                next_fts_side_value=self.futures_bank.value+prev_fts_net_value
                self.logger.info('stocks transactions begin %s'%ts)
                stock_value_target=self.wt_target_dic[self.ts].multiply(next_stock_side_value)
                if self.prev_ts is not None:
                    stock_book_value_current=pd.Series(self.get_stock_balances(self.stock_account_dic.keys(),weight=False,dictionary=True,signed_book_value=True,status='~Pending'))
                    stock_value_current=stock_book_value_current.loc[stock_book_value_current!=0].multiply(1/(self.stock_leverage*self.fund_leverage))
                    self.stock_value_todo_ps=stock_value_target.subtract(stock_value_current,fill_value=0)
                else:
                    self.stock_value_todo_ps=stock_value_target
                self.logger.info('jettison stocks to collect cash first %s'%ts)
                self.get_stock_balances(self.stock_value_todo_ps.index)
                jettison_stats=self.jettison(direction='close')
                self.logger.info('ballast portfolio using available cashes %s'%ts)
                open_value_target=jettison_stats['open_book_value']/(self.stock_leverage*self.fund_leverage)
                try:
                    if open_value_target>self.stock_bank.value:
                        adj_ratio=self.stock_bank.value/open_value_target
                    else:
                        adj_ratio=1
                except(FloatingPointError,ZeroDivisionError):
                    adj_ratio=0
                if adj_ratio<0:
                    self.logger.info('Majoy events detected, panic or joy? %s'%ts)
                    adj_ratio=0
                for open_event in jettison_stats['open_events']:
                    stock_ticker=open_event.account.ticker
                    sell_ref_price,buy_ref_price=self.md_mtx.loc[stock_ticker,[self.sell_price_ref,self.buy_price_ref]]
                    open_event.amount=amount_adjust(open_event.amount*adj_ratio*sell_ref_price/buy_ref_price,category='Sell')
                    if open_event.amount!=0:
                        self.orders.put(open_event,block=True)
                self.cv.notify_all()
                self.cv.wait()
                self.feedback_collector()
                self.logger.info('futures transactions begin %s'%ts)
                self.account_updater('close',action=False)
                after_trans_stock_book_value=sum(self.get_stock_balances(self.stock_account_dic.keys(),status='~Pending',signed_book_value=True))
                fts_account=self.futures_account_dic[self.benchmark]
                fts_price=self.fts_mtx.loc[self.benchmark,self.fts_sell_ref]
                if abs(after_trans_stock_book_value)/next_fts_side_value>fts_account.leverage:
                    if next_fts_side_value-prev_fts_net_value>0:
                        fts_amount=(next_fts_side_value-prev_fts_net_value)*fts_account.leverage/fts_price
                        self.orders.put(Event(fts_account,fts_amount,self.ts,fts_account.short_open))
                    else:
                        fts_amount=abs(next_fts_side_value-prev_fts_net_value)*fts_account.leverage/fts_price
                        self.orders.put(Event(fts_account,fts_amount,self.ts,fts_account.short_close))
                else:
                    fts_amount=after_trans_stock_book_value/fts_price-fts_account.short_amount
                    if fts_amount>0:
                        self.orders.put(Event(fts_account,fts_amount,self.ts,fts_account.short_open))
                    else:
                        self.orders.put(Event(fts_account,abs(fts_amount),self.ts,fts_account.short_close))
                self.cv.notify_all()
                self.cv.wait()
                self.fts_feedback_collector()
                stock_wt_after_trans=pd.Series(self.get_stock_balances(self.stock_account_dic.keys(),weight=True,dictionary=True,signed_book_value=True,status='~Pending'))
                stock_wt_after_trans=stock_wt_after_trans.loc[stock_wt_after_trans!=0]
                if self.no_entry_lst is not None:
                    stock_wt_after_trans.drop(self.no_entry_lst,errors='ignore',inplace=True)
                actual_stock_exposure_ps=pd.Series()
                if self.mu_ps is not None:
                    alpha_expo=self.mu_ps.reindex(stock_wt_after_trans.index).fillna(0).dot(stock_wt_after_trans)
                    actual_stock_exposure_ps['alpha_expo']=alpha_expo
                if self.fct_expo_mtx is not None:
                    fct_expo_ps=self.fct_expo_mtx.reindex(stock_wt_after_trans.index).fillna(0).T.dot(stock_wt_after_trans).subtract(self.bench_fct_exp_ps,fill_value=0)
                    actual_stock_exposure_ps=actual_stock_exposure_ps.append(fct_expo_ps)
                self.trans_fct_expo_dic[self.ts]=actual_stock_exposure_ps
            self.logger.info('call it a day by updating everything %s'%ts)
            self.account_updater('close',action=True)
            self.prober()
    def safety_check(self):
        if self.poke_func is not None:
            self._susp_days_threshold=np.inf
            msg='suspended stocks manipulation deactivated for third party weights input'
            warnings.warn(msg)
            self.logger.warning(msg)
        assert self.buy_price_ref==self.sell_price_ref,'sell & buy refs not same'
    def pilot(self):
        np.seterr(all='raise')
        self.safety_check()
        self.logger.info('safety check complete')
        self.logger.info('pilot in action')
        self.transaction_days=self.trade_days(offset=self.trade_days_offset)
        trading_days=tdt.get_trading_date_range(self.start_date,self.end_date,dfreq=DFreq.DAILY)
        try:
            for day in trading_days:
                self.navigator(day)
            if tdt.get_trading_day_offset(self.end_date,1,dfreq=DFreq.DAILY)[0]in self.transaction_days and self.poke_func is None:
                self.poke(tomorrow=True)
        except Exception as _exp:
            self.error_flag=True
            print('pilot raised exception: %s'%_exp)
            traceback.print_exc(file=sys.stdout)
            self.logger.error(traceback.format_exc())
        self.logger.info('pilot landed')
    def jettison(self,direction='both',check_run=False):
        open_lst=[]
        open_book_value=0
        close_lst=[]
        close_book_value=0
        both_lst=[]
        if self.stock_value_todo_ps is not None:
            for stock,value in self.stock_value_todo_ps.iteritems():
                account=self.stock_account_dic[stock]
                stock_sell_price=self.md_mtx.loc[stock,self.sell_price_ref]
                try:
                    amount=amount_adjust(value*account.leverage/stock_sell_price,category='Sell')
                except(ZeroDivisionError,FloatingPointError,ValueError):
                    self.logger.warning('%s sell price cannot be retrieved, pass %s'%(stock,self.ts))
                    continue
                if np.isnan(stock_sell_price)or np.isinf(amount):
                    self.logger.warning('%s sell price cannot be retrieved, pass %s'%(stock,self.ts))
                    continue
                if amount>0:
                    open_book_value+=amount*stock_sell_price
                    open_lst.append(Event(account,amount,self.ts,account.long_open))
                elif amount<0:
                    amount=abs(amount)
                    close_book_value+=amount*stock_sell_price
                    close_lst.append(Event(account,amount,self.ts,account.long_close))
        both_lst.extend(close_lst)
        both_lst.extend(open_lst)
        if not check_run:
            if direction=='close':
                [self.orders.put(event,block=True)for event in close_lst]
            elif direction=='open':
                [self.orders.put(event,block=True)for event in open_lst]
            else:
                [self.orders.put(event,block=True)for event in both_lst]
            self.cv.notify_all()
            self.cv.wait()
            self.feedback_collector()
        return{'close_events':close_lst,'open_events':open_lst,'close_book_value':close_book_value,'open_book_value':open_book_value}
    def chores(self):
        while True:
            try:
                item=self.orders_todo.get(block=False)
                self.orders.put(item,block=True)
            except queue.Empty:
                break
        self.cv.notify_all()
        self.cv.wait()
        self.feedback_collector()
    def prober(self):
        self.daily_stock_adjusted_close_price_dic[self.ts]=self.md_mtx['adjfactor']*self.md_mtx['close']
        self.daily_futures_close_price_dic[self.ts]=self.fts_mtx['close']
        if self.bench_stock_weights_ps is not None:
            self.daily_bench_stock_weights_dic[self.ts]=self.bench_stock_weights_ps
            self.daily_stock_industry_dic[self.ts]=self.ind_detail_ps
        self.daily_stock_dic[self.ts]=pd.Series(self.get_stock_balances(self.stock_account_dic.keys(),dictionary=True,signed_book_value=True))
        self.daily_stock_dic[self.ts]=self.daily_stock_dic[self.ts].loc[self.daily_stock_dic[self.ts]!=0]
        self.daily_stock_sum_dic[self.ts]=self.daily_stock_dic[self.ts].abs().sum()
        self.daily_stock_pnl_dic[self.ts]=pd.Series(self.get_stock_balances(self.stock_account_dic.keys(),dictionary=True,ref='estimated_profit'))
        self.daily_stock_pnl_dic[self.ts]=self.daily_stock_pnl_dic[self.ts].loc[self.daily_stock_pnl_dic[self.ts]!=0]
        self.daily_fts_dic[self.ts]=pd.Series(self.get_futures_balances(self.futures_account_dic.keys(),dictionary=True,signed_book_value=True))
        self.daily_fts_dic[self.ts]=self.daily_fts_dic[self.ts].loc[self.daily_fts_dic[self.ts]!=0]
        self.daily_fts_sum_dic[self.ts]=self.daily_fts_dic[self.ts].abs().sum()
        self.daily_cash_dic[self.ts]=self.futures_bank.value+self.stock_bank.value
        self.daily_wt_dic[self.ts]=pd.Series(self.get_stock_balances(self.stock_account_dic.keys(),weight=True,dictionary=True,signed_book_value=True))
        self.daily_wt_dic[self.ts]=self.daily_wt_dic[self.ts].loc[self.daily_wt_dic[self.ts]!=0]
        self.daily_net_dic[self.ts]=self.daily_cash_dic[self.ts]+sum(self.get_stock_balances(self.stock_account_dic.keys(),ref='value'))+sum(self.get_futures_balances(self.futures_account_dic,ref='value'))
        if self.prev_ts is not None:
            self.daily_rtn_sum_dic[self.ts]=self.daily_net_dic[self.ts]-self.daily_net_dic[self.prev_ts]+self.trans_bank_transfer
            self.daily_stock_rtn_dic[self.ts]=self.daily_stock_dic[self.ts].abs()-self.daily_stock_dic[self.prev_ts].abs()
            try:
                self.daily_turnover_dic[self.ts]=self.stock_turnover_value_dic[self.ts]/self.daily_stock_sum_dic[self.ts]
            except(KeyError,ZeroDivisionError,FloatingPointError):
                self.daily_turnover_dic[self.ts]=0
    def feedback_collector(self):
        self.logger.info('collecting stocks tear sheet feedback %s'%self.ts)
        total_book_value=0
        total_fee=0
        item_lst=[]
        while True:
            try:
                item=self.feedback.get(block=False)
                self.stock_tear_sheet_lst.append(item)
                total_book_value+=item.amount*item.unit
                total_fee+=item.fee
                partial_done_flag=False
                if 'O' in item.ts_type:
                    if amount_adjust(item.target)!=item.amount:
                        partial_done_flag=True
                else:
                    if amount_adjust(item.target,category='Sell')!=item.amount:
                        partial_done_flag=True
                if partial_done_flag:
                    if item.amount*item.unit!=0:
                        item_lst.append(item.item)
                        self.logger.warning('%s has been tagged Partial Done %s'%(item.item,self.ts))
                        self.stock_account_dic[item.item].status='Partial Done'
                    else:
                        self.logger.warning('%s suspended or reached limit price %s'%(item.item,self.ts))
            except queue.Empty:
                break
        if self.ts in self.stock_turnover_value_dic:
            self.stock_turnover_value_dic[self.ts]+=total_book_value
        else:
            self.stock_turnover_value_dic[self.ts]=total_book_value
        if self.ts in self.trans_cost_dic:
            self.trans_cost_dic[self.ts]+=total_fee
        else:
            self.trans_cost_dic[self.ts]=total_fee
        if self.ts in self.partial_done_set_dic:
            self.partial_done_set_dic.update(item_lst)
        else:
            self.partial_done_set_dic=set(item_lst)
    def fts_feedback_collector(self):
        self.logger.info('collecting futures tear sheet feedback %s'%self.ts)
        total_fee=0
        while True:
            try:
                item=self.feedback.get(block=False)
                self.fts_tear_sheet_lst.append(item)
                total_fee+=item.fee
            except queue.Empty:
                break
        if self.ts in self.trans_cost_dic:
            self.trans_cost_dic[self.ts]+=total_fee
        else:
            self.trans_cost_dic[self.ts]=total_fee
    def executor(self):
        self.logger.info('executor in action')
        with self.cv:
            while self.executor_active:
                try:
                    event=self.orders.get(block=False)
                except queue.Empty:
                    self.cv.notify_all()
                    self.cv.wait()
                    continue
                if event.account.ticker in self.futures_account_dic:
                    account_type='FTS'
                    if event.callback in[event.account.long_open,event.account.short_open]:
                        exec_price=self.fts_mtx.loc[event.account.ticker,self.fts_buy_ref]
                        exec_amount=amount_adjust(event.amount,category=self.benchmark)
                    else:
                        exec_price=self.fts_mtx.loc[event.account.ticker,self.fts_sell_ref]
                        exec_amount=amount_adjust(event.amount,category='Sell')
                    assert not np.isnan(exec_price),'futures price unknown'
                    fee=event.callback(exec_amount,exec_price)
                    if event.callback==event.account.short_open:
                        self.feedback.put(TearSheet(event.account.ticker,exec_amount,event.amount,exec_price,fee,self.ts,'SO',account_type))
                    elif event.callback==event.account.short_close:
                        self.feedback.put(TearSheet(event.account.ticker,exec_amount,event.amount,exec_price,fee,self.ts,'SC',account_type))
                    else:
                        raise AssertionError
                else:
                    cols=['pre_close','volume',self.buy_price_ref,self.sell_price_ref,'adjfactor','high','low']
                    md_sliced=self.md_mtx.loc[event.account.ticker].reindex(cols)
                    pre_close,volume,buy_ref_price,sell_ref_price,adjfactor,high,low=md_sliced
                    volume=volume*100 if not np.isnan(volume)else 0
                    account_type='STOCK'
                    try:
                        account_style_expo_ps=self.fct_expo_mtx.loc[event.account.ticker]
                        _=account_style_expo_ps[account_style_expo_ps==1]
                        if len(_)>=1:
                            account_type=_.index[-1]
                            self.stock_account_type_dic[event.account.ticker]=account_type
                    except KeyError:
                        if event.account.ticker in self.stock_account_type_dic:
                            account_type=self.stock_account_type_dic[event.account.ticker]
                    if event.callback in[event.account.long_open]:
                        exec_price=buy_ref_price
                        exec_amount=min(amount_adjust(event.amount),amount_adjust(self.trans_amt_ratio_lim*volume))
                    else:
                        exec_price=sell_ref_price
                        exec_amount=min(amount_adjust(event.amount,category='Sell'),amount_adjust(self.trans_amt_ratio_lim*volume))
                    if np.isnan(exec_price):
                        self.logger.warning('%s execute price cannot be retrieved at %s'%(event.account.ticker,self.ts))
                        exec_amount,exec_price,pct_chg=0,0,0
                    else:
                        pct_chg=(exec_price-pre_close)/pre_close*100
                    limit_flag=0
                    if high==low==buy_ref_price==sell_ref_price:
                        if pre_close<high:
                            limit_flag=1
                        elif pre_close>high:
                            limit_flag=-1
                    if event.callback==event.account.long_open:
                        if limit_flag in[-1,1]:
                            self.logger.warning('%s percentage change more than entry threshold %s'%(event.account.ticker,self.ts))
                            self.feedback.put(TearSheet(event.account.ticker,0,event.amount,exec_price,0,self.ts,'LO',account_type,adjfactor))
                            continue
                        else:
                            fee=event.callback(exec_amount,exec_price)
                            self.feedback.put(TearSheet(event.account.ticker,exec_amount,event.amount,exec_price,fee,self.ts,'LO',account_type,adjfactor))
                    elif event.callback==event.account.long_close:
                        if limit_flag in[-1,1]:
                            self.logger.warning('%s percentage change more than exit threshold %s'%(event.account.ticker,self.ts))
                            self.feedback.put(TearSheet(event.account.ticker,0,event.amount,exec_price,0,self.ts,'LC',account_type,adjfactor))
                            continue
                        else:
                            fee=event.callback(exec_amount,exec_price)
                            self.feedback.put(TearSheet(event.account.ticker,exec_amount,event.amount,exec_price,fee,self.ts,'LC',account_type,adjfactor))
                    else:
                        raise AssertionError
        self.logger.info('executor landed')
    def recorder(self):
        pd_daily_stock_adjusted_close_price=pd.DataFrame(self.daily_stock_adjusted_close_price_dic).T
        pd_daily_futures_close_price=pd.DataFrame(self.daily_futures_close_price_dic).T
        pd_daily_bench_stock_weight=pd.DataFrame(self.daily_bench_stock_weights_dic).T
        pd_daily_stock_industry=pd.DataFrame(self.daily_stock_industry_dic).T.fillna(method='ffill').fillna(method='bfill')
        pd_daily=pd.DataFrame()
        pd_daily['stocks_total_book_value']=pd.Series(self.daily_stock_sum_dic)
        pd_daily['fts_total_book_value']=pd.Series(self.daily_fts_sum_dic)
        pd_daily['net_value']=pd.Series(self.daily_net_dic)
        pd_daily['net_return']=pd.Series(self.daily_rtn_sum_dic)
        pd_daily['cash']=pd.Series(self.daily_cash_dic)
        pd_daily['turnover']=pd.Series(self.daily_turnover_dic)
        pd_daily['transaction_cost']=pd.Series(self.trans_cost_dic)
        pd_stock_bv_detail=pd.DataFrame(self.daily_stock_dic).T
        pd_fts_bv_detail=pd.DataFrame(self.daily_fts_dic).T
        pd_stock_wt_detail=pd.DataFrame(self.daily_wt_dic).T
        pd_stock_rtn_detail=pd.DataFrame(self.daily_stock_rtn_dic).T
        pd_stock_pnl_detail=pd.DataFrame(self.daily_stock_pnl_dic).T
        pd_stock_target_wt_detail=pd.DataFrame(dict((k,v)for k,v in self.wt_target_dic.items()if np.any(v))).T
        pd_stock_fct_expo_detail=pd.DataFrame(self.trans_fct_expo_dic).T
        pd_stock_tearsheet=pd.DataFrame([item.to_dic()for item in self.stock_tear_sheet_lst])
        pd_fts_tearsheet=pd.DataFrame([item.to_dic()for item in self.fts_tear_sheet_lst])
        pd_daily_futures_close_price.to_csv(os.path.join(self.output_path,'sim_futures_close_price.csv'))
        pd_daily_stock_adjusted_close_price.to_csv(os.path.join(self.output_path,'sim_stock_adjusted_close_price.csv'))
        pd_daily_bench_stock_weight.to_csv(os.path.join(self.output_path,'sim_bench_stock_weight.csv'))
        pd_daily_stock_industry.to_csv(os.path.join(self.output_path,'sim_stock_industry.csv'))
        pd_daily.to_csv(os.path.join(self.output_path,'sim_stats_daily.csv'))
        pd_stock_bv_detail.to_csv(os.path.join(self.output_path,'sim_stock_book_value_detail.csv'))
        pd_fts_bv_detail.to_csv(os.path.join(self.output_path,'sim_fts_book_value_detail.csv'))
        pd_stock_wt_detail.to_csv(os.path.join(self.output_path,'sim_stock_weights_detail.csv'))
        pd_stock_rtn_detail.to_csv(os.path.join(self.output_path,'sim_stock_return_detail.csv'))
        pd_stock_pnl_detail.to_csv(os.path.join(self.output_path,'sim_stock_pnl_detail.csv'))
        pd_stock_target_wt_detail.to_csv(os.path.join(self.output_path,'sim_stock_weights_target_detail.csv'))
        pd_stock_fct_expo_detail.to_csv(os.path.join(self.output_path,'sim_stock_factor_expo_detail.csv'))
        pd_stock_tearsheet.to_csv(os.path.join(self.output_path,'sim_stock_tear_sheet.csv'))
        pd_fts_tearsheet.to_csv(os.path.join(self.output_path,'sim_fts_tear_sheet.csv'))
        self.wt_target_dic[max(self.wt_target_dic.keys())].to_csv(os.path.join(self.output_path,max(self.wt_target_dic.keys()).strftime('%Y_%m_%d')+'_optimal_wt.csv'))
        self.daily_stock_dic[max(self.daily_stock_dic.keys())].to_csv(os.path.join(self.output_path,max(self.daily_stock_dic.keys()).strftime('%Y_%m_%d')+'_actual_stock_bv.csv'))
        self.daily_wt_dic[max(self.daily_wt_dic.keys())].to_csv(os.path.join(self.output_path,max(self.daily_wt_dic.keys()).strftime('%Y_%m_%d')+'_actual_stock_wt.csv'))
        if not self.error_flag:
            self.stash(os.path.join(self.output_path,'stash.db'))
        if self.const_capital is not None:
            interest_type='SIMPLE'
        else:
            interest_type='ACCUMULATIVE'
        report_generator(self.output_path,config_str=self.conf_str,stock_leverage=self.stock_leverage*self.fund_leverage,fts_leverage=self.fts_leverage*self.fund_leverage,interest_type=interest_type,benchmark=self.benchmark,trade_cycle=self.trade_cycle)
    def run(self):
        if self.start_date>self.end_date:
            self.logger.info('start date equals end date during restart run, abort simulation')
            return
        self.executor_active=True
        pilot_thread=threading.Thread(name='pilot_thread',target=self.pilot)
        exec_thread=threading.Thread(name='exec_thread',target=self.executor)
        pilot_thread.start()
        exec_thread.start()
        pilot_thread.join()
        self.executor_active=False
        with self.cv:
            self.cv.notify_all()
        exec_thread.join()
        self.logger.info('saving results to csv')
        self.recorder()
        self.logger.info('simulation complete')
class Account:
    def __init__(self,ticker,fee_in,fee_out,leverage,bank,category=None):
        self._ticker=ticker
        self._fee_in=fee_in
        self._fee_out=fee_out
        self._leverage=leverage
        self._bank=bank
        self._category=category
        self._cum_bank_transfer=0
        self._long_value=0
        self._short_value=0
        self._long_amount=0
        self._short_amount=0
        self._shadow=0
        self.susp_days=0
        self.adjfactor=None
        self.status='Normal'
    @property
    def bank(self):
        return self._bank
    @property
    def category(self):
        return self._category
    @property
    def fee_in(self):
        return self._fee_in
    @property
    def fee_out(self):
        return self._fee_out
    @property
    def ticker(self):
        return self._ticker
    @property
    def leverage(self):
        return self._leverage
    @property
    def cum_bank_transfer(self):
        return self._cum_bank_transfer
    @property
    def estimated_profit(self):
        liquidation_fee=self.long_value*self.fee_out+self.short_value*self.fee_in
        return self.value-self.cum_bank_transfer-liquidation_fee
    def gc(self):
        if self.long_amount==0 and self.short_amount==0:
            if abs(self.book_value)<=1E-2:
                self._long_value=0.0
                self._short_value=0.0
                self._shadow=0.0
            else:
                print(self.book_value)
                raise AssertionError
    def long_open(self,amount,unit):
        self._long_value+=amount*unit
        self._long_amount+=amount
        fee=amount*unit*self.fee_in
        self._shadow-=amount*unit+fee
        self.margin_align()
        return fee
    def short_open(self,amount,unit):
        self._short_value-=amount*unit
        self._short_amount+=amount
        fee=amount*unit*self.fee_in
        self._shadow+=amount*unit-fee
        self.margin_align()
        return fee
    def long_close(self,amount,unit):
        self._long_value-=amount*unit
        self._long_amount-=amount
        fee=amount*unit*self.fee_out
        self._shadow+=amount*unit-fee
        self.margin_align()
        self.gc()
        return fee
    def short_close(self,amount,unit):
        self._short_value+=amount*unit
        self._short_amount-=amount
        fee=amount*unit*self.fee_out
        self._shadow-=amount*unit+fee
        self.margin_align()
        self.gc()
        return fee
    def margin_align(self):
        margin=self.value-self.book_value/self.leverage
        if margin<0:
            self.bank.withdraw(-margin)
            self._shadow+=-margin
        else:
            self.bank.deposit(margin)
            self._shadow-=margin
        self._cum_bank_transfer-=margin
    def touch(self,percentage):
        self._long_value=self._long_value*(1+percentage/100)
        self._short_value=self._short_value*(1+percentage/100)
        self.margin_align()
        self.gc()
    def amount_touch(self,adj_ratio):
        self._long_amount=amount_adjust(self._long_amount*adj_ratio,category='Sell')
        self._short_amount=amount_adjust(self._short_amount*adj_ratio,category='Sell')
    @property
    def long_amount(self):
        return self._long_amount
    @property
    def short_amount(self):
        return self._short_amount
    @property
    def value(self):
        return self._long_value+self._short_value+self._shadow
    @property
    def book_value(self):
        return self._long_value-self._short_value
    @property
    def long_value(self):
        return self._long_value
    @property
    def short_value(self):
        return-self._short_value
class Bank:
    def __init__(self,value):
        self.value=value
    def estimate(self,leverage,fee):
        return self.value*leverage*(1-fee)
    def deposit(self,amount):
        self.value+=amount
    def withdraw(self,amount):
        self.value-=amount
class Event:
    counter=0
    def __init__(self,account,amount,ts,callback):
        self.__class__.counter+=1
        self._uid=self.__class__.counter
        self._account=account
        self._amount=amount
        self._ts=ts
        self._callback=callback
    @property
    def uid(self):
        return self._uid
    @property
    def account(self):
        return self._account
    @property
    def amount(self):
        return self._amount
    @amount.setter
    def amount(self,value):
        self._amount=value
    @property
    def ts(self):
        return self._ts
    @property
    def callback(self):
        return self._callback
class TearSheet:
    counter=0
    def __init__(self,item,amount,target,unit,fee,ts,ts_type,item_type=None,adjust_factor=1):
        self.__class__.counter+=1
        self._uid=self.__class__.counter
        self._item=item
        self._amount=amount
        self._target=target
        self._unit=unit
        self._fee=fee
        self._ts=ts
        self._ts_type=ts_type
        self._item_type=item_type
        self._adjust_factor=adjust_factor
    @property
    def uid(self):
        return self._uid
    @property
    def item(self):
        return self._item
    @property
    def amount(self):
        return self._amount
    @property
    def target(self):
        return self._target
    @property
    def unit(self):
        return self._unit
    @property
    def fee(self):
        return self._fee
    @property
    def ts(self):
        return self._ts
    @property
    def ts_type(self):
        return self._ts_type
    @property
    def item_type(self):
        return self._item_type
    @property
    def adjust_factor(self):
        return self._adjust_factor
    def to_dic(self):
        return{'ticker':self.item,'uid':self.uid,'amount':self.amount,'target':self.target,'unit':self.unit,'fee':self.fee,'ts':self.ts,'type':self.ts_type,'category':self.item_type,'adjfactor':self.adjust_factor}
def amount_adjust(amount,category='Stock'):
    min_unit=1
    if amount>0:
        amount=amount-amount%min_unit
    else:
        amount=-(abs(amount)-abs(amount)%min_unit)
    return int(np.floor(amount))
def opt_func(mu_path):
    _mu=mu_path
    def opt_func_helper(ts,benchmark):
        ts=IO.str_date_parser(ts)
        ts=tdt.get_trading_day_offset(ts,-1)[0]
        if _mu is not None:
            mu=IO.read_data(ts,alt=_mu).loc[ts].dropna()
        else:
            mu=IO.read_data(ts,columns='close').loc[ts].dropna()
        style_read = True
        max_loop = 10
        current_loop = 0
        while style_read:
            if current_loop<=max_loop:
                try:
                    style_pd=IO.read_data(ts,ftype=FType.RISK,dsource=DSource.STYLEFACTOR2)
                    style_read = False
                except:
                    print ('read style2 error - retry iter:%d'%(current_loop))
                    style_pd=IO.read_data(ts,ftype=FType.RISK,dsource=DSource.STYLEFACTOR2)
                    style_read = False
            else:
                print ('style read max fail hit!!!')
                raise Exception
        ind=style_pd[['Industry']]
        ind=pd.get_dummies(ind['Industry'])
        ind.columns=['ind'+str(int(item))for item in ind.columns]
        ind=ind.drop('ind0',axis=1,errors='ignore')
        style_factors=style_pd.join(ind).loc[ts].fillna(0)
        weight_book={'ZZ500':'index_weight_zz500','HS300':'index_weight_hs300','SZ50':'index_weight_sh50'}
        index_weight_col=weight_book[benchmark]
        bench_stock_weights_ps=IO.read_data(ts,columns=index_weight_col,ftype=FType.INDEXWEIGHT,dsource=DSource.CSI)[index_weight_col]
        bench_stock_weights_ps=bench_stock_weights_ps.loc[ts]
        bench_stock_weights_ps=bench_stock_weights_ps.loc[bench_stock_weights_ps!=0].dropna()
        bench_fct_exp_ps=style_factors.reindex(bench_stock_weights_ps.index).fillna(0).T.dot(bench_stock_weights_ps)
        ind_weight=bench_fct_exp_ps.reindex(ind.columns)
        return{'mu_mtx':mu,'cov_mtx':None,'fct_expo_mtx':style_factors,'idiosyn_mtx':None,'ind_weight_ps':ind_weight,'bench_fct_exp_ps':bench_fct_exp_ps,'bench_stock_weights_ps':bench_stock_weights_ps}
    return opt_func_helper
def md_func(ts):
    print(ts)
    codebook={'000905.SH':'ZZ500','000300.SH':'HS300'}
    ts=IO.str_date_parser(ts)
    md_mtx=IO.read_data(ts,columns=['open','high','low','close','pre_close','adjfactor','volume','vwap'],dsource=DSource.WIND)
    idx_mtx=IO.read_data(ts,dtype=DType.INDEX,dsource=DSource.WIND)
    return md_mtx.loc[ts],idx_mtx.loc[ts].rename(index=codebook)
