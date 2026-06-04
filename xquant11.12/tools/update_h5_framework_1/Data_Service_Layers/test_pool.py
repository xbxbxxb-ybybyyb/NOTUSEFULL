# _*_ coding:utf-8 _*_
from db import OPMysql
import datetime as dt
import time

if __name__ == '__main__':
    t1 = time.time()
    # 申请资源
    T1 = dt.datetime.now()
    print(T1)
    opm = OPMysql()
    # 增
    # sql = "insert into sina_stock_market (dt,symbol,trade) values (%s,%s,%s)"
    # value = ('20190325','000000.SZ',2.1)
    # opm.insertOne(sql,value)

    # 删
    # sql = "delete from sina_stock_market where symbol='000000.SZ'"
    # opm.delete(sql)

    # 改
    # sql = "update sina_stock_market set trade=3.1 where symbol='000000.SZ' and dt='20190325'"
    # opm.update(sql)

    # 查
    sql = "select S_INFO_WINDCODE,STATEMENT_TYPE,NET_INCR_DEP_COB from asharecashflow limit 100000"
    #params = ['300605.SZ']
    print(len(opm.getAll(sql)))
    T2 = dt.datetime.now()
    print(T2)

    t2 = time.time()
    print("运行时间为：%d"%(t2-t1))
    #释放资源
    opm.dispose()





