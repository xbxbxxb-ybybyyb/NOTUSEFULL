# _*_ coding:utf-8 _*_
from FactorProvider.storage.db import DML_mysql
from FactorProvider.setEnv import xquantEnv, sysFlag
from FactorProvider.utils.utils import is_valid_date
import threading
import time
import datetime as dt

# 实例化连接池与数据访问层类
if sysFlag == "xquant" or sysFlag == "big_data":
    dml = DML_mysql('xquant_data')
    dml2 = DML_mysql('xquant_wind')
    dml3 = DML_mysql('xquant_gogoal')
elif sysFlag == "tquant" or sysFlag == 'outside':
    if xquantEnv == 0:
        dml = DML_mysql('xquant_cusdata')
        dml2 = dml
        dml3 = dml
    else:
        dml = DML_mysql('htsc_dwa_quant')
        dml2 = dml
        dml3 = dml
else:
    raise Exception("未知运行系统异常！")


def __get_cname():
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    return c_name


def get_shhktinfo(start_date, end_date):
    # 获取沪深港通成交信息表数据
    c_name = __get_cname()
    assert is_valid_date(start_date, end_date, date_type='year_month_day')
    start_date = dt.datetime.strftime(dt.datetime.strptime(str(start_date), '%Y%m%d'), '%Y-%m-%d')
    end_date = dt.datetime.strftime(dt.datetime.strptime(str(end_date), '%Y%m%d') + dt.timedelta(1), '%Y-%m-%d')
    sql_use = "select * from stk_shhktinfo where tradingday>='{0}' and tradingday<='{1}'".format(start_date, end_date)
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    return df


def get_shhktlstocklist(start_date, end_date):
    # 获取沪港通证券名单表数据
    c_name = __get_cname()
    assert is_valid_date(start_date, end_date, date_type='year_month_day')
    start_date = dt.datetime.strftime(dt.datetime.strptime(str(start_date), '%Y%m%d'), '%Y-%m-%d')
    end_date = dt.datetime.strftime(dt.datetime.strptime(str(end_date), '%Y%m%d') + dt.timedelta(1), '%Y-%m-%d')
    sql_use = "select * from stk_shhktlstocklist where updatedate>='{0}' and updatedate<='{1}'".format(start_date, end_date)
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    return df


def get_shhkttradelist(start_date, end_date):
    # 获取沪深港通成交活跃股名单数据
    c_name = __get_cname()
    assert is_valid_date(start_date, end_date, date_type='year_month_day')
    start_date = dt.datetime.strftime(dt.datetime.strptime(str(start_date), '%Y%m%d'), '%Y-%m-%d')
    end_date = dt.datetime.strftime(dt.datetime.strptime(str(end_date), '%Y%m%d') + dt.timedelta(1), '%Y-%m-%d')
    sql_use = "select * from stk_shhkttradelist where tradingday>='{0}' and tradingday<='{1}'".format(start_date, end_date)
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    return df


def get_hshkiport(start_date, end_date):
    # 获取沪深港通行业投资组合数据
    c_name = __get_cname()
    assert is_valid_date(start_date, end_date, date_type='year_month_day')
    start_date = dt.datetime.strftime(dt.datetime.strptime(str(start_date), '%Y%m%d'), '%Y-%m-%d')
    end_date = dt.datetime.strftime(dt.datetime.strptime(str(end_date), '%Y%m%d') + dt.timedelta(1), '%Y-%m-%d')
    sql_use = "select * from fnd_hshkiport where pubdate>='{0}' and pubdate<='{1}'".format(start_date, end_date)
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    return df

def get_shhknorthward(start_date, end_date):
    c_name = __get_cname()
    assert is_valid_date(start_date, end_date, date_type='year_month_day')
    start_date = dt.datetime.strftime(dt.datetime.strptime(str(start_date), '%Y%m%d'), '%Y-%m-%d')
    end_date = dt.datetime.strftime(dt.datetime.strptime(str(end_date), '%Y%m%d') + dt.timedelta(1), '%Y-%m-%d')
    sql_use = "select * from stk_shhknorthward where tradingday>='{0}' and tradingday<='{1}'".format(start_date, end_date)
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    return df
