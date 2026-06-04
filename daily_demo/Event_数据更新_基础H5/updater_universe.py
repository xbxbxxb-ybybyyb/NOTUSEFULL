
import pandas as pd
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import os 
import datetime as dt
import subprocess
import json
from log import Log
import config_reader
from decimal import *
import time
from multifactor.data.utils import *


logger = Log('update_universe')
"""Stock List/Date List"""


def get_next_day(sdate,next_day = 1):
    fdate_list_dt = IO.read_data([20020101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    return fdate_list[fdate_list.index(sdate) + next_day]


def create_universe_v2(sdate,edate,h5_path):
    print ('-'*20,'\nForming Universe') 
    print ('Loading data') 
    sdate_prev,edate,cdate_list = check_update_date(sdate,edate,252)
    print(sdate_prev)
    # check base data    
    data_MI = IO.read_data([sdate_prev,edate],alt = h5_path,max_workers=1)
    col_list = ['Listing_date', 'OPENDOWNLIMIT', 'OPENUPLIMIT', 'SSO', 'STPT','SUSPEND']

    date_check = np.isfinite(data_MI.loc[str(edate)][col_list]).sum(axis=0)
    print(date_check)
    if (date_check >= [1000,1000,1000,1000,1000,1000]).sum() < 6:
        print ('Warning: universe raw data error')
        print (date_check)
        raise AssertionError     
        
    # check mkt_cap_ard        
    mkt_cap_MI = IO.read_data([sdate_prev,edate],columns=['mkt_cap_ard'],alt = '/data/group/800080/warehouse/prod/MD/CHINA_STOCK/DAILY/WIND/MD_CHINA_STOCK_DAILY_WIND.h5',max_workers=1)
    mkt_cap = mkt_cap_MI['mkt_cap_ard'].unstack()
    if (np.isfinite(mkt_cap).sum(axis=1)<500).sum()>0:
        print ('No data')
        raise AssertionError 
        
    mkt_cap_5pct = mkt_cap.quantile(q=0.05,axis=1)
    mk_cap_ind = mkt_cap.sub(mkt_cap_5pct,axis=0)>0
    mk_cap_ind_mi = pd.DataFrame(mk_cap_ind.stack(),columns=['mkt_cap_5pct'])
    print ('Computing')
    
    # listing date 
    fdate_list_dt = IO.read_data([19900101,20990101],ftype=FType.CALENDAR).index.get_level_values(0).tolist()
    fdate_list = [int(dt.datetime.strftime(i,'%Y%m%d')) for i in fdate_list_dt]
    listing_date = data_MI['Listing_date'].copy()
    listing_date = listing_date.reset_index()[['Ticker','Listing_date']].drop_duplicates()
    listing_date['Listing_date'] = listing_date['Listing_date'].apply(lambda x: 0 if x == 20990101 else x)
    listing_date['Listing_date'] = listing_date['Listing_date'].apply(lambda x: max(19910102,x))
    listing_date['listing_date_position'] = listing_date['Listing_date'].apply(lambda x: fdate_list.index(int(x)))
    listing_date = listing_date.set_index('Ticker')
    data_MI['current_date'] = data_MI.index.get_level_values(0)
    data_MI['current_stk'] = data_MI.index.get_level_values(1)
    td_position = {k:fdate_list_dt.index(k) for k in fdate_list_dt}
    stk_position = listing_date['listing_date_position'].to_dict()

    data_MI['current_date_position'] =  data_MI['current_date'].apply(lambda x:td_position[x])
    data_MI['listing_date_position'] =  data_MI['current_stk'].apply(lambda x:stk_position[x])
    data_MI['days_since_ipo'] =  data_MI['current_date_position'] - data_MI['listing_date_position'] 
    
    # print(data_MI.reset_index('dt').loc['002933.SZ'][['current_date','Listing_date','days_since_ipo','current_date_position','listing_date_position']])
    day_num_year = 242
    day_half_year = 121
    data_MI['listing_1yr'] =  data_MI['days_since_ipo'] > day_num_year * 1
    data_MI['listing_3yr'] =  data_MI['days_since_ipo'] > day_num_year * 3
    data_MI['listing_121d'] =  data_MI['days_since_ipo'] > day_half_year
    
    # universe
    filter_suspend = data_MI['SUSPEND'].unstack()
    over_half_for_half_year = filter_suspend.fillna(0).rolling(window=day_half_year).sum()>int(day_half_year/2)
    over_half_for_half_year_mi = pd.DataFrame(over_half_for_half_year.stack(),columns=['over_half_for_half_year'])
    
    data_MI = pd.concat([data_MI,over_half_for_half_year_mi,mk_cap_ind_mi],axis=1)

    # risk / alpha 
    data_MI['risk_universe'] = data_MI['listing_1yr']*data_MI['STPT']*data_MI['over_half_for_half_year']*data_MI['mkt_cap_5pct']
    data_MI['alpha_universe'] = data_MI['risk_universe']*data_MI['SUSPEND']

    # index    
    data_MI['index_50'].fillna(False,inplace=True)
    data_MI['index_300'].fillna(False,inplace=True)
    data_MI['index_500'].fillna(False,inplace=True)
    data_MI['index_1000'].fillna(False,inplace=True)

    data_MI['alla'].fillna(False,inplace=True)
    
        
    data_config = { 'index_name': ['dt','Ticker'],
                    'type_number': ['Listing_date','OPENDOWNLIMIT',
                                    'OPENUPLIMIT','SSO','STPT','SUSPEND','risk_universe','alpha_universe'],
                    'type_int': ['Listing_date'],
                    'type_bool': ['OPENDOWNLIMIT', 'OPENUPLIMIT','SSO','STPT', 'SUSPEND',
                                  'risk_universe','alpha_universe','alla','index_300','index_500','index_50','index_1000',
                                  'listing_1yr','listing_3yr','over_half_for_half_year'],
                    'name_orig':['Listing_date', 'OPENDOWNLIMIT', 'OPENUPLIMIT', 'SSO',
                                   'STPT', 'SUSPEND', 'risk_universe', 'alpha_universe',
                                   'listing_1yr', 'listing_3yr', 'over_half_for_half_year',
                                   'alla','index_300','index_500','index_50','index_1000'],

                    'name_new':[ 'Listing_date', 'filter_opendownlimit', 'filter_openuplimit', 
                                 'filter_sso','filter_stpt', 'filter_suspend', 'risk_universe', 'alpha_universe',
                               'listing_1yr', 'listing_3yr', 'over_half_for_half_year',
                               'alla','index_300','index_500','index_50','index_1000'],

                    'column_order': ['risk_universe', 'alpha_universe', 'filter_opendownlimit', 
                                'filter_openuplimit','filter_sso','filter_stpt', 'filter_suspend',  
                               'Listing_date','listing_1yr','listing_3yr','over_half_for_half_year',
                               'alla','index_300','index_500','index_50','index_1000']}
    
    dat = data_MI_formatter(data_MI[data_config['name_orig']],data_config)

    cut_list = [str(i) for i in cdate_list] if len(cdate_list)>1 else str(cdate_list[0])
    data_universe = dat.loc[cut_list].dropna()
    print ('Universe Complete\n','-'*20)
    return data_universe



def get_stock_list(cdate_list):
    cdate_list = [cdate_list] if type(cdate_list)!=list else cdate_list
    wind_stock_path = config_reader.getConfig('root_path', 'wind_stock_path')
    if not os.path.exists(wind_stock_path):
        os.makedirs(wind_stock_path)
    fdate_list = [int(i[:-4]) for i in os.listdir(wind_stock_path)]
    need_list = list(set(cdate_list) - set(fdate_list))
    logger.info('Need to download stock list for: ' + str(len(need_list)) + ' days')
    table_name = 'AShareDescription'
    h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_path = h5_path + table_name + '/' +  table_name + '.h5'
    df = IO.read_data([20000101,21000101],columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'],alt = table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)   
    df.fillna(20990101, inplace = True)
    for date in need_list:
        tmp_df = df[df['S_INFO_DELISTDATE'] > date]
        Ticker_list = list(tmp_df.index.values)
        delist_Ticker = []
        for ticker in Ticker_list:
            if not ticker[0].isdigit():
                delist_Ticker.append(ticker)
            elif ticker[0] == '9':
                delist_Ticker.append(ticker)
        Ticker_list = list(set(Ticker_list) - set(delist_Ticker))
        df1 = pd.DataFrame(Ticker_list, columns=['Ticker'])
        df1.to_csv(wind_stock_path+str(date) + '.csv', index = False)



def get_ST(date):
    h5_path2 = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_name = 'AShareST'
    table_path = h5_path2 + table_name + '/'  + table_name + '.h5'
    df = IO.read_data([20090101,21000101],columns=['ENTRY_DT', 'REMOVE_DT', 'S_TYPE_ST'],alt = table_path)
    df1 = df[df['S_TYPE_ST'] == 'S']
    df2 = df[df['S_TYPE_ST'] == 'T']
    df = df1.append(df2)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)
    Ticker_list = []
    for index, row in df.iterrows():
        if row['ENTRY_DT'] <= date:
            if row['REMOVE_DT'] <= date :
                continue
            else:
                Ticker_list.append(str(index))
    return Ticker_list

def stock_filter_v2(cdate_list, filter_type):
    # store_path = 'D:\\Quant\\backtest\\local_data\\stock_universe\\'
    store_path = config_reader.getConfig('update_universe', 'csv_path')
    if filter_type is 'STPT':
        file_path = store_path + filter_type + '/'
        logger.info('STPT:')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        for date in cdate_list:
            ST_list = get_ST(date)
            logger.info('--' + str(date))
            h5_path2 = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
            table_name = 'AShareEODPrices'
            table_path = h5_path2 + table_name + '/'  + table_name + '.h5'
            df = IO.read_data(date,columns=['S_DQ_OPEN'],alt = table_path)
            df.reset_index('dt', inplace=True)
            df.drop('dt', axis=1, inplace=True)
            Ticker_list = list(df.index.values)
            delist_Ticker = []
            for ticker in Ticker_list:
                if not ticker[0].isdigit():
                    delist_Ticker.append(ticker)
                elif ticker[0] == '9':
                    delist_Ticker.append(ticker)
            Ticker_list = list(set(Ticker_list) - set(delist_Ticker))
            df.reset_index('Ticker', inplace=True)
            df = df[df['Ticker'].isin(Ticker_list)]
            df['STPT'] = df.apply(lambda x: '0' if x['Ticker'] in ST_list else '1', axis = 1)
            df.drop(columns = ['S_DQ_OPEN'], inplace = True)
            df['STPT'] = df['STPT'].astype(float)
            df.set_index('Ticker', inplace=True)
            df.to_csv(file_path+str(date)+'.csv')
    else:
        # filter stock first
        logger.info('Download data for Computingg')
        factor_name_mapping = {'S_DQ_OPEN' : 'open', 'S_DQ_PRECLOSE':'pre_close', 'S_DQ_AMOUNT': 'amt'}
        table_name = 'AShareEODPrices'
        factor_name = ['S_DQ_OPEN', 'S_DQ_PRECLOSE', 'S_DQ_AMOUNT']
        h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/' 
        table_path = h5_path +  table_name + '/' +  table_name + '.h5'
        for date in cdate_list:
            STPT_list = get_ST(date)
            logger.info("--" + str(date))
            df = IO.read_data(date, columns = factor_name, alt = table_path)
            df.reset_index('dt', inplace = True)
            df.drop('dt', axis=1, inplace=True)
            factor_list = []
            for i in df.columns.values:
                factor_list.append(factor_name_mapping[i])
            df.columns = factor_list

            df = df.sort_index()
            df.index.name = 'Ticker'

            df = df.where(df.notnull(), 0)
            # SUSPEND
            df['SUSPEND'] = df.apply(lambda x: 1 if x.amt > 0 else 0, axis = 1)
            df['SUSPEND'] = df['SUSPEND'].astype(float)

            # OPENDOWNLIMIT
            def help1(df):
                a = df['open']
                b = df['pre_close']
                a = 100 * a
                b = 0.9 * b * 1000
                if b % 10 >= 5:
                    b = int(b / 10) + 1
                else:
                    b = int(b / 10)
                if int(a) <= int(b):
                    return 0
                else:
                    return 1
            df['OPENDOWNLIMIT'] = df.apply(lambda x: help1(x), axis = 1)
            
            df['OPENDOWNLIMIT'] = df['OPENDOWNLIMIT'].astype(float)
            #  OPENUPLIMIT
            def help2(df):
                a = df['open']
                b = df['pre_close']
                a = 100 * a
                b = 1.1 * b * 1000
                if b % 10 >= 5:
                    b = int(b / 10) + 1
                else:
                    b = int(b / 10)
                if int(a) >= int(b):
                    return 0
                else:
                    return 1
            df['OPENUPLIMIT'] = df.apply(lambda x: help2(x), axis = 1)
            df['OPENUPLIMIT'] = df['OPENUPLIMIT'].astype(float)

            #  SSO
            def help3(df):
                a = df['open']
                b = df['pre_close']
                c = df['amt']
                a = 100 * a
                b = 1.1 * b * 1000
                if b % 10 >= 5:
                    b = int(b / 10) + 1
                else:
                    b = int(b / 10)
                if int(a) >= int(b) or c <= 0:
                    return 0
                else:
                    return 1            
            df['SSO'] = df.apply(lambda x: help3(x), axis = 1)
            for stock_index in STPT_list:
                if stock_index in df.index.values:
                    df.loc[stock_index, 'SSO'] = 0
            df['SSO'] = df['SSO'].astype(float)
            # save to csv file
            # suspend
            logger.info('SUSPEND')
            file_path_suspend = store_path + 'SUSPEND/'
            if not os.path.exists(file_path_suspend):
                os.makedirs(file_path_suspend)
            df_suspend = df.drop(columns = ['open', 'pre_close','amt','OPENDOWNLIMIT', 'OPENUPLIMIT', 'SSO'])
            df_suspend.to_csv(file_path_suspend + str(date) + '.csv')

            # opendownlimit
            logger.info('OPENDOWNLIMIT')
            file_path_opendownlimit = store_path + 'OPENDOWNLIMIT/'
            if not os.path.exists(file_path_opendownlimit):
                os.makedirs(file_path_opendownlimit)            
            df_opendownlimit = df.drop(columns = ['open', 'pre_close','amt','SUSPEND', 'OPENUPLIMIT', 'SSO'])
            df_opendownlimit.to_csv(file_path_opendownlimit + str(date) + '.csv')

            # openuplimit
            logger.info('OPENUPLIMIT')
            file_path_openuplimit = store_path + 'OPENUPLIMIT/'
            if not os.path.exists(file_path_openuplimit):
                os.makedirs(file_path_openuplimit) 
            df_openuplimit = df.drop(columns = ['open', 'pre_close','amt','SUSPEND', 'OPENDOWNLIMIT', 'SSO'])
            df_openuplimit.to_csv(file_path_openuplimit + str(date) + '.csv')

            # SSO
            logger.info('SSO')
            file_path_sso = store_path + 'SSO/'
            if not os.path.exists(file_path_sso):
                os.makedirs(file_path_sso) 
            df_sso = df.drop(columns = ['open', 'pre_close','amt','SUSPEND', 'OPENDOWNLIMIT', 'OPENUPLIMIT'])
            df_sso.to_csv(file_path_sso + str(date) + '.csv')

            # total
            file_path_total = store_path + 'total/'
            if not os.path.exists(file_path_total):
                os.makedirs(file_path_total)
            df.to_csv(file_path_total+str(date)+'.csv')


def save_index_component(cdate_list,index_list,save_path):  

    # 000016.SH     50
    # 000300.SH     300
    # 000905.SH     500
    index_map = {'index_50':'000016.SH','index_300':'000300.SH','index_500':'000905.SH','index_1000':'000852.SH'}
    dat_size = {'index_300':300,'index_500':500,'index_50':50,'index_1000':1000}  
    if type(index_list) == str:
        index_list = [index_list]

    table_name = 'AIndexMembers'
    h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_path = h5_path + table_name + '/' +  table_name + '.h5'
    df = IO.read_data([20000101,21000101],alt = table_path)
    df.reset_index('dt',inplace=True)
    df.drop('dt',axis=1,inplace=True)
    df = df.loc[['000300.SH','000905.SH','000016.SH','000852.SH']]
    df.reset_index(inplace=True)
    df.set_index(['Ticker','S_CON_WINDCODE','S_CON_INDATE'],inplace=True)
    tmp_list = []
    dup_list = []
    for ind in df.index:
        if ind in tmp_list:
            dup_list.append(ind)
        else:
            tmp_list.append(ind)
    delete_list = []
    for i in dup_list:
        opdate = df.loc[i]['OPDATE'].max()
        a = df.loc[i][df.loc[i]['OPDATE'] != opdate]['OBJECT_ID']
        delete_list.extend(list(a))
    df = df[~df['OBJECT_ID'].isin(delete_list)]
    df.reset_index(['S_CON_WINDCODE','S_CON_INDATE'],inplace=True)
    df['S_CON_INDATE'].fillna(20991231,inplace=True)
    df['S_CON_OUTDATE'].fillna(20991231,inplace=True)

    for date in cdate_list:
        logger.info('--------------' + str(date))
        for index in index_list:
            logger.info('----' + index)
            save_folder = save_path + index +'/'    
            if not os.path.exists(save_folder):
                os.mkdir(save_folder)
            tmp_df = df.loc[index_map[index]]
            tmp_df = tmp_df[tmp_df['S_CON_INDATE'] <= date]
            tmp_df = tmp_df[tmp_df['S_CON_OUTDATE'] > get_next_day(date,-1)]
            ticker_list = list(set(tmp_df['S_CON_WINDCODE']))
            tmp_df = pd.DataFrame(ticker_list)
            print(tmp_df)
            try:
                tmp_df.columns = ['Ticker']
                tmp_df[index] = True
                tmp_df.set_index('Ticker',inplace=True)
                if len(tmp_df) != dat_size[index]:
                    logger.error(index + ' size Error! at ' + str(date))
                    logger.error(len(tmp_df))
            except Exception as e:
                tmp_df = pd.DataFrame(columns=['Ticker',index])
                tmp_df.set_index('Ticker',inplace=True)
                    # raise Exception
            tmp_df.to_csv(save_folder + str(date) + '.csv')
                
def save_index_alla(cdate_list,save_path):
    save_folder = save_path +'alla/'    
    if not os.path.exists(save_folder):
        os.mkdir(save_folder)
    table_name = 'AShareDescription'
    h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_path = h5_path + table_name + '/' +  table_name + '.h5'
    df = IO.read_data([20090101,21000101],columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'],alt = table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)   
    df.fillna(20990101, inplace = True)
    for date in cdate_list:
        logger.info('-----alla: ' + str(date))
        tmp_df = df[df['S_INFO_DELISTDATE'] > date]
        tmp_df = tmp_df[tmp_df['S_INFO_LISTDATE'] <= date]
        tmp_df['alla'] = True
        tmp_df = tmp_df[['alla']]
        tmp_df.to_csv(save_folder + str(date) + '.csv')




def updater_universe_csv(cdate_list):
    store_path = config_reader.getConfig('update_universe', 'csv_path')
    get_stock_list(cdate_list)
    # listing date
    fPath2 = store_path + 'Listing_date/'
    if not os.path.exists(fPath2):
        os.makedirs(fPath2)
    h5_path2 = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_name = 'AShareDescription'
    table_path = h5_path2  + table_name + '/' +  table_name + '.h5'
    df = IO.read_data([20090101,21000101],columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'],alt = table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)
    df.fillna(20990101, inplace = True)
    df = df[df['S_INFO_DELISTDATE'] >= 20090101]
    tmp_df = df
    tmp_df.drop('S_INFO_DELISTDATE', axis = 1, inplace=True)
    tmp_df.columns=['Listing_date']
    Ticker_list = list(tmp_df.index.values)
    delist_Ticker = []
    for ticker in Ticker_list:
        if not ticker[0].isdigit():
            delist_Ticker.append(ticker)
        elif ticker[0] == '9':
            delist_Ticker.append(ticker)
    Ticker_list = list(set(Ticker_list) - set(delist_Ticker))
    tmp_df.reset_index('Ticker', inplace=True)
    tmp_df = tmp_df[tmp_df['Ticker'].isin(Ticker_list)]
    tmp_df.set_index('Ticker', inplace=True)
    for date in cdate_list:
        # tmp_df = df[df['S_INFO_LISTDATE'] <= date]
        tmp_df.to_csv(fPath2+str(date)+'.csv')

    index_list = ['index_50', 'index_300','index_500','index_1000']
    save_index_component(cdate_list, index_list, store_path)
    save_index_alla(cdate_list,store_path)
    # stock filter
    logger.info('Stock filter')
    filter_list = ['STPT', 'SSO']

    for filter_type in filter_list:
        stock_filter_v2(cdate_list, filter_type)




def update_universe_raw(cdate_list,csv_path,h5_path,factor_list,operation='append'):
    logger.info ('-'*60+'\nUpdating H5 from CSV \n'+h5_path)
    dump_list = [str(i) + '.csv' for i in cdate_list]
    pre_cwd = os.getcwd()
    if operation == 'append':
        for date in cdate_list:
            logger.info('--' + str(date))
            for factor_name in factor_list:
                if factor_name == 'SH50' and date < 20100101:
                    continue
                fname = csv_path+factor_name+'/'+str(date)+'.csv'
                dat = pd.read_csv(fname)
                dat['dt'] = dt.datetime.strptime(str(date),'%Y%m%d')
                dat.set_index(['dt','Ticker'],inplace=True)
                if len(dat)>0:
                    IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name,append=True)


    elif operation == 'create':
        for factor_name in factor_list:
            logger.info (factor_name)
            result_folder = csv_path+factor_name+'/'
            os.chdir(result_folder)
            IO.csv_dumper(dump_list,h5_path,factor_name)
        os.chdir(pre_cwd)
    logger.info ('H5 update complete\n'+'-'*60)
        


        
def data_MI_formatter(dat,data_config):
    dat.index.names = data_config['index_name']
    dat = dat.reset_index()
    dat.Ticker = dat.Ticker.astype('object')
    dat = dat.set_index(data_config['index_name']) 
    dat[data_config['type_number']] = dat[data_config['type_number']].fillna(0)
    dat[data_config['type_int']] = dat[data_config['type_int']].astype('int')
    dat[data_config['type_bool']] = dat[data_config['type_bool']].astype('bool')
    dat.columns = data_config['name_new']
    dat = dat[data_config['column_order']]    
    return dat       
    


class unv_factor(object):
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.sdate_prev,self.edate,self.cdate_list = check_update_date(self.start_date,self.end_date)
        self.fail_dict = {}
        self.h5_root = config_reader.getConfig('root_path', 'h5_root')
    def retriever(self):
        updater_universe_csv(self.cdate_list)
        # updater_matlab_universe(self.cdate_list)

    def csv_to_database(self):
        csv_path = config_reader.getConfig('update_universe', 'csv_path')
        h5_path_source = config_reader.getConfig('update_universe', 'h5_path_source')
        h5_path_destination = IO.path_assembler(mkttype=MktType.CHINA, dtype=DType.STOCK, ftype=FType.UNIV, dfreq=DFreq.DAILY, dsource=DSource.OPTM, alt=None, h5root=self.h5_root)
        factor_list = ['alla','index_50','index_300','index_500','index_1000','Listing_date','OPENDOWNLIMIT','OPENUPLIMIT','SSO','STPT','SUSPEND']
        # factor_list = ['alla','index_50','index_300','index_500','index_1000','Listing_date','OPENDOWNLIMIT','OPENUPLIMIT','SSO','STPT','SUSPEND']

        update_universe_raw(self.cdate_list,csv_path,h5_path_source,factor_list,operation='append')
        """Create Universe"""
        data_universe = create_universe_v2(self.sdate_prev, self.edate,h5_path_source)
        check_universe = data_universe.sum()

        if check_universe['risk_universe'] <100:
            self.fail_dict['risk_universe'] = self.cdate_list
            logger.info (check_universe)
            log_file = csv_path+'log/'+str(self.cdate_list[-1])+'.json'
            raise AssertionError
    
        if check_universe['alpha_universe'] <100:
            logger.info (check_universe)
            self.fail_dict['alpha_universe'] = self.cdate_list
            log_file = csv_path+'log/'+str(self.cdate_list[-1])+'.json'
            raise AssertionError
    
        final_date_list = list(set(data_universe.index.get_level_values(0)))

        data_universe['index_800'] = data_universe['index_300'] | data_universe['index_500']
        final_date_list.sort()
        logger.info ('Updating Universe... takes 2 min due to network speed...')
        logger.info ('Date updated: \n'+str(final_date_list))
        dataset_name = 'stock_universe'
        data_universe['Listing_date'] = data_universe['Listing_date'].astype('int32')
        IO.pd_hdf5_writer(data_universe,h5_path_destination,dataset_name,append=True)
        # IO.pd_hdf5_writer(data_universe,h5_path_destination,dataset_name)

    def cronb(self):
        self.retriever()  #生成csv
        self.csv_to_database() #csv to h5

def updater_universe(sdate,edate):
    # sdate = 20180903
    # edate = 20180904
    sdate,edate,cdate_list = check_update_date(sdate, edate)
    unv_factor(sdate, edate).cronb()


# updater_universe(20200729,20200729)