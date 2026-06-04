import threading
import time
import requests
import random
import json
import pandas as pd
import numpy as np
from FactorProvider.storage.db import DML_mysql
from FactorProvider.conf.DubboConf import get_userid
from FactorProvider.setEnv import xquantEnv


def __get_cname():
    # 获取一个唯一的链接名，用于绑定链接池的链接
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    return c_name


def permission_apllo():
    if xquantEnv == 0:
        apollo_ip = "168.61.11.7:8085"
        appid = "XQUANT-THIRDPARTYDATA.c40857173f29cd20f509967567c791ce"
    else:
        apollo_ip_pool = ["168.9.26.28:8080", "168.9.26.29:8080", "168.15.77.196:8080", "168.15.77.197:8080"]
        i = random.randint(0, len(apollo_ip_pool) - 1)
        apollo_ip = apollo_ip_pool[i]
        appid = "XQUANT-THIRDPARTYDATA.c40857173f29cd20f509967567c791ce"
    apollo_http = "http://" + apollo_ip + "/configfiles/json/" + appid + "/default/table_authority"

    try:
        response = requests.get(apollo_http)
        status_code = response.status_code
        if status_code != 200:
            raise Exception("Apollo config connect failed !")
    except Exception as e:
        raise e
    res_json = response.text
    apollo_config = json.loads(res_json)
    permission_list = apollo_config["ttradestock"]
    return permission_list


def get_trade_stocks():
    permission_users = permission_apllo()
    user_id = get_userid()
    if user_id not in permission_users:
        raise Exception("Permission denied.")
    dml1 = DML_mysql("xquant_wind")
    dml2 = DML_mysql("xquant_data")
    c_name = __get_cname()
    sql1 = """
              select vc_inter_code as 证券代码,
                     vc_memo as 备注, 
                     l_begin_date as 有效开始日期, 
                     l_end_date as 有效截止日期
              from ttradestock
            """
    sql2 = """
              select vc_inter_code as 证券代码,
                     vc_stock_name as 证券名称,
                     c_market_no as 市场名称
              from tstockinfo
            """
    df1 = dml1.getAllByPandas(c_name, sql1)
    df2 = dml2.getAllByPandas(c_name, sql2)
    dml1.close(c_name)
    dml2.close(c_name)
    df = pd.merge(df1, df2, left_on="证券代码", right_on="证券代码", how="inner")
    df["证券代码"] = df["证券代码"].apply(lambda x: x[:6])
    df["备注"] = df["备注"].map({None: np.NAN})
    df = df[["证券名称", "证券代码", "市场名称", "备注", "有效开始日期", "有效截止日期"]]
    return df


if __name__ == '__main__':
    trade_stocks = get_trade_stocks()
    print(trade_stocks)
    """
           证券名称    证券代码 市场名称  备注  有效开始日期  有效截止日期
    0          平安银行  000001    2 NaN       0       0
    1         万  科Ａ  000002    2 NaN       0       0
    2          国华网安  000004    2 NaN       0       0
    3          深振业Ａ  000006    2 NaN       0       0
    4          神州高铁  000008    2 NaN       0       0
    ..          ...     ...  ...  ..     ...     ...
    893        天原股份  002386    2 NaN       0       0
    894         维信诺  002387    2 NaN       0       0
    895        新亚制程  002388    2 NaN       0       0
    896  招商安德灵活配置混合  002389    6 NaN       0       0
    897        航天彩虹  002389    2 NaN       0       0
    
    [898 rows x 6 columns]
    """
