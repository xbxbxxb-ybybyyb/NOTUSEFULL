# _*_ coding:utf-8 _*_
from sqlalchemy import create_engine
import traceback
import time
import pandas as pd
import os
from xquant1.xqutils.utils import utils_set_timeout
from DBUtils.PooledDB import PooledDB
if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION',False):
    import mysql.connector as mysql
else:
    import MySQLdb as mysql
from xquant1.factordata.storageConfig import get_sql_config,pool_config
from xquant1.factordata.utils import get_engine
from xquant1.conf.DubboConf import DUBBO_CONFIG
import datetime as dt
import threading

DUBBO_CONFIG_IP = DUBBO_CONFIG["DUBBO_CONFIG_IP"]
DUBBO_APPLICATIONCONFIG = DUBBO_CONFIG["DUBBO_CONFIG"]

# if not os.environ.get('BIG_DATA_PREPATH', False) or os.environ.get('ENV_VERSION',False):
if os.environ.get('ENV_VERSION',False) or os.environ.get('tmp_tmp',False):
    from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig

    config = ApplicationConfig(DUBBO_APPLICATIONCONFIG)
    registry = ZookeeperRegistry(DUBBO_CONFIG_IP, config)
    service_interface_db_pool = 'com.htsc.xquant.factor.manager.server.python.MySqlProcessConfigService'
    user_provider_db_pool = DubboClient(service_interface_db_pool, registry, version="1.0.0")
else:
    #如果是大数据平台
    config = None
    registry = None
    service_interface_db_pool = None
    user_provider_db_pool = None



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
    # if not pool_params:
    #     pool_params = pool_config
    # mincached:池中的初始空闲连接数
    # maxcached:池中的最大空闲连接数
    # maxshared:最大共享连接数
    # maxconnections:一般允许的最大连接数
    # blocking: 超过最大链接数后：True阻塞并等待连接数减少，False则报错
    # maxusage:单个连接的最大重用次数，0 or None标识不限制重用
    # setsession:
    sql_config = get_sql_config(user)
    def pool(sql_config,wait_time):
        try:
            __pool = PooledDB(creator=mysql, mincached=pool_config['mincached'], maxcached=pool_config['maxcached'],
                              maxconnections=pool_config['maxconnections'],maxshared=pool_config['maxshared'],blocking=True,
                              host=sql_config['host'],user=sql_config['user'], passwd=sql_config['passwd'], db=sql_config['db'],
                              port=sql_config['port'], charset=sql_config['charset'])
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
        __pool = pool(sql_config,wait_time)
        if __pool:
            return __pool
    # print('池子里目前有', __pool._idle_cache, '\r\n')
    raise Exception("mysql连接已达上限，创建链接池失败[%s]！"%(user))

def get_pool(user):
    # raise Exception("dubbo error!")

    def _get_pool(judge_bool,user,wait_time):
        if judge_bool:
            pool = OPMysql(user)
            return pool
        else:
            time.sleep(wait_time)
            return None
    for i in range(10):
        if not (i + 1) % 3:
            print("mysql连接数已达上限，尝试再次创建连接池！")
        judge_bool = user_provider_db_pool.QueryMySqlProcessList()
        wait_time = 3
        pool = _get_pool(judge_bool,user,wait_time)
        if pool:
            return pool

    raise Exception("mysql连接已达上限，创建链接池失败！")

class DML_mysql:
    def __init__(self,user):
        self.user = user
        try:
            self.pool = get_pool(user)
        except:
            self.pool = OPMysql(user)
        self.conn = {}
        self.cur = {}
        self.engine = {}

    def __del__(self):
        try:
            self.pool.close()
            del self.pool
        except:
            pass

    def commit(self,c_name):
        self.conn[c_name].commit()

    def rollback(self,c_name):
        self.conn[c_name].rollback()

    def __get_engine(self,c_name,retry=3):
        def connect(c_name, wait_time):
            if not self.engine.get(c_name):
                try:
                    engine = get_engine(self.user)
                except mysql.Error as e:
                    print("engine创建失败，等待下次创建...%s[%s]" % (e,self.user))
                    time.sleep(wait_time)
                    return None

                self.engine[c_name] = engine
            else:
                engine = self.engine[c_name]
            return engine

        for i in range(retry):
            if i == 0:
                wait_time = 10
            else:
                wait_time = 60
            engine = connect(c_name, wait_time=wait_time)
            if engine:
                return engine
        raise Exception("engine创建失败[%s]！"%(self.user))

    def df_to_mysql(self,df,tablename,c_name):
        engine = self.__get_engine(c_name)
        try:
            df.to_sql(name=tablename, con=engine, if_exists='append', index=True, index_label=['tradingcode','tdate'])
        except Exception as e:
            traceback.print_exc()
            print("【WARNING】sql语句执行失败!若是更新个人因子操作，且dataframe中有nan，-inf值，会更新失败！" )

    def getAllByPandas(self, c_name,sql):
        '''
        调用pandas.read_sql 直接生成dataframe
        :param c_name:
        :param sql:
        :return:
        '''
        self.__get_cursor(c_name)
        conn = self.conn[c_name]
        df = pd.read_sql(sql,conn,coerce_float=True)
        return df

    @utils_set_timeout(90, "sql查询超时！请缩短查询区间！")
    def getAll(self, c_name,sql, param=None):
        """
        执行查询，并取出所有结果集
        :param sql: 查询SQL，如果有查询条件，指定条件列表，并将条件值使用参数[param]传递进来
        :param param: 可选参数，条件列表值（元组/列表），需与sql中的%s 一一对应
        :return: list 查询到的结果集,list[0] 为数据表列名
        """
        cur = self.__get_cursor(c_name)
        try:
            if param is None:
                cur.execute(sql)
            else:
                cur.execute(sql, param)
        except mysql.Error as e:
            print("The query data failed : %s"%e)
            return
        result = cur.fetchall()
        if isinstance(result,tuple):
            result = list(result)
        column_name = []
        des = cur.description
        for i in des:
            column_name.append(i[0])
        result.insert(0,tuple(column_name))
        return result

    def getMany(self, c_name,sql, num, param=None):
        """
        执行查询，并取出num条结果
        :param sql: 查询SQL，如果有查询条件，指定条件列表，并将条件值使用参数[param]传递进来
        :param num: 取得的结果条数
        :param param: 可选参数，条件列表值（元组/列表），需与sql中的%s 一一对应
        :return: list 查询到的结果集,list[0] 为数据表列名
        """
        cur = self.__get_cursor(c_name)
        try:
            if param is None:
                cur.execute(sql)
            else:
                cur.execute(sql, param)
        except mysql.Error as e:
            print("The query data failed : %s" % e)
            return
        result = cur.fetchmany(num)
        if isinstance(result,tuple):
            result = list(result)
        column_name = []
        des = cur.description
        for i in des:
            column_name.append(i[0])
        result.insert(0, tuple(column_name))
        return result

    def insertOne(self, c_name, sql, value):
        """
        向数据表插入一条记录
        :param sql: 要插入的SQL格式
        :param value: 要插入的记录数据tuple/list
        :return:
        """
        cur = self.__get_cursor(c_name)
        try:
            cur.execute(sql, value)
            print("Insert data success!")
        except mysql.Error as e:
            print("Insert data failed: %s" % e)


    def insertMany(self, c_name, sql, values):
        """
        向数据表插入多条记录
        :param sql: 要插入的SQL格式
        :param values: 要插入的记录数据tuple(tuple)/list[list]
        :return:
        """
        cur = self.__get_cursor(c_name)
        try:
            cur.executemany(sql, values)
            print("Insert datas success!")
        except mysql.Error as e:
            print("Insert data failed: %s"%e)


    def __query(self, cur,sql, param=None):
        if param is None:
            cur.execute(sql)
        else:
            cur.execute(sql, param)
        # count = self.cur.rowcount

    def rowcount(self,c_name):
        cur = self.__get_cursor(c_name)
        return cur.rowcount

    def update(self, c_name, sql, param=None):
        """
        更新数据表记录
        :param sql: SQL格式及条件，使用(%s,%s)
        :param param: 要更新的值 tuple/list
        :return:
        """
        cur = self.__get_cursor(c_name)
        try:
            self.__query(cur, sql, param)
            print("update data success!")
        except mysql.Error as e:
            print("update data failed : %s"%e)

    def delete(self, c_name, sql, param=None):
        """
        删除数据表记录
        :param sql: SQL格式及条件，使用(%s,%s)
        :param param:  要删除的条件、值 tuple/list
        :return:
        """
        cur = self.__get_cursor(c_name)
        try:
            self.__query(cur, sql, param)
            print("delete data success!")
        except mysql.Error as e:
            print("delete data failed : %s" % e)

    def execute(self,c_name,sql):
        cur = self.__get_cursor(c_name)
        try:
            cur.execute(sql)
        except mysql.Error as e:
            print("Execute the sql failed : %s" % e)

    def executeMany(self,c_name,sql, values):
        cur = self.__get_cursor(c_name)
        try:
            cur.executemany(sql, values)
        except mysql.Error as e:
            traceback.print_exc()
            print("【WARNING】sql语句执行失败!若是更新个人因子操作，且dataframe中有nan，-inf值，会更新失败！")

    def call_proc(self,c_name,proc_name,params):
        cur = self.__get_cursor(c_name)
        params_num = ''
        for i in range(len(params)):
            params_num += '%s,'
        cur.nextset()
        cur.execute('call {0}({1})'.format(proc_name,params_num[:-1]),params)
        result = cur.fetchall()
        return result


    def close(self,c_name):
        """ 释放资源 """
        self.cur[c_name].close()
        self.conn[c_name].close()
        try:
            del self.cur[c_name]
            del self.conn[c_name]
        except Exception as e:
            print(e)

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


    # def __get_conn(self,c_name, retry=3):
    #     def connect(c_name, wait_time):
    #         if not self.conn.get(c_name):
    #             try:
    #                 # print("连接mysql...")
    #                 conn = self.pool.connection()
    #             except mysql.Error as e:
    #                 print("mysql链接数达到上限，等待再次取链接...%s[%s]" % (e,self.user))
    #                 time.sleep(wait_time)
    #                 return None
    #         else:
    #             conn = self.conn[c_name]
    #         return conn
    #
    #     for i in range(retry):
    #         if i == 0:
    #             wait_time = 10
    #         else:
    #             wait_time = 60
    #         conn = connect(c_name, wait_time=wait_time)
    #         if conn:
    #             return conn
    #     raise Exception("mysql连接已达上限，连接失败[%s]！"%(self.user))