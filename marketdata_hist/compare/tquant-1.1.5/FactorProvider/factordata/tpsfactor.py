# _*_ coding:utf-8 _*_
import os
import datetime
import traceback
import uuid
import time
import numpy as np
import pandas as pd
from FactorProvider.storage.db import DML_mysql, sql_connect
# from FactorProvider.conf import TDubboConf
from FactorProvider.conf.TDubboConf import get_userAccount
from FactorProvider.utils.utils import is_valid_date
import logging
import threading
import re
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.dataset as ds
from pyarrow import fs
from retrying import retry
from tquant.logger import setup_logging

setup_logging()
logger = logging.getLogger("quant_info")

StorageConfig = {
    "T+0": {"catalog_type": 2, "remark": "T+0高频因子", "parent_id": 0, "status": 1},
    "Alpha": {"catalog_type": 1, "remark": "Alpha非高频因子", "parent_id": 0, "status": 1}
}


class FactorData():
    def __init__(self):
        # 多个数据源
        self.dml_xquant = None
        self.base_save_path = '/app/mount/project_data/'
        self.userAccount = "013150"#os.environ.get("DSWMAP_username")
        self.library_info = None
        self.__sql_connect = None
        self.pa_types = {'double': pa.float64(), 'string': pa.string()}
        self.__init_folder()

    def __init_folder(self):
        low_fre_path = os.path.join(self.base_save_path, 'low_fre')
        high_fre_path = os.path.join(self.base_save_path, 'high_fre')
        if not os.path.exists(low_fre_path):
            os.makedirs(low_fre_path)
        if not os.path.exists(high_fre_path):
            os.makedirs(high_fre_path)

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

    def __set_library_info(self):
        if not self.library_info:
            self.library_info = self.__get_library_info()

    def __get_library_info(self):
        low_fre_libraries = {}
        high_fre_libraries = {}
        library_types = {}
        low_fre_path = os.path.join(self.base_save_path, 'low_fre')
        high_fre_path = os.path.join(self.base_save_path, 'high_fre')
        libraries = self.__get_all_factors()
        for lib in os.listdir(low_fre_path):
            if libraries.get(lib):
                low_fre_libraries[lib] = libraries[lib]
            library_types[lib] = 'low_fre'
        for lib in os.listdir(high_fre_path):
            if libraries.get(lib):
                high_fre_libraries[lib] = libraries[lib]
            library_types[lib] = 'high_fre'
        return {'low_fre': low_fre_libraries,
                'high_fre': high_fre_libraries,
                'library_types': library_types}

    def __set_dml_xquant(self):
        if not self.dml_xquant:
            self.dml_xquant = DML_mysql('xquant')

    def __set_sql_connect(self):
        if not self.__sql_connect or not self.__sql_connect.open:
            self.__sql_connect = sql_connect('xquant')

    @retry(stop_max_attempt_number=5, wait_fixed=2000)
    def __add_lock_high_factor(self, owner, nas_folder_name, security):
        def __select_lock(lock_key):
            select_lock_sql = """
                select lock_key, owner, create_time, expire_seconds
                from lock_distributed
                where lock_key = "{}" 
            """.format(lock_key)
            result = pd.read_sql(select_lock_sql, self.__sql_connect)
            return result

        def __add_lock(cur, lock_key, developer, owner):
            insert_lock_sql = """
                insert into lock_distributed (lock_key, developer, owner, expire_seconds)
                value ("{}", "{}", "{}", 60*3)
            """.format(lock_key, developer, owner)
            try:
                cur.execute(insert_lock_sql)
                self.__sql_connect.commit()
            except:
                self.__sql_connect.rollback()
                trace = traceback.print_exc()
                raise Exception('高频因子锁插入失败:{}'.format(trace))

        def __update_lock(cur, owner, lock_key, developer):
            new_lock_key = '{}_{}'.format(lock_key, owner)
            update_lock_sql = """
                update lock_distributed
                set lock_key="{}", is_timeout=1, is_concurrent=1
                where lock_key = "{}"
            """.format(new_lock_key, lock_key)
            insert_lock_sql = """
                insert into lock_distributed (lock_key, developer, owner, expire_seconds)
                value ("{}", "{}", "{}", 60*3)
            """.format(lock_key, developer, owner)
            try:
                cur.execute(update_lock_sql)
                cur.execute(insert_lock_sql)
                self.__sql_connect.commit()
            except:
                self.__sql_connect.rollback()
                trace = traceback.print_exc()
                raise Exception('高频因子锁修改失败:{}'.format(trace))

        logger.debug('{} __add_lock_high_factor {}'.format(owner, time.time()))
        self.__set_sql_connect()
        developer = get_userAccount()
        lock_key = '{}_{}'.format(nas_folder_name, security)
        cur = self.__sql_connect.cursor()
        while True:
            result = __select_lock(lock_key)
            if len(result) == 0:
                try:
                    __add_lock(cur, lock_key, developer, owner)
                    break
                except Exception as e:
                    raise e
            else:
                lock = result.iloc[0]
                now = datetime.datetime.now()
                is_timeout = True if now > lock[
                    'create_time'] + datetime.timedelta(
                    seconds=int(lock['expire_seconds'])) else False
                if is_timeout:
                    try:
                        __update_lock(cur, owner, lock_key, developer)
                        break
                    except Exception as e:
                        raise e
            time.sleep(10)
        cur.close()
        return True

    @retry(stop_max_attempt_number=5, wait_fixed=2000)
    def __delete_lock_high_factor(self, owner, nas_folder_name, security,
                                  error=None):
        def __select_lock(owner):
            select_lock_sql = """
                select lock_key, owner, create_time, expire_seconds
                from lock_distributed
                where owner = "{}" 
            """.format(owner)
            result = pd.read_sql(select_lock_sql, self.__sql_connect)
            return result

        def __update_lock(cur, owner, lock_key, is_timeout=False,
                          is_exception=False, error=None):
            new_lock_key = '{}_{}'.format(lock_key, owner)
            update_lock_sql = """
                update lock_distributed
                set lock_key="{}", is_finished=1
            """.format(new_lock_key)
            if is_timeout:
                update_lock_sql += ', is_timeout=1'
            if is_exception:
                update_lock_sql += ', is_exception=1, exception="{}"'.format(
                    error)
            update_lock_sql += ' where owner = "{}"'.format(owner)
            try:
                cur.execute(update_lock_sql)
                self.__sql_connect.commit()
            except:
                self.__sql_connect.rollback()
                trace = traceback.print_exc()
                raise Exception('高频因子锁修改失败:{}'.format(trace))

        def __delete_lock(cur, owner):
            delete_lock_sql = """
                delete from lock_distributed 
                where owner = "{}" 
            """.format(owner)
            try:
                cur.execute(delete_lock_sql)
                self.__sql_connect.commit()
            except:
                self.__sql_connect.rollback()
                trace = traceback.print_exc()
                raise Exception('高频因子锁删除失败:{}'.format(trace))

        logger.debug('{} __delete_lock_high_factor {}'.format(owner, time.time()))
        self.__set_sql_connect()
        lock_key = '{}_{}'.format(nas_folder_name, security)
        cur = self.__sql_connect.cursor()
        result = __select_lock(owner)
        if len(result) == 0:
            return
        lock = result.iloc[0]
        now = datetime.datetime.now()
        is_timeout = True if now > lock['create_time'] + datetime.timedelta(
            seconds=int(lock['expire_seconds'])) else False
        is_exception = True if error else False
        if is_exception or is_timeout:
            try:
                __update_lock(cur, owner, lock_key, is_timeout, is_exception,
                              error)
            except Exception as e:
                raise e
        else:
            try:
                __delete_lock(cur, owner)
            except Exception as e:
                raise e
        cur.close()
        return True

    def __get_all_factors(self):
        conn_name = str(int(time.time())) + str(threading.get_ident())
        sql = "select factor, library_name, col, factor_type from personal_factors where user_account='{}'".format(self.userAccount)
        self.__set_dml_xquant()
        result = self.dml_xquant.getAllByPandas(conn_name, sql)
        self.dml_xquant.close(conn_name)
        library_factors = {}
        for i, row in result.iterrows():
            if row['factor'] in ['MDDate', 'Factor']:
                continue
            if not library_factors.get(row['library_name']):
                library_factors[row['library_name']] = {}
            library_factors[row['library_name']][row['factor']] = {'col': str(row['col']), 'factor_type': row['factor_type']}
        return library_factors

    def create_factor_library(self, library_name, library_type):
        if not library_type in StorageConfig.keys():
            raise Exception("library_type 设置错误！请重新设置！目前只支持T+0和Alpha!")
        if not self.__naming_specification(library_name):
            raise Exception("library_name 命名不规范！请以字母开头且只能包含字母,数字和下划线！")
        # 得到所有库名
        self.__set_library_info()
        if library_type == 'Alpha':
            library_type = 'low_fre'
        else:
            library_type = 'high_fre'
        if library_name in self.library_info['library_types']:
            raise Exception("The library name already exists:该库名已存在！请重新输入！")
        # 创建文件夹
        lib_path = os.path.join(self.base_save_path, library_type)
        library_path = os.path.join(lib_path, library_name)
        if os.path.exists(library_path):
            raise Exception("因子库{}已存在！请重新输入！".format(library_path))
        os.makedirs(library_path)
        # 更新库信息
        self.library_info[library_type][library_name] = {}
        self.library_info['library_types'][library_name] = library_type
        return True

    def add_factor(self, library_name, factor_names):
        """
        向library_name的因子库中增加因子
        :param library_name: 库名
        :param factor_names: 因子名列表
        :return:

        """
        if not type(factor_names) == dict:
            raise Exception("factor_names 请传入字典！")
        for factor, _ in factor_names.items():
            if factor in ['MDTime', 'MDDate', 'HTSCSecurityID']:
                raise Exception('因子不允许以{}命名'.format(factor))
            if not self.__naming_specification(factor):
                raise Exception("%s因子命名不规范！" % str(factor))
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_library_info()
        library_type = self.library_info['library_types'].get(library_name)
        if not library_type:
            raise Exception(
                "library_name doesn't exists! %s不存在！" % str(library_name))
        # 得到该库所有因子名
        library_info = self.library_info[library_type].get(library_name)
        if library_info:
            factor_symbols = list(library_info.keys())
        else:
            if self.__library_occupied(library_name):
                raise Exception('没有访问因子库{}的权限'.format(library_name))
            factor_symbols = []
            self.library_info[library_type][library_name] = {}
        for factor_name in factor_names:
            if factor_name in factor_symbols:
                raise Exception(
                    "%s在%s库中已存在！" % (factor_name, library_name))
        for factor_name, factor_type in factor_names.items():
            if factor_type == 'float':
                factor_type = 'double'
            if factor_type not in ['string', 'double']:
                raise Exception('因子类型必须为string或double')
            result = self.__update_factor(factor_name, factor_type, library_name, library_type)
            # 更新权限文件
            self.library_info[library_type][library_name][factor_name] = {'col': result['col'], 'factor_type': result['factor_type']}
        return True

    def __library_occupied(self, library_name):
        # 有别的用户在该库创建因子，则该用户无法创建新因子
        conn_name = str(int(time.time())) + str(threading.get_ident())
        self.__set_dml_xquant()
        sql = "select factor from personal_factors where library_name='{}' and user_account != '{}'".format(library_name, self.userAccount)
        result = self.dml_xquant.getAllByPandas(conn_name, sql)
        self.dml_xquant.close(conn_name)
        if not result.empty:
            return True
        return False

    def __update_factor(self, factor_name, factor_type, library_name, library_type):
        conn_name = str(int(time.time())) + str(threading.get_ident())
        self.__set_dml_xquant()
        sql = "select factor, col from personal_factors where library_name='{}'".format(
            library_name)
        result = self.dml_xquant.getAllByPandas(conn_name, sql)

        if len(result) == 0:
            max_col = 0
            add_col = 0
        else:
            if len(result[result['factor'] == factor_name]) != 0:
                logger.debug('该因子库中已有{}'.format(factor_name))
                return True
            max_col = result['col'].max()
            add_col = max_col + 1
        if max_col >= 199 and library_type == 'high_fre':
            raise Exception("高频因子库最多存储200个因子，因子{}将超出总因子数！".format(factor_name))
        insert_sql = 'insert into personal_factors (factor, library_name, col, factor_type, user_account) values ("{}","{}",{},"{}","{}")'.format(
            factor_name, library_name, add_col, factor_type, self.userAccount)
        try:
            self.dml_xquant.execute(conn_name, insert_sql)
            self.dml_xquant.commit(conn_name)
        except:
            self.dml_xquant.rollback(conn_name)
            raise Exception('{}因子插入失败'.format(factor_name))
        finally:
            self.dml_xquant.close(conn_name)
        return {'factor': factor_name, 'library_name': library_name, 'col': str(add_col), 'factor_type': factor_type}

    def __get_factors(self, library_name):
        # 获取因子列表
        conn_name = str(int(time.time())) + str(threading.get_ident())
        self.__set_dml_xquant()
        sql = "select factor, col, factor_type from personal_factors where library_name='{}'".format(library_name)
        result = self.dml_xquant.getAllByPandas(conn_name, sql)
        self.dml_xquant.close(conn_name)
        factor_infos = {}
        for i, row in result.iterrows():
            if row['factor'] in ['MDDate', 'Factor']:
                continue
            factor_infos[row['factor']] = {'col': str(row['col']), 'factor_type': row['factor_type']}
        return factor_infos

    def get_library_info(self):
        """
        得到该用户所有的有权限访问的库信息和该库下面的所有因子信息
        :return:
        """
        self.__set_library_info()
        library_infos = {}
        for lib, lib_data in self.library_info['low_fre'].items():
            library_infos[lib] = [factor for factor, _ in lib_data.items()]
        for lib, lib_data in self.library_info['high_fre'].items():
            library_infos[lib] = [factor for factor, _ in lib_data.items()]

        return library_infos

    def get_library_securities(self):
        """
        得到该用户所有的有权限访问的库中的标的
        :return:
        """
        self.__set_library_info()
        library_infos = {}
        for lib, _ in self.library_info['high_fre'].items():
            library_path = os.path.join(self.base_save_path, 'high_fre', lib)
            file_list = os.listdir(library_path)
            library_infos[lib] = [file_name.split('=')[1] for file_name in file_list]
        return library_infos

    def update_factor_value_by_factor(self, library_name, factor_values, factor, check_olddata=False,
                                      allow_merge_olddata=True):
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_library_info()
        library_type = self.library_info['library_types'].get(library_name)
        if not library_type:
            raise Exception(
                "library_name doesn't exist: %s因子库不存在！" % library_name)
        if not library_type == 'low_fre':
            raise Exception('update_factor_value_by_factor方法仅支持低频因子数据更新！')
        library_info = self.library_info[library_type].get(library_name)
        if not library_info:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))
        factor_info = library_info.get(factor)
        if not factor_info:
            raise Exception('因子库{}中没有因子{},请先添加因子'.format(library_name, factor))
        factor_type = factor_info['factor_type']

        for d in factor_values.index.get_level_values('MDDate').unique():
            if not is_valid_date(d, date_type='year_month_day'):
                raise Exception(
                    "【mddate_list】-{0}的格式不符合要求，日期类型为YYYYMMDD格式，如 '20200330'".format(
                        d))

        if list(factor_values.index.names) != ['MDDate', 'HTSCSecurityID']:
            raise Exception('请将MDDate与HTSCSecurityID设为multiindex')

        if not factor_values.index.is_unique:
            raise Exception('索引不唯一')

        value_type = pa.Schema.from_pandas(factor_values).field('Value')
        if factor_type not in str(value_type.type):
            raise Exception(
                '因子类型应为{}, 实际为{}'.format(factor_type, str(value_type.type)))

        result_df = pd.DataFrame()
        low_fre_save_path = os.path.join(self.base_save_path, 'low_fre')
        library_path = os.path.join(low_fre_save_path, library_name)
        factor_name_path = os.path.join(library_path, 'Factor={}'.format(factor))
        # 是否检查旧数据
        if check_olddata:
            if os.path.exists(factor_name_path):
                dates = factor_values.index.get_level_values('MDDate').unique()
                schemas = pa.schema([("MDDate", pa.string()), ("HTSCSecurityID", pa.string()), value_type])
                result_df = self.__read_factor_data(library_path, factor, dates, schemas)
                if not allow_merge_olddata:
                    result_df_count = result_df.groupby('MDDate').count()
                    factor_values_count = factor_values.groupby('MDDate').count()
                    result_df_dates = result_df_count.index.tolist()
                    not_match_dates = []
                    for date in result_df_dates:
                        if result_df_count.loc[date]['Value'] != factor_values_count.loc[date]['Value']:
                            not_match_dates.append(date)
                    if not_match_dates:
                        raise Exception('以下日期:{} 新数据与原数据Security行数不一致'.format(not_match_dates))
        if result_df.empty:
            # 因子不存在，创建新dataframe
            result_df = pd.DataFrame(columns=['MDDate', 'HTSCSecurityID', 'Value'])

        factor_values_tmp = factor_values.reset_index(inplace=False)
        if result_df.empty:
            for col in result_df.columns:
                result_df[col] = result_df[col].astype(factor_values_tmp[col].dtype)
        result_df = pd.merge(result_df, factor_values_tmp, how='outer', on=['MDDate', 'HTSCSecurityID'], indicator=True)
        left_only = result_df[result_df['_merge'] == 'left_only']
        result_df.loc[left_only.index, 'Value_y'] = left_only['Value_x']
        result_df['Value'] = result_df['Value_y']
        result_df = result_df[['Value', 'MDDate', 'HTSCSecurityID']]
        result_df['Factor'] = factor
        table = pa.Table.from_pandas(result_df, preserve_index=False,
                                     nthreads=16)
        pq.write_to_dataset(table, library_path,
                            partition_cols=['Factor', 'MDDate'],
                            partition_filename_cb=lambda x: '-'.join(x) + '.parquet')
        return True

    def update_factor_value_by_security(self, library_name, factor_values, security, check_olddata=True):
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_library_info()
        owner = str(uuid.uuid4())
        library_type = self.library_info['library_types'].get(library_name)
        if not library_type:
            raise Exception(
                "library_name doesn't exist: %s因子库不存在！" % library_name)
        if not library_type == 'high_fre':
            raise Exception('update_factor_value_by_security方法仅支持高频因子数据更新！')
        factors = self.library_info[library_type].get(library_name)
        if not factors:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))

        if 'MDDate' not in factor_values:
            raise Exception('factor_values中未包含MDDate字段')
        if 'MDTime' not in factor_values:
            raise Exception('factor_values中未包含MDTime字段')
        factor_values[['MDDate', 'MDTime']] = factor_values[['MDDate', 'MDTime']].astype('str')
        for d in factor_values.MDDate.unique():
            if not is_valid_date(d, date_type='year_month_day'):
                raise Exception(
                    "【mddate_list】-{0}的格式不符合要求，日期类型为YYYYMMDD格式，如 '20200330'".format(
                        d))
        if False in factor_values['MDTime'].map(lambda x: len(x) == 9).values:
            raise Exception('MDTime格式错误，请传入9位字符串，如092500000')

        df_factors = list(set(factor_values.columns.tolist()) - {'MDDate', 'MDTime'})

        factor_values_schema = pa.Schema.from_pandas(factor_values[df_factors])
        factor_cols = {}
        for factor_name in df_factors:
            factor_data = factors.get(factor_name)
            if not factor_data:
                raise Exception('因子库{}中没有因子{},请先添加因子'.format(library_name, factor_name))

            # 判断因子类型是否正确
            value_type = factor_values_schema.field(factor_name)
            if factor_data['factor_type'] not in str(value_type.type):
                value_type = factor_values_schema.field(factor_name)
                raise Exception('因子{}类型应为{}, 实际为{}'.format(factor_name,
                                                           factor_data[
                                                               'factor_type'],
                                                           str(
                                                               value_type.type)))
            factor_cols[factor_name] = str(factor_data['col'])

        high_fre_save_path = os.path.join(self.base_save_path, 'high_fre')
        library_path = os.path.join(high_fre_save_path, library_name)
        security_name_path = os.path.join(library_path, 'HTSCSecurityID={}'.format(security))

        # 是否存在旧数据
        result_df = pd.DataFrame()
        if os.path.exists(security_name_path):
            dates = factor_values.MDDate.unique()
            result_df = self.__read_security_data_by_concat(library_path, security, dates)
            # 是否检查旧数据
            if check_olddata and not result_df.empty:
                result_df_count = result_df.groupby('MDDate').count()
                factor_values_count = factor_values.groupby('MDDate').count()
                result_df_dates = result_df_count.index.tolist()
                not_match_dates = []
                for date in result_df_dates:
                    if result_df_count.loc[date]['MDTime'] != factor_values_count.loc[date]['MDTime']:
                        not_match_dates.append(date)
                if not_match_dates:
                    raise Exception('以下日期:{} 新数据与原数据MDTime行数不一致'.format(not_match_dates))

        if result_df.empty:
            result_df = pd.DataFrame(np.full((len(factor_values.index), 200), np.NAN),
                                     columns=[str(i) for i in range(200)])
            result_df[["MDDate", "MDTime"]] = factor_values[["MDDate", "MDTime"]]

        factor_values_tmp = factor_values.set_index(['MDDate', 'MDTime'], drop=False, inplace=False)

        factor_values_tmp.rename(columns=factor_cols, inplace=True)
        result_df.set_index(['MDDate', 'MDTime'], drop=False, inplace=True)
        result_df.drop(factor_values_tmp.columns.tolist(), axis=1, inplace=True)
        result_df = pd.concat([result_df, factor_values_tmp], axis=1)
        result_df['HTSCSecurityID'] = security
        table = pa.Table.from_pandas(result_df, preserve_index=False, nthreads=16)
        try:
            self.__add_lock_high_factor(owner, library_name, security)
            error = None
            try:
                pq.write_to_dataset(table, library_path,
                                    partition_cols=['HTSCSecurityID',
                                                    'MDDate'],
                                    partition_filename_cb=lambda x: '-'.join(
                                        x) + '.parquet')
            except Exception as e:
                error = str(e)
            self.__delete_lock_high_factor(owner, library_name, security,
                                           error)
        except Exception as e:
            raise e
        finally:
            try:
                self.__sql_connect.close()
            except Exception as e:
                raise e
        return True

    def get_factor_value(self, library_name, mddate_list, security_list=None, factor_list=None, sort=False, in_dataframe=False):
        """
        查询指定因子库中的因子值
        :param library_name: 因子库名
        :param mddate_list: list, 必传，高频传入string（单个日期）
        :param security_list: list, 高频因子必传，低频选传，低频默认为因子库全部标的
        :param factor_list: list, 低频因子必传，高频选传，高频默认为因子库中全部因子
        :return:

        """
        # 查找所有库名，判断用户输入的库名是否存在
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        library_info = self.library_info[library_type].get(library_name)
        if not library_info:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))
        if type(mddate_list) != list:
            raise Exception('mddate_list类型为list')
        if len(mddate_list) == 0:
            raise Exception('请传入mddate_list')
        mddate_list = list(set(mddate_list))
        for i in mddate_list:
            if not is_valid_date(i, date_type='year_month_day'):
                raise Exception(
                    "【mddate_list】-{0}的格式不符合要求，日期类型为YYYYMMDD格式，如 '20200330'".format(
                        i))
        if library_type == 'low_fre':
            # 非高频操作
            if not factor_list:
                raise Exception('低频因子按factor独立分区存储，必须传入factor_list')
            result_df = self.__get_low_frequency_factor_value(library_name, mddate_list, factor_list, security_list,
                                                              sort, in_dataframe)
        elif library_type == 'high_fre':
            #  高频操作
            if not security_list:
                raise Exception('高频因子按security独立分区存储，必须传入security_list参数')
            result_df = self.__get_high_frequency_factor_value(library_name, mddate_list, security_list,
                                                               factor_list, sort)
        else:
            raise Exception("仅支持低频和高频两类因子！")
        return result_df

    def __get_low_frequency_factor_value(self, library_name, mddate_list,
                                         factor_list, security_list=None,
                                         sort=False, in_dataframe=False):
        low_fre_path = os.path.join(self.base_save_path, 'low_fre')
        library_path = os.path.join(low_fre_path, library_name)
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        library_info = self.library_info[library_type][library_name]
        factor_dict = {}
        for factor in factor_list:
            factor_type = library_info[factor]['factor_type']
            if factor_type not in self.pa_types:
                raise Exception(
                    '{}类型不在double,string'.format(factor_type))
            schemas = pa.schema(
                [("MDDate", pa.string()), ("HTSCSecurityID", pa.string()),
                 ('Value', self.pa_types[factor_type])])
            df = self.__read_factor_data(library_path, factor, mddate_list,
                                         schemas)
            df = df.reindex(columns=['MDDate', 'HTSCSecurityID', 'Value'])
            if security_list:
                df = df[df['HTSCSecurityID'].isin(security_list)]
            if sort:
                df.sort_values(['MDDate'], inplace=True)
            df.set_index(['MDDate', 'HTSCSecurityID'], inplace=True)
            if not in_dataframe:
                df = df['Value'].unstack(level='HTSCSecurityID')
                del df.columns.name
            factor_dict[factor] = df

        if not in_dataframe:
            result = factor_dict
        else:
            # 以dataframe形式返回
            dfs = []
            for factor, df in factor_dict.items():
                df.rename({'Value': factor}, axis=1, inplace=True)
                dfs.append(df)
            result = pd.concat(dfs, axis=1)
        return result

    def __get_high_frequency_factor_value(self, library_name, mddate_list,
                                          security_list, factor_list=None,
                                          sort=False):
        high_fre_path = os.path.join(self.base_save_path, 'high_fre')
        library_path = os.path.join(high_fre_path, library_name)
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        library_info = self.library_info[library_type][library_name]
        unset_columns = []
        factors = {}
        result_dict = {}

        if factor_list:
            for factor_name in factor_list:
                if factor_name in library_info:
                    factors[factor_name] = library_info[factor_name]
                else:
                    unset_columns.append(factor_name)
        else:
            factors = library_info

        if unset_columns:
            raise Exception('以下factor:{} 在因子库中不存在'.format(unset_columns))

        include_not_double = False
        factor_datas = {'cols': [], 'col_factors': {}, 'col_schemas': []}
        for factor_name, factor_data in factors.items():
            if factor_data['factor_type'] not in self.pa_types:
                raise Exception('{}类型不在double,string'.format(factor_data['factor_type']))
            factor_datas['cols'].append(factor_data['col'])
            factor_datas['col_factors'][factor_data['col']] = factor_name
            factor_datas['col_schemas'].append((factor_data['col'], self.pa_types[factor_data['factor_type']]))
            if factor_data['factor_type'] != 'double':
                include_not_double = True

        schemas = pa.schema(
            factor_datas['col_schemas'] + [("MDDate", pa.string()),
                                           ("MDTime", pa.string())])
        for security in security_list:
            if not include_not_double:
                df = self.__read_security_data(library_path, security, mddate_list,
                                               schemas)
            else:
                df = self.__read_security_data_by_concat(library_path, security,
                                                         mddate_list,
                                                         ['MDTime'] + factor_datas[
                                                             'cols'])
            if not df.empty:
                df = df.reindex(columns=['MDDate', 'MDTime'] + factor_datas[
                                                             'cols'])
                df.rename(columns=factor_datas['col_factors'], inplace=True)
                if sort:
                    df.sort_values(['MDDate', 'MDTime'], inplace=True)
            else:
                df = pd.DataFrame()
            result_dict[security] = df

        return result_dict

    @retry(stop_max_attempt_number=4, wait_fixed=2000)
    def __read_factor_data(self, library_path, factor, mddate_list, schemas):
        factor_path_list = []
        date_list = []
        factor_name_path = os.path.join(library_path,
                                        'Factor={}'.format(factor))
        for mddate in mddate_list:
            factor_mdate_path = os.path.join(factor_name_path,
                                             'MDDate={}'.format(mddate))
            factor_path = os.path.join(factor_mdate_path,
                                       '{}-{}.parquet'.format(factor, mddate))
            if not os.path.exists(factor_path):
                logger.debug('{}路径不存在'.format(factor_path))
                continue
            factor_path_list.append(
                'MDDate={0}/{1}-{0}.parquet'.format(mddate, factor))
            date_list.append(mddate)
        if date_list:
            partitions = [ds.field("MDDate") == date for date in date_list]
            dataset = ds.FileSystemDataset.from_paths(factor_path_list,
                                                      schema=schemas,
                                                      format=ds.ParquetFileFormat(),
                                                      filesystem=fs.SubTreeFileSystem(
                                                          factor_name_path,
                                                          fs.LocalFileSystem()),
                                                      partitions=partitions)
            df = dataset.to_table().to_pandas()
        else:
            df = pd.DataFrame()
        return df

    @retry(stop_max_attempt_number=4, wait_fixed=2000)
    def __read_security_data(self, library_path, security, mddate_list, schemas):
        security_path_list = []
        date_list = []
        security_name_path = os.path.join(library_path,
                                          'HTSCSecurityID={}'.format(security))
        for mddate in mddate_list:
            security_mdate_path = os.path.join(security_name_path,
                                               'MDDate={}'.format(mddate))
            factor_path = os.path.join(security_mdate_path,
                                       '{}-{}.parquet'.format(security, mddate))
            if not os.path.exists(factor_path):
                logger.debug('{}路径不存在'.format(factor_path))
                continue
            security_path_list.append(
                'MDDate={0}/{1}-{0}.parquet'.format(mddate, security))
            date_list.append(mddate)
        if date_list:
            partitions = [ds.field("MDDate") == date for date in date_list]
            dataset = ds.FileSystemDataset.from_paths(security_path_list,
                                                      schema=schemas,
                                                      format=ds.ParquetFileFormat(),
                                                      filesystem=fs.SubTreeFileSystem(
                                                          security_name_path,
                                                          fs.LocalFileSystem()),
                                                      partitions=partitions)
            df = dataset.to_table().to_pandas()
        else:
            df = pd.DataFrame()
        return df

    @retry(stop_max_attempt_number=4, wait_fixed=2000)
    def __read_security_data_by_concat(self, library_path, security,
                                       mddate_list, cols=None):
        security_df_list = []
        security_name_path = os.path.join(library_path,
                                          'HTSCSecurityID={}'.format(security))
        for mddate in mddate_list:
            security_mdate_path = os.path.join(security_name_path,
                                               'MDDate={}'.format(mddate))
            factor_path = os.path.join(security_mdate_path,
                                       '{}-{}.parquet'.format(security,
                                                              mddate))
            if not os.path.exists(factor_path):
                logger.debug('{}路径不存在'.format(factor_path))
                continue
            if not cols:
                security_df = pq.read_table(factor_path).to_pandas()
            else:
                security_df = pq.read_table(factor_path,
                                            columns=cols).to_pandas()
            security_df['MDDate'] = mddate
            security_df_list.append(security_df)
        if security_df_list:
            df = pd.concat(security_df_list, ignore_index=True)
        else:
            df = pd.DataFrame()
        return df

    def search_by_stock_date(self, library_name, stock, mddate, factor_list):
        """
        指定因子库名、股票、日期，查询在指定因子列表中哪些因子有数据
        :param library_name: string:因子库名
        :param stock: string:股票
        :param mddate: string:日期
        :param factor_list: list:因子名列表
        :return:
        """
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        if library_type != 'high_fre':
            raise Exception('该接口只在高频因子库使用')
        library_info = self.library_info[library_type].get(library_name)
        if not library_info:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))
        df = self.__get_high_frequency_factor_value(library_name, [mddate], [stock],
                                                    factor_list=factor_list)[stock]
        columns_na_dict = df.isna().all().to_dict()
        column_list = [col for col, is_na in columns_na_dict.items() if
                       not is_na]
        exist_factors = list(set(factor_list) & set(column_list))
        return exist_factors

    def search_by_stock_factor(self, library_name, stock, factor, mddate_list):
        """
        按因子库名、股票、因子查询指定日期列表中哪些日期有数据
        :param library_name: string:因子库名
        :param stock: string:股票
        :param factor: string:因子
        :param mddate_list: list:日期列表
        :return:
        """
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        if library_type != 'high_fre':
            raise Exception('该接口只在高频因子库使用')
        library_info = self.library_info[library_type].get(library_name)
        if not library_info:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))
        df = self.__get_high_frequency_factor_value(library_name, mddate_list, [stock],
                                                    factor_list=[factor])[stock]
        df.set_index('MDDate', inplace=True)
        date_list = df[df[factor].notna()].index.tolist()
        exist_dates = list(set(date_list) & set(mddate_list))
        return exist_dates

    def search_by_stock(self, library_name, stock, mddate_list):
        """
        按因子库名、股票查询指定日期列表中哪些天有数据
        :param library_name: string:因子库名
        :param stock: string:股票
        :param mddate_list: list:日期列表
        :return:
        """
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        if library_type != 'high_fre':
            raise Exception('该接口只在高频因子库使用')
        library_info = self.library_info[library_type].get(library_name)
        if not library_info:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))
        high_fre_path = os.path.join(self.base_save_path, 'high_fre')
        library_path = os.path.join(high_fre_path, library_name)
        security_name_path = os.path.join(library_path,
                                          'HTSCSecurityID={}'.format(stock))
        exist_date_list = []
        for mddate in mddate_list:
            security_mdate_path = os.path.join(security_name_path,
                                               'MDDate={}'.format(mddate))
            factor_path = os.path.join(security_mdate_path,
                                       '{}-{}.parquet'.format(stock,
                                                              mddate))
            if os.path.exists(factor_path):
                exist_date_list.append(mddate)
        return exist_date_list

    def search_by_date(self, library_name, mddate, stock_list):
        """
        按因子库名、日期查询指定股票列表中哪些股票有数据
        :param library_name: string:因子库名
        :param mddate: string:股票
        :param stock_list: list:股票列表
        :return:
        """
        self.__set_library_info()
        library_type = self.library_info['library_types'][library_name]
        if library_type != 'high_fre':
            raise Exception('该接口只在高频因子库使用')
        library_info = self.library_info[library_type].get(library_name)
        if not library_info:
            raise Exception('该用户没有权限访问因子库{}'.format(library_name))
        high_fre_path = os.path.join(self.base_save_path, 'high_fre')
        library_path = os.path.join(high_fre_path, library_name)
        exist_stock_list = []
        for stock in stock_list:
            security_name_path = os.path.join(library_path,
                                              'HTSCSecurityID={}'.format(
                                                  stock))
            security_mdate_path = os.path.join(security_name_path,
                                               'MDDate={}'.format(mddate))
            factor_path = os.path.join(security_mdate_path,
                                       '{}-{}.parquet'.format(stock, mddate))
            if os.path.exists(factor_path):
                exist_stock_list.append(stock)
        return exist_stock_list
