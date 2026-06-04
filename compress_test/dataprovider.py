import configparser
import contextlib
import hashlib
import logging
import pickle
import random
import socket
import os
from os import path, system, popen
import base64
import jpype
from jpype import *

import pandas as pd
from kerberos import GSSError
from retrying import retry
from thrift.Thrift import TException
from thrift.protocol import TBinaryProtocol
from thrift.transport import TSocket, TTransport
from quanthbase.hbasecore import Batch
from quanthbase.hbasethrift import Hbase
from quanthbase.hbasethrift.ttypes import ColumnDescriptor, TScan
from multiprocessing import Process, Queue
import subprocess
import zlib
import lzma
import zstd
import bz2
import pickletools
import time

def singleton(cls):
    # 单下划线的作用是这个变量只能在当前模块里访问,仅仅是一种提示作用
    # 创建一个字典用来保存类的实例对象
    _instance = {}

    def _singleton(*args, **kwargs):
        # 先判断这个类有没有对象
        if cls not in _instance:
            _instance[cls] = cls(*args, **kwargs)  # 创建一个对象,并保存到字典当中
        # 将实例对象返回
        return _instance[cls]

    return _singleton

@singleton
class DataProvider:
    def __init__(self, mod='online', compression='SNAPPY'):
        self.__mod = mod
        self.__config = configparser.ConfigParser()
        config_path = path.join(path.dirname(path.abspath(__file__)), 'dataprovider-' + mod + '.ini')
        self.__config.read(config_path)
        self.__jvm_path = self.__config['jpype']['jvm.path']
        # krb5 config
        self.__krb5_username = self.__config['hbase']['krb5.username']
        self.__krb5_conf_path = path.join(path.dirname(path.abspath(__file__)), 'resources/' + mod + '/krb5.conf')
        self.__krb5_keyTab_path = path.join(path.dirname(path.abspath(__file__)),
                                            'resources/' + mod + '/' + self.__krb5_username + '.keytab')
        # hbase config
        self.__hbase_conf_path = path.join(path.dirname(path.abspath(__file__)), 'resources/' + mod + '/hbase-site.xml')
        self.__hdfs_conf_path = path.join(path.dirname(path.abspath(__file__)), 'resources/' + mod + '/hdfs-site.xml')
        self.__zookeeper_quorum = self.__config['hbase']['zookeeper.quorum']
        self.__zookeeper_clientPort = self.__config['hbase']['zookeeper.property.clientPort']
        self.__thrift_servers = list(map(lambda x: x.strip(),
                                         self.__config['hbase']['thrift.servers'].split(',')))
        self.__thrift2_servers = list(map(lambda x: x.strip(),
                                          self.__config['hbase']['thrift2.servers'].split(',')))
        self.__factor_table_namespace = bytes(self.__config['hbase']['factor.table.namespace'], encoding='utf-8')
        self.__factor_table_family1 = bytes(self.__config['hbase']['factor.table.family1'], encoding='utf-8')
        self.__factor_table_family2 = bytes(self.__config['hbase']['factor.table.family2'], encoding='utf-8')
        self.__table_compression = compression
        self.__table_split_num = int(self.__config['hbase']['table.split_num'])
        # read/write params
        self.__batch_size = 1000
        self.__scan_rows = 100

        self.__client = None
        self.__transport = None
        if not self.__is_kerberos_cache_valid():
            system("kinit -kt {} {}".format(self.__krb5_keyTab_path, self.__krb5_username))

        # 测试连接是否成功
        self.__get_client()


    def create_factor_library(self, library_id):
        """
        for jpype jvm shutdown bug, use subprocess to retain context
        :param library_id:
        :return:
        """
        queue = Queue()
        p = Process(target=self.__create_factor_library, args=(queue, library_id))
        p.start()
        p.join()
        result = queue.get()
        return result

    def update_factor_value_by_jvm(self, library_name, symbol, date, factor_values, cell_size, compatible=False):
        import os
        table_name = str(self.__get_table_name(library_name), "utf-8")
        # 传递的参数
        rowkey = str(self.__get_row_key(symbol, date), "utf-8")
        jvm_path = self.__jvm_path
        srcenvConf = {"hbaseConfPath": self.__hbase_conf_path,
                      "hdfsConfPath": self.__hdfs_conf_path,
                      "krb5ConfPath": self.__krb5_conf_path,
                      "zooKeeperIp": self.__zookeeper_quorum,
                      "zooKeeperPort": self.__zookeeper_clientPort,
                      "cellSize": (cell_size * 1024 * 1024),
                      "keyName": self.__krb5_username,
                      "keyTabPath": self.__krb5_keyTab_path}

        srchbaseProps = {
            "batch": self.__batch_size,
            "tableName": table_name
        }

        srccfValues = self.__get_column_value_pairs(factor_values, compatible, compress=None, level=0)
        dict = {
            "rowkey": rowkey,
            "jvm_path": jvm_path,
            "srcenvConf": srcenvConf,
            "srchbaseProps": srchbaseProps,
            "srccfValues": srccfValues
        }
        pid = str(os.getpid())
        py_path = path.join(path.dirname(path.abspath(__file__)), "updatebyjava.py")
        filename = "/tmp/quanthbase-random-" + pid + ".pickle"
        if (os.path.exists(filename)):
            os.remove(filename)
        with open(filename,"wb")as file:
            pickle.dump(dict,file)
            file.close()
        if os.environ.get('BIG_DATA_PREPATH',None):
            child = subprocess.call(["/usr/lib/anaconda3/bin/python", py_path, filename])
        else:
            child = subprocess.call(["python3", py_path, filename])
        if (os.path.exists(filename)):
            os.remove(filename)
        if child == 0 :
            return True
        else:
            return False

    def create_factor_library_by_thrift(self,library_name):
        try:
            return self.__create_factor_library_by_thrift(library_name)
        except(TException, socket.error)as e:
            print("Warning: create table error, exception =  %s", e)
            return False

    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def add_factor(self, library_id, factor_id_list):
        client = self.__get_client()
        try:
            is_enabled = client.isTableEnabled(self.__get_table_name(library_id))
        except(TException, socket.error) as e:
            print("Warning: access not exist table = %s, exception = %s", library_id, e)
            self.__re_get_client()
            return None
        if is_enabled:
            return self.__get_table_name(library_id)
        else:
            return None

    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def remove_factor(self, library_id, factor_id_list):
        return True
        # columns = self.__get_columns(factor_names)
        # with self.__get_client() as client:
        #     try:
        #         # 批量扫描
        #         scan = TScan(columns=columns)
        #         scanner_id = client.scannerOpenWithScan(self.__get_table_name(library_name), scan, {})
        #         rowList = client.scannerGetList(scanner_id, self.__scan_rows)
        #         with Batch(client=client, table_name=self.__get_table_name(library_name),
        #                    batch_size=self.__batch_size) as b:
        #             while rowList:
        #                 for row in rowList:
        #                     b.delete(row.row, columns)
        #                 rowList = client.scannerGetList(scanner_id, self.__scan_rows)
        #             client.scannerClose(scanner_id)
        #         return True
        #     except(TException, socket.error) as e:
        #         print("Warning: scan table for delete failed. table = %s, exception = %s", library_name, e)
        #         return False


    def remove_factor_value(self, library_id, symbol, date, factor_id_list):
        try :
            return self.__remove_factor_value(library_id, symbol, date, factor_id_list)
        except(TException, socket.error) as e:
            print("Warning: remove factor value failed. table = %s, exception = %s", library_id, e)
            return False

    def update_factor_value(self, library_id, symbol, date, factor_values, compatible=False, compress=None, level=1):
        try:
            return self.__update_factor_value(library_id, symbol, date, factor_values, compatible, compress, level)
        except(TException, socket.error) as e:
            print("Warning: update table failed. table = %s, exception = %s", library_id, e)
            return False

    # @retry(tries=5, delay=1)
    # def get_factor_value(self, library_id, symbol, date, factor_id_list):
    #     row_key = self.__get_row_key(symbol, date)
    #     columns = self.__get_columns(factor_id_list, 1)
    #     with self.__get_client() as client:
    #         tresult = client.getRowWithColumns(tableName=self.__get_table_name(library_id), row=row_key,
    #                                            columns=columns, attributes=None)
    #         if len(tresult) != 1:
    #             print("Warning: get table data, return null. table = %s", library_id)
    #             return None
    #         res = [pickle.loads(v.value) for k, v in tresult[0].columns.items()]
    #         return pd.concat(res, axis=1)

    def get_factor_value(self, library_id, symbol, date, factor_id_list, compatible=False, compress=None):
        try:
            return self.__get_factor_value(library_id, symbol, date, factor_id_list, compatible, compress)
        except(TException, socket.error) as e:
            # todo 参数设置成函数输入的参数，之后的函数也一样
            print("Warning: update table failed. table = %s, exception = %s", library_id, e)

    def get_factor_list(self, library_id, symbol, date):
        try:
            return self.__get_factor_list(library_id, symbol, date)
        except(TException, socket.error) as e:
            # todo 参数设置成函数输入的参数，之后的函数也一样
            print("Warning: update table failed. table = %s, exception = %s", library_id, e)

    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def __create_factor_library_by_thrift(self, library_name):
        client = self.__get_client()
        try:
            client.createTable(
                tableName=(self.__get_table_name(library_name)),
                columnFamilies=[
                    ColumnDescriptor(name=self.__factor_table_family1, compression=self.__table_compression),
                    ColumnDescriptor(name=self.__factor_table_family2, compression=self.__table_compression)
                ])
            return True
        except (TException, socket.error) as e:
            self.__re_get_client()
            raise e

    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def __remove_factor_value(self, library_id, symbol, date, factor_id_list):
        columns = self.__get_columns(factor_id_list)
        row_key = self.__get_row_key(symbol, date)
        client = self.__get_client()
        try:
            with Batch(client=client, table_name=self.__get_table_name(library_id),
                       batch_size=self.__batch_size) as b:
                b.delete(row_key, columns)
            return True
        except(TException, socket.error) as e:
            self.__re_get_client()
            raise e

    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def __update_factor_value(self, library_id, symbol, date, factor_values, compatible, compress, level):
        row_key = self.__get_row_key(symbol, date)
        client = self.__get_client()
        try:
            with Batch(client=client, table_name=self.__get_table_name(library_id),
                       batch_size=self.__batch_size) as b:
                t1 = time.time()
                b.put(row_key, self.__get_column_value_pairs(factor_values, compatible, compress, level))
                print("save hbase time:{}".format(time.time()-t1))
            return True
        except(TException, socket.error) as e:
            # todo 参数设置成函数输入的参数，之后的函数也一样
            self.__re_get_client()
            raise e

    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def __get_factor_value(self, library_id, symbol, date, factor_id_list, compatible, compress=None):
        '''
        解决内存泄露
        :param library_id:
        :param symbol:
        :param date:
        :param factor_id_list:
        :param compatible: 是否兼容Pandas1.1.x+，True为兼容1.1.x+版本pandas，以json方式存取，False为不兼容，以pickle方式存取，性能稍差
        :return:
        '''
        row_key = self.__get_row_key(symbol, date)
        columns = self.__get_columns(factor_id_list, 1)
        client = self.__get_client()
        try:
            tresult = client.getRowWithColumns(tableName=self.__get_table_name(library_id), row=row_key,
                                               columns=columns, attributes=None)
            if len(tresult) != 1:
                print("Warning: get table data, return null. table = %s", library_id)
                return None
            t1 = time.time()
            if not compatible:
                if compress == 'zlib':
                    res = [pickle.loads(zlib.decompress(v.value)) for k, v in tresult[0].columns.items()]
                elif compress == "lzma":
                    res = [pickle.loads(lzma.decompress(v.value)) for k, v in tresult[0].columns.items()]
                elif compress == "zstd":
                    res = [pickle.loads(zstd.decompress(v.value)) for k, v in tresult[0].columns.items()]
                elif compress == "bz2":
                    res = [pickle.loads(bz2.decompress(v.value)) for k, v in tresult[0].columns.items()]
                else:
                    res = [pickle.loads(v.value) for k, v in tresult[0].columns.items()]
            else:
                res = [pd.read_json(v.value.decode(encoding='utf-8')) for k, v in tresult[0].columns.items()]
            print("decompress dataframe time:{}".format(time.time()-t1))
            return pd.concat(res, axis=1)
        except(TException, socket.error) as e:
            self.__re_get_client()
            raise e


    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def __get_factor_list(self, library_id, symbol, date):
        row_key = self.__get_row_key(symbol, date)
        client = self.__get_client()
        try:
            tresult = client.getRowWithColumns(tableName=self.__get_table_name(library_id), row=row_key,
                                               columns=[self.__factor_table_family2], attributes=None)
            if len(tresult) != 1:
                print("Warning: get table data, return null. table = %s", library_id)
                return None
            res = [str(v.value, encoding='utf-8') for k, v in tresult[0].columns.items()]
            return res
        except(TException, socket.error) as e:
            self.__re_get_client()
            raise e

    def __get_table_name(self, library_id):
        return self.__factor_table_namespace + b":" + bytes('xquant_factor_library_{}'.format(library_id), encoding='utf-8')

    @staticmethod
    def __get_row_key(symbol, date):
        return bytes(hashlib.md5(symbol.encode(encoding='utf-8')).hexdigest()[:2] + symbol + date, encoding='utf-8')

    def __get_columns(self, factor_id_list, cf=None):
        if cf is None:
            cf1_cols = [self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8') for x in factor_id_list]
            cf2_cols = [self.__factor_table_family2 + b":" + bytes(x, encoding='utf-8') for x in factor_id_list]
            return cf1_cols + cf2_cols
        if cf == 1:
            return [self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8') for x in factor_id_list]
        if cf == 2:
            return [self.__factor_table_family2 + b":" + bytes(x, encoding='utf-8') for x in factor_id_list]

    def __get_column_value_pairs(self, factor_values, compatible, compress, level):
        factor_id_list = factor_values.columns
        t1 = time.time()
        if not compatible:
            if compress == 'zlib':
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): zlib.compress(pickle.dumps(factor_values[[x]]), level=level) for x in factor_id_list}
            elif compress == "lzma":
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): lzma.compress(pickle.dumps(factor_values[[x]])) for x in factor_id_list}
            elif compress == "zstd":
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): zstd.compress(pickle.dumps(factor_values[[x]]), level) for x in factor_id_list}
            elif compress == "bz2":
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): bz2.compress(
                        pickle.dumps(factor_values[[x]]), compresslevel=level) for x in factor_id_list}
            elif compress == "protocol":
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): pickle.dumps(factor_values[[x]], protocol=level) for x in factor_id_list}
            elif compress == "optimize":
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): pickletools.optimize(pickle.dumps(factor_values[[x]],
                                                                                                  protocol=level)) for x in factor_id_list}
            else:
                pair1 = {
                    # 注意这里使用 dataframe[[x]]，目的是返回dataframe（因为[x]为列表，需要保留列信息做区分），从而保留column信息，方便读取时合并
                    self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'): pickle.dumps(
                        factor_values[[x]]) for
                    x in factor_id_list}
        else:
            pair1 = {
                self.__factor_table_family1 + b":" + bytes(x, encoding='utf-8'):
                    bytes(factor_values[[x]].to_json(), encoding='utf-8') for x in factor_id_list}
        print("compress dataframe time:{}".format(time.time() - t1))
        pair2 = {self.__factor_table_family2 + b":" + bytes(x, encoding='utf-8'): bytes(x, encoding='utf-8') for x in
                 factor_id_list}
        pair1.update(pair2)
        return pair1

    # @contextlib.contextmanager
    # def __get_client(self):
    #     curr_server = random.sample(self.__thrift_servers, 1)[0].split(":")
    #     transport = TTransport.TBufferedTransport(TSocket.TSocket(host=curr_server[0], port=curr_server[1]))
    #     try:
    #         transport = self.__get_valid_transport()
    #         protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)
    #         client = Hbase.Client(protocol)
    #         yield client
    #     except(TException, socket.error):
    #         raise
    #     finally:
    #         transport.close()

    def __get_client(self):
        # NOTE：self.__transport.isOpen 不能检测到断开的连接，因此不会重新建立连接
        # 因此在每个使用__get_client需要用try-catch捕获异常，并调用__re_get_client手动进行重新获取连接
        if self.__client == None or self.__transport.isOpen() == False:
            self.__re_get_client()
        return self.__client

    def __re_get_client(self):
        try:
            transport = self.__get_valid_transport()
            protocol = TBinaryProtocol.TBinaryProtocolAccelerated(transport)
            client = Hbase.Client(protocol)
            self.__transport = transport
            self.__client = client
        except(TException, socket.error):
            raise


    @retry(stop_max_attempt_number=5,wait_fixed=2000)
    def __get_valid_transport(self):
        curr_server = random.sample(self.__thrift_servers, 1)[0].split(":")
        if self.__mod == 'staging':
            transport = TTransport.TBufferedTransport(TSocket.TSocket(host=curr_server[0], port=curr_server[1]))
        else:
            transport = TTransport.TSaslClientTransport(TSocket.TSocket(host=curr_server[0], port=curr_server[1]),
                                                        host=curr_server[0], service='hbase', mechanism='GSSAPI')
        try:
            transport.open()
        except (GSSError, TException, socket.error):
            print("Warning: open transport to thrift server %s failed", curr_server[0])
            raise
        logging.debug("choose thrift server =  %s", curr_server)
        return transport

    def __create_factor_library(self, q, library_id):
        jar_path = path.join(
            path.dirname(path.abspath(__file__))) + '/libs/quanthbase-1.0-SNAPSHOT-jar-with-dependencies.jar'
        log_path = path.join(
            path.dirname(path.abspath(__file__))
        ) + "/libs"
        if not jpype.isJVMStarted():  # test whether the JVM is started
            jpype.startJVM(self.__jvm_path, '-ea', "-Djava.class.path=%s:%s" % (jar_path, log_path))
        table_creator = jpype.JClass('quant.hbase.OperateTable')()

        families = jpype.java.util.ArrayList()
        families.add(str(self.__factor_table_family1, encoding="utf-8"))
        families.add(str(self.__factor_table_family2, encoding="utf-8"))
        try:
            table_creator.createFactorTable(jpype.JString(str(self.__get_table_name(library_id), encoding="utf-8")),
                                            families,
                                            self.__table_split_num,
                                            self.__table_compression,
                                            self.__zookeeper_quorum,
                                            self.__zookeeper_clientPort,
                                            self.__krb5_conf_path,
                                            self.__krb5_keyTab_path,
                                            self.__krb5_username,
                                            self.__hbase_conf_path,
                                            self.__hdfs_conf_path)
            q.put(True)
        except Exception as e:
            print("Warning: create table error, exception =  %s", e)
            q.put(False)
        finally:
            jpype.shutdownJVM()


    # def __update_factor_value_by_jvm(self, q,library_name, symbol, date, factor_values, cell_size):
    #     row_key = str(self.__get_row_key(symbol, date),"utf-8")
    #     table_name = self.__get_table_name(library_name)
    #     table_name = str(table_name,"utf-8")
    #     jar_path = path.join(
    #         path.dirname(path.abspath(__file__))) + '/libs/quanthbase-1.0-SNAPSHOT-jar-with-dependencies.jar'
    #     log_path = path.join(
    #         path.dirname(path.abspath(__file__))
    #     ) + "/libs"
    #     if not jpype.isJVMStarted():  # test whether the JVM is started
    #         jpype.startJVM(self.__jvm_path, '-ea', "-Djava.class.path=%s:%s" % (jar_path, log_path))
    #     table_operate = jpype.JClass('quant.hbase.OperateTable')()
    #     srcenvConf = {"hbaseConfPath": self.__hbase_conf_path,
    #                   "hdfsConfPath": self.__hdfs_conf_path,
    #                   "krb5ConfPath": self.__krb5_conf_path,
    #                   "zooKeeperIp": self.__zookeeper_quorum,
    #                   "zooKeeperPort": self.__zookeeper_clientPort,
    #                   "cellSize": (cell_size * 1024 * 1024),
    #                   "keyName": self.__krb5_username,
    #                   "keyTabPath": self.__krb5_keyTab_path}
    #     envConf = java.util.HashMap()
    #     for k, v in srcenvConf.items():
    #         v = str(v)
    #         envConf.put(k, v)
    #
    #     srchbaseProps = {
    #                   "batch":self.__batch_size,
    #                   "tableName":table_name
    #                   }
    #     hbaseProps = java.util.HashMap()
    #     for k,v in srchbaseProps.items():
    #         v = str(v)
    #         hbaseProps.put(k,v)
    #
    #     srccfValues = self.__get_column_value_pairs(factor_values)
    #     cfValues = java.util.HashMap()
    #     for k,v in srccfValues.items():
    #         k = str(k,'utf-8')
    #         v = base64.b64encode(v)
    #         v = str(v,"utf-8")
    #         cfValues.put(k,v)
    #
    #     try:
    #         table_operate.putData(envConf, hbaseProps, row_key, cfValues)
    #         q.put(True)
    #     except Exception as e:
    #         print("Warning: update table error, exception =  %s", e)
    #         q.put(False)
    #     finally:
    #         jpype.shutdownJVM()

    def __is_kerberos_cache_valid(self):
        result = popen('klist')
        res = result.read()
        if 'Default principal: xquant' not in res:
            return False
        for line in res.splitlines():
            line_list = line.split("  ")
            if len(line_list) == 3 and 'krbtgt' in line:
                import datetime
                try:
                    if datetime.datetime.strptime(line_list[1], "%m/%d/%y %H:%M:%S") > datetime.datetime.now():
                        return True
                except ValueError:
                    if datetime.datetime.strptime(line_list[1], "%m/%d/%Y %H:%M:%S") > datetime.datetime.now():
                        return True
        result.close()
        return False

    def test(self):
        jar_path = path.join(
            path.dirname(path.abspath(__file__))) + '/libs/quanthbase-1.0-SNAPSHOT-jar-with-dependencies.jar'
        print(jpype.isJVMStarted())
        if not jpype.isJVMStarted():  # test whether the JVM is started
            jpype.startJVM(self.__jvm_path, '-ea', "-Djava.class.path=%s" % jar_path)
        jpype.shutdownJVM()
        return True
    def __del__(self):
        if self.__transport != None and self.__transport.isOpen == True : self.__transport.close()

