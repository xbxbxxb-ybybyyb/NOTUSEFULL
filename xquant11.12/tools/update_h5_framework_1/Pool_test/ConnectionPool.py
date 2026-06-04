# _*_ coding:utf-8 _*_

from DBUtils.PooledDB import PooledDB
import pymysql
import mysql.connector as mysql
from mysqlinfo import *
import pandas as pd
import time
import datetime as dt

class OPMysql(object):
    __pool = None
    def __init__(self):
        # 构造函数，创建数据库连接、游标
        t1 = time.time()
        self.coon = OPMysql.__getmysqlconn()
        self.cur = self.coon.cursor()
        t2 = time.time()
        print("建立连接池所需时间：%d"%(t2-t1))

    # 数据库连接池连接
    @staticmethod
    def __getmysqlconn():
        if OPMysql.__pool is None:
            __pool = PooledDB(creator=mysql, mincached=2, maxcached=20,maxshared=50, host=mysqlInfo_real['host'],
                              user=mysqlInfo_real['user'], passwd=mysqlInfo_real['passwd'], db=mysqlInfo_real['db'],
                              port=mysqlInfo_real['port'], charset=mysqlInfo_real['charset'])
        return __pool.connection()

    # # 插入\更新\删除sql
    # def op_insert(self, sql):
    #     print('op_insert', sql)
    #     insert_num = self.cur.execute(sql)
    #     print('mysql sucess ', insert_num)
    #     self.coon.commit()
    #     return insert_num

    # 查询
    def op_select(self, sql):

        t3 = dt.datetime.now()
        print("t3:",t3)
        self.cur.execute(sql)  # 执行sql
        t4 = dt.datetime.now()
        print("t4:",t4)
        # print("执行sql语句花费时间：%d 秒"%(t4-t3))
        column_name = []
        t7 = time.time()
        des = self.cur.description
        for i in des:
            column_name.append(i[0])
        result = []
        result.append(column_name)
        select_res = self.cur.fetchall()  # 返回结果为字典
        t8 = dt.datetime.now()
        print("游标：",t8)
        # t5 = time.time()
        # print("游标获取数据字典所需时间：%d 秒"%(t5-t7))
        for res in select_res:
            result.append(res)
        df = pd.DataFrame(result[1:],columns=column_name)
        print("数据量：",len(df))
        t9 = dt.datetime.now()
        print("t9:",t9)
        # t6 = time.time()
        # print("写入DataFrame所需时间：%d 秒"%(t6-t5))
        return df

    #释放资源
    def dispose(self):
        self.coon.close()
        self.cur.close()



