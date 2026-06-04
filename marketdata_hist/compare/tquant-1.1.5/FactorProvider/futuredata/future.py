# _*_ coding:utf-8 _*_
import threading
import time
import numpy as np
from FactorProvider.storage.db import DML_mysql
from FactorProvider.setEnv import xquantEnv, sysFlag
from FactorProvider.utils.utils import is_valid_date


# 实例化连接池与数据访问层类
if sysFlag == "xquant" or sysFlag == "big_data":
    dml = DML_mysql('xquant_data')
elif sysFlag == "tquant" or sysFlag == "outside":
    if xquantEnv == 0:
        dml = DML_mysql('xquant_cusdata')
    else:
        dml = DML_mysql('htsc_dwa_quant')
else:
    raise Exception("未知运行系统异常！")

class FutureDataFP:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls, *args, **kwargs)
            cls.__instance = obj
            return cls.__instance

    def __init__(self):
        self.CF_CONTRACT_LIST = ['IF', 'IC', 'IH', 'TS', 'TF', 'T']
        self.SHF_CONTRACT_LIST = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'SC', 'FU', 'BU',
                                  'RU', 'SP']
        self.ZCE_CONTRACT_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP',
                                  'TA', 'FG', 'SF', 'MA', 'ZC', 'SM']
        self.DCE_CONTRACT_LIST = ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD',
                                  'L', 'V', 'PP', 'J', 'JM', 'I', 'EG']


    def get_futures_cont_info(self, symbol):
        # symbol为品种的时候返回的是最新的一个合约的基本信息
        # contract合约 symbol品种
        if len(symbol.split('.')) > 1 or len(symbol)>3:
            symbol_type = "contract"
        else:
            symbol_type = "symbol"

        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        factor_names = ['name', 'tunit', 'punit', 'mfprice', 'ftmargins', 'cdmonths', 'thours', 'ltdated', 'ddate',
                        'multiplier', 'listdate', 'delistdate', 'exname', 'dmean', 'dsite', 'ltdatehour', 'cevalue',
                        'maxpricefluct', 'poslimit', 'udlsecode', 'fspunit', 'rtd', 'subtypcode', 'contract_id',
                        'dlmonth', 'lprice', 'ltdldate', 'type', 'cctype', 'sname', 'sfullname']
        factors = ",".join(factor_names)
        if symbol_type == "contract":
            sql_use = "select windcode,code,{0} from futures_cont_info where windcode='{1}'".format(factors, symbol)
        else:
            sql_use = "select windcode,code,{0} from futures_cont_info a where code='{1}' and listdate=(select max(listdate) from futures_cont_info b where a.code=b.code)".format(
                factors, symbol)
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        if len(df) > 1:
            df = df.iloc[-1:]
        return df

    def get_instrument_all(self, symbol, start_date, end_date):
        """
        获取某一个期货品种在时间区间内的所有合约列表
        :param symbol:合约品种符号，如RB, CU等，为字符串
        :param start_date:起始日期 int或str 如20170101或'20170101'
        :param end_date:终止日期 int或str 如20190702或'20190702'
        :return:返回指定时间区间内，所有的合约列表。(按日期从近到远排列）
        """
        if not is_valid_date(start_date, end_date, date_type='year_month_day'):
            raise Exception("【start_date,end_date】日期类型为string类型YYYYMMDD格式，如 '20200330'，且开始日期应小于结束日期")
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        symbol = symbol.upper()
        if isinstance(start_date, str):
            start_date = int(start_date)
        if isinstance(end_date, str):
            end_date = int(end_date)
        if end_date < start_date:
            raise Exception("start_date应小于等于end_date，请重新输入！")
        sql_use = "select windcode,listdate,delistdate from futures_cont_info where code='{0}'".format(symbol)
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        df = df[~df['listdate'].isnull()]
        df['listdate'] = df['listdate'].astype(int)
        df['delistdate'] = df['delistdate'].astype(int)
        df = df[~((df['listdate'] > end_date) | (df['delistdate'] < start_date))]
        df.sort_values(by=['windcode', 'listdate'], ascending=False, inplace=True)
        InstrumentList = df['windcode'].tolist()
        return InstrumentList

    def get_contract_zl_info(self, symbol, start_date, end_date, contract_type):
        """
        获取指定日期列表、品种的主力合约的信息
        :param symbol:合约品种符号，如rb, cu等，为字符串
        :param start_date:开始日期，str类型，如'20190702'
        :param end_date:结束日期，str类型，如'20190703'
        :param contract_type:合约类型，主力合约为'ZL00'，次主力合约为'ZL01'
        :return:
        """
        if not is_valid_date(start_date, end_date, date_type='year_month_day'):
            raise Exception("【start_date,end_date】日期类型为string类型YYYYMMDD格式，如 '20200330'，且开始日期应小于结束日期")
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        symbol = symbol.upper()
        zl_code = symbol + contract_type
        sql_use = """
                  select code, tdate, zl_code, zl_mappingcode, zl_startdate, zl_last_close, zl_cur_close, zl_adj, 
                  zl_total_volumetrade from future_contract_zl_info 
                  where code='{0}' and (tdate>={1} and tdate<={2}) and zl_code='{3}'
                  """.format(symbol, start_date, end_date, zl_code)
        df = dml.getAllByPandas(c_name, sql_use)
        df.fillna(value=np.nan, inplace=True)
        dml.close(c_name)
        return df

