import os
import sys
import numpy as np
import pandas as pd
import scipy.io as spio
import sys
sys.path.insert(0,'am_update_pf/')
from pf_generator_helper import *
from xquant.factordata import FactorData
from xquant.xqutils.helper import link
import config_path
lm = link.LinkMessage()
import datetime

def open_portfolio(time,pf_code,open_capital,today, mode=1,benchmark='500'):
    s = FactorData()

    result1 = s.tradingday(today,-2)
    last_dt = result1[-2]
    today_dt = result1[-1]
    model_list = config_path.model_name_map[benchmark][name_map[time]]
    excess_type = config_path.name_map[time]
    all_name = 'All_'+benchmark
    if '0930' in time:
        get_act(last_dt,model_list,excess_type,all_name,mode=1)
        o32_path = config_path.o32_path + 'morning/综合信息查询_组合证券_' + today_dt + '_516.xls'
    elif time == '1300':
        get_act(today_dt,model_list,excess_type,all_name,mode=1)
        o32_path = config_path.o32_path+'noon/综合信息查询_组合证券_' + today_dt + '_1130.xls'
    
    act_path = config_path.act_path +excess_type+'/'+all_name+'/'
    path_save = config_path.weight_path+'/Open_position/'+excess_type+'/'
    valid_stk_ = np.load(config_path.valid_stock_path + 'valid_stock_' + today_dt + '_' + time[:4] + '.npy').item()
    valid_pre_close = valid_stk_['valid_pre_close']
    maxup_stk = valid_stk_['maxup_stk']
    maxdown_stk = valid_stk_['maxdown_stk']
    trade_stk = valid_stk_['trade_stk']
    stocksAmtLowerThan5QianWan = valid_stk_['stocksAmtLowerThan5QianWan']


    if pf_code=='5160304':
        pf_name = 'BeyondIndex'
        turn_ad = 0.2#0.4
        amt_limit = 0.025   
        single_stock_max_weight=0.005            
        hedge_index = 'HS300'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.05, 0.05), 
            'Momentum':              (0.05, 0.05), 
            'Size':                  (0.5, 0.5), #(0.5, 0.5),(0.25, 0.25),
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.01
        dupl_industry = [6133,6134]#[6133,613401,613402,613403]
        split_fin = False
        contract_multiplier = 300
        index_w = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/HS300_data.pkl').iloc[-1]
        index_stk = index_w[index_w>0].index.tolist()
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
       
        
    elif pf_code=='5160803':
        pf_name = 'AlphaHunter'
        print(pf_code,pf_name)
        turn_ad = 0.6
        amt_limit = 0.025
        single_stock_max_weight=0.005
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
            'Momentum':              (0.01, 0.01), 
            'Size':                  (1000, 1000), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.05
        dupl_industry = None
        split_fin = False
        contract_multiplier = 200
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))


    elif pf_code=='5160503':
        pf_name = 'QuantMachine'
        print(pf_code,pf_name)
        turn_ad = 0.4
        amt_limit = 0.025
        single_stock_max_weight=0.0025
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
            'Momentum':              (0.01, 0.01), 
            'Size':                  (1000, 1000), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.05
        dupl_industry = None
        split_fin = False
        contract_multiplier = 200
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))


#    if pf_code=='5160304':
#        pf_name = 'BeyondIndex'
#        turn_ad = 0.4
#        hedge_index = 'HS300'
#        barra_limit_dict = {
#            'Beta'+hedge_index[-3:]: (0.05, 0.05), 
#            'Momentum':              (0.05, 0.05), 
#            'Size':                  (0.5, 0.5), 
#            'Volatility':            (1000, 1000), 
#            'EarningsYield':         (1000, 1000), 
#            'Liquidity':             (1000, 1000), 
#            'Leverage':              (1000, 1000), 
#            'Value':                 (1000, 1000), 
#            'Growth':                (1000, 1000)
#        }
#        industry_loose = 0.01
#        dupl_industry = [6133,6134]#[6133,613401,613402,613403]
#        split_fin = False
#        single_stock_max_weight = 0.005
#        contract_multiplier = 300
#        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
#        index_w = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/HS300_data.pkl').iloc[-1]
#        index_stk = index_w[index_w>0].index.tolist()
#        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
        
        
#    elif pf_code=='5160803':
#        pf_name = 'AlphaHunter'
#        print(pf_code,pf_name)
#        turn_ad = 0.6
#        hedge_index = 'ZZ500'
#        barra_limit_dict = {
#            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
#            'Momentum':              (0.01, 0.01), 
#            'Size':                  (1000, 1000), 
#            'Volatility':            (1000, 1000), 
#            'EarningsYield':         (1000, 1000), 
#            'Liquidity':             (1000, 1000), 
#            'Leverage':              (1000, 1000), 
#            'Value':                 (1000, 1000), 
#            'Growth':                (1000, 1000)
#        }
#        industry_loose = 0.05
#        dupl_industry = None
#        split_fin = False
#        single_stock_max_weight = 0.005
#        contract_multiplier = 200
#        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
        
#    elif pf_code=='5160503':
#        pf_name = 'QuantMachine'
#        print(pf_code,pf_name)
#        turn_ad = 0.5#0.6
#        hedge_index = 'ZZ500'
#        barra_limit_dict = {
#            'Beta'+hedge_index[-3:]: (0.01, 0.01), 
#            'Momentum':              (0.01, 0.01), 
#            'Size':                  (1000, 1000), 
#            'Volatility':            (1000, 1000), 
#            'EarningsYield':         (1000, 1000), 
#            'Liquidity':             (1000, 1000), 
#            'Leverage':              (1000, 1000), 
#            'Value':                 (1000, 1000), 
#            'Growth':                (1000, 1000)
#        }
#        industry_loose = 0.05
#        dupl_industry = None
#        split_fin = False
#        single_stock_max_weight = 0.0025
#        contract_multiplier = 200
#        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))    


    invalid_stk = stocksAmtLowerThan5QianWan.copy()
    open_valid_stk = sorted(set(valid_stk).difference(invalid_stk))
    if time[:4] == '0930':
        act = pd.read_csv(act_path + last_dt + '.csv', index_col=0, header=None).T
    else:
        act = pd.read_csv(act_path + today_dt + '.csv', index_col=0, header=None).T
        
    act.index = [pd.Timestamp(today_dt)]
    act_dict = {time:act}
    turn_ad_dict = {time:0.}
    last_weight = None

    if mode==1:
        #capital = 5.e7 # @
#        w_path = '/data/group/800020/AlphaDataCenter/DailyWeight/add_port/benchmark_%s/' % benchmark
        w_path = config_path.weight_path + 'benchmark_%s/' % benchmark
        print(w_path)
        act_am_path = config_path.prediction_path+'am/'+all_name+'/'
        act_pm_path = config_path.prediction_path+'pm/'+all_name+'/'
        act_vwap_path =config_path.prediction_path+'vwap/'+all_name+'/'
        if time=='0930':
            last_weight = pd.read_pickle(w_path + 'simulation_w_pm.pkl').loc[last_dt]
            act = pd.read_csv(act_am_path + last_dt + '.csv', index_col=0, header=None).T
            act.index = [pd.Timestamp(today_dt)]
            act_dict = {time:act}
            turn_ad_dict = {time:turn_ad}
        elif time=='1300':
            last_weight = pd.read_pickle(w_path + 'simulation_w_pm.pkl').loc[last_dt]
            act_am = pd.read_csv(act_am_path + last_dt + '.csv', index_col=0, header=None).T
            act_am.index = [pd.Timestamp(today_dt)]
            act_pm = pd.read_csv(act_pm_path + today_dt + '.csv', index_col=0, header=None).T
            act_pm.index = [pd.Timestamp(today_dt)]
            act_dict = {'0930':act_am, '1300':act_pm}
            turn_ad_dict = {'0930':turn_ad, '1300':turn_ad}
        elif time=='0930vwap':
            last_weight = pd.read_pickle(w_path + 'simulation_w_vwap.pkl').loc[last_dt]
            act = pd.read_csv(act_vwap_path + last_dt + '.csv', index_col=0, header=None).T
            act.index = [pd.Timestamp(today_dt)]
            act_dict = {time:act}
            turn_ad_dict = {time:turn_ad}
        else:
            raise AssertionError('wrong time input, supported times : 0930 and 1300 and 0930vwap')
        # remove invalid stock in last weight
        s_all = list(last_weight[last_weight>0].index)
        s_remove = list(set(s_all)-set(open_valid_stk))
        
        print('remove invalid stock in last weight',len(s_remove),len(s_all))
        last_weight.loc[s_remove] = 0
        last_weight = last_weight/last_weight.sum()
        last_weight = last_weight/last_weight.sum()
        assert round(last_weight.sum(),3)==1

    today_open_w = optInd.optimize_hf(act_dict, turn_ad_dict, hedge_index, open_capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, 
                               dupl_industry=dupl_industry, split_fin=split_fin, prev_weights=last_weight,\
                               pool_valid_stocks=open_valid_stk,amt_limit=0.025,single_stock_max_weight=single_stock_max_weight)
    today_open_w = today_open_w[time].loc[today_dt]
    today_open_w.to_pickle(path_save + today_dt + '.pkl')
    assert today_open_w[invalid_stk].sum()==0
    assert np.sum(today_open_w<0)==0
    assert np.sum(np.isinf(today_open_w))==0
    assert np.sum(np.isnan(today_open_w))==0

    today_open_fw = format_weight(today_open_w, pf_code, today_dt, time, open_position=True)


    Open_file_save(today_open_fw,time,pf_code,today_dt, benchmark)
    open_stk = [i + '.SH' if i[0]=='6' else i + '.SZ' for i in today_open_fw['证券代码'].tolist()]
    assert len(set(open_stk).intersection(invalid_stk))==0

    print('weight sum:',today_open_fw['权重'].sum())

    # reb and open position activation
    # if True:
    #     today_reb_w = pd.read_excel('reb_weight/' + pf_code + '_weight_' + today_dt + '.xlsx', index_col=0, converters={'证券代码':str})
    #     today_reb_w.index = [i+'.SH' if i[0]=='6' else i+'.SZ' for i in today_reb_w['证券代码']]
    #     today_reb_w = today_reb_w['权重'] / today_reb_w['权重'].sum()

        # print('reb  position activation:', (act * today_reb_w).sum())
    print('open position activation:', (act.loc[today_dt] * today_open_w).sum())
    lm.sendMessage("{0} 建(加)仓文件已上传，股票数量{1}".format(str(pf_code),str(today_open_fw.shape[0]))) 