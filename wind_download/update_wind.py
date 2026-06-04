# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 13:17:25 2018

@author:  015623
"""
from multifactor.data.utils import *
from FDD_qtr_with_caculation import fdd_qtr_retriever_withcal
from get_dividend import main
import settings
from loguru import logger
from multiprocessing import Process, Pool
import traceback


def get_stock_list(cdate_list):
    cdate_list = [cdate_list] if type(cdate_list) != list else cdate_list
    wind_stock_path = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/wind_stock_list/")
    if not os.path.exists(wind_stock_path):
        os.makedirs(wind_stock_path)
    fdate_list = [int(i[:-4]) for i in os.listdir(wind_stock_path)]
    need_list = list(set(cdate_list) - set(fdate_list))
    table_name = 'AShareDescription'
    h5_path = os.path.join(settings.BASE_DIR, 'DATABASE/WIND/')
    table_path = h5_path + table_name + '/' + table_name + '.h5'
    df = IO.read_data([20090101, 21000101], columns=['S_INFO_LISTDATE', 'S_INFO_DELISTDATE'], alt=table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)
    df.fillna(20990101, inplace=True)
    for date in need_list:
        tmp_df = df[df['S_INFO_DELISTDATE'] > date]
        ticker_list = list(tmp_df.index.values)
        delist_ticker = []
        for ticker in ticker_list:
            if not ticker[0].isdigit():
                delist_ticker.append(ticker)
            elif ticker[0] == '9':
                delist_ticker.append(ticker)
        ticker_list = list(set(ticker_list) - set(delist_ticker))
        df1 = pd.DataFrame(ticker_list, columns=['Ticker'])
        df1.to_csv(wind_stock_path + str(date) + '.csv', index=False)


def get_qtr_list(end_date=None, num_qtr=4):
    end_date = end_date[-1] if type(end_date) == list else end_date
    if end_date is None:
        end_date = get_current_date(new_date_time=18)

    if end_date < 20090105:
        last_day = 20090105
    else:
        last_day = end_date
    year_list = [str(i) for i in range(2000, 2200)]
    month_date = ['0331', '0630', '0930', '1231']
    date_list_complete = [i + j for i in year_list for j in month_date]
    qtr_list = [int(i) for i in date_list_complete if int(i) <= last_day][-1 * num_qtr:]
    get_stock_list(qtr_list)
    universe_folder = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/wind_stock_list/")
    stock_set = set()
    for qtr_date in qtr_list:
        stock_code = pd.read_csv(universe_folder + str(qtr_date) + '.csv', header=0)['Ticker'].values.tolist()
        stock_set = stock_set.union(set(stock_code))
    stock_code = list(stock_set)
    return qtr_list, stock_code


def get_wind_secu_status_v2():
    h5_path = os.path.join(settings.BASE_DIR, 'ETC/CHINA_STOCK/WIND/ETC_CHINA_STOCK_WIND.h5')
    if not os.path.exists(os.path.dirname(h5_path)):
        os.makedirs(os.path.dirname(h5_path))

    table_path = os.path.join(settings.BASE_DIR, 'DATABASE/WIND/AShareDescription/AShareDescription.h5')
    df = IO.read_data([20090101, 21000101], columns=['S_INFO_DELISTDATE', 'S_INFO_LISTDATE'], alt=table_path)
    df.reset_index('dt', inplace=True)
    df.drop('dt', axis=1, inplace=True)
    # df.reset_index('Ticker', inplace=True)
    ticker_list = list(df.index.values)
    delist_ticker = []
    for ticker in ticker_list:
        if not ticker[0].isdigit():
            delist_ticker.append(ticker)
        elif ticker[0] == '9':
            delist_ticker.append(ticker)
    ticker_list = list(set(ticker_list) - set(delist_ticker))
    df.reset_index('Ticker', inplace=True)
    df = df[df['Ticker'].isin(ticker_list)]
    df.set_index('Ticker', inplace=True)
    df.columns = ['ipo_date', 'delist_date']
    df.fillna(20991231, inplace=True)
    df['ipo_date'] = df['ipo_date'].apply(lambda x: dt.datetime.strptime(str(int(x)), '%Y%m%d'))
    df['delist_date'] = df['delist_date'].apply(lambda x: dt.datetime.strptime(str(int(x)), '%Y%m%d'))
    os.remove(h5_path) if os.path.exists(h5_path) else None
    with pd.HDFStore(h5_path) as h5_store:
        h5_store.append('SecDate', df)
    return


# rdf h5 to windapi (MD FDD)csv
def retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, save_path, over_ride_name=None,
                  use_stock_list=None):
    try:
        if over_ride_name is not None:
            save_folder = save_path + over_ride_name + '/'
        else:
            save_folder = save_path + dataset_name + '/'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        universe_folder = os.path.join(settings.LOCAL_CSV_DIR, "wind_data/wind_stock_list")
        h5_path = os.path.join(settings.BASE_DIR, 'DATABASE/WIND/')
        table_path = h5_path + table_name + '/' + table_name + '.h5'
        for date in cdate_list:
            if use_stock_list is None:
                stock_list = pd.read_csv(os.path.join(universe_folder, str(date) + '.csv'), header=0)[
                    'Ticker'].values.tolist()
            else:
                stock_list = use_stock_list
            if table_name == 'AShareBalanceSheet':
                df = IO.read_data(date, columns=[factor_name, 'STATEMENT_TYPE'], alt=table_path)
                df = df[df['STATEMENT_TYPE'] == 408001000.0]
                df.drop('STATEMENT_TYPE', axis=1, inplace=True)
            else:
                df = IO.read_data(date, columns=factor_name, alt=table_path)
            df.columns = [dataset_name]
            if dataset_name == 'ocftosales':
                df[dataset_name] = df[dataset_name].apply(lambda x: 100 * x)

            df.reset_index('dt', inplace=True)
            df.drop('dt', axis=1, inplace=True)
            exist_stock = df.index.values.tolist()
            stock_list1 = list(set(exist_stock) & set(stock_list))
            stock_list2 = list(set(stock_list) - set(stock_list1))
            df = df.loc[stock_list1]
            data = []
            for _ in stock_list2:
                data.append(np.nan)
            df2 = pd.DataFrame(data, index=stock_list2, columns=[dataset_name])

            df = df.append(df2)
            df = df.sort_index()
            df.index.name = 'Ticker'
            if dataset_name == 'stm_issuingdate':
                df.fillna(18991230.0, inplace=True)
                df['stm_issuingdate'] = df['stm_issuingdate'].apply(
                    lambda x: dt.datetime.strptime(str(int(x)), '%Y%m%d'))
            df.to_csv(save_folder + str(date) + '.csv')
    except Exception as e:
        logger.error("更新异常：msg={}".format(e))


def md_stock_retrieve(cdate_list):
    table_dict = {'AShareEODDerivativeIndicator': ['turn', 'total_shares', 'free_float_shares', 'mkt_cap_ard'],
                  'AShareEODPrices': ['close', 'open', 'high', 'low', 'vwap', 'adjfactor', 'volume', 'pct_chg',
                                      'pre_close', 'amt']}

    mapping_dict = {'close': 'S_DQ_CLOSE', 'open': 'S_DQ_OPEN', 'high': 'S_DQ_HIGH', 'low': 'S_DQ_LOW',
                    'vwap': 'S_DQ_AVGPRICE', 'adjfactor': 'S_DQ_ADJFACTOR', 'turn': 'S_DQ_TURN',
                    'volume': 'S_DQ_VOLUME', 'pct_chg': 'S_DQ_PCTCHANGE', 'pre_close': 'S_DQ_PRECLOSE',
                    'total_shares': 'TOT_SHR_TODAY', 'amt': 'S_DQ_AMOUNT', 'free_float_shares': 'FREE_SHARES_TODAY',
                    'mkt_cap_ard': 'S_VAL_MV'}
    get_stock_list(cdate_list)
    save_path = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/")
    for table_name in table_dict:
        for dataset_name in table_dict[table_name]:
            factor_name = mapping_dict[dataset_name]
            retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, save_path)


def md_index_retrieve(cdate_list, csv_path, index_list):
    table_dict = {'AIndexEODPrices': ['close', 'pre_close', 'open']}

    mapping_dict = {'close': 'S_DQ_CLOSE', 'pre_close': 'S_DQ_PRECLOSE', 'open': 'S_DQ_OPEN'}
    for table_name in table_dict:
        for dataset_name in table_dict[table_name]:
            factor_name = mapping_dict[dataset_name]
            retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, csv_path, use_stock_list=index_list)


def fdd_qtr_retrieve_nocal(cdate_list):
    qtr_list, _ = get_qtr_list(cdate_list)
    factor_table = pd.read_csv(os.path.join(os.path.dirname(__file__), 'fdd_qtr_nocal.csv'))
    save_path = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/")
    pool = Pool(20)
    for i, row in factor_table.iterrows():
        pool.apply_async(func=retrieve_htsc,
                         args=(qtr_list, row["factor_name"], row["table_name"], row["column_name"], save_path))
    pool.close()
    pool.join()


def fdd_qtr_retriever_withcal_master(cdate_list):
    save_path = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/")
    qtr_list, _ = get_qtr_list(cdate_list)
    factor_list = ['ocftocf', 'fcftocf', 'ocftoop',
                   'longdebttolongcaptial', 'longcapitaltoinvestment', 'currentdebttoequity', 'ncatoequity',
                   'longdebttodebt', 'operatecaptialturn', 'apturn', 'ebittoassets2',
                   'qfa_yoyeps', 'yoy_assets', 'yoy_cash', 'yoy_fixedassets', 'yoydebt',
                   'ocftoassets', 'cashtostdebt', 'yoyprofit', 'qfa_grossmargin']

    pool = Pool(20)
    for date in qtr_list:
        for factor in factor_list:
            pool.apply_async(func=__fdd_qtr_to_csv, args=(date, factor, save_path))
    pool.close()
    pool.join()


def __fdd_qtr_to_csv(date, factor, save_path):
    try:
        df = fdd_qtr_retriever_withcal(date, factor)
        save_folder = save_path + factor + '/'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)
        df.to_csv(save_folder + str(date) + '.csv')
    except Exception as e:
        logger.error("更新异常：msg={}".format(e))


def fdd_daily_retriever(cdate_list):
    fdd_list = ['pe_ttm', 'pb_lf', 'pcf_ocf_ttm', 'ps_ttm']
    save_path = os.path.join(settings.BASE_DIR, "LOCAL_DATA/CSV/wind_data/")
    main(cdate_list)
    for dataset_name in fdd_list:
        table_name = None
        factor_name = None
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
        retrieve_htsc(cdate_list, dataset_name, table_name, factor_name, save_path)


def update_wind_daily_h5(cdate_list, daily_factor, csv_path, h5_path, operation='append', factor_scale=None):
    """factor_scale for maintaining consistent level between HTSC and WIND data"""
    factor_scale = {} if factor_scale is None else factor_scale
    for factor_name in daily_factor:
        logger.info("写入字段：name={},keys={}".format(h5_path, factor_name))
        update_wind_daily_h5_for_factor(cdate_list, csv_path, h5_path, factor_name, operation, factor_scale)


def update_wind_daily_h5_for_factor(cdate_list, csv_path, h5_path, factor_name, operation='append', factor_scale=None):
    try:
        file_folder = csv_path + factor_name + '/'
        if operation == 'append':
            for date in cdate_list:
                fname = file_folder + str(date) + '.csv'
                dat = pd.read_csv(fname)
                dat['dt'] = dt.datetime.strptime(str(date), '%Y%m%d')
                dat.set_index(['dt', 'Ticker'], inplace=True)
                if factor_name in factor_scale:
                    dat[factor_name] = dat[factor_name] / factor_scale[factor_name]
                if len(dat) > 0:
                    if factor_name == 'industry_citiccode':  # for legacy reason
                        dat.columns = ['CITIC_I']
                        IO.pd_hdf5_writer(dat, h5_path, dataset='CITIC_I', append=True)
                    else:
                        IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name, append=True)
        elif operation == 'create':
            logger.info('create new dataset: ' + factor_name)
            file_list = [file_folder + i for i in os.listdir(file_folder)]
            file_list.sort()
            IO.csv_dumper(file_list, h5_path, factor_name)
    except Exception as e:
        logger.error("更新异常：h5={}, msg={}".format(h5_path, e))
        raise Exception


def update_wind_qtr_h5(qtr_list, factor_name_list, csv_path, h5_path, operation='append'):
    for factor_name in factor_name_list:
        try:
            file_folder = csv_path + factor_name + '/'
            if operation == 'append':
                for date in qtr_list:
                    fname = file_folder + str(date) + '.csv'
                    dat = pd.read_csv(fname)
                    dat['dt'] = dt.datetime.strptime(str(date), '%Y%m%d')
                    dat.set_index(['dt', 'Ticker'], inplace=True)
                    if len(dat) > 0:
                        # logger.info'success')
                        # 新增一列或者重刷表可以设置append=False，append=True时会搜索重复日期删除
                        IO.pd_hdf5_writer(dat, h5_path, dataset=factor_name, append=True)
            # 新建表
            elif operation == 'create':
                logger.info('create new dataset: ' + factor_name)
                file_list = [file_folder + i for i in os.listdir(file_folder)]
                file_list.sort()
                IO.csv_dumper(file_list, h5_path, factor_name)
        except Exception as e:
            logger.error("更新异常：h5={}, msg={}".format(h5_path, e))
            raise Exception


def industry_retriever(cdate_list, save_path):
    industry_code = ['b10100', 'b10200', 'b10300', 'b10400', 'b10500', 'b10600',
                     'b10700', 'b10800', 'b10900', 'b10a00', 'b10b00', 'b10c00',
                     'b10d00', 'b10e00', 'b10f00', 'b10g00', 'b10h00', 'b10i00',
                     'b10j00', 'b10k00', 'b10l00', 'b10n00', 'b10o00', 'b10p00',
                     'b10q00', 'b10r00', 'b10s00', 'b10t00', 'b10m01', 'b10m02', 'b10m03']

    industry_num = [i + 1 for i in range(len(industry_code))]
    industry_dict = dict(zip(industry_code, industry_num))
    save_folder = save_path + 'CITIC_I' + '/'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    h5_path = os.path.join(settings.BASE_DIR, 'DATABASE/WIND/')
    table_name = 'AShareIndustriesClassCITICS'
    table_path = h5_path + table_name + '/' + table_name + '.h5'
    for date in cdate_list:
        df = IO.read_data([20090101, 20301231], columns=['CITICS_IND_CODE', 'ENTRY_DT', 'REMOVE_DT', 'CUR_SIGN'],
                          alt=table_path)
        # df = df[df['CUR_SIGN'] == 1.0]
        df['REMOVE_DT'].fillna(20990101, inplace=True)
        df = df[df['ENTRY_DT'] <= date]
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

        def helper(x, p_industry_dict):
            return p_industry_dict[x]

        df['lv2_ind_num'] = df['lv2_ind_code'].apply(lambda x: helper(x, industry_dict))
        df.drop(['CITICS_IND_CODE', 'CUR_SIGN', 'ENTRY_DT', 'REMOVE_DT', 'lv2_ind_code', 'lv2_ind_code'], axis=1,
                inplace=True)
        df.reset_index('dt', inplace=True)
        df.drop('dt', axis=1, inplace=True)
        df.columns = ['CITIC_I']
        df.to_csv(save_folder + str(date) + '.csv')


def cindustry_retriever(cdate_list, save_path):
    save_folder = save_path + 'KNN_I' + '/'
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    source_path = os.path.join(settings.BASE_DIR, 'INDUSTRY/CHINA_STOCK/DAILY/WIND/INDUSTRY_CHINA_STOCK_DAILY_WIND.h5')
    map_dict = {29: 6, 30: 7, 31: 8, 21: 1, 27: 2, 24: 2, 26: 2, 25: 2, 5: 3, 2: 3, 3: 3, 19: 4, 18: 4, 15: 5, 4: 5,
                11: 5, 22: 5, 17: 5,
                12: 5, 10: 5, 6: 5, 16: 5, 8: 5, 7: 5, 23: 5, 20: 5, 13: 5, 9: 5, 14: 5, 1: 5, 28: 5}

    def helper(p_df, p_map_dict):
        x = p_df['CITIC_I']
        if x not in p_map_dict:
            return -1
        return p_map_dict[x]

    for date in cdate_list:
        df = IO.read_data(date, columns=['CITIC_I'], alt=source_path)
        df.reset_index('dt', inplace=True)
        df.drop('dt', axis=1, inplace=True)
        # df.dropna(inplace=True)
        df['KNN_I'] = df.apply(lambda x: helper(x, map_dict), axis=1)
        df.drop(['CITIC_I'], axis=1, inplace=True)
        df.to_csv(save_folder + str(date) + '.csv')


class Factor(object):
    def __init__(self, start_date, end_date, dtype, dfreq, dsource, mkttype, ftype, factor_list,
                 factor_scale=None, stock_list=None, max_process=5):
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
        self.sdate_prev, self.edate, self.cdate_list = check_update_date(self.start_date, self.end_date)
        self.csv_path = os.path.join(settings.LOCAL_CSV_DIR, "wind_data/")
        if self.dtype.name is 'INDEX':
            self.csv_path = self.csv_path + 'index/'
        self.h5_root = settings.BASE_DIR
        self.h5_path = IO.path_assembler(mkttype=mkttype, dtype=dtype, ftype=ftype, dfreq=dfreq, dsource=dsource,
                                         alt=None, h5root=self.h5_root)
        self.h5_file_name = os.path.basename(self.h5_path)
        if not os.path.exists(os.path.dirname(self.h5_path)):
            os.makedirs(os.path.dirname(self.h5_path))
        if not os.path.exists(os.path.dirname(self.csv_path)):
            os.makedirs(os.path.dirname(self.csv_path))

    def retriever(self, checker=None):
        pass

    def csv_to_database(self, h5_checker=None):
        pass

    def cronb(self):
        logger.info("开始更新：name={}, keys={}, path={}, ".format(self.h5_file_name, self.factor_list, self.h5_path))
        self.retriever()
        logger.info("开始写入h5：name={},keys={}, path={}".format(self.h5_file_name, self.factor_list, self.h5_path))
        self.csv_to_database()
        logger.info("更新完成：name={}, keys={}, path={}".format(self.h5_file_name, self.factor_list, self.h5_path))


class DailyFactor(Factor):
    def retriever(self, checker=None):
        pass

    def csv_to_database(self, h5_checker=None):
        update_wind_daily_h5(self.cdate_list, self.factor_list, self.csv_path,
                             self.h5_path, operation=self.operation,
                             factor_scale=self.factor_scale)


class QuarterlyFactor(Factor):
    def retriever(self, checker=None):
        pass

    def csv_to_database(self, h5_checker=None):
        qtr_list, stock_code = get_qtr_list(self.cdate_list)
        update_wind_qtr_h5(qtr_list, self.factor_list, self.csv_path,
                           self.h5_path, operation=self.operation)


class MdIndex(DailyFactor):
    def __init__(self, start_date, end_date):
        index_list = ['000001.SH', '000002.SH', '000016.SH', '000300.SH', '000905.SH', '000906.SH',
                      '399001.SZ', '399005.SZ', '399006.SZ', '000985.CSI']
        factor_list = ['close', 'pre_close', 'open']
        super(MdIndex, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.INDEX,
                                      dfreq=DFreq.DAILY, dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.MD,
                                      factor_list=factor_list, stock_list=index_list)

    def retriever(self, checker=None):
        md_index_retrieve(self.cdate_list, self.csv_path, self.stock_list)


class MdStock(DailyFactor):
    def __init__(self, start_date, end_date):
        md_list = ['close', 'open', 'high', 'low', 'vwap', 'adjfactor', 'turn', 'volume', 'pct_chg',
                   'pre_close', 'total_shares', 'amt', 'free_float_shares', 'mkt_cap_ard']
        # factor_scale ={'amt':10**3,'free_float_shares':10**4,'mkt_cap_ard':10**4,'total_shares':10**4,'volume':10**2}
        super(MdStock, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK,
                                      dfreq=DFreq.DAILY, dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.MD,
                                      factor_list=md_list,
                                      factor_scale=None)

    def retriever(self, checker=None):
        md_stock_retrieve(self.cdate_list)


class FddQtr(QuarterlyFactor):
    def __init__(self, start_date, end_date):
        csv_file = os.path.join(os.path.dirname(__file__), "fdd_qtr_factors.csv")
        factor_name_list = pd.read_csv(csv_file).iloc[:, 0].tolist()
        super(FddQtr, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK,
                                     dfreq=DFreq.QUARTERLY,
                                     dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.FDD,
                                     factor_list=factor_name_list)

    def retriever(self, checker=None):
        fdd_qtr_retrieve_nocal(self.cdate_list)
        fdd_qtr_retriever_withcal_master(self.cdate_list)


class FddDaily(DailyFactor):
    def __init__(self, start_date, end_date):
        fdd_list = ['pe_ttm', 'pb_lf', 'pcf_ocf_ttm', 'ps_ttm', 'dividendyield2']
        # fdd_list = ['dividendyield2']
        super(FddDaily, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.DAILY,
                                       dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.FDD,
                                       factor_list=fdd_list)

    def retriever(self, checker=None):
        fdd_daily_retriever(self.cdate_list)


def fdd_run(daily_factor):
    daily_factor.cronb()


class Industry(DailyFactor):
    def __init__(self, start_date, end_date):
        factor_list = ['CITIC_I']

        super(Industry, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.DAILY,
                                       dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.INDUSTRY,
                                       factor_list=factor_list)

    def retriever(self, checker=None):
        industry_retriever(self.cdate_list, self.csv_path)


class CIndustry(DailyFactor):
    def __init__(self, start_date, end_date):
        factor_list = ['KNN_I']
        super(CIndustry, self).__init__(start_date=start_date, end_date=end_date, dtype=DType.STOCK, dfreq=DFreq.DAILY,
                                        dsource=DSource.WIND, mkttype=MktType.CHINA, ftype=FType.INDUSTRY,
                                        factor_list=factor_list)

    def retriever(self, checker=None):
        cindustry_retriever(self.cdate_list, self.csv_path)


def update_wind(sdate=None, edate=None):
    get_wind_secu_status_v2()
    sdate, edate, cdate_list = check_update_date(sdate=sdate, edate=edate)

    # group1 = [MdIndex]
    # group2 = [MdStock, FddDaily]
    # group3 = [Industry, CIndustry]
    group4 = [FddQtr]

    # group_list = [group1, group2, group3, group4]
    group_list = [group4]
    process_list = [Process(target=__execute_type_work, args=(_group, sdate, edate,)) for _group in group_list]
    [p.start() for p in process_list]
    [p.join() for p in process_list]


def __execute_type_work(group, sdate, edate):
    for _task in group:
        task = _task(sdate, edate)
        try:
            logger.info("任务开始：type={}, sdate={}, edate={}".format(task.ftype, task.start_date, task.end_date))
            task.cronb()
        except Exception as e:
            logger.error(
                "任务失败：type={}, sdate={}, edate={}, msg={}".format(task.ftype, task.start_date, task.end_date, e))
            logger.error(traceback.format_exc())



def wind_weekend_job(sdate=None, edate=None):
    sdate, edate, cdate_list = check_update_date(sdate=sdate, edate=edate)
    update_fdd_qtr = FddQtr(sdate, edate)
    update_fdd_qtr.cronb()

sdate, edate, cdate_list = check_update_date()
update_wind(sdate,edate)
# update_fdd_qtr = QuarterlyFactor(sdate, edate)
# update_fdd_qtr.cronb()



