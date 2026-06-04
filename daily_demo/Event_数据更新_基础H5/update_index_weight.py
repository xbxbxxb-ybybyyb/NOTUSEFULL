    # -*- coding: utf-8 -*-
"""
Stock Universe
@gzj
"""


import pandas as pd
import numpy as np
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import os 
import datetime as dt  
from log import Log
import config_reader
from decimal import *
from multifactor.data.utils import *
import time
from xquant.factordata import FactorData
s = FactorData()


logger = Log('update_universe')
"""Stock List/Date List"""

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




def save_index_component(cdate_list,index_list,save_path):  
    date_min = {'HS300':20050411,
                'ZZ500':20100104,
                'SH50':20100104}
    dat_size = {'HS300':300,'ZZ500':500,'SH50':50}  
    if type(index_list) == str:
        index_list = [index_list]
    
    for date in cdate_list:        
        for index_name in index_list:
            logger.info('-'*10 + index_name + '-'*10)
            save_folder = save_path + index_name +'/'    
            if not os.path.exists(save_folder):
                os.mkdir(save_folder)
            logger.info(index_name +': '+str(date))
            
            if date<date_min[index_name]:
                logger.info('skip')
            else:
                if index_name == 'HS300':
                    # dat = qi.hset(PlateType.INDEX, op_date, IndexType.HS300)
                    df= s.hset('INDEX', str(date), 'HS300',1)

                elif index_name == 'ZZ500':
                    df= s.hset('INDEX', str(date), 'ZZ500',1)
                elif index_name == 'SH50':
                    df= s.hset('INDEX', str(date), 'SZ50',1)
                df.columns = ['Ticker','Stock_name',index_name]
                df.drop('Stock_name',axis=1,inplace=True)
                df.set_index('Ticker', inplace=True)
                df.sort_index(inplace=True)
                df.to_csv(save_folder+str(date)+'.csv')
 



def updater_universe_csv(cdate_list):
    store_path = config_reader.getConfig('update_universe', 'csv_path')
    index_list = ['SH50', 'HS300','ZZ500']
    save_index_component(cdate_list, index_list, store_path)




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
        h5_path_destination = IO.path_assembler(mkttype=MktType.CHINA, dtype=DType.STOCK, ftype=FType.UNIV, dfreq=DFreq.DAILY, dsource=DSource.OPTM, alt=None, h5root=self.h5_root)

        # factor_list = ['Listing_date','OPENDOWNLIMIT','OPENUPLIMIT','SSO','STPT','SUSPEND']
        factor_list = ['HS300','ZZ500','SH50']
        # factor_list = ['SH50']
        h5_path_source = '/data/group/800080/warehouse/prod/INDEXWEIGHT/CHINA_STOCK/DAILY/CSI/test.h5'

        update_universe_raw(self.cdate_list,csv_path,h5_path_source,factor_list,'create')


    def cronb(self):
        # self.retriever()
        self.csv_to_database()

def updater_universe(sdate=None,edate=None):

    sdate,edate,cdate_list = check_update_date(sdate, edate)
    unv_factor(sdate, edate).cronb()
    
    # flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
    # flag_path = flag_root + str(edate) + '_' + 'INDEX_WEIGHT.success'
    # with open(flag_path,'w') as file:
        # pass


updater_universe(20100101,20190903)