import os
import sys
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../../"))
import pandas as pd
from AlgoConfig_Apple_48 import start_date,end_date,config,PanelMinData_path,save_path
import DataAPI.DataToolkit as Dtk

days = Dtk.get_trading_day(start_date,end_date)
factor_names = sorted([item['name'] for item in config['FactorSet']])


for day in days:
    month = str(day)[:6]
    for factor in factor_names:
        monthly_data_path = PanelMinData_path+'{}/{}_{}.pkl'.format(factor[6:].lower(),month,factor[6:].lower())
        read_path = save_path+'{}/{}_{}.pkl'.format(factor[6:],day,factor[6:])
        if not os.path.exists(monthly_data_path):
#        if True:
            data_df = pd.read_pickle(read_path)
            data_df.to_pickle(monthly_data_path)
            print('{} saved'.format(monthly_data_path))
        else:
            original_df = pd.read_pickle(monthly_data_path)
            additional_df = pd.read_pickle(read_path)
            original_df_sub = original_df.loc[:str(day-1),:].copy()
            ans_df = pd.concat([original_df_sub,additional_df],axis=0)
            ans_df.to_pickle(monthly_data_path)
            print('{} updated to {}'.format(monthly_data_path,day))

if start_date == end_date:
    touch_path = '/data/user/015618/HQF_Update_Log/{}'.format(end_date)
    if not os.path.exists(touch_path):
        os.mkdir(touch_path)
    with open(touch_path+'/{}_HFF.success'.format(end_date),'w') as f:
        pass