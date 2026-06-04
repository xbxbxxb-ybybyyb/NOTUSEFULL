import sys
sys.path.insert(0,'/data/user/013546/DailyReport/')
from optimize import optimize_hf
import numpy as np
import pandas as pd
import os
def save_data(df_update,path):
    if os.path.exists(path):
        store_data = pd.read_pickle(path )
        if isinstance(df_update,dict):
            for k,v in store_data.items():
                v=v.append(df_update[k])
                v = v.loc[~v.index.duplicated(keep='last')].sort_index()
                store_data[k] = v
        else:
            store_data=store_data.append(df_update)
            store_data = store_data.loc[~store_data.index.duplicated(keep='last')].sort_index()
    else:
        store_data = df_update
    pd.to_pickle(store_data,path)
    return store_data
pkl_path = '/data/user/013546/AlphaDataCenter/DailyPrediction/pickles/'
save_path = '/data/user/013546/DailyReport/performance/'
vwap = pd.read_pickle(pkl_path+'vwap/All_5d.pkl')
start_date = '20190103'
vwap_model={}
vwap_model['0930'] = vwap.shift(1).iloc[1:]
amt_limit = 0.025
capital = 6e8
capital_dict={6e8:'6e8'}
hedge_index = 'ZZ500'
industry_loose = 0.001000
open_close_list=[('20190101','20191231'),
                ('20200101','20200508')]
t = 'vwap'
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
                '5d_no_control_size,turnover20%':(0.3,1000),
                '5d_control_size,turnover20%':(0.3,0.01),
              }
from sklearn.externals.joblib import Parallel,delayed

def single(k,v):
    turn_ad={'0930':v[0],'1300':v[0]}
    barra_limit_dict.update({'Size':(v[1],v[1])})
    print(k+' optimize')
    last_weight = None
    w_path = save_path+t+'_'+k+'_'+str(capital_dict[capital])+'_'+str(amt_limit)+'_'+str(v[0])+'_w.pkl'
    w = optimize_hf({k:v.loc[open_date:close_date] for k,v in vwap_model.items()},turn_ad, hedge_index, capital, barra_limit_dict=barra_limit_dict, industry_loose=industry_loose, amt_limit=amt_limit, 
          prev_weights=last_weight,dupl_industry=None,split_fin=False)
    # w = save_data(w,w_path)
    return w
for open_close_date in open_close_list:
    open_date = open_close_date[0]
    close_date = open_close_date[1]
    res = Parallel(len(w_path_dict))(delayed(single)(k,v) for k,v in w_path_dict.items())
    w_names = [t+'_'+k+'_capital'+str(capital_dict[capital])+'_amt'+str(amt_limit)+'_turn'+str(v[0])+'_w' for k,v in w_path_dict.items()]
    res = dict(zip(w_names,res))
    pd.to_pickle(res,save_path+t+open_date+'_'+close_date+'_ww2.pkl')