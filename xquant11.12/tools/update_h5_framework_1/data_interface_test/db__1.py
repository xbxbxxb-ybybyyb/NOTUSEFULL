# _*_ coding:utf-8 _*_

from DBUtils.PooledDB import PooledDB
import mysql.connector as mysql
from Config import *
import datetime as dt
from log import Log

logger = Log("Connect db")

class OPMysql(object):
    def __init__(self,pool_params=None):
        # 初始化连接池
        self.pool = OPMysql.__getmysqlconn(pool_params)

    # 构建数据库连接池
    @staticmethod
    def __getmysqlconn(pool_params):
        if not pool_params:
            pool_params = pool_config
        # mincached:池中的初始空闲连接数
        # maxcached:池中的最大空闲连接数
        # maxshared:最大共享连接数
        # maxconnections:一般允许的最大连接数
        # blocking: 超过最大链接数后：True阻塞并等待连接数减少，False则报错
        # maxusage:单个连接的最大重用次数，0 or None标识不限制重用
        # setsession:
        __pool = PooledDB(creator=mysql, mincached=pool_params['mincached'], maxcached=pool_params['maxcached'],
                          maxconnections=pool_params['maxconnections'],maxshared=pool_params['maxshared'],blocking=False,
                          host=sql_config['host'],user=sql_config['user'], passwd=sql_config['passwd'], db=sql_config['db'],
                          port=sql_config['port'], charset=sql_config['charset'])
        # print('池子里目前有', __pool._idle_cache, '\r\n')
        return __pool

    def get_pool(self):
        return self.pool

class DML_mysql:
    def __init__(self,conn):
        self.conn = conn
        self.cur = self.conn.cursor()

    def getAll(self, sql, param=None):
        """
        执行查询，并取出所有结果集
        :param sql: 查询SQL，如果有查询条件，指定条件列表，并将条件值使用参数[param]传递进来
        :param param: 可选参数，条件列表值（元组/列表），需与sql中的%s 一一对应
        :return: list 查询到的结果集,list[0] 为数据表列名
        """
        try:
            if param is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, param)
        except Exception as e:
            logger.error("The query data failed : %s"%e)
            return
        result = self.cur.fetchall()
        column_name = []
        des = self.cur.description
        for i in des:
            column_name.append(i[0])
        result.insert(0,tuple(column_name))
        self.close()
        return result

    def getMany(self, sql, num, param=None):
        """
        执行查询，并取出num条结果
        :param sql: 查询SQL，如果有查询条件，指定条件列表，并将条件值使用参数[param]传递进来
        :param num: 取得的结果条数
        :param param: 可选参数，条件列表值（元组/列表），需与sql中的%s 一一对应
        :return: list 查询到的结果集,list[0] 为数据表列名
        """
        try:
            if param is None:
                self.cur.execute(sql)
            else:
                self.cur.execute(sql, param)
        except Exception as e:
            logger.error("The query data failed : %s" % e)
            return
        result = self.cur.fetchmany(num)
        column_name = []
        des = self.cur.description
        for i in des:
            column_name.append(i[0])
        result.insert(0, tuple(column_name))
        self.close()
        return result

    def insertOne(self, sql, value):
        """
        向数据表插入一条记录
        :param sql: 要插入的SQL格式
        :param value: 要插入的记录数据tuple/list
        :return:
        """
        try:
            self.cur.execute(sql, value)
            self.conn.commit()
            logger.info("Insert data success!")
            self.close()
        except Exception as e:
            logger.error("Insert data failed: %s" % e)


    def insertMany(self, sql, values):
        """
        向数据表插入多条记录
        :param sql: 要插入的SQL格式
        :param values: 要插入的记录数据tuple(tuple)/list[list]
        :return:
        """
        try:
            self.cur.executemany(sql, values)
            self.conn.commit()
            logger.info("Insert datas success!")
            self.close()
        except Exception as e:
            logger.error("Insert data failed: %s"%e)


    def __query(self, sql, param=None):
        if param is None:
            self.cur.execute(sql)
        else:
            self.cur.execute(sql, param)
        # count = self.cur.rowcount


    def update(self, sql, param=None):
        """
        更新数据表记录
        :param sql: SQL格式及条件，使用(%s,%s)
        :param param: 要更新的值 tuple/list
        :return:
        """
        try:
            self.__query(sql, param)
            self.close()
            logger.info("update data success!")
        except Exception as e:
            logger.error("update data failed : %s"%e)

    def delete(self, sql, param=None):
        """
        删除数据表记录
        :param sql: SQL格式及条件，使用(%s,%s)
        :param param:  要删除的条件、值 tuple/list
        :return:
        """
        try:
            self.__query(sql, param)
            self.close()
            logger.info("delete data success!")
        except Exception as e:
            logger.error("delete data failed : %s" % e)

    def close(self):
        """ 释放资源 """
        self.cur.close()
        self.conn.close()
