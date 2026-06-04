# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 13:17:25 2018

@author:  015623
"""
import sys
import datetime as dt
import pandas as pd
import os
import numpy as np
import json
from multifactor.IO import IO
from multifactor.IO.IO_enums import *
import operator
from functools import reduce
from log import Log
import config_reader
from multifactor.data.utils import *
# import utils
import multifactor.utility.dt as tdt
from FDD_qtr_with_caculation import FDD_qtr_retriever_withcal
from get_dividend import main
import time

logger = Log('update_wind')

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
    df = IO.read_data([20090101,21000101],columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'],alt = table_path)
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

def get_qtr_list(end_date=None,num_qtr=4):
    end_date = end_date[-1] if type(end_date)==list else end_date
    if end_date == None:
        end_date = get_current_date(new_date_time=18)

    if end_date< 20090105:
        last_day = 20090105
    else:
        last_day = end_date
    year_list = [str(i) for i in range(2000,2200)]
    month_date = ['0331','0630','0930','1231']
    date_list_complete = [i+j for i in year_list for j in month_date]
    qtr_list = [int(i) for i in date_list_complete if int(i)<=last_day][-1*num_qtr:]
    get_stock_list(qtr_list)
    universe_folder = config_reader.getConfig('root_path', 'wind_stock_path')
    stock_set = set()
    for qtr_date in qtr_list:
        stock_code = pd.read_csv(universe_folder+str(qtr_date)+'.csv',header=0)['Ticker'].values.tolist()
        stock_set = stock_set.union(set(stock_code))
    stock_code = list(stock_set)
    return qtr_list,stock_code

def get_wind_secu_status_v2():
    logger.info('Get all stocks IPO date and delisting date')
    h5_root = config_reader.getConfig('root_path', 'h5_root')
    h5_path = h5_root + config_reader.getConfig('get_wind_secu_status', 'h5_path')
    if not os.path.exists(os.path.dirname(h5_path)):
        os.makedirs(os.path.dirname(h5_path))
    logger.debug('get_wind_secu_status: ' + h5_path)

    h5_path2 = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_name = 'AShareDescription'
    table_path = h5_path2 + table_name + '/' +  table_name + '.h5'
    df = IO.read_data([20090101,21000101],columns=['S_INFO_DELISTDATE', 'S_INFO_LISTDATE'],alt = table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)
    # df.reset_index('Ticker', inplace=True)
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
    df.set_index('Ticker', inplace=True)
    df.columns=['ipo_date', 'delist_date']
    df.fillna(20991231, inplace=True)
    df['ipo_date'] = df['ipo_date'].apply(lambda x: dt.datetime.strptime(str(int(x)),'%Y%m%d'))
    df['delist_date'] = df['delist_date'].apply(lambda x: dt.datetime.strptime(str(int(x)),'%Y%m%d'))
    logger.info('Create new h5: '+h5_path)
    os.remove(h5_path) if os.path.exists(h5_path) else None
    with pd.HDFStore(h5_path) as h5_store:
        h5_store.append('SecDate',df)
    logger.info('Done')
    return

# def get_wind_qtr_csv(cdate_list,csv_path,factor_name_dict):
#     qtr_list,stock_code = get_qtr_list(cdate_list)
#     logger.info('Getting quarterly wind data for ' + str(qtr_list))
#     fail_list = []
#     for ft in factor_name_dict:
#         logger.info(ft)
#         factor_list = factor_name_dict[ft]
#         fail_list.append(save_one_factor(factor_list,qtr_list,csv_path,use_wind_list=False,stock_code=stock_code))
#
#     return fail_list

#rdf h5 to windapi (MD FDD)csv
def retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, save_path, type, over_ride_name=None, use_stock_list = None):
    '''
    cdate_list is the date that should download
    dataset_name is the col name in the wind api
    factor_name is the col name in the htsc table
    table name is the table that contains the dataset
    if over_ride_name != None, will write the data in a new folder named over_ride_name
    save_path is the path store the csv file, it is stored in the config
    generally the save_path should be 'Z:\\warehouse\\prod\\LOCAL_DATA\\CSV\\wind_data\\'
    '''
    if over_ride_name !=None:
        save_folder = save_path + over_ride_name+'/'
    else:
        save_folder = save_path + dataset_name+'/'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    universe_folder = config_reader.getConfig('root_path', 'wind_stock_path')
    if type == 'FDD':
        h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    elif type == 'MD':
        h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'

    table_path = h5_path +  table_name + '/' +  table_name + '.h5'
    logger.info('---' + dataset_name)
    print(table_name, factor_name)
    for date in cdate_list:
        print(date)
        if use_stock_list is None:
            stock_list = pd.read_csv(universe_folder+str(date)+'.csv',header=0)['Ticker'].values.tolist()
        else:
            stock_list = use_stock_list
        if table_name == 'AShareBalanceSheet':
            df = IO.read_data(date, columns = [factor_name,'STATEMENT_TYPE'], alt = table_path)
            df = df[df['STATEMENT_TYPE'] == 408001000.0]
            df.drop('STATEMENT_TYPE', axis=1, inplace=True)
        else:   
            df = IO.read_data(date, columns = factor_name, alt = table_path)
        df.columns = [dataset_name]
        if dataset_name == 'ocftosales':
            df[dataset_name] = df[dataset_name].apply(lambda x:100 * x)

        df.reset_index('dt', inplace = True)
        df.drop('dt', axis=1, inplace=True)
        exist_stock = df.index.values.tolist()
        stock_list1 = list(set(exist_stock) & set(stock_list))
        stock_list2 = list(set(stock_list) - set(stock_list1))
        df = df.loc[stock_list1]
        data = []
        for stock in stock_list2:
            data.append(np.nan)
        df2 = pd.DataFrame(data, index=stock_list2, columns=[dataset_name])
        # print(df2)
        df = df.append(df2)
        df = df.sort_index()
        df.index.name = 'Ticker'
        if dataset_name == 'stm_issuingdate':
            df.fillna(18991230.0, inplace=True)
            df['stm_issuingdate'] = df['stm_issuingdate'].apply(lambda x : dt.datetime.strptime(str(int(x)),'%Y%m%d'))
        print(len(df))
        df.to_csv(save_folder+str(date)+'.csv')

def MD_retrieve(cdate_list):
    md_list = ['close','open','high','low','vwap','adjfactor','turn','volume','pct_chg',
                'pre_close','total_shares','amt','free_float_shares','mkt_cap_ard']

    table_dict = {'AShareEODDerivativeIndicator': ['turn', 'total_shares', 'free_float_shares', 'mkt_cap_ard'],
        'AShareEODPrices': ['close','open','high','low','vwap','adjfactor', 'volume','pct_chg', 'pre_close','amt']}

    mapping_dict = {'close':'S_DQ_CLOSE', 'open': 'S_DQ_OPEN', 'high': 'S_DQ_HIGH', 'low':'S_DQ_LOW',
                    'vwap': 'S_DQ_AVGPRICE', 'adjfactor': 'S_DQ_ADJFACTOR', 'turn': 'S_DQ_TURN',
                    'volume': 'S_DQ_VOLUME', 'pct_chg': 'S_DQ_PCTCHANGE', 'pre_close': 'S_DQ_PRECLOSE',
                    'total_shares': 'TOT_SHR_TODAY', 'amt': 'S_DQ_AMOUNT', 'free_float_shares': 'FREE_SHARES_TODAY', 'mkt_cap_ard': 'S_VAL_MV'}
    get_stock_list(cdate_list)
    save_path = config_reader.getConfig('root_path', 'csv_path')
    for table_name in table_dict:
        for dataset_name in table_dict[table_name]:
            factor_name = mapping_dict[dataset_name]
            retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, save_path, 'MD')

def INDEX_retrieve(cdate_list, csv_path, index_list):
    factor_list = ['close', 'pre_close','open']
    table_dict = {'AIndexEODPrices': ['close', 'pre_close','open']}
    # table_dict = {'AIndexEODPrices': ['open']}

    mapping_dict = {'close':'S_DQ_CLOSE', 'pre_close': 'S_DQ_PRECLOSE','open':'S_DQ_OPEN'}
    for table_name in table_dict:
        for dataset_name in table_dict[table_name]:
            factor_name = mapping_dict[dataset_name]
            retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, csv_path, 'MD', use_stock_list = index_list)

def FDD_qtr_retrieve_nocal(cdate_list):
    qtr_list, _ = get_qtr_list(cdate_list)
    factor_table = pd.read_excel('/data/group/800080/warehouse/prod/LOCAL_DATA/config/wind_mapping_without_cal.xlsx',header=0)
    save_path = config_reader.getConfig('root_path', 'csv_path')
    col_names = factor_table.columns.tolist()
    row_len = factor_table.shape[0]
    for i in range(row_len):
        dataset_name = factor_table.loc[i][col_names[0]]
        table_name = factor_table.loc[i][col_names[1]]
        factor_name = factor_table.loc[i][col_names[2]]
        retrieve_htsc(qtr_list, dataset_name, table_name, factor_name, save_path, 'FDD')

def FDD_qtr_retriever_withcal_master(cdate_list):
    save_path = config_reader.getConfig('root_path', 'csv_path')
    qtr_list, _ = get_qtr_list(cdate_list)
    factor_list = ['ocftocf', 'fcftocf', 'ocftoop',  
            'longdebttolongcaptial', 'longcapitaltoinvestment', 'currentdebttoequity', 'ncatoequity', 
            'longdebttodebt', 'operatecaptialturn', 'apturn', 'ebittoassets2', 
            'qfa_yoyeps', 'yoy_assets', 'yoy_cash', 'yoy_fixedassets', 'yoydebt', 
            'ocftoassets','cashtostdebt', 'yoyprofit','qfa_grossmargin']

    delete_list = ['ebitdatosales','ocftodividend','ocftointerest','qfa_yoycf','qfa_yoyocf','yoy_cf','faturn']

    factor_list1 = ['qfa_yoyocf', 'qfa_yoycf']
    for date in qtr_list:
        print(date)
        for factor in factor_list:
            try:
                df = FDD_qtr_retriever_withcal(date, factor)
#                print(df)
                save_folder = save_path + factor+'/'
                if not os.path.exists(save_folder):
                    os.makedirs(save_folder)
                df.to_csv(save_folder+str(date)+'.csv')
            except Exception as e:
                logger.error(e)

def FDD_daily_retriever(cdate_list):
    save_path = config_reader.getConfig('root_path', 'csv_path')
    fdd_list = ['pe_ttm','pb_lf','pcf_ocf_ttm','ps_ttm']
    save_path = config_reader.getConfig('root_path', 'csv_path')
    main(cdate_list)
    for dataset_name in fdd_list:
        if dataset_name == 'pe_ttm':
            table_name = 'AShareEODDerivativeIndicator'
            factor_name = 'S_VAL_PE_TTM'
        elif dataset_name == 'pb_lf':
            table_name = 'AShareEODDerivativeIndicator'
            factor_name = 'S_VAL_PB_NEW'
        elif dataset_name == 'pcf_ocf_ttm':
            table_name = 'AShareEODDerivativeIndicator'
            factor_name = 'S_VAL_PCF_OCFTTM'
        elif dataset_name == 'ps_ttm':
            table_name = 'AShareEODDerivativeIndicator'
            factor_name = 'S_VAL_PS_TTM'
        retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, save_path, 'MD')

def update_wind_daily_h5(cdate_list,daily_factor,csv_path,h5_path,operation='append',factor_scale=None):
    """factor_scale for maintaining consistent level between HTSC and WIND data"""
    factor_scale = {} if factor_scale == None else factor_scale
    fail_list = []
    print("update_wind_daily_h5: ", h5_path)
    for factor_name in daily_factor:
        logger.info(factor_name)
        try:
            file_folder = csv_path+factor_name+'/'
            if operation=='append':
                for date in cdate_list:
                    logger.info('--' + str(date))
                    fname = file_folder+str(date)+'.csv'
                    dat = pd.read_csv(fname)
                    dat['dt'] = dt.datetime.strptime(str(date),'%Y%m%d')
                    dat.set_index(['dt','Ticker'],inplace=True)
                    if factor_name in factor_scale:
                        logger.info('scale')
                        dat[factor_name] = dat[factor_name]/factor_scale[factor_name]
                    if len(dat)>0:
                        if factor_name == 'industry_citiccode': # for legacy reason
                            dat.columns = ['CITIC_I']
                            IO.pd_hdf5_writer(dat, h5_path, dataset='CITIC_I',append=True)
                        else:
                            IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name,append=True)
            elif operation =='create':
                logger.info('create new dataset: '+factor_name)
                file_list = [file_folder+i for i in os.listdir(file_folder)]
                file_list.sort()
                IO.csv_dumper(file_list, h5_path, factor_name)
        except Exception as e:
            print("update_wind_daily_h5:", str(e))
            logger.error(e)
            fail_list.append(factor_name)
    return fail_list

def update_wind_qtr_h5(qtr_list,factor_name_dict,csv_path,h5_path,operation='append'):
    """
    :param qtr_list: 嫉妒列表
    :param factor_name_dict: 财务数据字段
    :param csv_path:
    :param h5_path:
    :param operation:
    :return:
    """
    dump_fail_dict={}
    for factor_type in factor_name_dict:
        logger.info(factor_type)
        for factor_name in factor_name_dict[factor_type]:
            logger.info('-'+factor_name)
            dump_fail_dict[factor_name] = []
            try:
                file_folder = csv_path+factor_name+'/'
                if operation=='append':
                    for date in qtr_list:
                        logger.info('--'+str(date))
                        fname = file_folder+str(date)+'.csv'
                        dat = pd.read_csv(fname)
                        dat['dt'] = dt.datetime.strptime(str(date),'%Y%m%d')
                        dat.set_index(['dt','Ticker'],inplace=True)
                        if len(dat)>0:
                            # logger.info'success')
                            #新增一列或者重刷表可以设置append=False，append=True时会搜索重复日期删除
                            IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name, append=True)
                #新建表
                elif operation=='create':
                    logger.info('create new dataset: '+factor_name)
                    file_list = [file_folder+i for i in os.listdir(file_folder)]
                    file_list.sort()
                    IO.csv_dumper(file_list, h5_path, factor_name)
            except Exception as e:
                logger.error(e)
                dump_fail_dict[factor_name].append(date)
    return dump_fail_dict



def industry_retriever(cdate_list, save_path):

    industry_code = ['b10100', 'b10200', 'b10300', 'b10400', 'b10500', 'b10600',
        'b10700', 'b10800', 'b10900', 'b10a00', 'b10b00', 'b10c00', 
        'b10d00', 'b10e00', 'b10f00', 'b10g00', 'b10h00', 'b10i00',
        'b10j00', 'b10k00', 'b10l00', 'b10n00', 'b10o00', 'b10p00', 
        'b10q00', 'b10r00', 'b10s00', 'b10t00','b10m01', 'b10m02', 'b10m03']

    industry_num = [i+1 for i in range(len(industry_code))]
    industry_dict = dict(zip(industry_code,industry_num))
    save_folder = save_path + 'CITIC_I'+'/'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    h5_path = '/data/group/800080/warehouse/prod/DATABASE/WIND/'
    table_name = 'AShareIndustriesClassCITICS'
    table_path = h5_path +  table_name + '/' + table_name + '.h5'
    for date in cdate_list:
        df = IO.read_data([20090101, 20301231], columns=['CITICS_IND_CODE', 'ENTRY_DT','REMOVE_DT','CUR_SIGN'], alt = table_path)
        # df = df[df['CUR_SIGN'] == 1.0]
        df['REMOVE_DT'].fillna(20990101,inplace=True)
        df = df[df['ENTRY_DT']<=date]
        df = df[df['REMOVE_DT'] >= date]
        def industry_parser(ind_code):
            ind2 = ind_code[:6]
            if 'b10u' in ind2:
                ind2 = 'b10m03'
            if 'b10m' in ind2:
                ind_lv2_code = ind2
            else:
                ind_lv2_code = ind2[:4] + '00'
            return ind_lv2_code
        df['lv2_ind_code'] = df['CITICS_IND_CODE'].apply(industry_parser)
        def helper(x,industry_dict):
            # if x in industry_dict:
            return industry_dict[x]
            # else:
                # return -1
        df['lv2_ind_num'] = df['lv2_ind_code'].apply(lambda x:helper(x,industry_dict))
        df.drop(['CITICS_IND_CODE', 'CUR_SIGN','ENTRY_DT','REMOVE_DT','lv2_ind_code', 'lv2_ind_code'], axis=1, inplace=True)
        df.reset_index('dt', inplace=True)
        df.drop('dt', axis=1, inplace=True)
        df.columns = ['CITIC_I']
        df.to_csv(save_folder+str(date)+'.csv')

def cindustry_retriever(cdate_list,save_path):
    save_folder = save_path + 'KNN_I'+'/'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    source_path = '/data/group/800080/warehouse/prod/INDUSTRY/CHINA_STOCK/DAILY/WIND/INDUSTRY_CHINA_STOCK_DAILY_WIND.h5'
    # source_path = r'Z:\warehouse\prod\INDUSTRY\CHINA_STOCK\DAILY\WIND\tmp.h5'
    map_dict = {29:6,30:7,31:8,21:1,27:2,24:2,26:2,25:2,5:3,2:3,3:3,19:4,18:4,15:5,4:5,11:5,22:5,17:5,
    12:5,10:5,6:5,16:5,8:5,7:5,23:5,20:5,13:5,9:5,14:5,1:5,28:5}
    def helper(df,map_dict):
        x = df['CITIC_I']
        if not x in map_dict:
            return -1
        return map_dict[x]
        # else:
            # print(x)
            # return -1
    for date in cdate_list:
        print(date)
        df = IO.read_data(date,columns=['CITIC_I'],alt= source_path)
        df.reset_index('dt', inplace=True)
        df.drop('dt', axis=1, inplace=True)
        # df.dropna(inplace=True)
        df['KNN_I'] = df.apply(lambda x : helper(x,map_dict),axis=1)
#        print(df)
        df.drop(['CITIC_I'],axis=1,inplace=True)
        df.to_csv(save_folder+str(date)+'.csv')



class Factor(object):
    def __init__(self, start_date, end_date, dtype, dfreq, dsource, mkttype, ftype, factor_list, operation='append', factor_scale = None, stock_list= None, max_process=5):
        self.stock_list = stock_list
        self.factor_scale = factor_scale
        self.factor_list = factor_list
        self.dtype = dtype
        self.dfreq = dfreq
        self.dsource = dsource
        self.mkttype = mkttype
        self.ftype = ftype
        self.start_date = start_date
        self.end_date = end_date
        self.operation = 'append'
        self.max_process = max_process
        self.sdate_prev,self.edate,self.cdate_list = check_update_date(self.start_date,self.end_date)
        self.csv_path = config_reader.getConfig('root_path', 'csv_path')
        if self.dtype.name is 'INDEX':
            self.csv_path = self.csv_path + 'index/'
            print(self.csv_path)
        self.h5_root = config_reader.getConfig('root_path', 'h5_root')
        self.h5_path = IO.path_assembler(mkttype=mkttype, dtype=dtype, ftype=ftype, dfreq=dfreq, dsource=dsource, alt=None, h5root=self.h5_root)
        if not os.path.exists(os.path.dirname(self.h5_path)):
            os.makedirs(os.path.dirname(self.h5_path))
        if not os.path.exists(os.path.dirname(self.csv_path)):
            os.makedirs(os.path.dirname(self.csv_path))
        self.fail_dict_master = {}
        self.fail_dict_master['stock_list'] = get_stock_list(self.cdate_list)

    def retriever(self, checker=None):
        pass

    def csv_to_database(self, h5_checker = None):
        pass

    def cronb(self):
        self.retriever()
        self.csv_to_database()

class DailyFactor(Factor):
    def retriever(self, checker=None):
        pass
        # dict_name = self.ftype.name + '_' + self.dfreq.name
        # if self.stock_list:
        #     self.fail_dict_master[dict_name] = save_one_factor(self.factor_list,self.cdate_list,self.csv_path, stock_code=self.stock_list)
        # else:
        #     self.fail_dict_master[dict_name] = save_one_factor(self.factor_list,self.cdate_list,self.csv_path, use_wind_list=True)

    def csv_to_database(self, h5_checker = None):
        dict_name = self.ftype.name + '_' + self.dfreq.name + '_h5'
        print("====================================")
        self.fail_dict_master[dict_name] = update_wind_daily_h5(self.cdate_list, self.factor_list, self.csv_path,
                                                            self.h5_path, operation=self.operation, factor_scale=self.factor_scale)
class QuarterlyFactor(Factor):
    def retriever(self, checker=None):
        dict_name = self.ftype.name + '_' + self.dfreq.name
        self.fail_dict_master[dict_name] = get_wind_qtr_csv(self.cdate_list,self.csv_path,self.factor_list)

    def csv_to_database(self, h5_checker = None):
        dict_name = self.ftype.name + '_' + self.dfreq.name + '_h5'
        qtr_list, stock_code = get_qtr_list(self.cdate_list)
        self.fail_dict_master['fdd_qtr_h5'] = update_wind_qtr_h5(qtr_list,self.factor_list,self.csv_path,self.h5_path, operation=self.operation)
        # h5_daily_fdd_path = IO.path_assembler(mkttype=self.mkttype, dtype=self.dtype, ftype=self.ftype, dfreq=DFreq.DAILY, dsource=self.dsource, alt=None, h5root=self.h5_root)
        # self.fail_dict_master['fdd_qtr2daily_h5']  = update_wind_qtr2daily(self.cdate_list[0], self.cdate_list[-1],self.h5_path,h5_daily_fdd_path,operation=self.operation, max_process=self.max_process)

class INDEX(DailyFactor):
    def __init__(self, start_date, end_date):
        index_list = ['000001.SH','000002.SH', '000016.SH','000300.SH','000905.SH','000906.SH',
                '399001.SZ','399005.SZ','399006.SZ', '000985.CSI']   
        factor_list = ['close', 'pre_close','open']
        # factor_list = ['open']
        super(INDEX, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.INDEX,
                dfreq=DFreq.DAILY, dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.MD, factor_list=factor_list, stock_list=index_list)
    def retriever(self, checker=None):
        INDEX_retrieve(self.cdate_list, self.csv_path, self.stock_list)

class MD(DailyFactor):
    def __init__(self, start_date, end_date):
        md_list = ['close','open','high','low','vwap','adjfactor','turn','volume','pct_chg',
                        'pre_close','total_shares','amt','free_float_shares','mkt_cap_ard']
        # factor_scale ={'amt':10**3,'free_float_shares':10**4,'mkt_cap_ard':10**4,'total_shares':10**4,'volume':10**2}
        super(MD, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK,
                dfreq=DFreq.DAILY, dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.MD, factor_list=md_list,
                factor_scale=None)

    def retriever(self, checker=None):
        MD_retrieve(self.cdate_list)

class FDD_qtr(QuarterlyFactor):
    def __init__(self, start_date, end_date):
        csv_path = config_reader.getConfig('root_path', 'csv_path')
        factor_table = pd.read_excel('/data/group/800080/warehouse/prod/LOCAL_DATA/config/find_indicators1.xlsx',header=0)
        factor_name_dict = {}
        for factor_type in factor_table:
            factor_name_dict[factor_type] = factor_table[factor_type].dropna().values.tolist()
        super(FDD_qtr, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.QUARTERLY,
            dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.FDD, factor_list=factor_name_dict)
    def retriever(self, checker=None):
        FDD_qtr_retrieve_nocal(self.cdate_list)
        FDD_qtr_retriever_withcal_master(self.cdate_list)

class FDD_daily(DailyFactor):
    def __init__(self, start_date, end_date):
        fdd_list = ['pe_ttm','pb_lf','pcf_ocf_ttm','ps_ttm','dividendyield2']
        # fdd_list = ['dividendyield2']
        super(FDD_daily, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.DAILY,
            dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.FDD, factor_list=fdd_list)
    def retriever(self):
        FDD_daily_retriever(self.cdate_list)

class FDD:
    def __init__(self, start_date, end_date):
        self.sdate = start_date
        self.edate = end_date

    def cronb(self):
        update_fdd_qtr = FDD_qtr(self.sdate, self.edate)
        update_fdd_qtr.cronb()
        update_fdd_daily = FDD_daily(self.sdate, self.edate)
        update_fdd_daily.cronb()

class INDUSTRY(DailyFactor):
    def __init__(self, start_date, end_date):
        factor_list = ['CITIC_I']

        super(INDUSTRY, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.DAILY,
            dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.INDUSTRY, factor_list=factor_list)

    def retriever(self, checker=None):
        industry_retriever(self.cdate_list, self.csv_path)


class CINDUSTRY(DailyFactor):
    def __init__(self, start_date, end_date):
        factor_list = ['KNN_I']
        super(CINDUSTRY, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.DAILY,
            dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.INDUSTRY, factor_list=factor_list)

    def retriever(self, checker=None):
        cindustry_retriever(self.cdate_list, self.csv_path)

def test(sdate=None, edate=None):
    sdate,edate,cdate_list = check_update_date(sdate=sdate,edate=edate)

    for _type in [FDD]:
        _type(sdate, edate).cronb()


def update_wind(sdate=None, edate=None):
    get_wind_secu_status_v2()
    sdate,edate,cdate_list = check_update_date(sdate=sdate,edate=edate)
    for _type in [INDEX,MD]:  # [INDEX,MD,INDUSTRY,CINDUSTRY,FDD]
        _type(sdate, edate).cronb()
        
def update_wind1(sdate=None, edate=None):
#    get_wind_secu_status_v2()
    sdate,edate,cdate_list = check_update_date(sdate=sdate,edate=edate)
    for _type in [INDUSTRY,CINDUSTRY,FDD]:  # [INDEX,MD,INDUSTRY,CINDUSTRY,FDD]
        _type(sdate, edate).cronb()
        
#    for _type in [MD]:  # [INDEX,MD,INDUSTRY,CINDUSTRY,FDD]
#        _type(sdate, edate).cronb()
    
#    flag_root = '/data/group/800080/warehouse/prod/LOCAL_DATA/FLAG/' + str(edate) + '/'
#    flag_path1 = flag_root + str(edate) + '_' + 'MD_ori.success'
#    with open(flag_path1,'w') as file:
#        pass
#    while not os.path.exists(os.path.join(flag_root,str(edate)+"_"+"MD.success")):
#        time.sleep(60)
#        print("wait for MD.success") 
    
#    for _type in [INDEX,INDUSTRY,CINDUSTRY,FDD]:  # [INDEX,MD,INDUSTRY,CINDUSTRY,FDD]
#        _type(sdate, edate).cronb()



def wind_weekend_job(sdate=None,edate=None):
    sdate,edate,cdate_list = check_update_date(sdate=sdate,edate=edate)

    update_fdd_qtr = FDD_qtr(sdate, edate)
    update_fdd_qtr.cronb()

def tmp(sdate=None, edate=None):
    sdate,edate,cdate_list = check_update_date(sdate=sdate,edate=edate)

    for _type in [MD]:
        _type(sdate, edate).cronb()
        
# tmp(20200221,20200221)