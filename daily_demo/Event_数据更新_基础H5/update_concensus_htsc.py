# -*- coding: utf-8 -*-
"""
update_concensus_htsc

"""
import datetime as dt
import pandas as pd
import os
import numpy as np
import json
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import os
import subprocess
from functools import partial
import time
from log import Log
import config_reader
from multifactor.data.utils import *
from xquant.factordata import FactorData

logger = Log('update_concensus_htsc')
s = FactorData()



def ticker_match(ticker_num): # jit slow
    ticker_num = int(ticker_num)
    suffix = '.SH' if ticker_num>=600000 else '.SZ'
    pre_fill = (6 - len(str(ticker_num)))*'0'
    ticker = pre_fill + str(ticker_num) + suffix
    return ticker


def data_reformat(dat,dat_fig):
    if dat.empty:
        logger.info('data today is empty')
        return dat
    if 'drop' in dat_fig.keys():
        dat = dat.drop(dat_fig['drop'],axis=1)

    format_list = dat.dtypes
    # print(format_list)
    num_list = [i != np.dtype('object') for i in format_list]    
    str_list = [i==np.dtype('object') for i in format_list]
    col_list = dat.columns.values
    for i in range(len(str_list)):
        if str_list[i]:
            dat[col_list[i]] = dat[col_list[i]].astype('object')
    # print(dat.dtypes)
    # dat.iloc[:,str_list] = dat.iloc[:,str_list].applymap(lambda x:x if len(x)>0 else '')
    for i in range(len(num_list)):
        if num_list[i]:
            dat[col_list[i]] = dat[col_list[i]].astype('float64')
   
    if 'dt' in dat_fig.keys():
        dat[dat_fig['dt']] = dat[dat_fig['dt']].apply(lambda x: dt.datetime.strptime(str(int(x.replace('-','')[:8])),'%Y%m%d')
                                            if type(x) == np.str_ or type(x) == str else  dt.datetime.strptime(str(int(x)),'%Y%m%d'))
        
        if 'Ticker' in dat_fig.keys():
            if 'ticker_match' in dat_fig.keys():
                # dat = dat.query("dat_fig['Ticker'] != 'A00000'")
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(lambda x: 'drop' if not x.isnumeric() else x)
                dat = dat[dat[dat_fig['Ticker']] != 'drop']
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(ticker_match)
                # dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(lambda x: )

            else:
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].astype('str')
            dat = dat.sort_values([dat_fig['dt'],dat_fig['Ticker']])
            dat = dat.set_index([dat_fig['dt'],dat_fig['Ticker']])
            dat.index.names = ['dt','Ticker']
        else:
            dat = dat.sort_values([dat_fig['dt'], 'ID'])
            dat = dat.set_index([dat_fig['dt'], 'ID'])
            dat.index.names = ['dt', 'ID']

    return dat

def csv2h5(csv_list,h5_path,table_name,operation,min_size=0):
    fail_list = []   
    if operation=='create':
        logger.info('Create new h5: '+h5_path)
        if os.path.exists(h5_path):
            logger.info('Remove existing h5:'+h5_path)
            os.remove(h5_path) 
    elif operation == 'append':
        logger.info('Append to: '+ h5_path)
    with pd.HDFStore(h5_path) as h5_store:
        logger.info('check date list takes some time')
        if table_name in list(h5_store.root._v_groups.keys()):
            dt_lst = list(set(h5_store.select_column(table_name, 'dt')))
        else:
            dt_lst = []
        for fname in csv_list:
            logger.info(fname)
            dat = pd.read_csv(fname, encoding='utf_8_sig')
            columns = dat.columns.values

            if 'dt' in columns:
                dat['dt'] = dat['dt'].apply(lambda x: dt.datetime.strptime(x.replace('-',''),'%Y%m%d'))
                print(type(dat['dt'][0]))
            if 'dt' in columns and 'Ticker' in columns:
                dat.set_index(['dt', 'Ticker'], inplace=True)
            elif 'dt' in columns and 'ID' in columns:
                dat.set_index(['dt', 'ID'], inplace=True)

            if 'CON_HISDATE' in columns:
                dat['CON_HISDATE'] = dat['CON_HISDATE'].astype('str')

            if len(dat)<min_size or dat.empty:
                logger.info('csv data too little!')
                fail_list.append(fname+'@amount_fail')
            else:
                if operation == 'append':      
                    curr_date = list(set(dat.index.get_level_values('dt')))[0]
                    logger.info(curr_date)
                    if curr_date in dt_lst:
                        logger.info('Already exists: '+str(curr_date))
                        dummy_id = h5_store.remove(table_name,'dt=curr_date')
                        logger.info('Append: '+str(curr_date))
                        # continue
                h5_store.append(table_name,dat,data_columns=True)
                logger.info('done')


    logger.info('data loading complete!')     
    return fail_list    


def retrieve(table_name,cdate_list,root_folder):
    print('start to download table ' + table_name)

    table_name_sql = 'GOGOAL_' + table_name
    table_folder = root_folder + table_name + '/'
    if not os.path.exists(table_folder):
        os.makedirs(table_folder)
        
    for date in cdate_list:
        print('--' + str(date))
        if table_name in ['cmb_report_research', 'der_report_research','cmb_report_subtable', 'der_report_subtable', 
                            'cmb_report_adjust',  'report_author','cmb_report_score_adjust','change_type','change_event']:
            df = s.get_factor_value(table_name_sql, EntryDate=[str(date)])
        elif table_name in ['author_pj']:
            df = s.get_factor_value(table_name_sql, Rpt_Date=[str(date)[:4]])
        elif table_name in ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 'i_organ_score', 
                             'gg_org_list',  't_great_author', 'author_pjhb']:
          # t_author_honor
            df = s.get_factor_value(table_name_sql)
        elif table_name == 't_author_honor':
            df = s.get_factor_value(table_name_sql, EntryDate=['>=20150101']).append(s.get_factor_value(table_name_sql, EntryDate=['<20150101']))

        else:
            df = s.get_factor_value(table_name_sql,tdate=[str(date)])

        if table_name in ['con_forecast_schedule','con_forecast_stk','stock_diversity','con_stock_deviation',
        'stock_diversity', 'stock_emotion','stock_report_extremum','stock_report_number','con_forecast_c2_stk',
         'con_forecast_c3_cgb_stk','con_forecast_c3_stk','con_forecast_cb_stk','con_stock_income']:
            dat_fig = {'dt':'TDATE','Ticker':'STOCK_CODE','ticker_match':'STOCK_CODE'}    

        elif table_name in ['cmb_report_subtable', 'der_report_subtable', 
                  'i_organ_score', 'report_author', 'gg_org_list','i_report_type', 
                  'author_core_type',  't_great_author','cmb_report_research', 'der_report_research',
                  'change_type','change_event']:
            dat_fig = {'dt':'ENTRYDATE'}
        elif table_name in ['cmb_report_adjust', 'cmb_report_score_adjust','author_pj', 'author_pjhb','author_core']:
            dat_fig = {'dt':'ENTRYDATE','Ticker':'STOCK_CODE','ticker_match':'STOCK_CODE'}
        
        elif table_name in ['t_author_honor']:
            dat_fig = {'dt':'ENTRYDATE','Ticker':'CODE','ticker_match':'CODE'}

        elif table_name in ['researcher_info']:
            dat_fig = {}
            override = True
        else:    
            dat_fig = {'dt':'TDATE','Ticker':'STOCK_CODE','ticker_match':'STOCK_CODE','drop':['CONKEYTMS']}


        if table_name not in ['cmb_report_research','der_report_research','change_type','change_event']:
            df = data_reformat(df, dat_fig)

        if table_name in 'researcher_info':
            df.set_index('ID', inplace=True)
            df.to_csv(table_folder + 'researcher_info.csv', sep=',', encoding='utf_8_sig')
        elif table_name in ['author_core', 'author_core_type', 'i_report_type', 'i_organ_score', 
                         'gg_org_list',  't_great_author', 'author_pjhb','t_author_honor']:
            df.to_csv(table_folder + table_name + '.csv', sep=',', encoding='utf_8_sig')
        elif table_name in ['cmb_report_research','der_report_research']:
            tmp_csv_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/gogoal_htsc/' + table_name + '/'
            if not os.path.exists(tmp_csv_root):
                os.makedirs(tmp_csv_root)
            csv_path = tmp_csv_root + str(date) + '.csv'
            # df.to_csv(csv_path, sep=',', encoding='utf_8_sig')
            # df = pd.read_csv(csv_path)
            df['CONTENT'] = df['CONTENT'].astype(str)
            df['CONTENT'] = df['CONTENT'].apply(lambda x : x.replace('\n', ''))
            df['CONTENT'] = df['CONTENT'].apply(lambda x : x.replace('\r', ''))
            df['CONTENT'] = df['CONTENT'].apply(lambda x : x.replace(',', '，'))

            df['AUTHOR'] = df['AUTHOR'].astype(str)
            df['AUTHOR'] = df['AUTHOR'].apply(lambda x : x.replace('\n', ''))
            df['AUTHOR'] = df['AUTHOR'].apply(lambda x : x.replace('\r', ''))
            df['AUTHOR'] = df['AUTHOR'].apply(lambda x : x.replace(',', '，'))

            df['TITLE'] = df['TITLE'].astype(str)
            df['TITLE'] = df['TITLE'].apply(lambda x : x.replace('\n', ''))
            df['TITLE'] = df['TITLE'].apply(lambda x : x.replace('\r', ''))
            df['TITLE'] = df['TITLE'].apply(lambda x : x.replace(',', '，'))

            df.to_csv(csv_path, sep=',', encoding='utf_8_sig')

        elif table_name == 'der_report_subtable':
            tmp_csv_root = '/data/group/800080/warehouse/test/LOCAL_DATA/CSV/gogoal_htsc/' + table_name + '/'
            if not os.path.exists(tmp_csv_root):
                os.makedirs(tmp_csv_root)
            csv_path =  tmp_csv_root + str(date) + '.csv'
            df.to_csv(csv_path, sep=',', encoding='utf_8_sig')
            df = pd.read_csv(csv_path)         
            df['ID'] = df['ID'].astype('int')
            df['REPORT_SEARCH_ID'] = df['REPORT_SEARCH_ID'].astype('int')
            df['TIME_YEAR'] = df['TIME_YEAR'].astype('int')
            df.to_csv(csv_path, sep=',', encoding='utf_8_sig')
        elif table_name == 'author_pj':
            df.to_csv(table_folder + str(date)[:4] + '.csv', sep=',', encoding='utf_8_sig')
        else:
            df.to_csv(table_folder + str(date) + '.csv', sep=',', encoding='utf_8_sig')

def update_consensus_data(sdate=None,edate=None,operation='append'):
    logger.info('-'*40 + 'update concensus data' + '-'*40)
    table_list = ['con_forecast_stk', 'con_forecast_schedule','stock_order3','stock_report_adjustment',
                  'stock_report_number','stock_order2','stock_report_adjustment2','stock_concern_level',
                  'con_stock_deviation3','con_stock_deviation2','con_stock_deviation',
                  'stock_diversity','stock_emotion','stock_report_extremum',
                  'der_report_subtable', 'cmb_report_score_adjust', 'i_organ_score', 'report_author', 
                  'cmb_report_adjust', 'gg_org_list', 'i_report_type', 'author_core_type', 'author_core',
                  'cmb_report_subtable', 'author_pj', 'author_pjhb', 't_great_author',
                  'con_forecast_c2_stk', 'con_forecast_c3_cgb_stk', 'con_forecast_c3_stk', 'con_forecast_cb_stk', 
                  'researcher_info', 't_author_honor','der_report_research','cmb_report_research']
    
    table_list3 = ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 't_author_honor',
                    'i_organ_score', 'gg_org_list', 't_great_author', 'author_pjhb']

    sdate,edate,cdate_list = check_update_date(sdate,edate)
    print(sdate,edate)
    root_folder = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/gogoal_htsc/'
    root_path = '/data/group/800080/warehouse/prod/'
    for table_name in ['con_forecast_stk']:
        # if table_name in table_list3:
            # print(cdate_list[-1:])
            # retrieve(table_name, cdate_list[-1:], root_folder)
        # else:
            # retrieve(table_name, cdate_list,root_folder)

        if table_name not in ['cmb_report_research','der_report_research','author_pj']:
            if table_name =='con_forecast_stk':
                h5_root = root_path + 'FCD/CHINA_STOCK/DAILY/SUNTIME/'
                if not os.path.exists(h5_root):
                    os.makedirs(h5_root)
                h5_path = h5_root+'FCD_CHINA_STOCK_DAILY_SUNTIME.h5'
            else:
                h5_root = root_path + 'DATABASE/SUNTIME/'+ table_name + '/'
                if not os.path.exists(h5_root):
                    os.makedirs(h5_root)
                h5_path = h5_root+ table_name + '.h5'
            
            source_path = root_folder + table_name + '/'
            csv_list = [source_path+i for i in os.listdir(source_path)]
                
            if table_name in table_list3:
                csv2h5(csv_list, h5_path, table_name, 'create', min_size=0)
            else:
                csv_list.sort()
                csv_date_list = [int(i[-12:-4]) for i in csv_list]
                csv_date_list_take = [i for i in csv_date_list if i>=sdate and i<=edate]
                csv_list_take = [source_path+str(i)+'.csv' for i in csv_date_list_take]
                csv_list_take.sort()
                print(csv_list_take)
                csv2h5(csv_list_take,h5_path,table_name,'append',min_size=0)


if __name__ == '__main__':
    start_date = 20200101
    end_date = 20200304
    update_consensus_data(start_date,end_date)


