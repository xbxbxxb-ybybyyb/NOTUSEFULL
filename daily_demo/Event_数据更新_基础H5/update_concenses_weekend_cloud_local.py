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
import subprocess
from functools import partial
import time
from log import Log
# import config_reader
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

def index_match(ticker_num):
    if not ticker_num.isnumeric():
        return str(ticker_num)
    if str(ticker_num)[:3] == '000':
        suffix = '.SH'
    elif str(ticker_num)[:3] == '399':
        suffix = '.SZ'
    else:
        return str(ticker_num)
    ticker_num = int(ticker_num)
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
            elif 'index_match' in dat_fig.keys():
                # dat = dat.query("dat_fig['Ticker'] != 'A00000'")
                dat[dat_fig['Ticker']] = dat[dat_fig['Ticker']].apply(index_match)
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

 


def retrieve(table_name,cdate_list,root_folder):
    print('start to download table ' + table_name)

    table_name_sql = 'GOGOAL_' + table_name
    table_folder = root_folder + table_name + '/'
    if not os.path.exists(table_folder):
        os.makedirs(table_folder)
        
    for date in cdate_list:
        print('--' + str(date))
        if table_name in ['cmb_report_research', 'der_report_research','cmb_report_subtable', 'der_report_subtable', 
                            'cmb_report_adjust',  'report_author','cmb_report_score_adjust','change_event']:
            df = s.get_factor_value(table_name_sql, EntryDate=[str(date)])
         
        elif table_name in ['author_pj']:
            df = s.get_factor_value(table_name_sql, Rpt_Date=[str(date)[:4]])
        elif table_name in ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 'i_organ_score', 
                             'gg_org_list',  't_great_author', 'author_pjhb','change_type']:
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
        
        elif table_name in ['CON_FORECAST_IDX','CON_FORECAST_C2_IDX','CON_FORECAST_C3_IDX']:
            dat_fig = {'dt':'TDATE','Ticker':'STOCK_CODE','index_match':'STOCK_CODE'}
        
        elif table_name in ['cmb_report_subtable', 'der_report_subtable', 
                  'i_organ_score', 'report_author', 'gg_org_list','i_report_type', 
                  'author_core_type',  't_great_author','cmb_report_research', 'der_report_research']:
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
            tmp_csv_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/CSV/gogoal_htsc/' + table_name + '/'
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


def get_current_nature_date():
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    print('Current time: ' + str(current_time))
    h5_path = '/data/group/800080/warehouse/prod/CALENDAR/nature_days.h5'
    fdate_list_dt = IO.read_data([19980101, 20300101], alt=h5_path).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    idx = fdate_list.index(current_date)
    return fdate_list[idx-2], fdate_list[idx-1],current_date  

def get_all_days(sdate,edate):
    h5_path = '/data/group/800080/warehouse/prod/CALENDAR/nature_days.h5'
    df = IO.read_data([sdate,edate],alt=h5_path)
    df.reset_index(inplace=True)
    df['dt'] = df['dt'].apply(lambda x : int(str(x).replace('-','')[:8]))
    date_list = list(set(df['dt']))
    date_list.sort()
    return date_list

def update_consensus_data(sdate=None,edate=None,operation='append'):
    logger.info('-'*40 + 'update concensus data' + '-'*40)
    #

  
    table_list = ['der_report_subtable', 'cmb_report_score_adjust','report_author', 
                'cmb_report_adjust','cmb_report_subtable', 'author_pj',
                   'der_report_research','cmb_report_research','change_type','change_event']
    table_list3 = ['researcher_info', 'author_core', 'author_core_type', 'i_report_type', 't_author_honor',
                    'i_organ_score', 'gg_org_list', 't_great_author', 'author_pjhb']
                    

    cdate_list = get_all_days(sdate,edate)

    root_folder = '/data/user/015623/warehouse/prod/' + str(edate) + '/LOCAL_DATA/CSV/gogoal_htsc/'
    root_path = '/data/group/800080/warehouse/prod/'
    for table_name in table_list:
        try:
            if table_name in table_list3:
                print(cdate_list[-1:])
                retrieve(table_name, cdate_list[-1:], root_folder)
            else:
                retrieve(table_name, cdate_list,root_folder)
        except Exception as e:
            print(e)
        


if __name__ == '__main__':
    sdate, edate, monday = get_current_nature_date()
    # sdate,edate = 20191206,20191207
    update_consensus_data(sdate,edate)
    import os
    if not os.path.exists('/data/user/015623/zip_suntime/' + str(edate)):
        os.makedirs('/data/user/015623/zip_suntime/' + str(edate))
    os.system('zip -r /data/user/015623/zip_suntime/' + str(edate) + '/' + str(edate) + '.zip /data/user/015623/warehouse/prod/' + str(edate) + '/LOCAL_DATA/CSV/gogoal_htsc/')
    from xquant.pyfile.ftp import pyfileFTP
    ftp = pyfileFTP()
    ftp.uploadDir("/data/user/015623/zip_suntime/"+str(edate), "015623/zip_suntime/" + str(edate) )


