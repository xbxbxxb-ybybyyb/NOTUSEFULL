# _*_ coding:utf-8 _*_
import threading
import time
from FactorProvider.storage.db import DML_mysql
from FactorProvider.setEnv import xquantEnv, sysFlag
from FactorProvider.utils.utils import is_valid_date

# 实例化连接池与数据访问层类
if sysFlag == "xquant" or sysFlag == "big_data":
    dml = DML_mysql('xquant_data')
elif sysFlag == "tquant" or sysFlag == 'outside':
    if xquantEnv == 0:
        dml = DML_mysql('xquant_cusdata')
    else:
        dml = DML_mysql('htsc_dwa_quant')
else:
    raise Exception("未知运行系统异常！")


class FundDataFP:
    __instance = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance:
            return cls.__instance
        else:
            obj = object.__new__(cls, *args, **kwargs)
            cls.__instance = obj
            return cls.__instance

    def __init__(self):
        pass

    def get_fund_issuance_info(self, code):
        """
        获取基金的基本信息
        :param code: 可转债的代码，如 '159901.SZ'
        :return:
        """
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        factor_names = ['WINDCODE', 'CHINESENAME', 'ENGLISHNAME', 'SHORTNAME', 'MGRCOMP', 'CUSTODIANBANK', 'TYPE',
                        'INVESTYPE', 'ISSUEDATE', 'ISSUECOLPERIOD', 'ISSUEMAXCOLSHARE', 'ISSUENETPCHSHARE',
                        'ISSUENETPCHNUM', 'PARVALUE', 'PTMYEAR', 'MANAFEERATIO', 'CUSTFEERATIO', 'SALEFEERATIO',
                        'SETUPDATE', 'MATURITYDATE', 'ISSUESHARES', 'FELLOWDISTOR', 'LISTDATE', 'PCHSTARTDATE',
                        'REDMSTARTDATE', 'ISSUESTARTDATEIND', 'ISSUEENDDATEIND', 'ISSUEMINAMTIND', 'ISSUEMAXAMTIND',
                        'PCHREDMPCHMINAMT', 'PCHREDMREDMMINAMT', 'PCHREDMHUGEREDMPRO', 'CRNCYCODE', 'ISSUEPRICE',
                        'OVRSUBRATIO', 'CHANGEDATE', 'FUNDSHARE', 'FBUYFEERATIO', 'SELLFEERATIO', 'BUYFEERATIO',
                        'ENDDATE', 'AFDASSETNAV', 'FUNDTYPE']
        factors = ",".join(factor_names)
        sql_use = "select {0} from fnd_etfbasic_info where WINDCODE='{1}'".format(
            factors, code)
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        return df

    def get_fund_set(self, date, fund_type='ETF'):
        """
        查询指定日期的基金列表
        :param date:查询时间, 类型为string，如 '20200330'
        fund_type: 基金类型, 类型为string, 如'ETF, LOF, ALL',默认ETF, ALL为全部
        :return:
        """
        if not is_valid_date(date, date_type='year_month_day'):
            raise Exception("【date】日期类型为string类型YYYYMMDD格式，如 '20200330'")
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        if len(date) != 8:
            raise Exception('日期错误，格式为yyyymmdd，例如20200330')
        sql_use = "select tradingcode from fund_d_marketindex where tdate={} and trade_status=1".format(date)
        fund_type = fund_type.upper()
        if fund_type not in ['ETF', 'LOF', 'ALL']:
            raise Exception('基金类型错误，应为ETF,LOF或ALL')
        if fund_type != 'ALL':
            sql_use = "{0} and FUNDTYPE='{1}'".format(sql_use, fund_type)

        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        fund_list = df['tradingcode'].tolist()
        return fund_list


