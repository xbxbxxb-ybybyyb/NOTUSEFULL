'''
if reload history data, you should remove csv in SH50 by hand first.
weiych
'''


from xquant.factordata import FactorData
s = FactorData()
from multifactor.IO import IO
import pandas as pd

from multifactor.IO import IO
from multifactor.data.utils import *
import time
import os

from log import Log
logger = Log('update_universe')


    
def retriver(cdate_list, factor_list):
    namedict = {'HS300':'index_weight_hs300','SH50':'index_weight_sh50','ZZ500':'index_weight_zz500'}
    for date in cdate_list:
        date = str(date)
        for factor in factor_list:
            df = s.get_factor_value('Basic_factor', stock = [], mddate = [date], factor_names = [namedict[factor]])
            if len(df) == 0:
                continue
            df = df.reset_index()[['stock',namedict[factor]]]
            df = df.rename(columns = {'stock':'Ticker',namedict[factor]:factor})
            df = df.set_index('Ticker')
            df.to_csv("/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/stock_universe/" + factor + '/' + date + '.csv')
            print(factor, ' ', date, '  retriver done')
    
    
def update_universe_raw(cdate_list,csv_path,h5_path,factor_list,operation='append'):
    weight_list = ['index_weight_sh50','index_weight_hs300','index_weight_zz500']
    logger.info ('-'*60+'\nUpdating H5 from CSV \n'+h5_path)
    dump_list = [str(i) + '.csv' for i in cdate_list]
    pre_cwd = os.getcwd()
    df_list = []
    for date in cdate_list:
        tmp_list = []
        logger.info('--' + str(date))
        df = get_stock_list(date)
        df.reset_index(inplace=True)
        df['dt'] = dt.datetime.strptime(str(date),'%Y%m%d')
        df.set_index(['dt','Ticker'],inplace=True)
        tmp_list.append(df)
        for factor_name in factor_list:
            if factor_name == 'SH50':
                weight_name = 'index_weight_sh50'
                bool_name = 'index_50'
            elif factor_name == 'ZZ500':
                weight_name = 'index_weight_zz500'
                bool_name = 'index_500'
            elif factor_name == 'HS300':
                weight_name = 'index_weight_hs300'
                bool_name = 'index_300'

            if factor_name == 'SH50' and date < 20100101:
                continue
            fname = csv_path+factor_name+'/'+str(date)+'.csv'
            dat = pd.read_csv(fname)
            dat['dt'] = dt.datetime.strptime(str(date),'%Y%m%d')
            dat.set_index(['dt','Ticker'],inplace=True)
            dat.columns = [weight_name]
            dat = pd.concat([df,dat],axis=1)
            dat.fillna(0,inplace=True)
            # dat[bool_name] = dat[weight_name] > 0
            dat[weight_name] = dat[weight_name] / 100.0

            if len(dat)>0:
                tmp_list.append(dat[[weight_name]])


        df = pd.concat(tmp_list,axis=1)

        for col in weight_list:
            if col not in df.columns:
                continue
            df[col].fillna(0,inplace=True)
        df_list.append(df)
    df = pd.concat(df_list)
    print(df)
    for colume in df.columns:
        if colume == 'alla':
            continue
        if operation == 'append':
            IO.pd_hdf5_writer(df[[colume]],h5_path,dataset=colume,append=True)
        else:
            IO.pd_hdf5_writer(df[[colume]],h5_path,dataset=colume)
            
def get_stock_list(date):
    table_name = 'AShareDescription'
    h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_path = h5_path + table_name + '/' +  table_name + '.h5'
    df = IO.read_data([20090101,21000101],columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'],alt = table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)   
    df.fillna(20990101, inplace = True)

    tmp_df = df[df['S_INFO_DELISTDATE'] > date]
    tmp_df = tmp_df[tmp_df['S_INFO_LISTDATE'] <= date]
    tmp_df['alla'] = True
    tmp_df = tmp_df[['alla']]
    return tmp_df
    
sdate, edate, cdate_list = check_update_date()
print(cdate_list)

csv_path = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/stock_universe/'
h5_path_source = '/data/group/800080/warehouse/prod/INDEXWEIGHT/CHINA_STOCK/DAILY/CSI/INDEXWEIGHT_CHINA_STOCK_DAILY_CSI.h5'
factor_list = ['HS300', 'ZZ500', 'SH50']

flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
if not os.path.exists(flag_root):
    os.makedirs(flag_root)
flag_path_start = flag_root + str(edate) + '_' + 'INDEX_WEIGHT.start'

with open(flag_path_start,'w') as file:
    pass 
    
fileflag = True
while fileflag:
    retriver(cdate_list, factor_list)
    if os.path.exists("/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/stock_universe/" + 'SH50' + '/' + str(cdate_list[-1]) + '.csv'):
        print('retriver finish!')
        fileflag = False
    else:
        print('file not retriver!')
        time.sleep(300)

        
update_universe_raw(cdate_list,csv_path,h5_path_source,factor_list)

flag_path_success = flag_root + str(edate) + '_' + 'INDEX_WEIGHT.success'
with open(flag_path_success,'w') as file:
    pass 

print('h5 is done.')