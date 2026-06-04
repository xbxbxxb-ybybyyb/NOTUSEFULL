# _*_ coding:utf-8 _*_

from impala.dbapi import connect
from .config import *

class Connect_hive:
    def __init__(self):
        self.host = hive_config['host']
        self.port = hive_config['port']
        self.database = hive_config['database']
        self.user = hive_config['user']
        self.password = hive_config['password']
        self.auth_mechanism = hive_config['auth_mechanism']

    def get_conn(self):
        conn = connect(host=self.host, port=self.port, database=self.database, user=self.user,
                       password=self.password,auth_mechanism=self.auth_mechanism)
        return conn

    def getAll(self,sql):
        """
        执行查询，并取出所有结果集
        :param sql: 查询SQL
        :return: list 查询到的结果集,list[0] 为数据表列名
        """
        conn = self.get_conn()
        cur = conn.cursor()
        cur.execute('set hive.cli.print.header=true')
        cur.execute('set hive.resultset.use.unique.column.names=false')
        cur.execute(sql)
        result = cur.fetchall()
        column_name = []
        des = cur.description
        for i in des:
            column_name.append(i[0])
        result.insert(0, tuple(column_name))
        cur.close()
        conn.close()
        return result