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


class BondDataFP:
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

    def get_bond_issuance_info(self, code):
        """
        获取可转债代码的基本信息
        :param code: 可转债的代码，如 '125930.SZ'
        :return:
        """
        thread = threading.currentThread()
        thread_id = str(thread.ident)
        time_stamp = str(int(round(time.time() * 1000)))
        c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
        factor_names = ["WINDCODE", "CRNCYCODE", "PUBDATE", "PREPLANDATE", "SMTGANNCEDATE", "ISSUEANNCELSTDATE",
                        "LISTEDDATE", "LISTDATE", "LISTDATENAME", "ISSEPARATION", "DISTRIBUTO", "RECOMMENDER",
                        "ISCHAINTEREST", "ISCOMINTEREST", "COMINTEREST", "COMINTERESTITEM", "CONVERSIONITEM",
                        "CONVCHANGEITEM", "CONVMONTH", "INICONVPRICE", "INICONVPROPORTION", "CALLITEM", "RESETITEM",
                        "RESETLOWITEM", "RATIONITEM", "PASSDATE", "PERMITDATE", "ANNOUNCEDATE", "ANNOCEDATE",
                        "LISTTYPE", "LISTFEE", "LISTRATIONDATE", "LISTRATIONCHKINDATE", "LISTRATIONPAYMTDATE",
                        "LISTRATIONCODE", "LISTRATIONNAME", "LISTRATIONPRICE", "LISTRATIONRATIODE", "LISTRATIONRATIOMO",
                        "LISTRATIONVOL", "LISTORIGINALS", "LISTDTONL", "LISTPCHASECODEONL", "LISTPCHNAMEONL",
                        "LISTPCHPRICEONL", "LISTISSUEVOLONL", "LISTCODEONL", "LISTEXCESSPCHONL", "RESULTEFSUBSCRPOFF",
                        "RESULTSUCRATEOFF", "LISTDATEINSTOFF", "LISTVOLINSTOFF", "RESULTSUCRATEON",
                        "LISTEFFECTPCHVOLOFF", "LISTEFFPCHOF", "LISTSUCRATEOFF", "LISTPRERATIONVOL", "COMPCODE",
                        "LISTISSUESIZE", "LISTISSUEQUANTITY", "SECID", "MINUNLINENO", "DEPUNLINERATIO", "MAXUNLINENO",
                        "UNLINEUD", "ISCONVERTIBLEBONDS", "MINUNLINEPUBLIC", "MAXUNLINEPUBLIC", "TERMYEAR",
                        "INTERESTTYPE", "COUPONRATE", "INTERESTFREQUENCY", "RESULTSUCRATEON2", "COUPONTXT",
                        "RATIOANNCEDATE", "RATIODATE"]
        factors = ",".join(factor_names)
        sql_use = "select {0} from ccbond_issuance_info where WINDCODE='{1}'".format(
            factors, code)
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        return df

    def get_bond_set(self, date, bond_type='kzz'):
        """
        查询指定日期正在发行的可转债列表
        :param date: 查询时间, 类型为string，如 '20200330'
        :param bond_type: 债券类型, 类型为string，默认 'kzz'代表可转债
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

        if bond_type == 'kzz':
            is_convertible_bond = 1
            sql_use = """
            select tradingcode from BOND_D_MARKETINDEX a, CCBond_Issuance_info b
            where a.tradingcode = b.WINDCODE
            and a.tdate = {0} and b.ISCONVERTIBLEBONDS = {1}
            """.format(date, is_convertible_bond)
        else:
            raise Exception('该接口目前仅支持kzz(可转债)类型')

        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        bond_list = df['tradingcode'].tolist()
        return bond_list
