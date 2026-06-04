import scipy.io as spo
from xquant.factordata import FactorData
import pandas as pd
from xquant.xqutils.helper import link
import datetime
import config_path
def update_tool():
    universe = spo.loadmat(config_path.universe_path + 'universe.mat')['universe']
    stock_list = sorted([x[0][0] for x in universe])
    date = datetime.datetime.today().strftime('%Y%m%d')
    df = FactorData().get_factor_value('Basic_factor', stock = stock_list, mddate=[date], factor_names=['mdc_adjfactor'])
    print(df)
    adj_today=df['mdc_adjfactor'][date].to_frame().T
    adj_all=pd.read_pickle(config_path.basic_data_path + 'daily/adjfactor.pkl')
    adj_all = adj_all[adj_all.index!=date]
    adj_today.index = [pd.to_datetime(date)]
    adj_new = pd.concat([adj_all,adj_today])
    adj_new.to_pickle(config_path.basic_data_path + 'daily/adjfactor.pkl')
    
    df = FactorData().get_factor_value('Basic_factor', stock = stock_list, mddate=[date], factor_names=['stpt'])
    print(df)
    adj_today=df['stpt'][date].to_frame().T
    adj_all=pd.read_pickle(config_path.basic_data_path + 'daily/stpt.pkl')
    adj_all = adj_all[adj_all.index!=date]
    adj_today.index = [pd.to_datetime(date)]
    adj_new = pd.concat([adj_all,adj_today])
    adj_new.to_pickle(config_path.basic_data_path + 'daily/stpt.pkl')    
    
#    print(adj_new.tail(10))

    # update is_valid,is_valid_raw,industry_code_all,mkt_cap_ard
    need_cover_list = ['is_valid','is_valid_raw','industry_code_all','mkt_cap_ard']
    for f in need_cover_list:
        tmp = pd.read_pickle(config_path.basic_data_path + 'daily/'+f+'.pkl')
        tmp.loc[pd.to_datetime(date)] = tmp.iloc[-1]
        tmp.sort_index().to_pickle(config_path.basic_data_path + 'daily/'+f+'.pkl')

   ####add 20200212########
    cc=pd.read_pickle(config_path.basic_data_path + 'minute/Close/'+date+'.pkl')[119:120]
    cc.index = [pd.to_datetime(date)]
    close_adj = pd.read_pickle(config_path.basic_data_path + 'daily/close_adj.pkl').shift(1)
    adj = pd.read_pickle(config_path.basic_data_path + 'daily/adjfactor.pkl')
    return_today = cc*adj.loc[date]/close_adj.iloc[-1] - 1
    flag = 1*(return_today<0.098)*(return_today>-0.098)
    old = pd.read_pickle(config_path.basic_data_path + 'daily/updown_limit.pkl')
    new = pd.concat([old, flag])
    new.to_pickle(config_path.basic_data_path + 'daily/updown_limit.pkl')



    lm = link.LinkMessage()
    lm.sendMessage("Daily Data Needed for AM-Factors Updated.")
