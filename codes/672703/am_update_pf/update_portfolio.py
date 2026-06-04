import os
import sys
import numpy as np
import pandas as pd
import scipy.io as spio
import sys
sys.path.insert(0,'am_update_pf/')
from pf_generator_helper import *
from xquant.factordata import FactorData

import datetime
def update_portfolio(reb_path,today,time = '0930',pf_code = '5160701',reb = True,close_after_open = False,
        index_price = 0.,first_open = False,open_capital = 1e9):
    s = FactorData()
    result1 = s.tradingday(today,-2)
    last_dt = result1[-2]
    today_dt = result1[-1]
    print('time:',time,'last:',last_dt,'today',today_dt)
    if time=='0930':
        get_act_am(last_dt)
        act_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/am/All/'
        o32_path = '/data/user/011477/order/O32/morning/综合信息查询_组合证券_' + today_dt + '_516.xls'
        o32_path_ = '/data/user/011477/order/O32/morning/综合信息查询_组合证券' + today_dt + '_516.xls'
    else:
        get_act_pm(today_dt)
        act_path = '/data/group/800020/AlphaDataCenter/DailyPrediction/pm/All/'
        o32_path = '/data/user/011477/order/O32/noon/综合信息查询_组合证券_' + today_dt + '_1130.xls'
        o32_path_ = '/data/user/011477/order/O32/noon/综合信息查询_组合证券' + today_dt + '_1130.xls'
    # prepare
    if not first_open:
        try:
            pf, long, short = load_pf(pf_code, o32_path)
        except FileNotFoundError:
            pf, long, short = load_pf(pf_code, o32_path_)
        last_position, valid_position = (long['持仓'], long['持仓']) if time=='0930' else (long['持仓'], long['T日指令可用数量'])
        close_price = long['最新价']
        if reb:
            if time == '0930':
                act = pd.read_csv(act_path + last_dt + '.csv', index_col=0, header=None).T
            else:
                act = pd.read_csv(act_path + today_dt + '.csv', index_col=0, header=None).T
            act.index = [pd.Timestamp(today_dt)]

    # valid_stk = np.load('valid_stock/valid_stock_' + today_dt + '_' + time + '.npy').item()
    valid_stk_ = np.load('/data/group/800020/AlphaTask/valid_stock/valid_stock/valid_stock_' + today_dt + '_' + time + '.npy').item()
    valid_pre_close = valid_stk_['valid_pre_close']
    maxup_stk = valid_stk_['maxup_stk']
    maxdown_stk = valid_stk_['maxdown_stk']
    trade_stk = valid_stk_['trade_stk']

    # universe = spio.loadmat('/data/group/800020/AlphaDataCenter/PoolManagement/universe.mat', squeeze_me=True)['universe'].tolist()
    # trade_stk = sorted(set(trade_stk).intersection(universe))

    if pf_code=='5160504':
        pf_name = 'BeyondIndex'
        turn_ad = 0.04
        hedge_index = 'HS300'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
            'Momentum':              (0.01, 0.01), 
            'Size':                  (0.01, 0.01), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 1000
        dupl_industry = [6133,613401,613402,613403]
        split_fin = True
        contract_multiplier = 300
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
        index_w = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/HS300_data.pkl').iloc[-1]
        index_stk = index_w[index_w>0].index.tolist()
        valid_stk = sorted(set(valid_stk).intersection(index_stk))
        
        
    elif pf_code=='5160701':
        pf_name = 'QuantMachine'
        turn_ad = 0.8
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
            'Momentum':              (0.01, 0.01), 
            'Size':                  (0.01, 0.01), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.001000
        dupl_industry = None
        split_fin = False
        contract_multiplier = 200
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
    #     maxup_in_pf_stk = [] if first_open else list(set(long.index.tolist()).intersection(maxup_stk))
    #     valid_stk = list(set(trade_stk)-set(maxup_in_pf_stk))
    #     index_w = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/ZZ500_data.pkl').iloc[-1]
    #     index_stk = index_w[index_w>0].index.tolist()
    #     valid_stk = sorted(set(valid_stk).intersection(index_stk))

    if not first_open:
        # last_stats = pd.read_excel('stats/' + last_dt + '_' + pf_code + '_组合收益.xlsx', index_col=0, sheet_name='汇总')
        # capital = last_stats.loc[last_dt, '期货规模']
        # # capital = last_stats.loc[last_dt, '现货规模']
        # long_capital = last_stats.loc[last_dt, '现货规模']
        cash = 0.
        # capital = long['市值'].sum()
        capital = short['市值'].sum() + cash
        long_capital = long['市值'].sum()
        
    # close position settings
    # load real-time position and valid stocks if close position after open
    if close_after_open:
        print('close position after open')
        pf, long, short = load_pf(pf_code, '综合信息查询_组合证券_' + today_dt + '.xls') # temporal o32 stats file
        last_position = long['持仓']
        trade_stk = np.load('valid_stk_close_position_' + today_dt + '.npy').tolist()
        capital = long['市值'].sum()
    else:
        # index_price = pd.read_pickle('index_future_data/index_close.pkl').loc[last_dt, hedge_index]
        index_price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close_000905SH.pkl').loc[last_dt].iloc[0]
        # index_price = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close_000300SH.pkl').loc[last_dt].iloc[0]

    # check the percentage of valid stocks
    is_valid_raw = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/is_valid_raw.pkl').iloc[-1]
    print('\npercentage of valid stocks: ', len((set(is_valid_raw.index) & set(trade_stk)) - set(maxup_stk)) / is_valid_raw.shape[0])
    if not first_open:
        print('total asset: ', capital)
        print('cash: ', cash)
        print('len of valid_stk:',len(valid_stk))   
        
    #rebalance
    if reb:
        today_position, w, fw = pf_generator(act, time, last_position, valid_position, valid_stk, pf_code, turn_ad, hedge_index, capital, cash, barra_limit_dict, industry_loose, dupl_industry, split_fin)
        t0_position = cal_t0_position(last_position, today_position, valid_position, trade_stk)
        t0_xlsx = generate_t0_xlsx(t0_position, pf_code, today_dt, time)
        reb_position = cal_reb_position(last_position, today_position, valid_position, valid_stk)
        reb_xlsx = generate_reb_xlsx(reb_position, pf_code, today_dt, time)
        reb_xlsx.to_excel(reb_path + pf_code + '_rebalance_' + today_dt + '_' + time + '.xlsx')
        print(reb_path + pf_code + '_rebalance_' + today_dt + '_' + time + '.xlsx')

        # calculate buy and sell amount
        if time=='0930':
            close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl').loc[last_dt]
        else:
            close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/minute/Close/' + today_dt + '.pkl').iloc[119]
        buy_stk = reb_xlsx[reb_xlsx['委托方向']==1].index.tolist()
        sell_stk = reb_xlsx[reb_xlsx['委托方向']==2].index.tolist()
        buy_amt = (close[buy_stk] * reb_xlsx.loc[buy_stk, '指令数量']).sum()
        sell_amt = (close[sell_stk] * reb_xlsx.loc[sell_stk, '指令数量']).sum()
        print('buy  amount(wan): ', buy_amt/1e4)
        print('sell amount(wan): ', sell_amt/1e4)
        print('reb stocks:',reb_xlsx.shape[0])

    else:
        # intraday only
        today_position = last_position.copy()
        t0_position = cal_t0_position(last_position, today_position, trade_stk)
        t0_xlsx = generate_t0_xlsx(t0_position, pf_code, today_dt, time) 
        
        
        