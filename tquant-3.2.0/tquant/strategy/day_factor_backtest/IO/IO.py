# -*- coding: utf-8 -*-
# 
import pandas as pd
import datetime as dt
import os
from .IO_enums import *
import concurrent.futures


#sjl
h5root = '/'.join(os.path.abspath(__file__).split('/')[:-3])+"/backtest_data"
# print(h5root)

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


def get_root_keys(h5_store):
    '''
    --- DESCRIPTION ---
    Get group keys
    '''
    if type(h5_store) is pd.io.pytables.HDFStore:
        return ['/' + item for item in list(h5_store.root._v_groups.keys())]


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
            print(
                '%s last tapped date: %s' % (dataset, h5_store.get_storer(dataset).attrs.modification_date.isoformat()))
        else:
            dt_lst = []

        for file in file_list:
            date_ticker = str_date_parser(os.path.basename(file).split('.')[0])
            if date_ticker in dt_lst:
                print('%s already exists in database, skipping...' % date_ticker.isoformat())
                # Neglect intentionally to protect hdf5 old data
                pass
            else:
                dt_lst.append(date_ticker)
                # Prepare multiIndex DataFrame
                pd_file = pd.read_csv(file)
                # In case Ticker column is unnamed
                pd_file.rename(columns={'Unnamed: 0': 'Ticker'}, inplace=True)
                pd_file.rename(columns={'ticker': 'Ticker'}, inplace=True)
                pd_file['dt'] = date_ticker
                pd_file.set_index(['dt', 'Ticker'], append=False, inplace=True)
                # Dump DataFrame
                h5_store.append(dataset, pd_file, data_columns=True)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
                print('%s appended to %s' % (date_ticker.isoformat(), dataset))


def hdf5_replacer(file_list, hdf5, dataset):
    '''
    --- DESCRIPTION ---
    Reads in csv files as specified in file_list and tries to concatenate csv contents into one multiIndexed Pandas DataFrame
    Stores the generated DataFrame object in a single dataset of HDF5 database WITH intention to replace old data in dataset

    --- CAUTION ---
    File names are parsed as 'YYYYMMDD.xxx' string as DataFrame primary index 'dt'
    If dataset 'dt' index does not contain dates specified by csv files, hdf5_replacer will raise an NameErro Exception

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
            dt_lst = list(set(h5_store.select_column(dataset, 'dt')))
            print(
                '%s last tapped date: %s' % (dataset, h5_store.get_storer(dataset).attrs.modification_date.isoformat()))
        else:
            print('%s dataset not created, use csv_dumper to initialise instead' % dataset)
            raise NameError

        for file in file_list:
            date_ticker = str_date_parser(os.path.basename(file).split('.')[0])
            if date_ticker not in dt_lst:
                print('%s does not exist in database, aborting...' % date_ticker.isoformat())
                raise NameError
            else:
                # Prepare multiIndex DataFrame
                pd_file = pd.read_csv(file)
                # In case Ticker column is unnamed
                pd_file.rename(columns={'Unnamed: 0': 'Ticker'}, inplace=True)
                pd_file.rename(columns={'ticker': 'Ticker'}, inplace=True)
                pd_file['dt'] = date_ticker
                pd_file.set_index(['dt', 'Ticker'], append=False, inplace=True)
                # Delete old records
                record_num = h5_store.remove(dataset, 'dt=date_ticker')
                print('%d records deleted at %s %s' % (record_num, date_ticker.isoformat(), dataset))
                # Append new records
                h5_store.append(dataset, pd_file, data_columns=True)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
                print('%s appended to %s' % (date_ticker.isoformat(), dataset))


def pd_hdf5_writer(pd_factor, hdf5, dataset=None, override=None, append=None):
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

    # DataFrame format verification
    if pd_factor.index.names != ['dt', 'Ticker']:
        print('DataFrame passed in is not legit multiIndex DataFrame, aborting...')
        raise TypeError
    else:
        pd_factor = pd_factor.sort_index(level=0)

    if dataset is None:
        # dataset should be able to be inferred by name attribute
        try:
            dataset = pd_factor.name
        except:
            print('dataset cannot be inferred by Dataframe name, aborting...')
            raise AssertionError

    if '/' not in dataset:
        dataset = '/' + dataset

    # Parameter verification
    # Only three modes are valid: override, append, new
    if override is not None and append is not None:
        print('Only one tag of override and append can be specified, aborting...')
        raise SyntaxError
    if override is not None:
        if override is not True:
            print('The override tag should only be True or unset, aborting...')
            raise SyntaxError
    if append is not None:
        if append is not True:
            print('The append tag should only be True or unset, aborting...')
            raise SyntaxError

    with pd.HDFStore(hdf5) as h5_store:
        # Common actions, dt_lst extraction
        if dataset in get_root_keys(h5_store):
            # dataset is already created
            # dt_lst = []
            dt_lst = list(set(h5_store.select_column(dataset, 'dt')))
            print(
                '%s last tapped date: %s' % (dataset, h5_store.get_storer(dataset).attrs.modification_date.isoformat()))
        else:
            dt_lst = []

        if override:
            if not dt_lst:
                # dt_lst is empty
                print('%s does not exit in %s, aborting...' % (dataset, hdf5))
                raise AssertionError
            h5_store.put(dataset, pd_factor, format='table', append=False, data_columns=True)
            h5_store.get_storer(dataset).attrs.modification_date = ts_meta
            print('%s is overriden with newly input DataFrame in %s' % (dataset, hdf5))
        elif append:
            # Append Func with data replacement
            dt_lst_to_process = list(set(pd_factor.index.get_level_values('dt')))
            for date_ticker in dt_lst_to_process:
                if date_ticker in dt_lst:
                    # Delete old records
                    record_num = h5_store.remove(dataset, 'dt=date_ticker')
                    print('%d records deleted at %s %s' % (record_num, date_ticker.isoformat(), dataset))
                # Append new records
                h5_store.append(dataset, pd_factor.loc[date_ticker.isoformat()], data_columns=True)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
                print('%s appended to %s' % (date_ticker.isoformat(), dataset))
        else:
            # new stash
            if not dt_lst:
                h5_store.put(dataset, pd_factor, format='table', append=False, data_columns=True)
                h5_store.get_storer(dataset).attrs.modification_date = ts_meta
                print('%s is newly created to store input DataFrame in %s' % (dataset, hdf5))
            else:
                print('%s already exits in %s, aborting...' % (dataset, hdf5))
                raise AssertionError


def hdf5_node_remover(hdf5, dataset=None):
    '''
    --- DESCRIPTION ---
    Remove dataset from hdf5 database
    --- CAUTION ---
    This Func only makes dataset inaccessible, use h5repack/prepack to reclaim disk spaces
    '''
    with pd.HDFStore(hdf5) as h5_store:
        h5_store.get_node(dataset)._f_remove(recursive=True)


def read_data(trading_days, columns=None, universe=None, mkttype=MktType.CHINA, dtype=DType.STOCK,
              ftype=FType.MD, dfreq=DFreq.DAILY, dsource=DSource.HTSC, dtable=None, alt=None,
                h5root= h5root, max_workers=1):
              # h5root='/data/group/800080/warehouse/prod', max_workers=1):
    #sjl: 修改h5root
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
    alt          : '/example/backtest.h5' absolute path to custom HDF5 database
    '''
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
    abs_h5_path = path_assembler(mkttype=mkttype, dtype=dtype, ftype=ftype, dfreq=dfreq, dsource=dsource, dtable=dtable,
                                 alt=alt, h5root=h5root)
    # Data retrieve
    print('read data from: ' + abs_h5_path)
    pd_retrieved = pd.DataFrame()
    print("filename:", abs_h5_path)
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
            # print(s_type_cols)
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


def path_assembler(mkttype, dtype, ftype, dfreq, dsource, dtable, alt, h5root):
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
    elif dtable is not None:
        dtable = dtable.name
        h5_file_name = dtable + '.h5'
        abs_h5_path = os.path.join(abs_path_root, 'DATABASE', dsource, dtable, h5_file_name)
    else:
        h5_file_name = '_'.join([ftype, mkttype, dtype, dfreq, dsource]) + '.h5'
        abs_h5_path = '/'.join([abs_path_root, ftype, '_'.join([mkttype, dtype]), dfreq, dsource, h5_file_name])
    return abs_h5_path


def get_available_cols(mkttype=MktType.CHINA, dtype=DType.STOCK, ftype=FType.MD, dfreq=DFreq.DAILY,
                       dsource=DSource.WIND, dtable=None, alt=None, h5root='/data/group/800080/warehouse/prod'):
    abs_h5_path = path_assembler(mkttype=mkttype, dtype=dtype, ftype=ftype, dfreq=dfreq, dsource=dsource, dtable=dtable,
                                 alt=alt, h5root=h5root)
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
