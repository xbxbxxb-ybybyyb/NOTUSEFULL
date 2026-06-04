import os
import pandas as pd
import numpy as np
from multiprocessing.pool import Pool
from utils import *
import pickle
from factor import *
from data_prepare import *

root = '/data/user/000053/'
share = '/data/user/018187/InternData/RawData/'
output_path = '/data/user/000053/yaxuan/factor_data/version0/'

lst = sorted([i for i in os.listdir(share)])[10:20]
date = sorted([i[-15:-7] for i in os.listdir(share+lst[0])])[::3]
paths = [[[share+i+'/'+j+'_'+d+'.pickle' for j in ['tick','order','trade']] for d in date[15:30]] for i in lst]
output_paths = [[(output_path+i+'/',d) for d in date[15:30]] for i in lst]

input_lst = [(paths[i],output_paths[i]) for i in range(len(output_paths))]
print(len(input_lst))

basic_columns = ['T_Time','T_Code','T_Date','tagLong','tagShort','T_TimeSlot']
remain_columns = ['T_Volume_60','T_LastPrice_60']
remain_columns += ['T_LastPrice','T_PreviousClose','T_OpenPrice','T_AskVolume','T_BidVolume',
                                     'T_MinPrice','T_MaxPrice','T_Volume']
remain_columns = list(set(remain_columns))
        
def factor_main(input_lst):

    paths,output_paths=input_lst
    new_paths = paths
        
    print('prepare done')

    for i in range(len(new_paths)):
        print('new days :',i,'/',len(new_paths))
        p = new_paths[i]
        list_df = read_data(p)
        lost_copy = list(list_df).copy()
        list_df =(fill_nan_and_inf(x) for x in list_df)
        df_tick,df_order,df_trade = list_df
        df_tick = df_tick[remain_columns+basic_columns]
            
        df_tick = df_tick.fillna(0)
        df_tmp = tick_purebuyloc(df_tick.copy()).fillna(0)
        df_tick = pd.merge(df_tick,df_tmp,on='T_Time',how='left')
        
        save_cols = [i for i in df_tick.columns.values if i not in remain_columns]
        print('after',df_tick.shape)
        print(df_tick.columns.values)
        save_df(df_tick[save_cols],output_paths[i][0],output_paths[i][1])


pool  = Pool()
pool.map(factor_main,input_lst)