import threading
import os
from sqlalchemy import create_engine
import pymysql as mysql
from os import path
import json
from FactorProvider.setEnv import xquantEnv
import platform
from DBUtils.PooledDB import PooledDB
import time
import pandas as pd

file_path = path.join(path.dirname(__file__),
                      "encrypted_database.json")
with open(file_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)
mySQLHost="168.11.33.141"
mySQLPort=3306
mySQLUser="marketmake_grey_dml"
mySQLPassword="GXNA_idnd_0807"
mySQLDBName="ats_quant_star_gray"
if xquantEnv == 0:
    sql_config = {'ats-quant': {
        'host': '168.64.33.17',
        'user': 'xtraderops',
        'passwd': ENCRYPTED_HOSTS['ats-quant']['uat']['ciphertext'], # YV_turi_86
        'db': 'ats_quant',
        'port': 3306,
        'charset': 'utf8'
    }}
else:
    sql_config = {'ats-quant': {
        'host': '168.63.1.130',
        'user': 'xquant',
        'passwd': ENCRYPTED_HOSTS['ats-quant']['prd']['ciphertext'],
        'db': 'xquant',
        'port': 3306,
        'charset': 'utf8'
    }}


def get_engine(user):
    engine = create_engine('mysql+pymysql://%s:%s@%s:%d/%s?charset=utf8' % (
        sql_config[user]['user'], sql_config[user]['passwd'],
        sql_config[user]['host'], sql_config[user]['port'], sql_config[user]['db']))
    return engine


def synchronized(func):
    # 多线程单例模式需用线程锁
    func.__lock__ = threading.Lock()

    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func


def singleton(OPMysql):
    _instance = {}
    # print(OPMysql)
    @synchronized
    def inner(user):
        if user not in _instance:
            _instance[user] = OPMysql(user)
        return _instance[user]
    return inner


@singleton
def OPMysql(user):
    def pool(sql_config,wait_time):
        try:
            __pool = PooledDB(creator=mysql, mincached=0, maxcached=1,
                              maxconnections=2, maxshared=1, blocking=True,
                              host=sql_config[user]['host'], user=sql_config[user]['user'],
                              passwd=sql_config[user]['passwd'], db=sql_config[user]['db'],
                              port=sql_config[user]['port'], charset=sql_config[user]['charset'])
        except Exception as e:
            print("mysql链接数达到上限，等待创建连接池...%s[%s]" % (e,user))
            time.sleep(wait_time)
            return None
        return __pool

    for i in range(3):
        if i == 0:
            wait_time = 10
        else:
            wait_time = 60
        __pool = pool(sql_config, wait_time)
        if __pool:
            return __pool
    # print('池子里目前有', __pool._idle_cache, '\r\n')
    raise Exception("mysql连接已0达上限，创建链接池失败[%s]！"%(user))


class DML_mysql:
    def __init__(self,user):
        self.user = user
        self.pool = OPMysql(user)
        self.conn = {}
        self.cur = {}
        self.engine = {}

    def __get_cursor(self, c_name, retry=3):
        def connect(c_name, wait_time):
            if not self.conn.get(c_name):
                try:
                    # print("连接mysql...")
                    conn = self.pool.connection()
                except mysql.Error as e:
                    print("mysql链接数达到上限，等待再次取链接...%s[%s]" % (e,self.user))
                    time.sleep(wait_time)
                    return None

                cur = conn.cursor()
                self.conn[c_name] = conn
                self.cur[c_name] = cur
            else:
                conn = self.conn[c_name]
                cur = self.cur[c_name]
            return cur
        for i in range(retry):
            if i == 0:
                wait_time = 10
            else:
                wait_time = 60
            cur = connect(c_name, wait_time=wait_time)
            if cur:
                return cur
        raise Exception("mysql连接已达上限，连接失败[%s]！"%(self.user))

    def getAllByPandas(self, c_name, sql):
        '''
        调用pandas.read_sql 直接生成dataframe
        :param c_name:
        :param sql:
        :return:
        '''
        self.__get_cursor(c_name)
        conn = self.conn[c_name]
        df = pd.read_sql(sql, conn, coerce_float=True)
        return df