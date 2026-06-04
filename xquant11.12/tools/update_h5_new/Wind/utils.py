# _*_ coding:utf-8 _*_
import cx_Oracle
import pandas as pd
import numpy as np
import re
import datetime as dt
from enum import Enum, unique
import concurrent.futures
import datetime
import time
import os
from log import Log
from xml.dom.minidom import parse
import xml.etree.ElementTree as ET
import collections
from Wind.push_kafka import push_data
import json
logger = Log("utils")


@unique
class DType(Enum):
    STOCK = 1
    FUTURES = 2
    SPOT = 3
    INDEX = 4


@unique
class DFreq(Enum):
    TICK = 1
    MINUTE = 2
    DAILY = 3
    WEEKLY = 4
    QUARTERLY = 5
    MONTHLY = 6
    YEARLY = 7


@unique
class DSource(Enum):
    HTSC = 1
    WIND = 2
    OPTM = 3
    STYLEFACTOR = 4
    STYLE = 5
    WEIGHT = 6


@unique
class UniType(Enum):
    HS300 = 1
    ZZ500 = 2
    SZ50 = 3


@unique
class MktType(Enum):
    CHINA = 1
    HK = 2
    US = 3


@unique
class FType(Enum):
    FDD = 1  # Fundamental Data
    MD = 2  # Market Data
    FCD = 3  # Forcast Data
    FACTOR = 4  # Factor Data
    ALPHA = 5  # Alpha Factor
    RISK = 6  # Risk Factor
    UNIV = 7  # Universe Data
    INDUSTRY = 8  # Industry Data
    CALENDAR = 9  # Calendar Data
    FWD5 = 10
    FWD10 = 11

def queryUserTableData(sql_use,sql_config):
    logger.info("Create connect to Oracle...")
    # conn = cx_Oracle.connect("center_read/Htsc_Htzx@168.9.2.43/qdb04", encoding="UTF-8", nencoding="UTF-8")
    # conn = cx_Oracle.connect("center_admin/timegao@168.61.2.2/servdb", encoding="UTF-8", nencoding="UTF-8")
    conn = cx_Oracle.connect(sql_config, encoding="UTF-8", nencoding="UTF-8")
    cur = conn.cursor()
    logger.info("Execute the sql...")
    cur.execute(sql_use)
    index = cur.description
    column_name = []
    for i in index:
        column_name.append(i[0])
    result = []
    result.append(column_name)
    for res in cur.fetchall():
        result.append(list(res))
    logger.info("Close the cursor and connect...")
    cur.close()
    conn.close()
    return str(result)

def sql_parser(data):
    NaN = np.nan
    try:
        _data = eval(data)
    except SyntaxError as _exp:
        print(_exp)
        if 'triple-quoted string' in _exp.msg:
            data = re.sub(r"'{3,}", '', data)
            data = re.sub(r'"{3,}', '', data)
            _data = eval(data)
        else:
            raise SyntaxError
    try:
        res = pd.DataFrame(_data[1:], columns=_data[0])
    except OverflowError:
        res = pd.DataFrame(_data, columns=_data[0])
        res = res.drop([0], axis=0).reset_index(drop=True)
    return res

def get_wind_data(table,factor_list,sql_config,date=None):
    sql1 = "select distinct "
    params = "%s," * len(factor_list)
    factor_param = params[:-1] % tuple(factor_list)
    sql2 = " from %s where %s = %s"%(table,factor_list[1],str(date))
    sql3 = " from %s"%table
    if table in ["Wind.AShareIndustriesClassCITICS","Wind.AShareDescription","Wind.AShareST"]:
        sql_use = sql1 + factor_param + sql3
    else:
        sql_use = sql1 + factor_param + sql2
    logger.info(sql_use)
    df = sql_parser(queryUserTableData(sql_use,sql_config))
    logger.info("Success get data from Oracle - %s" % table)
    return df

def get_root_keys(h5_store):
    '''
    --- DESCRIPTION ---
    Get group keys
    '''
    if type(h5_store) is pd.io.pytables.HDFStore:
        return ['/' + item for item in list(h5_store.root._v_groups.keys())]


def pd_hdf5_writer(pd_factor, hdf5, dataset=None, override=None, append=None,append_all=None,
                   min_itemsize=None,from_scratch=True,date_column=None,override_overlap=True,date=None):
    '''
    --- DESCRIPTION ---
    Dump DataFrame/Series into HDF5 dataset with override and append switch
    By default, override and append switch are both unset (None)

    --- CAUTION ---
    Only ONE tag should be set during one single Func call
    Input DataFrame should be multiIndexed by ['dt', 'Ticker']
    dataset should be explicitly specified or can be inferred by DataFrame name

    --- PARAMETER ---
    override : DataFrame will replace dataset content in hdf5 file
    append   : DataFrame will be appended (possibly override certain data) to dataset in hdf5 file
    otherwise: DataFrame will be stored as new dataset in hdf5 file
    '''

    ts_meta = dt.datetime.today()
    # date 执行的任务日期，补历史数据时date设为20990101 不在xquant面板显示任务
    if date:
        execDate = str(date)
    else:
        execDate = str(20990101)
    key = "stop"
    # DataFrame format verification
    if pd_factor.index.names != ['dt', 'Ticker'] and pd_factor.index.names != ['dt', 'OBJECT_ID'] and pd_factor.index.names != ['dt', 'ID']:
        logger.info('DataFrame passed in is not legit multiIndex DataFrame, aborting...')
        raise TypeError
    else:
        pd_factor = pd_factor.sort_index(level=0)

    if dataset is None:
        # dataset should be able to be inferred by name attribute
        try:
            dataset = pd_factor.name
        except:
            logger.info('dataset cannot be inferred by Dataframe name, aborting...')
            raise AssertionError

    if '/' not in dataset:
        dataset = '/' + dataset

    # Parameter verification
    # Only three modes are valid: override, append, new
    if override is not None and append is not None:
        logger.info('Only one tag of override and append can be specified, aborting...')
        raise SyntaxError
    if override is not None:
        if override is not True:
            logger.info('The override tag should only be True or unset, aborting...')
            raise SyntaxError
    if append is not None:
        if append is not True:
            logger.info('The append tag should only be True or unset, aborting...')
            raise SyntaxError

    with pd.HDFStore(hdf5) as h5_store:
        # Common actions, dt_lst extraction
        if dataset in get_root_keys(h5_store):
            # dataset is already created
            try:
                if from_scratch:
                    dt_lst = pd.to_datetime(h5_store.select_column(dataset, 'dt').dt.date.unique()).tolist()
                    logger.info('%s last tapped date: %s' % (dataset, h5_store.get_storer(dataset).attrs.modification_date.isoformat()))
                else:
                    dt_lst = list(set(h5_store.select_column(dataset, 'dt')))
                    logger.info('%s last tapped date: %s' % (dataset, h5_store.get_storer(dataset).attrs.modification_date.isoformat()))
            except AttributeError:
                logger.info('Last tapped date unknown, data may be corrupted...')
                if append or override:
                    raise AttributeError
                else:
                    dt_lst = []
        else:
            dt_lst = []
        try:
            h5_name = os.path.split(hdf5)[-1][:-3]
            if h5_name == dataset[1:]:
                isH5 = 1
            else:
                isH5 = 0
        except Exception as e:
            logger.error("split h5_path occurred:%s"%e)
            isH5 = 0
        

        if override:
            # time_stamp = list(set(pd_factor.index.levels[0]))[0]
            # execDate = dt.datetime.strftime(time_stamp,"%Y%m%d")
            if from_scratch:
                exist_flag = len(dt_lst) != 0
            else:
                exist_flag = not is_empty_dataset(h5_store, dataset)
            if not exist_flag:
                # dt_lst is empty
                logger.info('%s does not exit in %s, aborting...' % (dataset, hdf5))
                raise AssertionError
            try:
                produceTime1 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                if isH5:
                    params = {'method':key,'taskNames':dataset[1:],'execDate':execDate,'taskStatus':2,
                              'isH5':'0','produceTime':produceTime1}
                else:
                    params = {'method': key, 'taskNames': h5_name+'_'+dataset[1:], 'execDate': execDate, 'taskStatus': 2,
                              'isH5': '0', 'produceTime': produceTime1}
                h5_store.put(dataset, pd_factor, format='table', append=False, data_columns=True,min_itemsize=min_itemsize)
                if date:
                    push_data(params)
                    params_message = json.dumps(params)
                    logger.info("kafka_message" + params_message)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
            except Exception as e:
                produceTime2 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                if isH5:
                    params = {'method':key,'taskNames':dataset[1:],'execDate':execDate,'taskStatus':3,
                              'isH5': '0', 'produceTime': produceTime2}
                else:
                    params = {'method': key, 'taskNames': h5_name+'_'+dataset[1:], 'execDate': execDate, 'taskStatus': 3,
                              'isH5': '0', 'produceTime': produceTime2}
                if date:
                    push_data(params)
                    params_message = json.dumps(params)
                    logger.info("kafka_message" + params_message)
                logger.error("store h5name is %s table is %s Error occurred: %s" % (hdf5, dataset, e))
            logger.info('%s is overriden with newly input DataFrame in %s' % (dataset, hdf5))
        elif append:
            # Append Func with data replacement
            if date_column is not None:
                dt_lst_to_process = pd.to_datetime(pd.unique(pd_factor[date_column])).tolist()
            else:
                dt_lst_to_process = pd.to_datetime(pd.unique(pd_factor.index.get_level_values('dt').date)).tolist()
            dt_lst_to_process.sort()
            # dt_lst_to_process = list(set(pd_factor.index.get_level_values('dt')))
            for date_ticker in dt_lst_to_process:
                # execDate = dt.datetime.strftime(date_ticker,"%Y%m%d")
                # if from_scratch:
                #     exist_flag = date_ticker in dt_lst
                # else:
                #     exist_flag = date_is_exist(date_ticker, h5_store, dataset)
                if date_ticker in dt_lst:
                    # Delete old records
                    if date_column is None:
                        record_num = h5_store.remove(dataset, 'dt>=%s & dt<%s' % (date_ticker.strftime('%Y%m%d'),
                                                                                 (date_ticker + pd.Timedelta('1D')).strftime('%Y%m%d')))
                    else:
                        record_num = h5_store.remove(dataset, '%s=date_ticker' % date_column)
                    # record_num = h5_store.remove(dataset, 'dt=date_ticker')
                    logger.info('%d records deleted at %s %s' % (record_num, date_ticker.isoformat(), dataset))
                # Append new records
                try:
                    produceTime3 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                    if isH5:
                        params = {'method':key,'taskNames':dataset[1:],'execDate':execDate,'taskStatus':2,
                                  'isH5': '0', 'produceTime': produceTime3}
                    else:
                        params = {'method': key, 'taskNames': h5_name+'_'+dataset[1:], 'execDate': execDate, 'taskStatus': 2,
                                  'isH5': '0', 'produceTime': produceTime3}
                    if date_column is not None:
                        h5_store.append(dataset, pd_factor.loc[pd_factor[date_column]==date_ticker], data_columns=True,min_itemsize=min_itemsize)
                    else:
                        h5_store.append(dataset, pd_factor.loc[date_ticker.isoformat()], data_columns=True,min_itemsize=min_itemsize)
                    if date:
                        push_data(params)
                        params_message = json.dumps(params)
                        logger.info("kafka_message" + params_message)
                    h5_store.get_storer(dataset).attrs.modification_date = ts_meta
                except Exception as e:
                    produceTime4 = dt.datetime.strftime(dt.datetime.now(), '%Y-%m-%d %H:%M:%S')
                    if isH5:
                        params = {'method':key,'taskNames':dataset[1:],'execDate':execDate,'taskStatus':3,
                                  'isH5': '0', 'produceTime': produceTime4}
                    else:
                        params = {'method': key, 'taskNames': h5_name+'_'+dataset[1:], 'execDate': execDate, 'taskStatus': 3,
                                  'isH5': '0', 'produceTime': produceTime4}
                    if date:
                        push_data(params)
                        params_message = json.dumps(params)
                        logger.info("kafka_message" + params_message)
                    logger.error("store h5name is %s factor is %s Error occurred: %s" % (hdf5, dataset, e))
                    continue
                logger.info('%s appended to %s' % (date_ticker.isoformat(), dataset))
        elif append_all:
            dt_lst_to_process = list(set(pd_factor.index.get_level_values('dt')))
            for date_ticker in dt_lst_to_process:
                if date_ticker in dt_lst:
                    # Delete old records
                    record_num = h5_store.remove(dataset, 'dt=date_ticker')
                    logger.info('%d records deleted at %s %s' % (record_num, date_ticker.isoformat(), dataset))
            try:
                h5_store.append(dataset, pd_factor, data_columns=True,min_itemsize=min_itemsize)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
            except Exception as e:
                logger.error("store h5name is %s factor is %s Error occurred: %s" % (hdf5, dataset, e))
            logger.info('appended all to %s' % (dataset))
        else:
            # new stash
            if from_scratch:
                exist_flag = len(dt_lst) != 0
            else:
                exist_flag = not is_empty_dataset(h5_store, dataset)
            if not exist_flag:
                h5_store.put(dataset, pd_factor, format='table', append=False, data_columns=True)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
                logger.info('%s is newly created to store input DataFrame in %s' % (dataset, hdf5))
            else:
                logger.info('%s already exits in %s, aborting...' % (dataset, hdf5))
                raise AssertionError

def is_empty_dataset(h5_store, dataset):
    try:
        res = h5_store.select(dataset, start=0, end=1)
    except KeyError:
        return True
    if len(res) == 0:
        return  True
    else:
        return False

def date_is_exist(date, h5_store, dataset):
    date = str_date_parser(date)
    sc_date = 'dt>=%s & dt<%s' % (date.strftime('%Y%m%d'), (date+pd.Timedelta('1D')).strftime('%Y%m%d'))
    pd_little = h5_store.select(dataset, where=sc_date)
    if len(pd_little) != 0:
        return True
    else:
        return False


def check_update_date(sdate=None, edate=None, use_len=None,sql_config=None):
    # check_update_date(sdate=None,edate=None)
    use_len = 0 if use_len is None else use_len
    sdate, edate = date_period_handler(sdate, edate)
    if sql_config:
        fdate_list_dt = get_Tradingday_list(sql_config, 19980101, 20300101)
        fdate_list = fdate_list_dt
    else:
        fdate_list_dt = read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    cdate_list = [i for i in fdate_list if i >= sdate and i <= edate]
    idx = max(0, fdate_list.index(cdate_list[0]) - use_len)
    sdate_prev = fdate_list[idx]
    print('-' * 20, '\ndata used: %d - %d ' % (sdate_prev, edate))
    print('factor data: %d - %d \ntotal count: %d' % (sdate_prev, edate, len(cdate_list)))
    print('-' * 20)
    return sdate_prev, edate, cdate_list

def get_current_date(new_date_time=17):
    """if current date is not pass new_date_time such as 18 (6pm)
       it will return previous trading day
    """
    current_time = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    current_date = int(current_time[:8])
    current_hour = int(current_time[9:11])
    print('Current time: ' + str(current_time))
    fdate_list_dt = read_data([19980101, 20300101], ftype=FType.CALENDAR).index.get_level_values(0)
    fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
    nearest_date = min(fdate_list, key=lambda x: abs(x - current_date) if x <= current_date else 100)
    if current_hour < new_date_time and nearest_date == current_date:
        print('Not till refresh time ' + str(new_date_time) + ':00')
        current_date = fdate_list[fdate_list.index(current_date) - 1]
        print('Use previous trading date: ' + str(current_date))
    elif nearest_date < current_date:
        current_date = nearest_date
    elif current_hour >= new_date_time and nearest_date == current_date:
        print('Right on time: ' + str(current_date))
    return current_date

def date_period_handler(sdate=None, edate=None):
    last_day = get_current_date()
    if sdate is None and edate is None:
        sdate = last_day
        edate = last_day
        print('update for one day: ' + str(sdate))
    if sdate is not None and edate is None:
        edate = last_day
    else:
        fdate_list_dt = read_data([19980101, 20200101], ftype=FType.CALENDAR).index.get_level_values(0)
        fdate_list = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in fdate_list_dt]
        cdate_list = [i for i in fdate_list if i <= min(edate, last_day) and i >= sdate]
        sdate, edate = cdate_list[0], cdate_list[-1]
    return sdate, edate

def str_date_parser(str_name):
    '''
    --- DESCRIPTION ---
    Parse 'YYYMMMDD.xxx' styled string / file name to datetime object
    '''
    if any([isinstance(str_name, dt.date), isinstance(str_name, dt.datetime), isinstance(str_name, pd.Timestamp)]):
        return pd.Timestamp(str_name)
    if type(str_name) is int:
        str_name = str(str_name)
    if type(str_name) is str:
        if len(str_name) == 8:
            return pd.Timestamp(dt.datetime.strptime(str_name, '%Y%m%d'))
        elif len(str_name) == 14:
            return pd.Timestamp(dt.datetime.strptime(str_name, '%Y%m%d%H%M%S'))
        else:
            raise AssertionError
    else:
        raise AssertionError

def automatic_date(trading_days):
    #[19980101, 20200101]
    trading_days = [int(dt.datetime.strftime(i,"%Y%m%d")) for i in trading_days if isinstance(i,pd.Timestamp)] + [j for j in trading_days if isinstance(j,int)]

    start_date = str(min(trading_days))
    end_date = str(max(trading_days))

    datestart = dt.datetime.strptime(start_date, '%Y%m%d')
    dateend = dt.datetime.strptime(end_date, '%Y%m%d')
    date_list = []
    date_list.append(datestart)
    while datestart < dateend:
        datestart += dt.timedelta(days=1)
        date_list.append(datestart)
    df = pd.DataFrame({'dt': date_list}).set_index('dt')
    return df


def read_data(trading_days, columns=None, universe=None, mkttype=MktType.CHINA, dtype=DType.STOCK,
              ftype=FType.MD, dfreq=DFreq.DAILY, dsource=DSource.HTSC, alt=None, h5root=None, max_workers=1):
    '''
    --- DESCRIPTION ---
    Read data from dsource or alt source by specifing trading days, universe, columns, etc...
    --- CAUTION ---
    alt source will override dsource
    dsource could be given as list, which will generate multiIndexed columns in return
    --- PARAMETER ---
    trading_days : [start, end] or date list as in type dt.date
    universe     : stock ticker list or UniType or None for all
    columns      : [open, close, moment] alike
    mkttype      : MktType.CHINA, MktType.HK, ...
    dtype        : DType.STOCK, DType.FUTURES, ...
    ftype        : FType.FDD, FType.MD, ...
    dfreq        : DFreq.TICK, DFreq.MINUTE, ...
    dsrouce      : DSource.HTSC, DSource.WIND, ...
    alt          : '/example/test.h5' absolute path to custom HDF5 database
    '''

    if ftype == FType.CALENDAR:
        return automatic_date(trading_days)
    # if alt is None:
    #     raise Exception('Illegal argument: alt must not be empty')

    start_date = None
    end_date = None
    # Parameter verification
    # Date process
    if type(trading_days) is not list:
        trading_days = [trading_days]
    try:
        trading_days = [str_date_parser(item) for item in trading_days]
    except:
        print('Illegal input in trading days, aborting...')
        raise TypeError
    if len(trading_days) == 2:
        start_date, end_date = min(trading_days), max(trading_days)
    # NPY_MAXARGS 32 limitation
    NPY_MAXARGS = 30
    if universe is not None:
        if type(universe) is not list:
            universe = [universe]
    if columns is not None:
        if type(columns) is not list:
            columns = [columns]
    # Path assembly
    abs_h5_path = path_assembler(mkttype=mkttype, dtype=dtype, ftype=ftype, dfreq=dfreq, dsource=dsource, alt=alt,
                                 h5root=h5root)

    # Data retrieve
    print('read data from: ' + abs_h5_path)
    pd_retrieved = pd.DataFrame()
    with pd.HDFStore(abs_h5_path, 'r') as h5_store:
        s_type = None
        # Tags to check after data retrieve
        filter_trading_day = False
        filter_universe = False
        filter_columns = False
        h5_root_keys = get_root_keys(h5_store)
        # Two formats of hdf5 internal structure supported
        if len(h5_root_keys) == 1:
            # Only one dataset inside
            s_type = 1
            s_type_cols = h5_store.get_node(h5_root_keys[0]).table.colnames
        else:
            # Factors/data stores as separate datasets
            s_type = 2
            s_type_cols = [item.replace('/', '') for item in h5_root_keys]
        # User request columns verification
        if columns is not None:
            if not all([item in s_type_cols for item in columns]):
                print('Illegal column item(s) found: %s' % ' '.join(
                    [item for item in columns if item not in s_type_cols]))
                raise AssertionError
        else:
            # Retrieve all columns available
            if s_type == 2:
                columns = s_type_cols
        # Search string prepare
        # columns/universe/trading_days dimension exceed NPY_MAXARGS limit check in mind
        if len(trading_days) >= NPY_MAXARGS:
            start_date, end_date = min(trading_days), max(trading_days)
            filter_trading_day = True
        sc_date = 'dt >= %r & dt <= %r' % (
        start_date, end_date) if start_date is not None else 'dt in %r' % trading_days
        if universe is not None and len(universe) >= NPY_MAXARGS:
            filter_universe = True
            sc_univ = None
        else:
            sc_univ = 'Ticker in %r' % universe if universe is not None else None
        if columns is not None and s_type == 1 and len(columns) >= NPY_MAXARGS:
            filter_columns = True
            sc_col = None
        else:
            sc_col = 'columns = %r' % columns if columns is not None else None
        # Real thing
        if s_type == 1:
            sc_string = ' & '.join([item for item in [sc_date, sc_col, sc_univ] if item is not None])
            pd_retrieved = h5_store.select(h5_root_keys[0], where=sc_string)
        elif s_type == 2:
            def little_retriever(abs_h5_path, fct, where_cls):
                with pd.HDFStore(abs_h5_path, 'r') as h5_store:
                    pd_little = h5_store.select(fct, where=where_cls)
                return pd_little

            sc_string = ' & '.join([item for item in [sc_date, sc_univ] if item is not None])
            # Never concat in iteration
            pd_cat_store = []
            # Multithread for IO intensive tasks
            if max_workers is None:
                max_workers = min(6, len(columns))
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_retrieving = {executor.submit(little_retriever, abs_h5_path, fct, sc_string): fct for fct in
                                     columns}
                for future in concurrent.futures.as_completed(future_retrieving):
                    fct = future_retrieving[future]
                    try:
                        pd_cat_store.append(future.result())
                    except Exception as exc:
                        print('%s generated an exception during retrieval: %s' % (fct, exc))

            pd_retrieved = pd.concat(pd_cat_store, axis=1)
        # Filter after data retrieval
        idx = pd.IndexSlice
        if filter_trading_day:
            pd_retrieved = pd_retrieved.loc[idx[trading_days, :], :]
        if filter_universe:
            pd_retrieved = pd_retrieved.loc[idx[:, universe], :]
        if filter_columns:
            pd_retrieved = pd_retrieved.loc[:, columns]
    return pd_retrieved.sort_index(level=0)


def path_assembler(mkttype, dtype, ftype, dfreq, dsource, alt, h5root):
    abs_path_root = h5root
    # Type process
    mkttype = mkttype.name
    dtype = dtype.name
    ftype = ftype.name
    dfreq = dfreq.name
    dsource = dsource.name
    # Path assembly
    if alt is not None:
        abs_h5_path = alt
        # names = alt.split('/')
        # if len(names) > 1:
        #     abs_h5_path = '/app/data/wdb_h5/' + names[0].upper() + '/' + names[1] + '/' + names[1] + '.h5'
        # else:
        #     abs_h5_path = '/app/data/wdb_h5/WIND_TEST/' + names[0] + '/' + names[0] + '.h5'
    else:
        h5_file_name = '_'.join([ftype, mkttype, dtype, dfreq, dsource]) + '.h5'
        # 路径不需要dfreq, dsource
        # abs_h5_path = '/'.join([abs_path_root, ftype.lower(), '_'.join([mkttype, dtype]), dfreq, dsource, h5_file_name])
        abs_h5_path = '/'.join([abs_path_root, h5_file_name])
    return abs_h5_path


def get_available_cols(mkttype=MktType.CHINA, dtype=DType.STOCK, ftype=FType.MD, dfreq=DFreq.DAILY, dsource=DSource.HTSC, alt=None, h5root='/app/data/wdb_h5/'):
    abs_h5_path = path_assembler(mkttype=mkttype, dtype=dtype, ftype=ftype, dfreq=dfreq, dsource=dsource, alt=alt, h5root=h5root)
    with pd.HDFStore(abs_h5_path, 'r') as h5_store:
        h5_root_keys = get_root_keys(h5_store)
        if len(h5_root_keys) == 1:
            # Only one dataset inside
            s_type = 1
            s_type_cols = h5_store.get_node(h5_root_keys[0]).table.colnames
        else:
            # Factors/data stores as separate datasets
            s_type = 2
            s_type_cols = [item.replace('/', '') for item in h5_root_keys]
    return s_type_cols


def get_trading_date_range(start_date, end_date, dfreq=DFreq.DAILY, dtype=DType.STOCK, mkttype=MktType.CHINA, dsource=DSource.HTSC):

    pd_trading_dates = read_data([start_date, end_date], dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR)
    return pd_trading_dates.index.get_level_values('dt').tolist()

def get_trading_date_range2(start_date, end_date, dfreq=DFreq.DAILY, dtype=DType.STOCK,
                           mkttype=MktType.CHINA, dsource=DSource.HTSC, alt=None):
    pd_trading_dates = cached_read_data([start_date, end_date], dfreq=dfreq, dtype=dtype,
                                         mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR, alt=alt)
    return pd_trading_dates.index.get_level_values('dt').tolist()

def get_trading_date_range_new(start_date, end_date):
    alt_path = "/app/data/wdb_h5/WIND_TEST/MD_CHINA_INDEX_DAILY_WIND/MD_CHINA_INDEX_DAILY_WIND.h5"
    pd_trading_dates = read_data([start_date, end_date],alt=alt_path)
    date_list = list(set(pd_trading_dates.index.get_level_values('dt').tolist()))
    date_list.sort()
    return date_list

def csv_dumper(file_list, hdf5, dataset):
    '''
    --- DESCRIPTION ---
    Reads in csv files as specified in file_list and tries to concatenate csv contents into one multiIndexed Pandas DataFrame
    Stores the generated DataFrame object in a single dataset of HDF5 database WITHOUT intention to override original dataset data

    --- CAUTION ---
    File names are parsed as 'YYYYMMDD.xxx' string as DataFrame primary index 'dt'
    In case dataset 'dt' index already contains dates specified by csv files, csv_dumper will NOT override dataset old data

    --- PARAMETER ---
    file_list: ['xxx.xx', 'xxx.xx']
    hdf5     : file name of HDF5 database
    dataset  : dataset name to store DataFrame
    '''
    ts_meta = dt.datetime.today()

    if '/' not in dataset:
        dataset = '/' + dataset
    if type(file_list) is not list:
        file_list = [file_list]
    with pd.HDFStore(hdf5) as h5_store:

        if dataset in get_root_keys(h5_store):
            # dataset is already created
            # retrieve dt list
            dt_lst = list(set(h5_store.select_column(dataset, 'dt')))
            print('%s last tapped date: %s' % (dataset, h5_store.get_storer(dataset).attrs.modification_date.isoformat()))
        else:
            dt_lst = []

        for file in file_list:
            date_ticker = str_date_parser(os.path.basename(file).split('.')[0])
            if date_ticker in dt_lst:
                # Delete old records
                record_num = h5_store.remove(dataset, 'dt=date_ticker')
                logger.info('%d records deleted at %s %s' % (record_num, date_ticker.isoformat(), dataset))
                # print('%s already exists in database, skipping...' % date_ticker.isoformat())
                # # Neglect intentionally to protect hdf5 old data
                # pass
            # else:
            dt_lst.append(date_ticker)
            # Prepare multiIndex DataFrame
            pd_file = pd.read_csv(file)
            # In case Ticker column is unnamed
            pd_file.rename(columns={'Unnamed: 0':'Ticker'}, inplace=True)
            pd_file.rename(columns={'ticker':'Ticker'}, inplace=True)
            pd_file['dt'] = date_ticker
            pd_file.set_index(['dt', 'Ticker'], append=False, inplace=True)
            # Dump DataFrame
            h5_store.append(dataset, pd_file, data_columns=True)
            h5_store.get_storer(dataset).attrs.modification_date = ts_meta
            print('%s appended to %s' % (date_ticker.isoformat(), dataset))

def get_stock_list(date,sql_config):
    """
    获取当天前上市的股票列表并存入csv文件
    :param date: 日期
    :param sql_config: Oracle配置项
    :return:
    """
    wind_stock_path = "/app/data/wdb_h5/WIND_TEST/universe_complete/stocklst/"
    if not os.path.exists(wind_stock_path):
        os.makedirs(wind_stock_path)
    table = "Wind.AShareDescription"
    factor_list = ['S_INFO_WINDCODE','S_INFO_LISTDATE', 'S_INFO_DELISTDATE']
    logger.info("Start to get %s data from Oracle"%table)
    df = get_wind_data(table,factor_list,sql_config,date=None)
    df.rename(columns={"S_INFO_WINDCODE": "Ticker"}, inplace=True)
    df.set_index("Ticker", inplace=True)
    df.fillna(20990101, inplace = True)
    if df['S_INFO_LISTDATE'].dtype == 'object':
        df["S_INFO_LISTDATE"] = df["S_INFO_LISTDATE"].apply(pd.to_numeric)
    if df['S_INFO_DELISTDATE'].dtype == 'object':
        df["S_INFO_DELISTDATE"] = df["S_INFO_DELISTDATE"].apply(pd.to_numeric)
    if isinstance(df['S_INFO_DELISTDATE'].iloc[0],str):
        df.loc[:,'S_INFO_DELISTDATE'] = pd.to_numeric(df.loc[:,'S_INFO_DELISTDATE'])
    # 只取上市日期小于等于当天的股票
    tmp_df = df[(df['S_INFO_DELISTDATE'] > date) & (df['S_INFO_LISTDATE'] <= date)]
    if tmp_df.empty:
        logger.info("The stock_list DataFrame is empty...")
    Ticker_list = list(tmp_df.index.values)
    delist_Ticker = []
    for ticker in Ticker_list:
        if not ticker[0].isdigit():
            delist_Ticker.append(ticker)
        elif ticker[0] == '9':
            delist_Ticker.append(ticker)
    Ticker_list = list(set(Ticker_list) - set(delist_Ticker))
    df1 = pd.DataFrame(Ticker_list, columns=['Ticker'])
    logger.info("Start to write stock_list to csv!")
    df1.to_csv(wind_stock_path+str(date) + '.csv', index = False)

def stock_select(df,date,dataset_name,sql_config,use_stock_list=None):
    """
    对DataFrame中的股票进行过滤
    :param df: DataFrame
    :param date: 当天日期
    :param dataset_name: 因子
    :param sql_config: Oracle配置项
    :return:
    """
    wind_stock_path = "/app/data/wdb_h5/WIND_TEST/universe_complete/stocklst/"
    csv_name = wind_stock_path + str(date) + '.csv'
    csv_exist = os.path.exists(csv_name)
    while not csv_exist:
        get_stock_list(date,sql_config)
        if os.path.exists(csv_name):
            break
    df.set_index('Ticker', inplace=True)
    if isinstance(df['dt'].iloc[0], int) or isinstance(df['dt'].iloc[0], str):
        df['dt'] = pd.Timestamp(str(date))
    if use_stock_list is None:
        stock_list = pd.read_csv(csv_name, header=0)['Ticker'].values.tolist()
    else:
        stock_list = use_stock_list
    exist_stock = df.index.values.tolist()
    stock_list1 = list(set(exist_stock) & set(stock_list))
    stock_list2 = list(set(stock_list) - set(stock_list1))
    df = df.loc[stock_list1]
    data = []
    for stock in stock_list2:
        data.append(np.nan)
    df2 = pd.DataFrame(data, index=stock_list2, columns=[dataset_name])
    df2.index.name = 'Ticker'
    df2['dt'] = pd.Timestamp(str(date))
    df2 = df2[['dt', dataset_name]]
    if df2.empty or dataset_name == "KNN_I" or dataset_name == "CITIC_I":
        df.reset_index('Ticker', inplace=True)
        return df
    else:
        df = df.append(df2)
        df.reset_index('Ticker', inplace=True)
        return df

def parse_xml(xml):
    """
    解析XML配置文件
    :param xml: xml文件地址
    :return: 配置项字典
    """
    logger.info("Start to parse the xml:%s"%xml)
    tree = ET.parse(xml)
    root = tree.getroot()
    # h5_direct_factor_dict = {}
    h5_direct_factor_dict = collections.OrderedDict()
    for h5_node in root.iter("h5_table"):
        h5_name = h5_node.text.strip()
        if h5_name not in h5_direct_factor_dict:
            h5_direct_factor_dict[h5_name]={}
        if not h5_node.attrib:
            raise Exception("The hdf5 file need the type to parse factor!")
        type_name = "type" + "_" + h5_node.attrib['type']
        if h5_node.attrib['type'] == '0' or h5_node.attrib['type'] == '2':
            h5_direct_factor_dict[h5_name][type_name] = {}
            h5_direct_factor_dict[h5_name][type_name]["wind_table"] = {}
            for child_node in h5_node:
                child_tag = child_node.tag
                if child_tag == "source_table":
                    continue
                child_data = child_node.text.strip()
                h5_direct_factor_dict[h5_name][type_name][child_tag] = child_data
            for wind_node in h5_node.iter("source_table"):
                wind_table = wind_node.text.strip()
                h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table] = {}
                child_wind_tag = []
                for child_wind_node in wind_node:
                    child_wind_tag.append(child_wind_node.tag)
                # print(child_wind_tag)
                if "dt_field" in child_wind_tag:
                    dt_field = wind_node.find("dt_field").text.strip()
                    h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["dt_field"] = dt_field
                
                if "ticker_match" in child_wind_tag:
                    ticker_match = wind_node.find("ticker_match").text.strip()
                    h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["ticker_match"] = ticker_match
                if "category" in child_wind_tag:
                    category = wind_node.find("category").text.strip()
                    h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["category"] = category
                h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["factor_list"] = []
                h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["wind_fields"] = []
                h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["delete_columns"] = []
                for factor_nodes in wind_node.iter("f_name"):
                    for factor_node in factor_nodes:
                        factor = factor_node.text.strip()
                        h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["factor_list"].append(factor)
                for field_nodes in wind_node.iter("t_name"):
                    for field_node in field_nodes:
                        field = field_node.text.strip()
                        h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["wind_fields"].append(field)
                for delete_nodes in wind_node.iter("delete_columns"):
                    for delete_node in delete_nodes:
                        delete_column = delete_node.text.strip()
                        h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["delete_columns"].append(delete_column)
                if "Indefinite_character" in child_wind_tag:
                    h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["Indefinite_character"] = {}
                    for Indefinite_nodes in wind_node.iter("Indefinite_character"):
                        for Indefinite_node in Indefinite_nodes:
                            Indefinite_tag = Indefinite_node.tag
                            Indefinite_length = int(Indefinite_node.text.strip())
                            h5_direct_factor_dict[h5_name][type_name]["wind_table"][wind_table]["Indefinite_character"][Indefinite_tag] = Indefinite_length

        elif h5_node.attrib['type'] == '1':
            h5_direct_factor_dict[h5_name][type_name] = {}
            factor_list = []
            for factor_nodes in h5_node.iter("f_name"):
                for factor_node in factor_nodes:
                    f_name = factor_node.text.strip()
                    factor_list.append(f_name)
            h5_direct_factor_dict[h5_name][type_name]["factor_list"] = factor_list
            for child_node in h5_node:
                child_tag = child_node.tag
                if child_tag == "f_name":
                    continue
                child_data = child_node.text.strip()
                h5_direct_factor_dict[h5_name][type_name][child_tag] = child_data

    return h5_direct_factor_dict

def get_sql_config(xml):
    """
    获取Oracle配置项
    :param xml: xml文件地址
    :return:
    """
    DOMTree = parse(xml)
    data = DOMTree.documentElement
    nodelist = data.getElementsByTagName("sql_config")
    config_dict = {}
    tag_list = ["user","password","ip_address","database"]
    for node in nodelist:
        for tag in tag_list:
            node_name = node.getElementsByTagName(tag)
            tag_value = node_name[0].childNodes[0].nodeValue
            config_dict[tag] = tag_value
    sql_config = config_dict["user"] + "/" + config_dict["password"] + "@" + \
                 config_dict["ip_address"] + "/" + config_dict["database"]
    return sql_config


def factor_transform(field_list,factor_list):
    if len(field_list) != len(factor_list):
        raise Exception("XML配置中因子与Oracle字段不对应！")
    ofield_factor = {}
    if not field_list:
        return ofield_factor,field_list
    for i in range(len(field_list)):
        ofield_factor[field_list[i]] = factor_list[i]
    fields = ""
    for field in field_list:
        fields += field + ","
    return ofield_factor,fields[:-1]


def get_h5table_date(hdf5, dataset):
    """
    获取h5文件dataset的日期列表
    :param hdf5: h5路径
    :param dataset: 要查询的h5组名
    :return:
    """
    if not os.path.exists(hdf5):
        return None
    if '/' not in dataset:
        dataset = '/' + dataset
    with pd.HDFStore(hdf5) as h5_store:
        if dataset in get_root_keys(h5_store):
            dt_lst = list(set(h5_store.select_column(dataset, 'dt')))
            return dt_lst
        else:
            return None

def get_Lasttradingday(date,sql_config):
    """
    获取上一个交易日期
    :param date: 查询日期
    :param sql_config:oracle 配置项
    :return:
    """
    sql_use = "select lasttradingday from quant_data.qd_tradingdays where tradingday =%s"%str(date)
    lasttradingday_ = sql_parser(queryUserTableData(sql_use, sql_config))
    lasttradingday = int(lasttradingday_.iloc[0][0])
    return lasttradingday

def get_Oracle_column_attrs(table,sql_config,column):
    """
    获取Oracle数据库中列的属性
    :param sql_use: sql语句
    :param sql_config: Oracle配置
    :param column: 列名
    :return: 列类型，列宽
    """
    real_table = table.split('.')[-1]
    owner = table.split('.')[0]
    sql_use = "SELECT column_name,data_type ,data_length  FROM  all_tab_columns  " \
              "where table_name='%s' and owner='%s'"%(real_table.upper(),owner.upper())
    df = sql_parser(queryUserTableData(sql_use, sql_config))
    df.set_index('COLUMN_NAME', inplace=True)
    data_type = df.loc[column,'DATA_TYPE']
    data_length = df.loc[column,'DATA_LENGTH']
    return data_type,data_length

def get_qtr_list(sql_config,end_date=None,num_qtr=3):
    end_date = end_date[-1] if type(end_date)==list else end_date
    if end_date == None:
        end_date = get_current_date(new_date_time=17)
    if end_date< 20090105:
        last_day = 20090105
    else:
        last_day = end_date
    year_list = [str(i) for i in range(2000,2200)]
    month_date = ['0331','0630','0930','1231']
    date_list_complete = [i+j for i in year_list for j in month_date]
    qtr_list = [int(i) for i in date_list_complete if int(i)<=last_day][-1*num_qtr:]
    for qtr in qtr_list:
        get_stock_list(qtr,sql_config)
    return qtr_list

def get_month_list(sql_config,date,num=3):
    if isinstance(date,int):
        date = str(date)
    year = dt.datetime.strptime(date,'%Y%m%d').year
    dt_ends = []
    years = [year-1,year]
    for j in years:
        for i in range(1,13):
            if i == 12:
                dt_end = dt.datetime.strftime(dt.datetime(j,i,31),"%Y%m%d")
                dt_ends.append(dt_end)
            else:
                dt_end = dt.datetime.strftime(dt.datetime(j,i+1,1) - dt.timedelta(1),"%Y%m%d")
                dt_ends.append(dt_end)
    month_list = [int(i) for i in dt_ends if int(i) <= int(date)][-1*num:]
    for mon in month_list:
        get_stock_list(mon,sql_config)
    return month_list

def Judge_Tradingday(date,sql_config):
    sql_tradingday = "select istradingday from quant_data.qd_tradingdays where tradingday = %s" % str(date)
    is_tradingday = sql_parser(queryUserTableData(sql_tradingday,sql_config))
    if is_tradingday.empty:
        return "No_tradingday"
    else:
        is_trading = int(is_tradingday.iloc[0][0])
    if is_trading:
        return "Tradingday"
    else:
        return "No_tradingday"

def get_Tradingday_list(sql_config,start_date,end_date):
    """
    获取交易日列表
    :param start_date: 开始日期，int
    :param end_date: 结束日期，int
    :return:
    """
    sql_use = "select tradingday from quant_data.qd_tradingdays where (tradingday >= {0} and tradingday <= {1}) and istradingday=1".format(start_date,end_date)
    res = sql_parser(queryUserTableData(sql_use,sql_config))
    res.sort_values("TRADINGDAY", inplace=True)
    tradingday_list = list(res["TRADINGDAY"])
    return tradingday_list

def judge_Quarterly(date,sql_config):
    sql_tradingday = "select istradingday from quant_data.qd_tradingdays where tradingday = %s" % str(date)
    is_tradingday = sql_parser(queryUserTableData(sql_tradingday,sql_config))
    if is_tradingday.empty:
        logger.info("Warning: date %s not in quant_data.qd_tradingdays"%str(date))
        return "No_tradingday"
    else:
        is_trading = int(is_tradingday.iloc[0][0])
    fdate = dt.datetime.strptime(str(date),'%Y%m%d')
    gdate = fdate + dt.timedelta(1)
    if gdate.month - fdate.month == 1:
        Month_end = True
    else:
        Month_end = False
    QUARTERLY_date_list = [331, 630, 930, 1231]
    if date % 10000 in QUARTERLY_date_list and is_trading:
        return "Q_daily"
    elif date % 10000 in QUARTERLY_date_list and not is_trading:
        return "Quarterly"
    elif Month_end and is_trading:
        return "M_daily"
    elif Month_end and not is_trading:
        return "Monthly"
    elif is_trading:
        return "Daily"
    else:
        return "No_tradingday"

def ticker_match(ticker_num): # jit slow
    ticker_num = int(ticker_num)
    suffix = '.SH' if ticker_num>=600000 else '.SZ'
    pre_fill = (6 - len(str(ticker_num)))*'0'
    ticker = pre_fill + str(ticker_num) + suffix
    return ticker


def get_trading_day_offset(start_date, offset_list, dfreq=DFreq.DAILY, dtype=DType.STOCK,
                           mkttype=MktType.CHINA, dsource=DSource.HTSC, alt=None):
    if type(offset_list) is not list:
        offset_list = [offset_list]
    try:
        offset_list = [int(item) for item in offset_list]
    except:
        print('Illegal offsets found, aborting...')
    start_date = str_date_parser(start_date)
    # 从MD_CHINA_INDEX_DAILY_WIND.h5 读取交易日数据
    # alt = "/app/data/wdb_h5/WIND_TEST/MD_CHINA_INDEX_DAILY_WIND/MD_CHINA_INDEX_DAILY_WIND.h5"
    if dfreq == DFreq.DAILY:
        temp_data = cached_read_data([start_date+pd.tseries.offsets.DateOffset(days=min(int(min(offset_list)*5), -20)),
                                      start_date+pd.tseries.offsets.DateOffset(days=max(int(max(offset_list)*5),  20))],
                                      dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.MD,
                                      alt=alt)
    elif dfreq == DFreq.WEEKLY:
        temp_data = cached_read_data([start_date+pd.tseries.offsets.DateOffset(days=min(int(min(offset_list)*7-10), -20)),
                                      start_date+pd.tseries.offsets.DateOffset(days=max(int(max(offset_list)*7+10),  20))],
                                      dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR,
                                      alt=alt)
    elif dfreq == DFreq.MONTHLY:
        temp_data = cached_read_data([start_date+pd.tseries.offsets.DateOffset(months=min(int(min(offset_list)-2), -2)),
                                      start_date+pd.tseries.offsets.DateOffset(months=max(int(max(offset_list)+2),  2))],
                                      dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR,
                                      alt=alt)
    elif dfreq == DFreq.YEARLY:
        temp_data = cached_read_data([start_date+pd.tseries.offsets.DateOffset(years=min(int(min(offset_list)-2), -2)),
                                      start_date+pd.tseries.offsets.DateOffset(years=max(int(max(offset_list)+2),  2))],
                                      dfreq=dfreq, dtype=dtype, mkttype=mkttype, dsource=dsource, ftype=FType.CALENDAR,
                                      alt=alt)
    else:
        raise ValueError
    # Move start data to nearest trading date
    start_date = temp_data.loc[:start_date].tail(1).index.get_level_values('dt')[0]
    temp_data_lst = temp_data.index.get_level_values('dt').tolist()
    sd_idx = temp_data_lst.index(start_date)
    return [temp_data_lst[sd_idx + item] for item in offset_list]


def static_vars(**kwargs):
    def decorate(func):
        for k in kwargs:
            setattr(func, k, kwargs[k])
        return func
    return decorate


@static_vars(cache=dict())
def cached_read_data(dates, **kwargs):
    assert len(dates) == 2
    start_date = str_date_parser(dates[0])
    end_date = str_date_parser(dates[1])
    key = tuple(kwargs.values())
    if key in cached_read_data.cache:
        data = cached_read_data.cache[key]
    else:
        # data = read_data(**kwargs)
        xml_path = "./config-h5.xml"
        sql_config = get_sql_config(xml_path)
        data = get_calendar_data(sql_config)
        cached_read_data.cache[key] = data
    return data.loc[start_date:end_date]




def print_time(toc,tic):
    time_diff = toc-tic
    if time_diff>60:
        time_spent = (str((round((toc-tic)/60,2)))+' minutes')
    else:
        time_spent = (str((round(toc-tic,2)))+' s')
    return '(used %s)'%(time_spent)


def get_prev_sdate(sdate,day_num,sql_config):
    if isinstance(sdate,str):
        sdate = int(sdate)
    elif isinstance(sdate,pd.Timestamp):
        sdate = int(dt.datetime.strftime(sdate,'%Y%m%d'))
    sql_use = "select * from (select a.* from quant_data.qd_tradingdays a where tradingday <= %s and istradingday=1 order by tradingday desc) where rownum <= %d" % (
    str(sdate), day_num)
    df = sql_parser(queryUserTableData(sql_use, sql_config=sql_config))
    prev_sdate = list(df.tail(1).loc[:,'TRADINGDAY'])[0]
    return prev_sdate


def get_calendar_data(sql_config):
    sql_use = "select a.* from quant_data.qd_tradingdays a where istradingday=1 order by tradingday desc"
    df = sql_parser(queryUserTableData(sql_use, sql_config=sql_config))
    df.sort_values(by='TRADINGDAY',ascending=True,inplace=True)
    df['TRADINGDAY'] = df['TRADINGDAY'].astype(str)
    df['TRADINGDAY'] = pd.to_datetime(df['TRADINGDAY'])
    # trading_date_range = df.loc[:,'TRADINGDAY'].tolist()
    df.rename(columns={'TRADINGDAY': 'dt'}, inplace=True)
    df.set_index('dt', inplace=True)
    return df

