import pandas as pd 
import os
import sys
import numpy as np
import pandas as pd 
import scipy.io as spio
sys.path.insert(0,'/data/user/013546/shipan/AlphaTools/')
sys.path.insert(0, config_path.tools_path)
sys.path.insert(0, 'am_update_pf/')
import optimize_hf_industry_dealST_LF_fix as optf

from xquant.factordata import FactorData
from xquant.xqutils.helper import link
import config_path
lm = link.LinkMessage()
import datetime

timepoint_list = ['0930','1000','1030','1100','1300','1330','1400','1430']
turn_ad_params = '0.45_0.5_0.45'.split('_')
basic_data_path = '/data/group/800469/AlphaDataCenter/Basic/'
def get_price_type(transaction_time='1300',transaction_period=120):
    if (transaction_time=='0930')&(transaction_period==240):
        return 'vwap'
    d = '20140102'
    df = pd.read_pickle(basic_data_path+'minute/Amount/'+d+'.pkl').loc[d+transaction_time+'00':].iloc[:transaction_period]
    return df.index[0].strftime('%H%M')+'_'+df.index[-1].strftime('%H%M')
def map_act(df):
    from scipy.stats import norm
    df = df.round(10)
    df = df.rank(pct=True,axis=1)
    df[pd.DataFrame(index=df.index,columns=df.columns,data=(df.values==1))] = 1 -1/3676
    df[pd.DataFrame(index=df.index,columns=df.columns,data=(df.values==0))] = 1/3676
    df_norm = pd.DataFrame(norm.ppf(df.values),index=df.index,columns=df.columns)
    return df_norm
def map_param(x):
    if x=='0930':
        return turn_ad_params[0]
    elif x=='1000':
        return turn_ad_params[1]
    else:
        return turn_ad_params[2]
turn_ad_params = {t:map_param(t) for t in timepoint_list}
optimize_conf ={
   'turnover_adversion_dict':{t:turn_ad_params[t] for t in timepoint_list},
    'capital':float('8e8'),'hedge_index':'ZZ500','industry_loose':0.05,'amt_limit':0.025,'dupl_industry':None,
    'split_fin':False,'pool_valid_stocks':None,'single_stock_max_weight':0.0025,'simulate_label':True,'amt_fix':True,
    'barra_limit_dict':{
        'Beta500':               (0.01, 0.01), 
        'Momentum':              (0.01, 0.01), 
        'Size':                  (0.1, 0.1), 
        'Volatility':            (1000, 1000), 
        'EarningsYield':         (1000, 1000), 
        'Liquidity':             (1000, 1000), 
        'Leverage':              (1000, 1000), 
        'Value':                 (1000, 1000), 
        'Growth':                (1000, 1000)
        }
}
act_path = '/data/group/800469/AlphaDataCenter/DailyPrediction/'
model_list = ['LinearRegression','XgboostRegression']
timepoint_list = ['0930','1000','1030','1100','1300','1330','1400','1430']
model_name_map = {t:[(m,get_price_type(t,30)+'_re_5d') for m in model_list] for t in timepoint_list}

def get_half_predict(today):
    act_all = {}
    for k, v in model_name_map.items():
        this_act_path = act_path+k+'/'
        print(k)
        models = os.listdir(this_act_path)
        fix_need_models = [c[0]+'_'+c[1] for c in v]
        models = [m for m in models if m in fix_need_models]
        print(models)
        act = {}
        for m in models:
            df = get_act(act_path+k+'/'+m+'/',today,today).reindex(columns=stocks).astype(np.float64)
           
            act[m] = df
        all_act[k] = map_act(norm_ppf(act))
        all_act[k].loc[today].to_csv(act_path+k+'/All/'+today+'.csv')
    return act_all
def half_open_portfolio(time,pf_code,open_capital,today, mode=1,benchmark='500',test_label=False):
    s = FactorData()

    result1 = s.tradingday(today,-2)
    last_dt = result1[-2]
    today_dt = result1[-1]
    excess_type = config_path.name_map[time]
 
    print(pf_code,model_list,act_path)
    path_save = config_path.weight_path+'/Open_position/'+excess_type+'/'
    valid_stk_ = np.load(config_path.valid_stock_path + 'valid_stock_' + today_dt + '_' + time[:4] + '.npy').item()
    valid_pre_close = valid_stk_['valid_pre_close']
    maxup_stk = valid_stk_['maxup_stk']
    maxdown_stk = valid_stk_['maxdown_stk']
    trade_stk = valid_stk_['trade_stk']
    stocksAmtLowerThan5QianWan = valid_stk_['stocksAmtLowerThan5QianWan']

    pf_name = 'AlphaHunter'
    print(pf_code,pf_name)

    valid_stk = sorted(set(trade_stk)-set(maxup_stk)-set(maxdown_stk))

    invalid_stk = stocksAmtLowerThan5QianWan.copy()
    open_valid_stk = sorted(set(valid_stk).difference(invalid_stk))
    
    w_path = config_path.weight_path + 'benchmark_%s/' % benchmark
    print(w_path)
    
    last_weight = pd.read_pickle(w_path + 'simulation_w_1430.pkl').loc[last_dt]
    
    # remove invalid stock in last weight
    s_all = list(last_weight[last_weight>0].index)
    s_remove = list(set(s_all)-set(open_valid_stk))
    
    print('remove invalid stock in last weight',len(s_remove),len(s_all))
    last_weight.loc[s_remove] = 0
    last_weight = last_weight/last_weight.sum()
    last_weight = last_weight/last_weight.sum()
    assert round(last_weight.sum(),3)==1
    act = get_half_predict(today)
    today_open_w = optimize_hf_industry_dealST_LF_fix.optimize_hf({k:v.loc[test_start_date:test_end_date] for k,v in act.items()}, 
                              prev_weights=last_weight_hf,open_label=False,simulate_label=False,**optimize_conf)
    
    today_open_w = today_open_w[time[:4]].loc[today_dt]
    try:
        os.makedirs(path_save)
    except:
        pass
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

    print('open position activation:', (act.loc[today_dt] * today_open_w).sum())
    lm.sendMessage("{0} 建(加)仓文件已上传，股票数量{1}".format(str(pf_code),str(today_open_fw.shape[0]))) 


    