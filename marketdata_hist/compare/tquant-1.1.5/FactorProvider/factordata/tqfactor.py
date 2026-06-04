# _*_ coding:utf-8 _*_
from FactorProvider.storage.db import DML_mysql
from FactorProvider.setEnv import xquantEnv,sysFlag
import threading
import time
import datetime as dt

if sysFlag == "tquant":
    if xquantEnv == 0:
        dml = DML_mysql('xquant_cusdata')
    else:
        dml = DML_mysql('htsc_dwa_quant')
else:
    dml = None


def get_stock_basics(trading_codes):
    """
    获取股票的基本信息
    :param trading_codes: list/string，单支股票代码或多支股票的列表
    :return: DataFrame
    """
    if isinstance(trading_codes, str):
        trading_codes = "(" + "'" + trading_codes + "'" + ")"
    elif isinstance(trading_codes, list):
        if len(trading_codes) == 1:
            trading_codes = "(" + "'" + trading_codes[0] + "'" + ")"
        else:
            trading_codes = tuple(trading_codes)
    else:
        raise Exception("【参数trading_codes】为list/string类型，单支股票代码或多支股票的列表，请重新输入！")
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    sql_use = """
    SELECT * FROM 
        (SELECT
               (CASE A.EXCHANGECODE WHEN '101' THEN CONCAT(A.TRADINGCODE,'.SH') WHEN '105' THEN CONCAT(A.TRADINGCODE,'.SZ') END) AS TRADINGCODE,
               A.SECUABBR,
               A.COMCODE,
               A.CHINAME,
               A.CHINAMEABBR,
               A.CHISPELLING,
               A.ENGNAME, 
               A.ENGNAMEABBR, 
               A.SECUCATEGORY, 
               A.SECUCATEGORYCODEII,
               A.EXCHANGENAME,
               A.EXCHANGECODE, 
               A.LISTINGDATE, 
               A.DELISTINGDATE, 
               A.BOARDNAME,
               CASE
                 WHEN A.LISTINGSTATECODE = 1 THEN
                  '上市交易'
                 WHEN A.LISTINGSTATECODE = 3 THEN
                  '终止上市'
                 ELSE
                  '其他'
               END AS LISTINGSTATE,
                      CASE
                 WHEN A.SECUABBR LIKE 'S%' AND A.SECUABBR NOT LIKE 'ST%' THEN
                  '1'
                 ELSE
                  '0'
               END AS SSHARES 
        FROM STK_BASICINFO A
        WHERE A.SECUCATEGORYCODEII IN (1001, 1002)
              AND A.EXCHANGECODE IN (101, 105)) AS B
    WHERE TRADINGCODE in {0}
        """.format(trading_codes)
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    return df


def get_conception(trading_code):
    """
    根据输入的股票代码，返回对应的所属板块信息
    :param trading_code: string,股票代码
    :return: DataFrame
    """
    date = dt.datetime.strftime(dt.datetime.now().date(), "%Y%m%d")
    date = "str_to_date" + "(" + date + "," + "'%Y%m%d'" + ")"
    sql_use = """
        SELECT * FROM 
        (SELECT B.CONCEPTTYPECODE,
               B.CONCEPTTYPENAME,
               (CASE C.EXCHANGECODE WHEN '101' THEN CONCAT(A.TRADINGCODE,'.SH') WHEN '105' THEN CONCAT(A.TRADINGCODE,'.SZ') END) AS TRADINGCODE,
               C.SECUABBR, 
               C.EXCHANGECODE,
               C.EXCHANGENAME,
               A.CONCEPTLEADRANK,
               A.ENTRYDATE,
               A.REMOVEDATE,
               A.POSNEGEFFECT,
               A.FITDEGRANK,
               D.CATEGORYNCODE AS CONCEPTTYPE
          FROM PUB_CONCEPTIONELEM A
          JOIN PUB_CONCEPTIONTYPE B
            ON A.CONCEPTTYPECODE = B.CONCEPTTYPECODE
          JOIN PUB_SECURITIESMAIN C
            ON A.TRADINGCODE = C.TRADINGCODE
           AND C.EXCHANGECODE IN (101, 105)
           AND C.SECUCATEGORYCODEII IN (1001, 1002)
          LEFT JOIN PUB_CONCEPTIONCATEGORY D
            ON B.CONCEPTTYPECODE = D.CONCEPTTYPECODE
         WHERE A.ISVALID = 1
           AND B.ISVALID = 1
           AND SUBSTR(B.CONCEPTTYPECODE, 1, 4) IN ('0003')
           AND (REMOVEDATE > {0} OR REMOVEDATE IS NULL)) AS D
           WHERE TRADINGCODE = '{1}'
        """.format(date, trading_code)
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    return df
