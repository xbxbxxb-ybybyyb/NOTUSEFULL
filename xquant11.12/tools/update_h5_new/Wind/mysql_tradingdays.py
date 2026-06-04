# _*_ coding:utf-8 _*_

import MySQLdb
import pandas as pd



def get_prev_sdate(sdate,day_num):
    conn = MySQLdb.connect(host='168.61.3.100',user='xquant_wind',passwd='XU_viah_8826',db='xquant_wind',
                           port=3307)
    cur = conn.cursor()
    sql_use = "select a.* from qd_tradingdays a where tradingday <= {0} and istradingday=1 order by tradingday desc limit {1}".format(sdate, day_num)

    cur.execute(sql_use)
    des = cur.description
    columns = []
    for i in des:
        columns.append(i[0])
    data = list(cur.fetchall())
    df = pd.DataFrame(data,columns=columns)
    df['tradingday'] = df['tradingday'].astype(int)
    prev_sdate = list(df.tail(1).loc[:,'tradingday'])[0]
    return prev_sdate

def get_calendar_data():
    conn = MySQLdb.connect(host='168.61.3.100', user='xquant_wind', passwd='XU_viah_8826', db='xquant_wind',
                           port=3307)
    cur = conn.cursor()
    sql_use = "select a.* from qd_tradingdays a where istradingday=1 order by tradingday"

    cur.execute(sql_use)
    des = cur.description
    columns = []
    for i in des:
        columns.append(i[0])
    data = list(cur.fetchall())
    df = pd.DataFrame(data, columns=columns)
    df['tradingday'] = df['tradingday'].astype(str)
    df['tradingday'] = pd.to_datetime(df['tradingday'])
    df.rename(columns={'tradingday':'dt'},inplace=True)
    df.set_index('dt',inplace=True)
    return df



