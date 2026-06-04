# _*_ coding:utf-8 _*_

import pandas as pd
import numpy as np
from Wind.utils import *
import os
import datetime as dt
import subprocess
import json
from log import Log


logger = Log('update_universe')


def updater_universe_csv(cdate_list,sql_config):
    logger.info("updater_universe_csv")
    store_path = "/app/data/wdb_h5/WIND/universe_complete/csvlst/"
    # listing date
    fPath2 = store_path + 'Listing_date/'
    if not os.path.exists(fPath2):
        os.makedirs(fPath2)
    factor_list = ['S_INFO_WINDCODE','S_INFO_LISTDATE', 'S_INFO_DELISTDATE']
    table = "Wind.AShareDescription"
    df = get_wind_data(table,factor_list,sql_config)
    df.rename(columns={"S_INFO_WINDCODE":"Ticker"},inplace=True)
    df.set_index("Ticker",inplace=True)
    df.fillna(20990101, inplace = True)
    if df['S_INFO_LISTDATE'].dtype == 'object':
        df['S_INFO_LISTDATE']=df['S_INFO_LISTDATE'].apply(pd.to_numeric)
    if df['S_INFO_DELISTDATE'].dtype == 'object':
        df['S_INFO_DELISTDATE']=df['S_INFO_DELISTDATE'].apply(pd.to_numeric)
    if isinstance(df['S_INFO_DELISTDATE'][0], str):
        df.loc[:,'S_INFO_DELISTDATE'] = pd.to_numeric(df.loc[:,'S_INFO_DELISTDATE'])
    df = df[(df['S_INFO_DELISTDATE'] >= 20090101) & (df['S_INFO_LISTDATE'] <= cdate_list[-1])]
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
    tmp_df_1 = tmp_df[tmp_df['Ticker'].isin(Ticker_list)]
    tmp_df_1.set_index('Ticker', inplace=True)
    for date in cdate_list:
        tmp_df_1.to_csv(fPath2+str(date)+'.csv')


    index_list = ['SH50', 'HS300','ZZ500']
    logger.info("Start to write SH50,HS300,ZZ500 to csv ....")
    save_index_component(cdate_list, index_list, store_path,sql_config)
    # stock filter
    logger.info('Stock filter')
    filter_list = ['STPT', 'SSO']
    for filter_type in filter_list:
        logger.info("Start stock filter -- %s"%filter_type)
        stock_filter_v2(cdate_list, filter_type,sql_config)


def stock_filter_v2(cdate_list, filter_type,sql_config):
    store_path = "/app/data/wdb_h5/WIND/universe_complete/csvlst/"
    if filter_type is 'STPT':
        file_path = store_path + filter_type + '/'
        logger.info('STPT:')
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        for date in cdate_list:
            logger.info("STPT--- %s"%str(date))
            ST_list = get_ST(date,sql_config)
            table_name = 'Wind.AShareEODPrices'
            sql_use = "select S_INFO_WINDCODE,TRADE_DT,S_DQ_OPEN from %s where TRADE_DT = %s" % (table_name,str(date))
            logger.info("STPT:start to get data from Oracle ...")
            df = sql_parser(queryUserTableData(sql_use,sql_config))
            logger.info("STPT:success write to DataFrame...")
            # 无数据则跳过此次循环
            if df.empty:
                continue
            df.rename(columns={"S_INFO_WINDCODE": "Ticker","TRADE_DT":"dt"}, inplace=True)
            df.set_index("Ticker", inplace=True)
            Ticker_list = list(df.index.values)
            delist_Ticker = []
            for ticker in Ticker_list:
                if not ticker[0].isdigit():
                    delist_Ticker.append(ticker)
                elif ticker[0] == '9':
                    delist_Ticker.append(ticker)
            Ticker_list = list(set(Ticker_list) - set(delist_Ticker))
            df.reset_index('Ticker', inplace=True)
            df.set_index('dt',inplace=True)
            df = df[df['Ticker'].isin(Ticker_list)]
            df['STPT'] = df.apply(lambda x: '0' if x['Ticker'] in ST_list else '1', axis=1)
            df.drop(columns=['S_DQ_OPEN'], inplace=True)
            df['STPT'] = df['STPT'].astype(float)
            df.reset_index('dt',drop=True,inplace=True)
            df.set_index('Ticker', inplace=True)
            df.to_csv(file_path + str(date) + '.csv')
        logger.info('STPT write to csv end!')
    else:
        # filter stock first
        logger.info('Download data for Computingg')
        factor_name_mapping = {'S_DQ_OPEN': 'open', 'S_DQ_PRECLOSE': 'pre_close', 'S_DQ_AMOUNT': 'amt'}
        table_name = 'Wind.AShareEODPrices'
        for date in cdate_list:
            STPT_list = get_ST(date,sql_config)
            logger.info("--" + str(date))
            sql_use = "select S_INFO_WINDCODE,S_DQ_OPEN,S_DQ_PRECLOSE,S_DQ_AMOUNT from %s where TRADE_DT = %s" % (table_name,str(date))
            logger.info("SSO:start to get data from Oracle...")
            df = sql_parser(queryUserTableData(sql_use,sql_config))
            logger.info("SSO:success write to DataFrame...")
            # 无数据则跳过此次循环
            if df.empty:
                continue
            df.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
            df.set_index("Ticker", inplace=True)
            factor_list = []
            for i in df.columns.values:
                factor_list.append(factor_name_mapping[i])
            df.columns = factor_list

            df = df.sort_index()
            df.index.name = 'Ticker'

            df = df.where(df.notnull(), 0)
            # SUSPEND
            df['SUSPEND'] = df.apply(lambda x: 1 if x.amt > 0 else 0, axis=1)
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

            df['OPENDOWNLIMIT'] = df.apply(lambda x: help1(x), axis=1)

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

            df['OPENUPLIMIT'] = df.apply(lambda x: help2(x), axis=1)
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

            df['SSO'] = df.apply(lambda x: help3(x), axis=1)
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
            df_suspend = df.drop(columns=['open', 'pre_close', 'amt', 'OPENDOWNLIMIT', 'OPENUPLIMIT', 'SSO'])
            df_suspend.to_csv(file_path_suspend + str(date) + '.csv')

            # opendownlimit
            logger.info('OPENDOWNLIMIT')
            file_path_opendownlimit = store_path + 'OPENDOWNLIMIT/'
            if not os.path.exists(file_path_opendownlimit):
                os.makedirs(file_path_opendownlimit)
            df_opendownlimit = df.drop(columns=['open', 'pre_close', 'amt', 'SUSPEND', 'OPENUPLIMIT', 'SSO'])
            df_opendownlimit.to_csv(file_path_opendownlimit + str(date) + '.csv')

            # openuplimit
            logger.info('OPENUPLIMIT')
            file_path_openuplimit = store_path + 'OPENUPLIMIT/'
            if not os.path.exists(file_path_openuplimit):
                os.makedirs(file_path_openuplimit)
            df_openuplimit = df.drop(columns=['open', 'pre_close', 'amt', 'SUSPEND', 'OPENDOWNLIMIT', 'SSO'])
            df_openuplimit.to_csv(file_path_openuplimit + str(date) + '.csv')

            # SSO
            logger.info('SSO')
            file_path_sso = store_path + 'SSO/'
            if not os.path.exists(file_path_sso):
                os.makedirs(file_path_sso)
            df_sso = df.drop(columns=['open', 'pre_close', 'amt', 'SUSPEND', 'OPENDOWNLIMIT', 'OPENUPLIMIT'])
            df_sso.to_csv(file_path_sso + str(date) + '.csv')

            # total
            file_path_total = store_path + 'total/'
            if not os.path.exists(file_path_total):
                os.makedirs(file_path_total)
            df.to_csv(file_path_total + str(date) + '.csv')


def save_index_component(cdate_list, index_list, save_path,sql_config):
    date_min = {'HS300': 20020104,
                'ZZ500': 20050104,
                'CYB': 20100601,
                'MS_cap': 20050609,
                'SH50': 20100104}
    if type(index_list) == str:
        index_list = [index_list]

    for index in index_list:
        logger.info('-' * 10 + index + '-' * 10)
        save_folder = save_path + index + '/'
        if not os.path.exists(save_folder):
            os.mkdir(save_folder)

        for date in cdate_list:
            logger.info(index + ': ' + str(date))
            if date < date_min[index]:
                logger.info('skip')
            elif date >= date_min[index]:
                if index == 'HS300':
                    dat = get_hset(date,'000300',sql_config)
                elif index == 'ZZ500':
                    dat = get_hset(date, '000905',sql_config)
                elif index == 'SH50':
                    dat = get_hset(date, '000016',sql_config)
                dict_index = {}
                dict_index['Ticker'] = dat[0]
                dict_index[index] = dat[2]
                df = pd.DataFrame(dict_index)
                df.set_index('Ticker', inplace=True)
                df.sort_index(inplace=True)
                df.to_csv(save_folder + str(date) + '.csv')
        logger.info("The %s write to csv success!" % index)


def get_hset(date,index_stock,sql_config):
    # 获取成分股信息
    sql_use = "select stock_code as symbol, stock_name as name, weight from quant_data.qd_index_weights_view where tradingcode = %s%s%s and tradingday = (select lasttradingday from quant_data.qd_tradingdays where tradingday = %s) "%("'",index_stock,"'",str(date))
    logger.info(sql_use)
    logger.info("Start to get the constituent stocks info...")
    df = sql_parser(queryUserTableData(sql_use,sql_config))
    logger.info("Success get constituent stocks info...")
    df_array = np.array([df["SYMBOL"], df["NAME"], df["WEIGHT"]])
    dat = df_array.tolist()
    return dat


def get_ST(date,sql_config):
    table_name = 'Wind.AShareST'
    factor_list = ['S_INFO_WINDCODE','ENTRY_DT', 'REMOVE_DT', 'S_TYPE_ST']
    df = get_wind_data(table_name,factor_list,sql_config)
    df.rename(columns={"S_INFO_WINDCODE":"Ticker"},inplace=True)
    df.set_index("Ticker",inplace=True)
    df1 = df[df['S_TYPE_ST'] == 'S']
    df2 = df[df['S_TYPE_ST'] == 'T']
    df = df1.append(df2)
    Ticker_list = []
    if df['REMOVE_DT'].dtype == 'object':
        df['REMOVE_DT'] = df['REMOVE_DT'].apply(pd.to_numeric)
    if df['ENTRY_DT'].dtype == 'object':
        df['ENTRY_DT'] = df['ENTRY_DT'].apply(pd.to_numeric)
    if isinstance(df['ENTRY_DT'][0], str):
        df.loc[:,'ENTRY_DT'] = pd.to_numeric(df.loc[:,'ENTRY_DT'])
    if isinstance(df['REMOVE_DT'][0], str):
        df.loc[:,'REMOVE_DT'] = pd.to_numeric(df.loc[:,'REMOVE_DT'])
    for index, row in df.iterrows():
        if row['ENTRY_DT'] <= date:
            if pd.isnull(row['REMOVE_DT']):
                Ticker_list.append(str(index))
                continue
            if row['REMOVE_DT'] <= date :
                continue
            else:
                Ticker_list.append(str(index))
    return Ticker_list


def update_universe_raw(cdate_list,csv_path,h5_path,factor_list,sql_config):
    logger.info ('-'*60+'\nUpdating H5 from CSV \n'+h5_path)
    dump_list1 = [str(i) + '.csv' for i in cdate_list]
    pre_cwd = os.getcwd()
    for factor_name in factor_list:
        dump_list = []
        logger.info (factor_name)
        result_folder = csv_path+factor_name+'/'
        os.chdir(result_folder)
        csv_list = os.listdir(result_folder)
        if len(csv_list) == 0 or "%s" % str(cdate_list[-1]) + '.csv' not in csv_list:
            updater_universe_csv(cdate_list,sql_config)
            csv_list = os.listdir(result_folder)
        for csv in csv_list:
            if csv in dump_list1:
                dump_list.append(csv)
        if not dump_list:
            updater_universe_csv(cdate_list,sql_config)
        csv_dumper(dump_list,h5_path,factor_name)

    os.chdir(pre_cwd)
    logger.info ('H5 update complete\n'+'-'*60)


def create_universe_v2(sdate, edate, h5_path,sql_config):
    print('-' * 20, '\nForming Universe')
    logger.info('create_universe_v2: Loading data')
    sdate_prev, edate, cdate_list = check_update_date(sdate, edate, 252,sql_config)

    # check base data
    data_MI = read_data([sdate_prev, edate], alt=h5_path, max_workers=1)
    date_check = np.isfinite(data_MI.loc[str(edate)]).sum(axis=0)
    if (date_check >= [300,1000,1000,1000,50,1000,1000,1000,500]).sum() < 9:
        logger.info ('Warning: universe raw data error at date:%s'%str(edate))
        logger.info("date_check:\n %s" % str(date_check))
        return "Warning"
        # raise AssertionError

    # check mkt_cap_ard
    # mkt_cap_MI = IO.read_data([sdate_prev,edate],columns=['mkt_cap_ard'],alt = r'Z:\warehouse\prod\MD\CHINA_STOCK\DAILY\WIND\MD_CHINA_STOCK_DAILY_WIND.h5',max_workers=1)
    alt_path = '/app/data/wdb_h5/WIND/MD_CHINA_STOCK_DAILY_WIND/MD_CHINA_STOCK_DAILY_WIND.h5'
    mkt_cap_MI = read_data([sdate_prev, edate], columns=['mkt_cap_ard'],alt=alt_path, max_workers=1)
    mkt_cap = mkt_cap_MI.unstack()
    if (np.isfinite(mkt_cap).sum(axis=1)<500).sum()>0:
        logger.info('mkt_cap has no data...')
        raise AssertionError

    mkt_cap_5pct = mkt_cap.quantile(q=0.05, axis=1)
    mk_cap_ind = mkt_cap.sub(mkt_cap_5pct, axis=0) > 0
    mk_cap_ind_mi = pd.DataFrame(mk_cap_ind.stack())
    mk_cap_ind_mi.rename(columns={"mkt_cap_ard":"mkt_cap_5pct"},inplace=True)
    logger.info('Computing')

    # listing date
    # fdate_list_dt = read_data([19900101, 20990101], ftype=FType.CALENDAR).index.get_level_values(0).tolist()
    # fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    # 获取交易日列表
    fdate_list = get_Tradingday_list(sql_config,19900101, 20990101)
    fdate_list_dt = [pd.Timestamp(str(i)) for i in fdate_list]

    data_MI.reset_index(inplace=True)
    data_MI["delete_column"] = data_MI["dt"]
    dt_list = list(set(data_MI["dt"]))
    map_dict = {k:k in fdate_list_dt for k in dt_list}
    data_MI["delete_column"] = data_MI["delete_column"].map(map_dict)
    data_MI = data_MI[data_MI["delete_column"]]
    data_MI.drop("delete_column",axis=1,inplace=True)
    data_MI.set_index(["dt","Ticker"],inplace=True)

    listing_date = data_MI['Listing_date'].copy()
    listing_date = listing_date.reset_index()[['Ticker', 'Listing_date']].drop_duplicates()
    listing_date['Listing_date'] = listing_date['Listing_date'].apply(lambda x: 0 if x == 20990101 else x)
    listing_date['Listing_date'] = listing_date['Listing_date'].apply(lambda x: max(19910102, x))
    listing_date['listing_date_position'] = listing_date['Listing_date'].apply(lambda x: fdate_list.index(int(x)))
    listing_date = listing_date.set_index('Ticker')
    data_MI['current_date'] = data_MI.index.get_level_values(0)
    data_MI['current_stk'] = data_MI.index.get_level_values(1)
    td_position = {k: fdate_list_dt.index(k) for k in fdate_list_dt}
    stk_position = listing_date['listing_date_position'].to_dict()

    data_MI['current_date_position'] = data_MI['current_date'].apply(lambda x: td_position[x])
    data_MI['listing_date_position'] = data_MI['current_stk'].apply(lambda x: stk_position[x])
    data_MI['days_since_ipo'] = data_MI['current_date_position'] - data_MI['listing_date_position']


    day_num_year = 242
    day_half_year = 121
    data_MI['listing_1yr'] = data_MI['days_since_ipo'] > day_num_year * 1
    data_MI['listing_3yr'] = data_MI['days_since_ipo'] > day_num_year * 3
    data_MI['listing_121d'] = data_MI['days_since_ipo'] > day_half_year

    # universe
    filter_suspend = data_MI['SUSPEND'].unstack()

    over_half_for_half_year = filter_suspend.fillna(0).rolling(window=day_half_year).sum() > int(day_half_year / 2)
    over_half_for_half_year_mi = pd.DataFrame(over_half_for_half_year.stack(), columns=['over_half_for_half_year'])

    data_MI = pd.concat([data_MI, over_half_for_half_year_mi, mk_cap_ind_mi], axis=1)

    # risk / alpha
    data_MI['risk_universe'] = data_MI['listing_1yr'] * data_MI['STPT'] * data_MI['over_half_for_half_year'] * data_MI['mkt_cap_5pct']
    data_MI['alpha_universe'] = data_MI['risk_universe'] * data_MI['SUSPEND']

    # index
    data_MI['index_50'] = data_MI['SH50'] > 0
    data_MI['index_300'] = data_MI['HS300'] > 0
    data_MI['index_500'] = data_MI['ZZ500'] > 0

    data_config = {'index_name': ['dt', 'Ticker'],
                   'type_number': ['HS300', 'ZZ500', 'SH50', 'Listing_date', 'OPENDOWNLIMIT',
                                   'OPENUPLIMIT', 'SSO', 'STPT', 'SUSPEND', 'risk_universe', 'alpha_universe'],
                   'type_int': ['Listing_date'],
                   'type_bool': ['OPENDOWNLIMIT', 'OPENUPLIMIT', 'SSO', 'STPT', 'SUSPEND',
                                 'risk_universe', 'alpha_universe', 'index_50', 'index_300', 'index_500',
                                 'listing_1yr', 'listing_3yr', 'over_half_for_half_year'],
                   'type_weight': ['HS300', 'SH50', 'ZZ500'],
                   'name_orig': ['HS300', 'Listing_date', 'OPENDOWNLIMIT', 'OPENUPLIMIT', 'SH50', 'SSO',
                                 'STPT', 'SUSPEND', 'ZZ500', 'risk_universe', 'alpha_universe',
                                 'listing_1yr', 'listing_3yr', 'over_half_for_half_year', 'index_50',
                                 'index_300', 'index_500'],
                   'name_new': ['index_weight_hs300', 'Listing_date', 'filter_opendownlimit', 'filter_openuplimit',
                                'index_weight_sh50', 'filter_sso',
                                'filter_stpt', 'filter_suspend', 'index_weight_zz500', 'risk_universe',
                                'alpha_universe',
                                'listing_1yr', 'listing_3yr', 'over_half_for_half_year', 'index_50',
                                'index_300', 'index_500'],
                   'column_order': ['risk_universe', 'alpha_universe', 'index_50', 'index_300', 'index_500',
                                    'index_weight_sh50', 'index_weight_hs300', 'index_weight_zz500',
                                    'filter_opendownlimit', 'filter_openuplimit', 'filter_sso', 'filter_stpt',
                                    'filter_suspend',
                                    'Listing_date', 'listing_1yr', 'listing_3yr', 'over_half_for_half_year']}
    dat = data_MI_formatter(data_MI[data_config['name_orig']], data_config)

    cut_list = [str(i) for i in cdate_list] if len(cdate_list) > 1 else str(cdate_list[0])
    data_universe = dat.loc[cut_list].dropna()
    logger.info('Universe Complete\n'+'-' * 20)
    return data_universe


def data_MI_formatter(dat,data_config):
    dat.index.names = data_config['index_name']
    dat = dat.reset_index()
    dat.Ticker = dat.Ticker.astype('object')
    dat = dat.set_index(data_config['index_name'])
    dat[data_config['type_number']] = dat[data_config['type_number']].fillna(0)
    dat[data_config['type_int']] = dat[data_config['type_int']].astype('int')
    dat[data_config['type_bool']] = dat[data_config['type_bool']].astype('bool')
    dat[data_config['type_weight']] = dat[data_config['type_weight']]/100.0
    dat.columns = data_config['name_new']
    dat = dat[data_config['column_order']]
    return dat


class unv_factor(object):
    def __init__(self, start_date, end_date,sql_config):
        self.start_date = start_date
        self.end_date = end_date
        self.sdate_prev, self.edate, self.cdate_list = check_update_date(self.start_date, self.end_date)
        self.sql_config = sql_config
        self.fail_dict = {}
        # self.h5_root = "/app/data/wdb_h5/"

    def retriever(self):
        updater_universe_csv(self.cdate_list,self.sql_config)
        # updater_matlab_universe(self.cdate_list)

    def csv_to_database(self):
        csv_path = "/app/data/wdb_h5/WIND/universe_complete/csvlst/"
        source_table = "universe_complete"
        destination_table = "UNIV_CHINA_STOCK_DAILY_OPTM"
        h5_path = "/app/data/wdb_h5/WIND/"
        if not os.path.exists(h5_path + source_table):
            os.mkdir(h5_path + source_table)
        h5_path_source = h5_path + source_table + "/" + source_table + ".h5"
        if not os.path.exists(h5_path + destination_table):
            os.mkdir(h5_path + destination_table)
        h5_path_destination = h5_path + destination_table + "/" +destination_table + ".h5"
        # h5_path_destination = IO.path_assembler(mkttype=MktType.CHINA, dtype=DType.STOCK, ftype=FType.UNIV,
        #                                         dfreq=DFreq.DAILY, dsource=DSource.OPTM, alt=None, h5root=self.h5_root)
        factor_list = ['HS300','Listing_date','OPENDOWNLIMIT','OPENUPLIMIT','SH50','SSO','STPT','SUSPEND','ZZ500']
        update_universe_raw(self.cdate_list, csv_path, h5_path_source, factor_list,self.sql_config)
        """Create Universe"""
        data_universe = create_universe_v2(self.sdate_prev, self.edate, h5_path_source,self.sql_config)
        if not isinstance(data_universe,pd.DataFrame) and data_universe == "Warning":
            return
        check_universe = data_universe.sum()
        
        if check_universe['risk_universe'] < 100:
            self.fail_dict['risk_universe'] = self.cdate_list
            logger.info(check_universe)
            # log_file = csv_path + 'log/' + str(self.cdate_list[-1]) + '.json'
            raise AssertionError

        if check_universe['alpha_universe'] < 100:
            logger.info(check_universe)
            self.fail_dict['alpha_universe'] = self.cdate_list
            # log_file = csv_path + 'log/' + str(self.cdate_list[-1]) + '.json'
            raise AssertionError

        final_date_list = list(set(data_universe.index.get_level_values(0)))
        final_date_list.sort()
        logger.info('Updating Universe... takes 2 min due to network speed...')
        logger.info('Date updated: \n' + str(final_date_list))
        # dataset_name = 'stock_universe'
        dataset_names = ["Listing_date", "alpha_universe", "filter_opendownlimit",
                         "filter_openuplimit", "filter_sso", "filter_stpt", "filter_suspend",
                         "index_300", "index_50", "index_500", "index_weight_hs300",
                         "index_weight_sh50", "index_weight_zz500", "listing_1yr", "listing_3yr",
                         "over_half_for_half_year", "risk_universe"]
        # data_universe.reset_index(inplace=True)
        return data_universe

    def cronb(self):
        self.retriever()
        return self.csv_to_database()

def updater_universe(sql_config,cdate_list,date,factor_name):
    logger.info("Start to update universe!")
    if len(cdate_list)>1:
        start_date = min(cdate_list)
        end_date = max(cdate_list)
    else:
        start_date = end_date =cdate_list[0]
    return unv_factor(end_date, end_date,sql_config).cronb()




