import pandas as pd
close = pd.read_pickle('/data/group/800020/AlphaDataCenter/Basic/daily/close.pkl')
last_date = close.index[-2].strftime('%Y%m%d')
today = close.index[-1].strftime('%Y%m%d')
pkl_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/'
am = pd.read_pickle(pkl_path+'am/All_5d.pkl')
pm = pd.read_pickle(pkl_path+'pm/All_5d.pkl')
vwap = pd.read_pickle(pkl_path+'vwap/All_5d.pkl')
if am.index[-1]!=pd.to_datetime(today):
    am = am.append(pm.loc[today:today])
if vwap.index[-1]!=pd.to_datetime(today):
    vwap = vwap.append(pm.loc[today:today])
start_date = '20190103'
hf_model={}
hf_model['0930'] = map_act(am).shift(1).iloc[1:]
hf_model['1300'] = map_act(pm).loc[start_date:]
vwap_model={}
vwap_model['0930'] = map_act(vwap).shift(1).iloc[1:]
capital_dict={'hf':(8e8,'8e8'),'vwap':(8e8,'8e8')}
t='hf'
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
hedge_index='ZZ500'
industry_loose = 0.05
amt_limit = 0.025
dupl_industry=None#[6133,613401,613402,613403]
split_fin=False
pool_valid_stocks=None
single_stock_max_weight=0.005
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
w_path_dict = {
                '5d_no_control_size,turnover20%':(0.6,1000),
                '5d_control_size,turnover20%':(0.6,0.01),
                '5d_no_control_size,turnover40%':(0.4,1000),
                '5d_control_size,turnover40%':(0.4,0.01),
              }
save_perform_path = '/data/user/013546/DailyReport/performance/'
from sklearn.externals.joblib import Parallel,delayed
def single(k,v):
    turn_ad={'0930':v[0],'1300':v[0]}
    
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_hf_path = save_perform_path+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    if first:
        last_weight_hf = None
    else:
        last_weight_hf = pd.read_pickle(w_hf_path)['1300'].loc[last_date]
    w_today = optimize_hf({k:v.loc[open_date:close_date] for k,v in hf_model.items()}, turn_ad, hedge_index, capital, barra_limit_dict=barra_limit_dict, 
                          industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight_hf, pool_valid_stocks=pool_valid_stocks, dupl_industry=dupl_industry, split_fin=split_fin,
                          single_stock_max_weight=single_stock_max_weight)
    save_data(w_today,w_hf_path)
open_close_list=[('20190101','20191231'),('20200101','20200624')]
open_close_list = [(today,today)]
first = False
for open_close_date in open_close_list:
    open_date = open_close_date[0]
    close_date = open_close_date[1]
    Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
t='vwap'
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
hedge_index='ZZ500'
industry_loose = 0.05
amt_limit = 0.025
dupl_industry=None#[6133,613401,613402,613403]
split_fin=False
pool_valid_stocks=None
single_stock_max_weight=0.0025
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
w_path_dict = {
                '5d_no_control_size,turnover10%':(0.5,1000),
                '5d_control_size,turnover10%':(0.5,0.01),
                '5d_no_control_size,turnover20%':(0.4,1000),
                '5d_control_size,turnover20%':(0.4,0.01),
              }
save_perform_path = '/data/user/013546/DailyReport/performance/'
from sklearn.externals.joblib import Parallel,delayed
def single(k,v):
    turn_ad={'0930':v[0]}
    
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_hf_path = save_perform_path+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    if first:
        last_weight_hf = None
    else:
        last_weight_hf = pd.read_pickle(w_hf_path)['0930'].loc[last_date]
    w_today = optimize_hf({k:v.loc[open_date:close_date] for k,v in vwap_model.items()}, turn_ad, hedge_index, capital, 
                          barra_limit_dict=barra_limit_dict, 
                          industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight_hf, pool_valid_stocks=pool_valid_stocks, dupl_industry=dupl_industry, split_fin=split_fin,
                          single_stock_max_weight=single_stock_max_weight)
    save_data(w_today,w_hf_path)
for open_close_date in open_close_list:
    open_date = open_close_date[0]
    close_date = open_close_date[1]
    Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
capital_dict={'vwap':(4e8,'4e8')}
benchmark = '300'
save_perform_path = '/data/user/013546/DailyReport/performance/benchmark_'+benchmark+'/'
t='vwap'
capital = capital_dict[t][0]
str_cap = capital_dict[t][1]
hedge_index='HS300'
industry_loose = 0.01
amt_limit = 0.025
dupl_industry=[6133,6134]
split_fin=False
pool_valid_stocks=None
single_stock_max_weight=0.005
barra_limit_dict = {
    'Beta'+hedge_index[-3:]: (0.05, 0.05), 
    'Momentum':              (0.05, 0.05), 
    'Size':                  (1000, 1000), 
    'Volatility':            (1000, 1000), 
    'EarningsYield':         (1000, 1000), 
    'Liquidity':             (1000, 1000), 
    'Leverage':              (1000, 1000), 
    'Value':                 (1000, 1000), 
    'Growth':                (1000, 1000)
}
w_path_dict = {
                '5d_no_control_size,turnover10%':(0.4,0.5)
              }
from sklearn.externals.joblib import Parallel,delayed
def single(k,v):
    turn_ad={'0930':v[0]}
    
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    w_hf_path = save_perform_path+t+'_'+k+'_capital'+str_cap+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w.pkl'
    if first:
        last_weight_hf = None
    else:
        last_weight_hf = pd.read_pickle(w_hf_path)['0930'].loc[last_date]
    w_today = optimize_hf({k:v.loc[open_date:close_date] for k,v in vwap_model.items()}, turn_ad, hedge_index, capital, barra_limit_dict=barra_limit_dict, 
                          industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight_hf, pool_valid_stocks=pool_valid_stocks, dupl_industry=dupl_industry, split_fin=split_fin,
                          single_stock_max_weight=single_stock_max_weight)
    save_data(w_today,w_hf_path)
open_close_list = [(today,today)]
for open_close_date in open_close_list:
    open_date = open_close_date[0]
    close_date = open_close_date[1]
    Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
a = pd.read_pickle('/data/user/013546/DailyReport/performance/benchmark_300/vwap_5d_no_control_size,turnover10%_capital4e8_amt0.025_turn0.4_w.pkl')['0930']
a.to_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/add_port/benchmark_300/simulation_w_vwap.pkl')
a = pd.read_pickle('/data/user/013546/DailyReport/performance/vwap_5d_no_control_size,turnover10%_capital8e8_amt0.025_turn0.5_w.pkl')['0930']
a.to_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/add_port/benchmark_500/simulation_w_vwap.pkl')
a = pd.read_pickle('/data/user/013546/DailyReport/performance/hf_5d_no_control_size,turnover20%_capital8e8_amt0.025_turn0.6_w.pkl')['0930']
a.to_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/add_port/benchmark_500/simulation_w_am.pkl')
a = pd.read_pickle('/data/user/013546/DailyReport/performance/hf_5d_no_control_size,turnover20%_capital8e8_amt0.025_turn0.6_w.pkl')['1300']
a.to_pickle('/data/group/800020/AlphaDataCenter/DailyWeight/add_port/benchmark_500/simulation_w_pm.pkl')