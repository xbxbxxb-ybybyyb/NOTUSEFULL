import os
import sys
import numpy as np
import pandas as pd
import scipy.io as spio
import sys
from pf_generator_helper import *
sys.path.insert(0, config_path.tools_path)
sys.path.insert(0, 'am_update_pf/')
#from optimize import optimize_hf
import optimize_hf_industry as optInd
import optimize_hf_industry_dealST_LF as optLF
import optimize_hf_industry_dealST_LF_300 as optLF300
import optimize_hf_industry_dealST_LF_fix as optLF_fix
from xquant.factordata import FactorData
from xquant.xqutils.helper import link
import config_path
lm = link.LinkMessage()
import datetime

def open_portfolio(time,pf_code,open_capital,today, mode=1,benchmark='500',test_label=False):
    s = FactorData()
    year=today[:4]
    ratio_=0.8
    cap = pd.read_pickle(config_path.basic_data_path+'/daily/mkt_cap_ard.pkl')
    stockSet_all = cap.columns.tolist()
    tt = cap.rolling(window=120,min_periods=60).mean().loc[:str(year)+'0101'].iloc[-1]    
    stockSet_part = tt.sort_values(ascending=False).iloc[:int(len(stockSet_all)*ratio_)].index.tolist()
    
    result1 = s.tradingday(today,-2)
    last_dt = result1[-2]
    today_dt = result1[-1]
    model_list = config_path.model_name_map[benchmark][name_map[time]]
    excess_type = config_path.name_map[time]
    all_name = 'All_'+benchmark
    
    year=today_dt[:4]
    ratio_=0.8
    cap = pd.read_pickle(config_path.basic_data_path+'/daily/mkt_cap_ard.pkl')
    stockSet_all = cap.columns.tolist()
    tt = cap.rolling(window=120,min_periods=60).mean().loc[:str(year)+'0101'].iloc[-1]    
    stockSet_part = tt.sort_values(ascending=False).iloc[:int(len(stockSet_all)*ratio_)].index.tolist()
    
    
    
    if '0930' in time:
        if time == '0930':
            get_act(today_dt,model_list,excess_type,all_name,mode=1)
        else:
            get_act(last_dt,model_list,excess_type,all_name,mode=1)
        o32_path = config_path.o32_path + 'morning/综合信息查询_组合证券_' + today_dt + '_516.xls'
    elif time == '1300':
        get_act(today_dt,model_list,excess_type,all_name,mode=1)
        o32_path = config_path.o32_path+'noon/综合信息查询_组合证券_' + today_dt + '_1130.xls'
    
    act_path = config_path.act_path +excess_type+'/'+all_name+'/'
    print(pf_code,model_list,act_path)
    path_save = config_path.weight_path+'/Open_position/'+excess_type+'/'
    valid_stk_ = np.load(config_path.valid_stock_path + 'valid_stock_' + today_dt + '_' + time[:4] + '.npy').item()
    valid_pre_close = valid_stk_['valid_pre_close']
    maxup_stk = valid_stk_['maxup_stk']
    maxdown_stk = valid_stk_['maxdown_stk']
    trade_stk = valid_stk_['trade_stk']
    stocksAmtLowerThan5QianWan = valid_stk_['stocksAmtLowerThan5QianWan']

    if time[:4] == '0930':
        if time == '0930':
            act = pd.read_csv(act_path + today_dt + '.csv', index_col=0, header=None).T
        else:
            act = pd.read_csv(act_path + last_dt + '.csv', index_col=0, header=None).T
    else:
        act = pd.read_csv(act_path + today_dt + '.csv', index_col=0, header=None).T
        
    act.index = [pd.Timestamp(today_dt)]

    if pf_code=='5160304':
        pf_name = 'BeyondIndex'
        turn_ad = 0.6#0.4
        amt_limit = 0.025   
        single_stock_max_weight=0.012
        hedge_index = 'HS300'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.1, 0.1), 
            'Momentum':              (0.1, 0.1), 
            'Size':                  (0.1, 0.1), #(0.5, 0.5),(0.25, 0.25),
            'Volatility':            (0.05, 0.05), 
            'EarningsYield':         (0.05, 0.05),
            'Liquidity':             (0.05, 0.05),
            'Leverage':              (0.05, 0.05), 
            'Value':                 (0.05, 0.05),
            'Growth':                (0.05, 0.05),
        }
        industry_loose = 0.1
        dupl_industry = None#[6133,6134]#[6133,613401,613402,613403]
        split_fin = False
        contract_multiplier = 300
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))
       
        
    elif pf_code=='5160803':
        pf_name = 'AlphaHunter'
        print(pf_code,pf_name)
        turn_ad = 0.4
        amt_limit = 0.025
        single_stock_max_weight=0.006
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.1, 0.1), 
            'Momentum':              (0.1, 0.1), 
            'Size':                  (0.1, 0.1), 
            'Volatility':            (1000, 1000), 
            'EarningsYield':         (1000, 1000), 
            'Liquidity':             (1000, 1000), 
            'Leverage':              (1000, 1000), 
            'Value':                 (1000, 1000), 
            'Growth':                (1000, 1000)
        }
        industry_loose = 0.1
        dupl_industry = None
        split_fin = False
        contract_multiplier = 200
        valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))


    elif pf_code=='5161003':
        pf_name = 'Marathon'
        print(pf_code,pf_name)
        turn_ad = 0.5
        amt_limit = 0.025
        single_stock_max_weight=0.006
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.1, 0.1), 
            'Momentum':              (0.1, 0.1), 
            'Size':                  (0.1, 0.1), 
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
        act = act.reindex(columns= stockSet_part)
        print('act.shape',act.shape)
        act = act.reindex(columns= stockSet_all)   
        act = map_act(act)     
        print('act.describe',act.T.describe())                
    elif pf_code=='5160503':
        pf_name = 'QuantMachine'
        print(pf_code,pf_name)
        turn_ad = 0.4
        amt_limit = 0.025
        single_stock_max_weight=0.005
        hedge_index = 'ZZ500'
        barra_limit_dict = {
            'Beta'+hedge_index[-3:]: (0.1, 0.1), 
            'Momentum':              (0.1, 0.1), 
            'Size':                  (0.1, 0.1), 
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
        act = act.reindex(columns= stockSet_part)
        print('act.shape',act.shape)
        act = act.reindex(columns= stockSet_all)   
        act = map_act(act)     
        print('act.describe',act.T.describe())        

    invalid_stk = stocksAmtLowerThan5QianWan.copy()
    open_valid_stk = sorted(list(set(valid_stk)))
    open_valid_stk = sorted(set(valid_stk).difference(invalid_stk)) 

    act_dict = {time:act}
    turn_ad_dict = {time:0.}
    last_weight = None

    if mode==1:
#        w_path = '/data/group/800469/AlphaDataCenter/DailyWeight/add_port/benchmark_%s/' % benchmark
        w_path = config_path.weight_path + 'benchmark_%s/' % benchmark
        print(w_path)
        act_am_path = config_path.prediction_path+'0930/'+all_name+'/'
        act_pm_path = config_path.prediction_path+'pm/'+all_name+'/'
        if time != '0930vwap300':
            act_vwap_path =config_path.prediction_path+'vwap/'+all_name+'/'
        else:
            act_vwap_path =config_path.prediction_path+'vwap300/'+all_name+'/'
        if time=='0930':
            last_weight = pd.read_pickle(config_path.weight_hf_path + 'simulation_w_pm.pkl').loc[last_dt]
            act = pd.read_csv(act_am_path + today_dt + '.csv', index_col=0, header=None).T
            act.index = [pd.Timestamp(today_dt)]
            act = act.reindex(columns= stockSet_part)
            act = act.reindex(columns= stockSet_all)   
            act = map_act(act)               
            act_dict = {time:act}
            turn_ad_dict = {time:turn_ad}
#        elif time=='1300':
#            last_weight = pd.read_pickle(w_path + 'simulation_w_pm.pkl').loc[last_dt]
#            act_am = pd.read_csv(act_am_path + last_dt + '.csv', index_col=0, header=None).T
#            act_am.index = [pd.Timestamp(today_dt)]
            
#            act_pm = pd.read_csv(act_pm_path + today_dt + '.csv', index_col=0, header=None).T
#            act_pm.index = [pd.Timestamp(today_dt)]
#            act_dict = {'0930':act_am, '1300':act_pm}
#            turn_ad_dict = {'0930':turn_ad, '1300':turn_ad}
        elif time in ['0930vwap','0930vwap300']:
            last_weight = pd.read_pickle(w_path + 'simulation_w_vwap.pkl').loc[last_dt]
#            print('@',w_path + 'simulation_w_vwap.pkl')
            act = pd.read_csv(act_vwap_path + last_dt + '.csv', index_col=0, header=None).T
            act.index = [pd.Timestamp(today_dt)]
            act = act.reindex(columns= stockSet_part)
            act = act.reindex(columns= stockSet_all)   
            act = map_act(act)                           
            act_dict = {time[:4]:act}
            turn_ad_dict = {time[:4]:turn_ad}
        elif time in ['0930lf']:
            last_weight = pd.read_pickle(w_path + 'simulation_w_lf.pkl').loc[last_dt]
            act = pd.read_csv(act_vwap_path + last_dt + '.csv', index_col=0, header=None).T
            print('act_vwap_path',act_vwap_path)
            act.index = [pd.Timestamp(today_dt)]
            act = act.reindex(columns= stockSet_part)
            act = act.reindex(columns= stockSet_all)   
            act = map_act(act)                           
            act_dict = {time[:4]:act}
            turn_ad_dict = {time[:4]:turn_ad}        
        else:
            raise AssertionError('wrong time input, supported times : 0930 and 1300 and 0930vwap')
        # remove invalid stock in last weight
        s_all = list(last_weight[last_weight>0].index)
        s_remove = list(set(s_all)-set(open_valid_stk))
        
        print('remove invalid stock in last weight',len(s_remove),len(s_all))
        last_weight.loc[s_remove] = 0 
        last_weight = last_weight/last_weight.sum() 
        last_weight = last_weight/last_weight.sum()
        print(last_weight.sum(),round(last_weight.sum(),2),round(last_weight.sum(),2)==1)  
        assert round(last_weight.sum(),2)==1
    if time in ['0930','1300']:
        today_open_w = optLF_fix.optimize_hf(act_dict, turn_ad_dict, hedge_index, open_capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, 
                                   dupl_industry=dupl_industry, split_fin=split_fin, prev_weights=last_weight,\
                                   pool_valid_stocks=open_valid_stk,amt_limit=0.025,single_stock_max_weight=single_stock_max_weight,simulate_label=False,\
                                   amt_fix=True)
    else:
        if time not in ['0930vwap300']:
            today_open_w = optLF.optimize_hf(act_dict, turn_ad_dict, hedge_index, open_capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, 
                                    dupl_industry=dupl_industry, split_fin=split_fin, prev_weights=last_weight,\
                                    pool_valid_stocks=open_valid_stk,amt_limit=0.025,single_stock_max_weight=single_stock_max_weight,simulate_label=False)
        else:
            today_open_w = optLF300.optimize_hf(act_dict, turn_ad_dict, hedge_index, open_capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, 
                                    dupl_industry=dupl_industry, split_fin=split_fin, prev_weights=last_weight,\
                                    pool_valid_stocks=open_valid_stk,amt_limit=0.025,single_stock_max_weight=single_stock_max_weight,simulate_label=False)                                        
            print('@',time,pf_code,' New optLF300')         
    today_open_w = today_open_w[time[:4]].loc[today_dt]
    try:
        os.makedirs(path_save)
    except:
        pass
    print('path_save',path_save)
    today_open_w.to_pickle(path_save + today_dt + '.pkl')
    assert today_open_w[invalid_stk].sum()==0
    assert np.sum(today_open_w<0)==0
    assert np.sum(np.isinf(today_open_w))==0
    assert np.sum(np.isnan(today_open_w))==0

    today_open_fw = format_weight(today_open_w, pf_code, today_dt, time, open_position=True)

    if test_label is False:
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