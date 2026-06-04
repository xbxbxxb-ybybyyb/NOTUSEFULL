# _*_ coding:utf-8 _*_

import pandas as pd
import pyarrow.parquet as pq
import numpy as np
import time
import os
import sys
from datetime import datetime, timedelta
from os import path
import random
import configparser
from threading import current_thread
from pyarrow import hdfs
from fastparquet import ParquetFile

from xquant.thirdpartydata.marketdata import MarketData

hdfsDict = {}


class DataProvider:
    def __init__(self, dfs=None):
        conf_dir = path.join(path.dirname(__file__), "conf")
        conf_path = path.join(conf_dir, "dataprovider.ini")

        env = os.environ.get('ENV_VERSION', False)
        if env == 'sit':
            hadoop_tag = 'hadoopsit'
        else:
            hadoop_tag = 'hadoopprd'

        self.__config = configparser.ConfigParser()
        self.__config.read(conf_path, encoding="utf-8")
        self.__tmp_dir = self.__config['local']['tmp.dir']
        self.__hdfs_base_dir = self.__config[hadoop_tag]['base.dir']
        self.__timeframe_max = int(self.__config['task']['timeframe.max'])
        self.__current_month_splittime = self.__config['task']['current.month.splittime']
        self.__month_dir_prefix = self.__config['task']['month.dir.prefix']
        self.__etl_finish_time = int(self.__config['task']['etl.finish.time'])
        self.__segment_dir = self.__config[hadoop_tag]['segment.dir']
        self.__segment_threshold = int(self.__config[hadoop_tag]['segment.threshold'])
        self.__segment_types = self.__config[hadoop_tag]['segment.types'].split(',')
        if dfs is None:
            self.__created_by_own = True
            global hdfsDict
            if hdfsDict.get(current_thread().ident) is None:
                os.environ['JAVA_HOME'] = self.__config[hadoop_tag]['java.home']
                os.environ['JAVA_TOOL_OPTIONS'] = '-Xss1280K'
                os.environ['ARROW_LIBHDFS_DIR'] = self.__config[hadoop_tag]['libhdfs.dir']
                os.environ['HADOOP_HOME'] = self.__config[hadoop_tag]['hadoop.home']
                os.environ['HADOOP_CONF_DIR'] = self.__config[hadoop_tag]['hadoop.conf.dir']
                os.environ['YARN_CONF_DIR'] = self.__config['yarn']['yarn.conf.dir']
                hdfsDict[current_thread().ident] = hdfs.connect()
                hdfsDict[str(current_thread().ident) + "_refs"] = 0
            self.dfs = hdfsDict.get(current_thread().ident)
            hdfsDict[str(current_thread().ident) + "_refs"] += 1
        else:
            self.__created_by_own = False
            self.dfs = dfs

    def __del__(self):
        if self.__created_by_own:
            hdfsDict[str(current_thread().ident) + "_refs"] -= 1
            if hdfsDict[str(current_thread().ident) + "_refs"] <= 0:
                del hdfsDict[current_thread().ident]
                del hdfsDict[str(current_thread().ident) + "_refs"]
                try:
                    self.dfs.close()
                except Exception:
                    self.dfs = None

    def __get_file_path(self, table_name):
        dir_path = path.join(self.__hdfs_base_dir, table_name)
        return dir_path

    def __download(self, src_file):
        thread_random = random.Random()
        thread_random.seed(time.time())
        tmp_file = path.join(self.__tmp_dir, src_file.split("/")[-1] + '-' + str(thread_random.randint(0, sys.maxsize)))
        if not path.exists(self.__tmp_dir):
            os.makedirs(self.__tmp_dir)
        with open(tmp_file, "wb") as lf, self.dfs.open(src_file, "rb", 1024 * 1024) as hf:
            while True:
                buf = hf.read(1024 * 64)
                if buf == b'':
                    break
                lf.write(buf)
        return tmp_file

    def __resolve(self, file):
        """
        Read and transfer parquet to pandas
        :param file:    parquet file
        :return:        pandas data frame
        """
        # df = ParquetFile(file).to_pandas()
        df = pd.read_parquet(file)
        # df = pq.read_table(file, nthreads=4).to_pandas()
        return df

    def __fetch(self, src_file):
        """
        Fetch Pandas DataFrame from source file.
        :param src_file:    source file
        :return:            Pandas DataFrame
        """
        tmp_file = self.__download(src_file)
        try:
            return self.__resolve(tmp_file)
        finally:
            self.__delete(tmp_file)

    def __delete(self, file):
        if path.exists(file):
            os.remove(file)

    def get_contract_data(self, table_name):
        file_path = self.__get_file_path(table_name)
        if self.dfs.exists(file_path):
            df_ret = self.__fetch(file_path)
            return df_ret
        else:
            return None


class FutureData:
    def __init__(self):
        self.dp = DataProvider()
        self.ma = MarketData()
        self.CF_CONTRACT_LIST = ['IF', 'IC', 'IH']
        self.SHF_CONTRACT_LIST = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'SC', 'FU', 'BU',
                                  'RU', 'SP']
        self.ZCE_CONTRACT_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP',
                                  'TA', 'FG', 'SF', 'MA', 'ZC', 'SM']
        self.DCE_CONTRACT_LIST = ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD',
                                  'L', 'V', 'PP', 'J', 'JM', 'I', 'EG']

    def get_instrument_info(self, symbol, data_source="HDFS"):
        """
        获取任一期货合约的具体属性
        :param symbol: 期货合约品种符号
        :param data_source: 数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase
        :return:
        """
        if data_source == "HDFS":
            df = self.__get_instrument_info_hdfs(symbol)
            return df
        elif data_source == "HBASE":
            raise Exception("数据源暂时只支持HDFS，请重新输入！")
        else:
            raise Exception("【data_source参数】数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase，请重新输入！")

    def get_change_date(self, symbol, date, contract_type, data_source="HDFS"):
        """
        获取指定日期、品种的主力合约的信息
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param date:查询日期，str或int型，如'20190702'或20190702
        :param contract_type: 合约类型，主力合约为'ZL00'，次主力合约为'ZL01'
        :param data_source: 数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase
        :return:包含当日主力合约名称（如rb1809），主力合约换仓日和移仓合约名称
        """
        if data_source == "HDFS":
            dataList = self.__get_change_date_hdfs(symbol, date, contract_type)
            return dataList
        elif data_source == "HBASE":
            raise Exception("数据源暂时只支持HDFS，请重新输入！")
        else:
            raise Exception("【data_source参数】数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase，请重新输入！")

    def get_instrument_all(self, symbol, start_date, end_date, data_source="HDFS"):
        """
        获取某一个期货品种在时间区间内的所有合约列表
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param start_date:起始日期 int或str 如20170101或'20170101'
        :param end_date:终止日期 int或str 如20190702或'20190702'
        :param data_source: 数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase
        :return:返回指定时间区间内，所有的合约列表。(按日期从近到远排列）
        """
        if data_source == "HDFS":
            InstrumentList = self.__get_instrument_all_hdfs(symbol, start_date, end_date)
            return InstrumentList
        elif data_source == "HBASE":
            raise Exception("数据源暂时只支持HDFS，请重新输入！")
        else:
            raise Exception("【data_source参数】数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase，请重新输入！")

    def get_future_data(self, symbol, start_time, end_time, bar_size, method=False, contract_type='ZL00',
                        data_source="HDFS"):
        """
        获取期货行情数据
        :param symbol: 普通合约名称（如RB1808），主力合约输入品种名+ZL（如RBZL）
        :param start_time:起始日期，string类型，如'20190102000000000'
        :param end_time:终止日期，string类型，如'20190102235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK')
        :param method:是否复权，默认False 不复权
        :param contract_type:主力合约'ZL00'或次主力合约'ZL01'
        :param data_source: 数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase
        :return:
        """
        if data_source == "HDFS":
            df = self.__get_future_data_hdfs(symbol, start_time, end_time, bar_size, method, contract_type)
            return df
        elif data_source == "HBASE":
            raise Exception("数据源暂时只支持HDFS，请重新输入！")
        else:
            raise Exception("【data_source参数】数据源，默认'HDFS'表示数据来源hdfs，'HBASE'表示数据来源hbase，请重新输入！")

    def __get_instrument_info_hdfs(self, symbol):
        """
        获取任一期货合约的具体属性
        :param symbol: 期货合约品种符号
        :return:
        """
        if not self.__judge_symbol(symbol):
            raise Exception("【%s】品种暂不支持，请重新输入！" % symbol)
        table_name = "CONTRACT_PROPERTY.parquet"
        df_all = self.dp.get_contract_data(table_name)
        if df_all is None or df_all.empty:
            df = pd.DataFrame(
                columns=["CODE", "NAME", "TUNIT", "PUNIT", "MFPRICE", "FTMARGINS", "CDMONTHS", "THOURS", "STARTDATE",
                         "ENDDATE", "MULTIPLIER", "EXNAME", "MAXPRICELIMIT"])
            return df
        else:
            df = df_all[df_all["CODE"] == symbol]
            return df

    def __get_change_date_hdfs(self, symbol, date, contract_type):
        """
        获取指定日期、品种的主力合约的信息
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param date:查询日期，str或int型，如'20190702'或20190702
        :param contract_type: 合约类型，主力合约为'ZL00'，次主力合约为'ZL01'
        :return:包含当日主力合约名称（如rb1809），主力合约换仓日和移仓合约名称
        """
        if not self.__judge_symbol(symbol):
            raise Exception("【%s】品种暂不支持，请检查后重新输入！" % symbol)
        table_name = "CONTRACT_ZL_INFO.parquet"
        if contract_type not in ['ZL00', 'ZL01']:
            raise Exception("【contract_type参数】合约类型，主力合约为'ZL00'，次主力合约为'ZL01'，请重新输入！")
        ZL_CODE = symbol + contract_type
        if isinstance(date, str):
            date = int(date)
        df = self.dp.get_contract_data(table_name)
        if df is None or df.empty:
            return []
        df = df[df['ZL_CODE'] == ZL_CODE]
        if df is None or df.empty:
            return []
        df['TDATE'] = df['TDATE'].astype(int)
        df['ZL_STARTDATE'] = df['ZL_STARTDATE'].astype(int)
        df['ZL_ENDDATE'] = df['ZL_ENDDATE'].astype(int)
        df.set_index('TDATE', inplace=True)
        ZL_MAPPINGCODE = df.loc[date, 'ZL_MAPPINGCODE']
        ZL_STARTDATE = df.loc[date, 'ZL_STARTDATE']
        ZL_STARTDATE_LIST = list(set(df['ZL_STARTDATE'].tolist()))
        STARTDATE_LIST = []
        for i in ZL_STARTDATE_LIST:
            if i < ZL_STARTDATE:
                STARTDATE_LIST.append(i)
        if len(STARTDATE_LIST) >= 1:
            PRE_ZL_STARTDATE = max(STARTDATE_LIST)
            PRE_ZL_MAPPINGCODE = df.loc[PRE_ZL_STARTDATE, 'ZL_MAPPINGCODE']
        else:
            PRE_ZL_MAPPINGCODE = ZL_MAPPINGCODE
        dataList = [ZL_MAPPINGCODE, ZL_STARTDATE, PRE_ZL_MAPPINGCODE]
        return dataList

    def __get_instrument_all_hdfs(self, symbol, start_date, end_date):
        """
        获取某一个期货品种在时间区间内的所有合约列表
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param start_date:起始日期 int或str 如20170101或'20170101'
        :param endDate:终止日期 int或str 如20190702或'20190702'
        :return:返回指定时间区间内，所有的合约列表。(按日期从近到远排列）
        """
        if not self.__judge_symbol(symbol):
            raise Exception("【%s】品种暂不支持，请检查后重新输入！" % symbol)
        table_name = "CONTRACT_ALL_INFO.parquet"
        if isinstance(start_date, str):
            start_date = int(start_date)
        if isinstance(end_date, str):
            end_date = int(end_date)
        if end_date < start_date:
            raise Exception("start_date应小于等于end_date，请重新输入！")
        df = self.dp.get_contract_data(table_name)
        if df is None or df.empty:
            return []
        df = df[df["CODE"] == symbol]
        df['STARTDATE'] = df['STARTDATE'].astype(int)
        df['ENDDATE'] = df['ENDDATE'].astype(int)
        df = df[~((df['STARTDATE'] > end_date) | (df['ENDDATE'] < start_date))]
        df['con_number'] = df['HTSCCODE'].apply(lambda x: x[len(symbol):len(symbol) + self.__code_len(symbol)])
        df['con_number'] = df['con_number'].apply(lambda x: '1' + x if int(x[0]) >= 7 else '2' + x)
        df.sort_values(by='con_number', ascending=False, inplace=True)
        InstrumentList = df['HTSCCODE'].tolist()
        return InstrumentList

    def __get_future_data_hdfs(self, symbol, start_time, end_time, bar_size, method=False, contract_type='ZL00'):
        """
        获取期货行情数据
        :param symbol: 普通合约名称（如RB1808），主力合约输入品种名+ZL（如RBZL）
        :param start_time:起始日期,string类型，如'20190102000000000'
        :param end_time:终止日期，string类型，如'20190102235900000'
        :param bar_size:数据周期枚举类，支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK')
        :param method:是否复权，默认False 不复权
        :param contract_type:主力合约'ZL00'或次主力合约'ZL01'
        :return:
        """
        assert len(start_time) == 17
        assert len(end_time) == 17
        if len(symbol) <= 2:
            raise Exception("【symbol参数】普通合约名称（如RB1808），主力合约输入品种名+ZL（如RBZL），请检查后重新输入！")
        if not isinstance(method, bool):
            raise Exception("【method参数】是否复权，bool值，默认False 不复权，请检查后重新输入！")
        if contract_type not in ["ZL00", "ZL01"]:
            raise Exception("【contract_type参数】主力合约为'ZL00'，次主力合约为'ZL01'，请检查后重新输入！")
        if symbol[-2:] == "ZL":
            ZL_CODE = symbol[:-2] + contract_type
            if bar_size == 'K_DAY':
                df = pd.DataFrame(
                    columns=['MDDate', 'MDTime', 'OpenPx', 'HighPx', 'LowPx', 'ClosePx', 'NumTrades',
                             'TotalVolumeTrade', 'IOPV', 'OpenInterest', 'SettlePrice', 'TotalValueTrade', 'PeriodType',
                             'KLineCategory', 'CODE', 'ZL_CODE', 'ZL_MAPPINGCODE'])
                startTime = int(start_time[:8])
                endTime = int(end_time[:8])
                assert endTime >= startTime
                start_year = start_time[:4]
                end_year = end_time[:4]
                df_list = [df]
                for year in range(int(start_year), int(end_year) + 1):
                    table_name = "{0}_kline_day_{1}.parquet".format(symbol[:-2], year)
                    df_p = self.dp.get_contract_data(table_name)
                    df_list.append(df_p)
                df = pd.concat(df_list, ignore_index=True)
                if df is None or df.empty:
                    return df
                df["MDDate"] = df["MDDate"].astype(int)
                df = df[(df["MDDate"] >= startTime) & (df["MDDate"] <= endTime)]
                df.drop(['NumTrades', 'IOPV', 'SettlePrice', 'PeriodType', 'KLineCategory'], axis=1, inplace=True)
                df["MDDate"] = df["MDDate"].astype(str)
                df["MDTime"] = df["MDTime"].astype(str)
            elif bar_size == 'K_1MIN':
                df = pd.DataFrame(
                    columns=['MDDate', 'MDTime', 'OpenPx', 'HighPx', 'LowPx', 'ClosePx', 'NumTrades',
                             'TotalVolumeTrade', 'IOPV', 'OpenInterest', 'SettlePrice', 'TotalValueTrade', 'PeriodType',
                             'KLineCategory', 'CODE', 'ZL_CODE', 'ZL_MAPPINGCODE'])
                assert int(end_time) >= int(start_time)
                start_date = start_time[:8]
                end_date = end_time[:8]
                df_list = [df]
                date_list = pd.date_range(start_date, end_date)
                for date in date_list:
                    date = datetime.strftime(date, '%Y%m%d')
                    table_name = "{0}_kline_minute_{1}.parquet".format(symbol[:-2], date)
                    df_p = self.dp.get_contract_data(table_name)
                    if df_p is None or df_p.empty:
                        continue
                    df_list.append(df_p)
                df = pd.concat(df_list, ignore_index=True)
                if df is None or df.empty:
                    return df
                df["minute_level_time"] = df["MDDate"] + df["MDTime"]
                df["minute_level_time"] = df["minute_level_time"].astype(int)
                df = df[(df["minute_level_time"] >= int(start_time)) & (df["minute_level_time"] <= int(end_time))]
                df.drop("minute_level_time", axis=1, inplace=True)
                df = df[df['MDTime'] != '113000000']
                df.drop(['NumTrades', 'IOPV', 'SettlePrice', 'PeriodType', 'KLineCategory'], axis=1, inplace=True)
            elif bar_size == 'TICK':
                df = pd.DataFrame(
                    columns=['MDDate', 'MDTime', 'PreClosePx', 'PreOpenInterest', 'PreSettlePrice', 'LastPx', 'OpenPx',
                             'HighPx', 'LowPx', 'ClosePx', 'TotalVolumeTrade', 'TotalValueTrade', 'Buy1Price',
                             'Buy1OrderQty', 'Sell1Price', 'Sell1OrderQty', 'OpenInterest', 'SettlePrice', 'CODE',
                             'ZL_CODE', 'ZL_MAPPINGCODE'])
                assert int(end_time) >= int(start_time)
                start_date = start_time[:8]
                end_date = end_time[:8]
                date_list = pd.date_range(start_date, end_date)
                df_list = [df]
                for date in date_list:
                    date = datetime.strftime(date, '%Y%m%d')
                    table_name = "{0}_tick_{1}.parquet".format(symbol[:-2], date)
                    df_p = self.dp.get_contract_data(table_name)
                    if df_p is None or df_p.empty:
                        continue
                    df_p.reset_index(drop=True, inplace=True)
                    df_p['TotalValueTrade_1'] = df_p['TotalValueTrade'].diff()
                    df_p.loc[0, 'TotalValueTrade_1'] = df_p.loc[0, 'TotalValueTrade']
                    df_p['TotalValueTrade'] = df_p['TotalValueTrade_1']
                    df_p.drop('TotalValueTrade_1', axis=1, inplace=True)
                    df_list.append(df_p)
                df = pd.concat(df_list, ignore_index=True)
                if df is None or df.empty:
                    return df
                df['ClosePx'] = df['LastPx']
                df["minute_level_time"] = df["MDDate"] + df["MDTime"]
                df["minute_level_time"] = df["minute_level_time"].astype(int)
                df = df[(df["minute_level_time"] >= int(start_time)) & (df["minute_level_time"] <= int(end_time))]
                df.drop(["minute_level_time", "SettlePrice"], axis=1, inplace=True)
            else:
                raise Exception(
                    "【bar_size参数】暂时只支持支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK')，请重新输入！")
            df = df[df["ZL_CODE"] == ZL_CODE]
            df.reset_index(drop=True, inplace=True)
            if df.empty:
                return df
            if method:
                df.set_index('MDDate', inplace=True)
                MAPPINGCODE_LIST = list(set(df['ZL_MAPPINGCODE'].tolist()))
                date_list_e = []
                date_list_s = []
                for i in MAPPINGCODE_LIST:
                    date_s = min(df[df["ZL_MAPPINGCODE"] == i].index.values)
                    date_e = max(df[df["ZL_MAPPINGCODE"] == i].index.values)
                    date_list_e.append(date_e)
                    date_list_s.append(date_s)
                date_list_e.sort()
                date_list_s.sort()
                assert len(date_list_s) == len(date_list_e)
                df = self.__get_zl_adj(date_list_s, date_list_e, df, ZL_CODE)
                df.reset_index(inplace=True)
        else:
            month = int(symbol[-2:])
            try:
                date_len = 4
                year = int(symbol[-4:-2])
            except:
                date_len = 3
                year = int(symbol[-3:-2])
            code = self.__create_params(symbol[:-date_len], year, month)
            if bar_size == 'K_DAY':
                df_list = []
                time_generator = self.dividend_date_interval(start_time, end_time, bar_size, 7)
                for time_t in time_generator:
                    sdate, edate = time_t
                    df_1 = self.ma.getMDSecurityKLineDataFrame(code, sdate, edate, 10, 25)
                    df_list.append(df_1)
                if df_list:
                    df = pd.concat(df_list, ignore_index=True)
                    df.drop(['NumTrades', 'IOPV', 'SettlePrice', 'PeriodType', 'KLineCategory'], axis=1, inplace=True)
                else:
                    df = pd.DataFrame(
                        columns=['MDDate', 'MDTime', 'HTSCSecurityID', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx',
                                 'TotalVolumeTrade', 'TotalValueTrade', 'OpenInterest'])
            elif bar_size == 'K_1MIN':
                df_list = []
                time_generator = self.dividend_date_interval(start_time, end_time, bar_size, 7)
                for time_t in time_generator:
                    sdate, edate = time_t
                    df_1 = self.ma.getMDSecurityKLineDataFrame(code, sdate, edate, 10, 20)
                    df_list.append(df_1)
                if df_list:
                    df = pd.concat(df_list, ignore_index=True)
                    df = df[df['MDTime'] != '113000000']
                    df.drop(['NumTrades', 'IOPV', 'SettlePrice', 'PeriodType', 'KLineCategory'], axis=1, inplace=True)
                else:
                    df = pd.DataFrame(
                        columns=['MDDate', 'MDTime', 'HTSCSecurityID', 'OpenPx', 'ClosePx', 'HighPx', 'LowPx',
                                 'TotalVolumeTrade', 'TotalValueTrade', 'OpenInterest'])
            elif bar_size == 'TICK':
                df_list = []
                time_generator = self.dividend_date_interval(start_time, end_time, bar_size, 1)
                for time_t in time_generator:
                    sdate, edate = time_t
                    df_1 = self.ma.getMDSecurityTickDataFrame(code, sdate, edate, 1)
                    if df_1 is None or df_1.empty:
                        continue
                    df_1.reset_index(drop=True, inplace=True)
                    df_1['TotalValueTrade_1'] = df_1['TotalValueTrade'].diff()
                    df_1.loc[0, 'TotalValueTrade_1'] = df_1.loc[0, 'TotalValueTrade']
                    df_1['TotalValueTrade'] = df_1['TotalValueTrade_1']
                    df_1.drop('TotalValueTrade_1', axis=1, inplace=True)
                    df_list.append(df_1)
                if df_list:
                    df = pd.concat(df_list, ignore_index=True)
                    df['ClosePx'] = df['LastPx']
                    df.drop('SettlePrice', axis=1, inplace=True)
                else:
                    df = pd.DataFrame(
                        columns=['MDDate', 'MDTime', 'SecurityType', 'TradingDate', 'PreOpenInterest', 'PreClosePx',
                                 'PreSettlePrice', 'OpenPx', 'HighPx', 'LowPx', 'LastPx', 'TotalVolumeTrade',
                                 'TotalValueTrade', 'OpenInterest', 'ClosePx', 'PreDelta', 'CurrDelta',
                                 'HTSCSecurityID', 'WeightedAvgBidPx', 'WeightedAvgOfferPx', 'TotalBidNumber',
                                 'TotalOfferNumber', 'Buy1Price', 'Buy1OrderQty', 'Sell1Price', 'Sell1OrderQty',
                                 'Buy2Price', 'Buy2OrderQty', 'Sell2Price', 'Sell2OrderQty', 'Buy3Price',
                                 'Buy3OrderQty', 'Sell3Price', 'Sell3OrderQty', 'Buy4Price', 'Buy4OrderQty',
                                 'Sell4Price', 'Sell4OrderQty', 'Buy5Price', 'Buy5OrderQty', 'Sell5Price',
                                 'Sell5OrderQty'])
            else:
                raise Exception(
                    "【bar_size参数】暂时只支持支持1day('K_DAY'), 1min('K_1MIN'), tick('TICK')，请重新输入！")
        return df

    def __get_zl_adj(self, date_list_s, date_list_e, df, ZL_CODE):
        table_name = "CONTRACT_ZL_INFO.parquet"
        df_zl = self.dp.get_contract_data(table_name)
        df_zl = df_zl[df_zl['ZL_CODE'] == ZL_CODE]
        df_zl = df_zl[df_zl['TDATE'] >= int(date_list_e[0])]
        if df_zl.empty:
            return
        df_zl.set_index('TDATE', inplace=True)
        df_zl.sort_index(inplace=True)
        df_zl['ZL_ADJ'] = df_zl['ZL_ADJ'].astype(float)
        df_zl['ZL_ADJ'].fillna(0.0, inplace=True)
        df_zl.sort_index(ascending=False, inplace=True)
        df_zl['ADJ_VALUE'] = df_zl['ZL_ADJ'].cumsum()
        # 前复权列名 "OpenPx","HighPx","LowPx","ClosePx","OpenPxAdj","HighPxAdj","LowPxAdj","ClosePxAdj"
        for i in range(len(date_list_s)):
            df.loc[date_list_s[i]:date_list_e[i], 'OpenPx'] = df.loc[date_list_s[i]:date_list_e[i], 'OpenPx'] + \
                                                              df_zl.loc[int(date_list_e[i]), 'ADJ_VALUE']
            df.loc[date_list_s[i]:date_list_e[i], 'HighPx'] = df.loc[date_list_s[i]:date_list_e[i], 'HighPx'] + \
                                                              df_zl.loc[int(date_list_e[i]), 'ADJ_VALUE']
            df.loc[date_list_s[i]:date_list_e[i], 'LowPx'] = df.loc[date_list_s[i]:date_list_e[i], 'LowPx'] + \
                                                             df_zl.loc[int(date_list_e[i]), 'ADJ_VALUE']
            df.loc[date_list_s[i]:date_list_e[i], 'ClosePx'] = df.loc[date_list_s[i]:date_list_e[i], 'ClosePx'] + \
                                                               df_zl.loc[int(date_list_e[i]), 'ADJ_VALUE']
        return df

    def __create_params(self, contract, year, month):
        ZCE_CONTRACT_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP',
                             'TA', 'FG', 'SF', 'MA', 'ZC', 'SM']
        year_str = str(year)
        month_str = str(month) if month > 9 else '0' + str(month)
        suffix = self.__get_htsc_contract_suffix(contract)
        year_str = year_str if contract not in ZCE_CONTRACT_LIST else year_str[1]
        code = "{}{}{}.{}".format(contract, year_str, month_str, suffix)
        return code

    def __get_htsc_contract_suffix(self, contract):
        if contract in self.CF_CONTRACT_LIST:
            return 'CF'
        elif contract in self.SHF_CONTRACT_LIST:
            return 'SHF'
        elif contract in self.ZCE_CONTRACT_LIST:
            return 'ZCE'
        elif contract in self.DCE_CONTRACT_LIST:
            return 'DCE'
        else:
            raise Exception('Unknown contract: {}'.format(contract))

    def __judge_symbol(self, symbol):
        valid_symbol_list = self.CF_CONTRACT_LIST + self.SHF_CONTRACT_LIST + self.ZCE_CONTRACT_LIST + self.DCE_CONTRACT_LIST
        if symbol in valid_symbol_list:
            return True
        else:
            return False

    def __code_len(self, symbol):
        if symbol in self.ZCE_CONTRACT_LIST:
            code_len = 3
        else:
            code_len = 4
        return code_len

    def dividend_date_interval(self, start_time, end_time, bar_size, interval_num):
        """
        分割日期区间获取数据，日k线、分钟k线最长查询时间为7天，tick数据最长查询时间为1天
        :param start_time: 开始时间string，如：'20180408093000000'
        :param end_time: 结束时间string，如：'20190805104500000'
        :param bar_size: 日k线'K_DAY'，分钟k线'K_1MIN'，tick数据'TICK'
        :param interval_num: 划分区间的长度
        :return:
        """
        startTime = start_time[:8]
        endTime = end_time[:8]
        date_range = pd.date_range(startTime, endTime)
        date_num = len(date_range)
        i = list(range(date_num))
        for j in i[0:len(i):interval_num]:
            sdate = datetime.strftime(datetime.strptime(startTime, '%Y%m%d') + timedelta(j), '%Y%m%d')
            if bar_size == 'TICK':
                edate = sdate
            else:
                edate = datetime.strftime(datetime.strptime(startTime, '%Y%m%d') + timedelta(j + 6), '%Y%m%d')
            if int(edate) > int(endTime):
                edate = endTime
            if bar_size == 'K_DAY':
                sdate = '{}000000000'.format(sdate)
                edate = '{}235900000'.format(edate)
            else:
                if sdate == startTime:
                    sdate += start_time[8:]
                else:
                    sdate += '000000000'
                if edate == endTime:
                    edate += end_time[8:]
                else:
                    edate += '235900000'
            yield (sdate, edate)
