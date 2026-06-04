import pandas as pd
import pymysql1
import re
import os
import json

encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_database.json")

with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)

switch = 0
# sysFlag = "tquant"
sysFlag = "xquant"
if switch == 0:
    sysEnv = "测试环境"
else:
    sysEnv = "生产环境"
v = input("现在正准备向 【{0}】的【{1}】插入元数据，请确认，y or n ！".format(sysEnv, sysFlag))
if v.lower() == 'n':
    raise Exception("请重新设置 switch与sysFlag")

if switch == 0:
    if sysFlag == "xquant":
        sql_config = {
            'host': '168.63.1.130',
            'user': 'xquant',
            'passwd': ENCRYPTED_HOSTS[sysFlag]['test']['xquant']['ciphertext'],
            'db': 'xquant',
            'port': 3309,
            'charset': 'utf8'
        }
    elif sysFlag == "tquant":
        sql_config = {
            'host': '168.63.1.131',
            'user': 'xquant',
            'passwd': ENCRYPTED_HOSTS[sysFlag]['test']['xquant']['ciphertext'],
            'db': 'xquant',
            'port': 3307,
            'charset': 'utf8'
        }
    else:
        raise Exception("元数据新增暂只支持'xquant', 'tquant'")
else:
    if sysFlag == "xquant":
        sql_config = {
            'host': '168.6.68.72',
            'user': 'xquant',
            'passwd': ENCRYPTED_HOSTS[sysFlag]['prd']["xquant"]['ciphertext'],
            'db': 'xquant',
            'port': 3306,
            'charset': 'utf8'
        }
    elif sysFlag == "tquant":
        sql_config = {'host': '168.11.241.39',
                      'user': 'htsc_dwa_quant',
                      'passwd': ENCRYPTED_HOSTS[sysFlag]['prd']["htsc_dwa_quant"]['ciphertext'],
                      'db': 'htsc_dwa_quant_mgr',
                      'port': 3306,
                      'charset': 'utf8'}
    else:
        raise Exception("元数据新增暂只支持'xquant', 'tquant'")


class MetaData:
    def __init__(self):
        self.xquant_conn = pymysql1.connect(**sql_config)
        self.xquant_cur = self.xquant_conn.cursor()

    def __del__(self):
        try:
            self.xquant_cur.close()
            self.xquant_conn.close()
        except Exception as e:
            # print(e)
            pass

    def __mysql_close(self):
        self.xquant_cur.close()
        self.xquant_conn.close()

    def __get_library_id(self, library_name):
        if sysFlag == "xquant":
            table = "tbl_factor_library"
        else:
            table = "factor_library"
        # 获取库id
        sql_library_id = "select id from {0} where library_name = '{1}'".format(table, library_name)
        df = pd.read_sql(sql_library_id, self.xquant_conn, coerce_float=True)
        if df.empty:
            raise Exception("{0}库不存在，请检查后输入！".format(library_name))
        library_id = int(df.loc[0, 'id'])
        return library_id

    def __get_catalog_id(self, library_name, library_id, cata_name):
        # 获取因子目录id
        if sysFlag == "xquant":
            table = "tbl_factor_catalog"
        else:
            table = "factor_catalog"
        sql_use = "select catalog_id from {0} where library_id = {1} and cata_name = '{2}'".format(
            table, library_id, cata_name)
        df = pd.read_sql(sql_use, self.xquant_conn)
        if len(df) > 1:
            raise Exception("查询库有两个相同的目录！".format(library_name))
        if df.empty:
            raise Exception("{0}库不存在因子目录{1}".format(library_name, cata_name))
        catalog_id = df.loc[0, 'catalog_id']
        return catalog_id

    def __get_factor_id(self, library_id, factor_list):
        # 获取因子id
        if sysFlag == "xquant":
            table = "tbl_factor_meta"
        else:
            table = "factor_meta"
        if len(factor_list) == 1:
            factor_symbol = "(" + "'" + factor_list[0] + "'" + ")"
        else:
            factor_symbol = tuple(factor_list)
        sql_use = "select factor_symbol,id from {0} where library_id = {1} and factor_symbol in {2}".format(
            table, library_id, factor_symbol)
        df = pd.read_sql(sql_use, self.xquant_conn)
        df['id'] = df['id'].astype(int)
        id_list = df['id'].tolist()
        return id_list

    def __create_catalog_id(self):
        # 生成catalog_id  因子目录结构id 小于5000大于现有最大值
        if sysFlag == "xquant":
            table = "tbl_factor_catalog"
        else:
            table = "factor_catalog"
        sql_id = "select catalog_id from {0} where catalog_id < 5000".format(table)
        df_id = pd.read_sql(sql_id, self.xquant_conn, coerce_float=True)
        # 新建目录id数值+1
        if df_id.empty:
            catalog_id = 1
        else:
            catalog_id = int(max(df_id['catalog_id'].tolist()) + 1)
        if catalog_id >= 5000:
            raise Exception("基础因子catalog_id 已大于等于5000 ！")
        return catalog_id

    def __get_parent_id(self, library_id):
        # 获取库的根目录id
        if sysFlag == "xquant":
            table = "tbl_factor_catalog"
        else:
            table = "factor_catalog"
        sql_use = "select catalog_id from {0} where library_id = {1} and parent_id = 0".format(
            table, library_id)
        df = pd.read_sql(sql_use, self.xquant_conn)
        catalog_id = df.loc[0, 'catalog_id']
        return catalog_id

    def __check_factor_repeat(self, library_id, factors):
        """
        检测是否有重复因子，返回重复因子的列表
        :param library_id: 库id
        :param factors: list，因子列表
        :return:
        """
        if sysFlag == "xquant":
            table = "tbl_factor_meta"
        else:
            table = "factor_meta"
        sql_use = "select factor_symbol from {0} where library_id = {1}".format(table, library_id)
        df = pd.read_sql(sql_use, self.xquant_conn)
        factor_existed = df['factor_symbol'].tolist()
        # 取交集，repeat_factors非空则有重复因子
        repeat_factors = list(set(factors) & set(factor_existed))
        return repeat_factors

    def __naming_specification(self, name):
        '''
        判断命名规范
        :return:
        '''
        try:
            if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', name):
                return False
            else:
                return True
        except:
            return False

    def add_factor_library(self, library_name):
        """
        新增库操作
        :param library_name: 库名
        :return:
        """
        # xquant id 非高频小于10大于现有的最大值 tquant 单独设置一个id区域 大概100个左右
        if sysFlag == "xquant":
            # 库id的范围
            id_range = [1, 10]
            table = "tbl_factor_library"
        else:
            id_range = [1, 100]
            table = "factor_library"
        # 生成id
        sql_id = "select id from {0} where id >= {1} and id <= {2}".format(table, id_range[0], id_range[1])
        df_id = pd.read_sql(sql_id, self.xquant_conn, coerce_float=True)
        if df_id.empty:
            id = id_range[0]
        else:
            id = int(max(df_id['id'].tolist()) + 1)
        if id > id_range[-1]:
            raise Exception("【system】{0}-因子library id 已超出范围{1}".format(sysFlag, id_range))
        sql_use = "insert into {0}(id, library_type, library_name, remark) values({1}, 1, '{2}', null)".format(
            table, id, library_name)
        try:
            self.xquant_cur.execute(sql_use)
            self.xquant_conn.commit()
        except Exception as e:
            raise Exception("新增库失败：{0}".format(e))

    def add_factor_catalog(self, library_name, cata_name, cata_id=None):
        """
        在指定库下新增目录
        :param library_name: 库名
        :param cata_name: 目录名称
        :return:
        """
        # creator_account 因子创建者的账号 万得数据
        # status 目录状态（1 ： 正在用； 2：已删除）
        if sysFlag == "xquant":
            table = "tbl_factor_catalog"
        else:
            table = "factor_catalog"
        library_id = self.__get_library_id(library_name)
        sql_library_id = "select library_id from {0}".format(table)
        df_library_id = pd.read_sql(sql_library_id, self.xquant_conn)
        library_id_list = list(set(df_library_id['library_id'].tolist()))
        # 如果tbl_factor_catalog表内没有新增目录的库，则先创建该库的根目录
        if library_id not in library_id_list:
            print("{0}库还未在tbl_factor_catalog创建目录，默认先创建根目录-{0}".format(library_name))
            catalog_id = self.__create_catalog_id()
            sql = """
                    insert into {0}(catalog_id, parent_id, library_id, 
                    cata_name,creator_account,status,create_time) 
                    values 
                    ({1}, {2}, {3}, '{4}', '{5}', {6}, now())
                    """.format(table, catalog_id, 0, library_id, library_name, '万得数据', 1)
            try:
                self.xquant_cur.execute(sql)
                self.xquant_conn.commit()
            except Exception as e:
                raise Exception("创建根目录失败：{0}".format(e))
        if cata_name == library_name:
            self.__mysql_close()
            raise Exception("【cata_name】-{0} 目录名称已创建为根目录，请重新为目录命名！".format(cata_name))
        parent_id = self.__get_parent_id(library_id)
        if not cata_id:
            catalog_id = self.__create_catalog_id()
        else:
            catalog_id = cata_id
        sql_use = """
                insert into {0}(catalog_id, parent_id, library_id, 
                cata_name,creator_account,status,create_time) 
                values 
                ({1}, {2}, {3}, '{4}', '{5}', {6}, now())
                """.format(table, catalog_id, parent_id, library_id, cata_name, '万得数据', '1')
        try:
            self.xquant_cur.execute(sql_use)
            self.xquant_conn.commit()
        except Exception as e:
            raise Exception("创建目录-{0} 失败：{1}".format(cata_name, e))

    def add_factor_meta(self, library_name, factor_dict, data_frequency, owner_table_name):
        """
        新增因子查询配置
        :param library_name: 库名
        :param factor_dict: dict类型，key为因子，value为因子中文名称
        :param data_frequency: 数据频率 (0 : 每日 ,1 : 每周 , 2 : 每月 ,3 : 每季度 ,4 : 每年，5：高频，6：非高频)
        :param owner_table_name: 因子存放的表名
        :return:
        """
        # owner_col_name 因子
        # creator_account 因子创建者的账号 万得数据
        # status 因子状态（1 ： 正在用； 2：已删除 ；3 已删除但其它的地方还在用）
        if sysFlag == "xquant":
            table = "tbl_factor_meta"
        else:
            table = "factor_meta"
        if not isinstance(factor_dict, dict):
            raise Exception("【factor_dict】为dict类型，key为因子，value为因子名称，请重新输入！")
        if len(factor_dict) == 0:
            raise Exception("【factor_dict】新增因子不能为空，请重新输入！")
        for factor in list(factor_dict.keys()):
            if not self.__naming_specification(factor):
                raise Exception("%s 因子命名不规范！" % str(factor))
        library_id = self.__get_library_id(library_name)
        repeat_factors = self.__check_factor_repeat(library_id, list(factor_dict.keys()))
        if repeat_factors:
            print("【factor_dict】新增因子-{0}在库{1}已存在，现入库其他因子".format(repeat_factors, library_name))
            for i in repeat_factors:
                del factor_dict[i]
        if not factor_dict:
            print("{0}-无新增因子！".format(owner_table_name))
            return
        sql_use = """
            INSERT INTO {0} (factor_symbol, factor_name, data_frequency, library_id, 
            owner_table_name, owner_col_name, creator_account, status) 
            VALUES 
            (%s, %s, %s, %s, %s, %s, %s, %s)
            """.format(table)
        values = []
        for item in factor_dict.items():
            value = (item[0], item[-1], data_frequency, library_id, owner_table_name, item[0], '万得数据', 1)
            values.append(value)
        try:
            if len(values) == 1:
                self.xquant_cur.execute(sql_use, values[0])
            else:
                self.xquant_cur.executemany(sql_use, values)
            self.xquant_conn.commit()
        except pymysql1.err.OperationalError as e:
            self.xquant_conn.rollback()
            raise Exception("因子配置插入失败：{0}".format(e))

    def add_factor_catalog_rela(self, library_name, cata_name, factor_list):
        """
        新增因子与目录关联
        :param library_name: 库名
        :param cata_name: 目录名
        :param factor_list: list类型，因子列表
        :return:
        """
        if sysFlag == "xquant":
            table = "tbl_factor_catalog_rela"
        else:
            table = "factor_catalog_rela"
        if not isinstance(factor_list, list):
            raise Exception("【factor_list】为list类型，请重新输入！")
        if len(factor_list) == 0:
            raise Exception("【factor_list】因子列表不能为空，请重新输入！")
        # catalog_id 因子目录的id
        library_id = self.__get_library_id(library_name)
        catalog_id = self.__get_catalog_id(library_name, library_id, cata_name)
        # factor_id 因子id
        factor_id_list = self.__get_factor_id(library_id, factor_list)
        assert len(factor_list) == len(factor_id_list)
        sql_id = "select factor_id from {0} where catalog_id={1}".format(table,catalog_id)
        df_id = pd.read_sql(sql_id, self.xquant_conn)
        df_id['factor_id'] = df_id['factor_id'].astype(int)
        exist_id = df_id['factor_id'].tolist()
        for i in factor_id_list[::-1]:
            if i in exist_id:
                factor_id_list.remove(i)
        if not factor_id_list:
            print("{}-无新增因子！".format(cata_name))
            return
        sql_use = "INSERT INTO {0} (catalog_id, factor_id) values (%s, %s)".format(table)
        values = []
        for factor_id in factor_id_list:
            value = (int(catalog_id), int(factor_id))
            values.append(value)
        try:
            if len(values) == 1:
                self.xquant_cur.execute(sql_use, values[0])
            else:
                self.xquant_cur.executemany(sql_use, values)
            self.xquant_conn.commit()
        except pymysql1.err.OperationalError as e:
            self.xquant_conn.rollback()
            print("ERROR-新增因子与目录关联失败：{0}".format(e))
            raise Exception("新增因子与目录关联失败：{0}".format(e))

    def del_factor_meta(self, library_name, cata_name, factors):
        """
        批量删除因子
        :param library_name: str, 库名
        :param cata_name: str, 目录名
        :param factors: list, 因子列表
        :return:
        """
        if sysFlag == "xquant":
            table1 = "tbl_factor_catalog_rela"
            table2 = "tbl_factor_meta"
        else:
            table1 = "factor_catalog_rela"
            table2 = "factor_meta"
        if not isinstance(factors, list):
            raise Exception("【factors】为list类型，请重新输入！")
        library_id = self.__get_library_id(library_name)
        if len(factors) == 0:
            raise Exception("【factors】不能为空！")
        elif len(factors) == 1:
            factor_symbol = "(" + "'" + factors[0] + "'" + ")"
        else:
            factor_symbol = tuple(factors)
        # numpy.int64 pymysql不识别
        catalog_id = int(self.__get_catalog_id(library_name, library_id, cata_name))
        factor_id_list = self.__get_factor_id(library_id, factors)
        factor_id_list = [int(i) for i in factor_id_list]
        if len(factor_id_list) == 1:
            factor_id = "(" + str(factor_id_list[0]) + ")"
        else:
            factor_id = tuple(factor_id_list)
        sql_del_catalog = "delete from {0} where catalog_id = {1} and factor_id in {2}".format(
            table1, catalog_id, factor_id)
        sql_del_factor = "delete from {0} where library_id = {1} and factor_symbol in {2}".format(
            table2, library_id, factor_symbol)
        try:
            # 删除catalog与factor的顺序不能变
            self.xquant_cur.execute(sql_del_catalog)
            self.xquant_cur.execute(sql_del_factor)
            self.xquant_conn.commit()
        except pymysql1.err.OperationalError as e:
            self.xquant_conn.rollback()
            print("删除因子失败：{0}".format(e))
