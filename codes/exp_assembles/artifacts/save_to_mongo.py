import pymongo
import os
import pandas as pd
import numpy as np
from datetime import datetime
import json
from FactorProvider.conf.DubboConf import get_userid
import inspect
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from . import utils

from xquant.setXquantEnv import xquantEnv

encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_copy.json")

with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)


# def UserEventToDB(func):
#     """
#     调用时自动记录用户行为数据
#     :param
#     :return:
#         inserted_id 插入数据库时的一个生成id
#     """
#     def _call(*args, **kw):
#         env_id = xquantEnv
#         time = datetime.now()
#         if env_id == 0:
#             __ip = ENCRYPTED_HOSTS['mongo']['test']['ip']
#             __password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['test']['ciphertext'])
#             mongo = 'mongodb://xquant_mgr:' + __password + __ip
#             database = "xquant_mgr"
#         elif env_id == 1:
#             __ip = ENCRYPTED_HOSTS['mongo']['prd']['ip']
#             __password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['prd']['ciphertext'])
#             mongo = 'mongodb://xquant_mgr:' + __password + __ip
#             database = "xquant_mgr"
#         client = pymongo.MongoClient(mongo)
#         db = client[database]
#         model_collection = db["user_event"]
#         rst = func(*args, **kw)
#         exp_id = args[1]
#         version_alias = args[2]
#         event_type = args[3]
#         params = args[6]
#         if event_type == "save_strategy_data" and 'strategy' in params \
#                 or event_type == "model_file_save" and 'singal' in params:
#             try:
#                 insert_info = {
#                     "exp_id": exp_id,
#                     "version_alias": version_alias,
#                     "event_type": event_type,
#                     "user_id": get_userid(),
#                     "operate_time": time,
#                     "params": params,
#                 }
#                 result = model_collection.insert_one(insert_info)
#                 print("存入成功")
#                 client.close()
#                 return result.inserted_id
#             except pymongo.errors.PyMongoError as e:
#                 print("Error occurred while inserting data:", e)
#                 client.close()
#         else:
#             print("固定参数与行为类型不符，请确认")
#             client.close()
#         return rst
#
#     return _call


class MongoDB:

    def __init__(self):
        self.env_id = xquantEnv
        # now = datetime.now()
        # formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        # self.time = formatted_now
        self.time = datetime.now()
        self.user_id = get_userid()
        if self.env_id == 0:
            self.__ip = ENCRYPTED_HOSTS['mongo']['test']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['test']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "xquant_mgr"
        elif self.env_id == 1:
            self.__ip = ENCRYPTED_HOSTS['mongo']['prd']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['prd']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "xquant_mgr"

    # def load_configs(self):
    #     """
    #     返回exp_params集合中所有的参数信息version_alias和原始参数
    #     :param
    #     :return:
    #         dataframe
    #     """
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["exp_params"]
    #     params = {
    #         "-": "all"
    #     }
    #     try:
    #         df = pd.DataFrame(list(model_collection.find({}, {'version_alias': 1, 'hash256': 1, 'params_jsonstr': 1,
    #                                                           'params_jsonstr_extra': 1})))
    #         self.user_event_todb("-",
    #                              "-", inspect.currentframe().f_code.co_name,
    #                              "exp_params", "load", params)
    #         print("success")
    #         client.close()
    #         return df
    #     except pymongo.errors.PyMongoError as e:
    #         print("Error occurred while finding data:", e)
    #         client.close()

    # def load_user_event(self, exp_id):
    #     """
    #     返回user_event集合中实验id对应的所有数据
    #     :param
    #         exp_id  实验id
    #     :return:
    #         dataframe
    #     """
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["user_event"]
    #     params = {
    #         'exp_id': exp_id,
    #     }
    #     # 投影，用来设置返回的查询中包含哪些字段
    #     projection = {
    #         'exp_id': 1,
    #         'user_id': 1,
    #         'event_type': 1,
    #         'create_time': 1,
    #         'params': 1,
    #     }
    #     try:
    #         df = pd.DataFrame(list(model_collection.find({'exp_id': exp_id}, projection)))
    #         self.user_event_todb(exp_id,
    #                              "-", inspect.currentframe().f_code.co_name,
    #                              "user_event", "load", params)
    #         print("success")
    #         client.close()
    #         return df
    #     except pymongo.errors.PyMongoError as e:
    #         print("Error occurred while finding data:", e)
    #         client.close()

    # def load_signal_evaluation_data(self, exp_id, symbol):
    #     """
    #     返回signal_evaluation_data集合中实验id和标的对应的所有数据
    #     :param
    #         exp_id  实验id
    #         symbol  标的
    #     :return:
    #         dataframe
    #     """
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["signal_evaluation_data"]
    #     params = {
    #         'exp_id': exp_id,
    #         'symbol': symbol,
    #     }
    #     projection = {
    #         'exp_id': 1,
    #         'symbol': 1,
    #         'evaluation_type': 1,
    #         'condition': 1,
    #     }
    #     try:
    #         df = pd.DataFrame(list(model_collection.find({'symbol': symbol, 'exp_id': exp_id})))
    #         self.user_event_todb(exp_id,
    #                              "-", inspect.currentframe().f_code.co_name,
    #                              "signal_evaluation_data", "load", params)
    #         print("success")
    #         client.close()
    #         return df
    #     except pymongo.errors.PyMongoError as e:
    #         print("Error occurred while finding data:", e)
    #         client.close()
    #
    # def load_backtest_evaluation_data(self, exp_id, symbol):
    #     """
    #     返回backtest_evaluation_data集合中实验id和标的对应的所有数据
    #     :param
    #         exp_id  实验id
    #         symbol  标的
    #     :return:
    #         dataframe
    #     """
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["backtest_evaluation_data"]
    #     params = {
    #         'exp_id': exp_id,
    #         'symbol': symbol,
    #     }
    #     projection = {
    #         'exp_id': 1,
    #         'symbol': 1,
    #         'backtest_evaluation_type': 1,
    #         'condition': 1,
    #     }
    #     try:
    #         df = pd.DataFrame(list(model_collection.find({'symbol': symbol, 'exp_id': exp_id})))
    #         self.user_event_todb(exp_id,
    #                              "-", inspect.currentframe().f_code.co_name,
    #                              "backtest_evaluation_data", "load", params)
    #         print("success")
    #         client.close()
    #         return df
    #     except pymongo.errors.PyMongoError as e:
    #         print("Error occurred while finding data:", e)
    #         client.close()

    def load_factor_evaluation_data(self, factor_name_list, symbol_list, label_list, start_time, end_time):
        """
        返回factor_evaluation_data集合中和查询条件对应的所有数据
        :param
            factor_name_list  因子名称列表
            symbol_list       标的列表
            label_list        标签列表
            start_time        查询开始时间
            end_time          查询结束时间
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        collection = db["factor_evaluation_data_new"]
        date_start = datetime.strptime(start_time, "%Y%m%d")
        date_end = datetime.strptime(end_time, "%Y%m%d")
        params = {
            "symbol_list": symbol_list,
            "factor_name_list": factor_name_list,
            "label_list": label_list,
            "date_start": date_start,
            "date_end": date_end
        }
        query = {
            'index.symbol': {'$in': symbol_list},
            'index.factor_name': {'$in': factor_name_list},
            'index.label': {'$in': label_list},
            'index.MDDatetime': {'$gte': date_start, '$lt': date_end}
        }
        try:
            df = pd.DataFrame(list(collection.find(query)))
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "factor_evaluation_data", "load", params)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def exp_params_todb(self, exp_id, version_alias, hash256, exp_type, params_jsonstr,
                        params_jsonstr_extra=None):
        """
        将一次实验对应的模型数据存入mongodb中
        :param
            version_alias   版本号，唯一	string
            hash256     与版本号对应，唯一	int
            type	        参数类型    string
            params_jsonstr	原始参数，已剔除value过长的key    jsonstring
            user_id	        用户id    string
            create_time	            string
            params_jsonstr_extra	原始参数中过长的list（元素个数超过10个），非必传
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["exp_params_new"]
        create_time = self.time
        params = {
            "exp_type": exp_type
        }
        if params_jsonstr_extra:
            insert_info = {
                "version_alias": version_alias,
                "hash256": hash256,
                "exp_type": exp_type,
                "params_jsonstr": params_jsonstr,
                "params_jsonstr_extra": params_jsonstr_extra,
                "user_id": self.user_id,
                "create_time": create_time,
                "update_time": self.time,
            }
        else:
            insert_info = {
                "version_alias": version_alias,
                "hash256": hash256,
                "exp_type": exp_type,
                "params_jsonstr": params_jsonstr,
                "user_id": self.user_id,
                "create_time": create_time,
                "update_time": self.time,
            }
        try:
            existing_data = model_collection.find_one(
                {'version_alias': insert_info['version_alias'], 'hash256': insert_info['hash256']})
            if existing_data:
                update_info = {
                    "version_alias": version_alias,
                    "hash256": hash256,
                    "exp_type": exp_type,
                    "params_jsonstr": params_jsonstr,
                    "user_id": self.user_id,
                    "update_time": self.time,
                }
                filter = {'version_alias': version_alias, 'hash256': hash256}
                result = model_collection.update_one(filter, {'$set': update_info})
                self.user_event_todb(exp_id,
                                     version_alias, inspect.currentframe().f_code.co_name, "exp_params", "更新", params)
                print('更新成功')
                client.close()
                return result.modified_count
            else:
                # 尝试插入数据到 MongoDB 集合中
                result = model_collection.insert_one(insert_info)
                self.user_event_todb(exp_id,
                                     version_alias, inspect.currentframe().f_code.co_name, "exp_params", "插入", params)
                client.close()
                return result.inserted_id
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def user_event_todb(self, exp_id, version_alias, event_type, collection, operate, params):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["user_event_new"]
        insert_info = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "event_type": event_type,
            "user_id": self.user_id,
            "collection": collection,
            "operate": operate,
            "operate_time": self.time,
            "params": params,
        }
        #         if event_type == "save_strategy_data" and 'strategy' in params \
        #                 or event_type == "model_file_save" and 'singal' in params:
        try:
            # 尝试插入数据到 MongoDB 集合中
            result = model_collection.insert_one(insert_info)
            print("存入成功")
            client.close()
            return result.inserted_id
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def user_event_todb_get(self, exp_id, version_alias, event_type, collection, params):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["user_event_new"]
        insert_info = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "event_type": event_type,
            "user_id": self.user_id,
            "collection": collection,
            "operate": "get",
            "operate_time": self.time,
            "params": params,
        }
        #         if event_type == "save_strategy_data" and 'strategy' in params \
        #                 or event_type == "model_file_save" and 'singal' in params:
        try:
            # 尝试插入数据到 MongoDB 集合中
            result = model_collection.insert_one(insert_info)
            client.close()
            return result.inserted_id
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def signal_evaluation_data_todb(self, exp_id, version_alias, symbol, evaluation_type, condition, metrics):
        # 102条放一个数组里
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["signal_evaluation_data_new"]
        df = metrics
        df['date'] = pd.to_datetime(df['date'])
        date = df.iloc[0]['date']
        dict_from_df = df.to_dict(orient='list')
        document = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "symbol": symbol,
            "date": date,
            "evaluation_type": evaluation_type,
            "condition": condition,
            "create_time": self.time,
            # "metrics": flattened_array.tolist()
            "metrics": dict_from_df
        }
        params = {
            "symbol": symbol
        }
        existing_data = model_collection.find_one({'symbol': symbol, 'exp_id': exp_id})
        if existing_data:
            query = {'symbol': symbol, 'exp_id': exp_id}
            model_collection.delete_many(query)
            self.user_event_todb(exp_id,
                                 version_alias, inspect.currentframe().f_code.co_name,
                                 "signal_evaluation_data", "delete", params)
        try:
            # 尝试插入数据到 MongoDB 集合中
            model_collection.insert_one(document)
            self.user_event_todb(exp_id,
                                 version_alias, inspect.currentframe().f_code.co_name,
                                 "signal_evaluation_data", "insert", params)
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()
            return False

    # def backtest_evaluation_data_todb(self, exp_id, version_alias, symbol, strategy_name, strategy_params,
    # backtest_evaluation_type, condition, metrics, signal_path):
    def backtest_evaluation_data_todb(self, exp_id, version_alias, symbol, strategy_name, strategy_params,
                                      backtest_evaluation_type, condition, metrics):
        # 102条放一个数组里
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["backtest_evaluation_data_new"]
        df = metrics
        df['date'] = pd.to_datetime(df['date'])
        date = df.iloc[0]['date']
        dict_from_df = df.to_dict(orient='list')
        document = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "symbol": symbol,
            "date": date,
            "strategy_name": strategy_name,
            "strategy_params": strategy_params,
            "backtest_evaluation_type": backtest_evaluation_type,
            "condition": condition,
            "create_time": self.time,
            "metrics": dict_from_df,
            # "signal_path": signal_path
        }
        params = {
            "strategy_name": strategy_name,
        }
        existing_data = model_collection.find_one({'symbol': symbol, 'exp_id': exp_id})
        if existing_data:
            query = {'symbol': symbol, 'exp_id': exp_id}
            model_collection.delete_many(query)
            self.user_event_todb(exp_id,
                                 version_alias, inspect.currentframe().f_code.co_name,
                                 "backtest_evaluation_data", "delete", params)
        try:
            # 尝试插入数据到 MongoDB 集合中
            model_collection.insert_one(document)
            self.user_event_todb(exp_id,
                                 version_alias, inspect.currentframe().f_code.co_name,
                                 "backtest_evaluation_data", "insert", params)
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()
            return False

    def factor_evaluation_data_todb(self, factor_name, symbol, label, evaluation_df):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["factor_evaluation_data_new"]
        df = evaluation_df
        df['MDDatetime'] = pd.to_datetime(df['MDDate'])
        data_list = df.to_dict(orient='records')
        params = {
            "factor_name": factor_name,
        }
        print(data_list)
        for row in data_list:
            insert_index = {
                "factor_name": factor_name,
                "label": label,
                "symbol": symbol,
                'MDDatetime': row['MDDatetime'],
            }
            try:
                result = model_collection.insert_one({
                    "index": insert_index,
                    "factor_name": factor_name,
                    'data': row,  # 将元组转换为字典，字典的键是列的名字，值是列的值
                    "update_time": self.time,
                })
            except pymongo.errors.PyMongoError as e:
                # 如果插入过程中发生错误，打印错误信息
                print("Error occurred while inserting data:", e)
                client.close()
                return False
        self.user_event_todb("-",
                             "-", inspect.currentframe().f_code.co_name,
                             "factor_evaluation_data", "insert", params)
        print("存入成功")
        client.close()
        return True

    def factor_evaluation_data(self, trading_frequency=None, stock=None, label_name=None, factor_name=None):
        fp = FactorProvider('016869')
        data_type = None
        factor_list = None
        if trading_frequency == '1s':
            data_type = 'tick_l2p'
        if trading_frequency == '3s':
            data_type = 'enhanced_tick'
        if factor_name is not None:
            factor_list = [factor_name]
        df = fp.load_factor_analysis_res(data_type=data_type, stock=stock,
                                         label_name=label_name, factor_list=factor_list)
        column_names = df.columns.tolist()
        # 创建一个空的聚合函数字典
        agg_dict = {}
        for col in column_names:
            # 需要计算均值的列添加到聚合函数字典中
            if col not in ['factor_name', 'MDDate', 'label_name', 'stock']:
                agg_dict[col] = np.mean
        # 聚合
        df1 = df.groupby('factor_name').agg(agg_dict)
        df['MDDate'] = pd.to_datetime(df['MDDate'])  # 转换为datetime对象
        # 找出最大的日期和最小的日期
        end_of_date = df['MDDate'].max()
        start_of_date = df['MDDate'].min()
        # max_min_dates = pd.DataFrame({'start_of_date': start_of_date,
        #                              'end_of_date': end_of_date})
        # 将结果添加到原始的DataFrame中
        insert_position = 1

        # 添加新列
        df1.insert(insert_position, 'symbol', df.iloc[0]['stock'])
        df1.insert(insert_position, 'label_name', df.iloc[0]['label_name'])
        df1.insert(insert_position, 'end_of_date', end_of_date)
        df1.insert(insert_position, 'start_of_date', start_of_date)
        # df1['start_of_date'] = start_of_date
        # df1['end_of_date'] = end_of_date
        # df1['label_name'] = df.iloc[0]['label_name']
        # df1['symbol'] = df.iloc[0]['stock']
        df = df.drop(columns='MDDate')
        df = df.drop(columns=df.columns[1:])
        print(df.columns)
        df2 = df.merge(df1, on='factor_name', how='left')
        return df2

    def formal_factor_evaluation_data_describe(self, trading_frequency=None, stock=None, label_name=None, factor_name=None):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["formal_factor_evaluation_data_describe_new"]
        fp = FactorProvider('016869')
        data_type = None
        factor_list = None
        if trading_frequency == '1s':
            data_type = 'tick_l2p'
        if trading_frequency == '3s':
            data_type = 'enhanced_tick'
        if factor_name is not None:
            factor_list = [factor_name]
        df = fp.load_factor_analysis_res(data_type=data_type, stock=stock,
                                         label_name=label_name, factor_list=factor_list)
        column_names = df.columns.tolist()
        findfilter = {'start_of_date': df.iloc[0]['start_of_date'],
                      'end_of_date': df.iloc[0]['end_of_date'],
                      'label_name': df.iloc[0]['label_name'],
                      'symbol': df.iloc[0]['symbol'],
                      }
        df1 = df.drop(['MDDate', 'label_name', 'stock', 'valid_count'], axis=1)
        df3 = df1.groupby('factor_name').apply(lambda x: x.describe()).reset_index()
        end_of_date = df['MDDate'].max()
        start_of_date = df['MDDate'].min()
        df3 = df3.rename(columns={'level_1': 'index'})
        # max_min_dates = pd.DataFrame({'start_of_date': start_of_date,
        #                              'end_of_date': end_of_date})
        # 将结果添加到原始的DataFrame中
        insert_position = 1
        # 添加新列
        df3.insert(insert_position, 'symbol', df.iloc[0]['stock'])
        df3.insert(insert_position, 'label_name', df.iloc[0]['label_name'])
        df3.insert(insert_position, 'end_of_date', end_of_date)
        df3.insert(insert_position, 'start_of_date', start_of_date)
        df3.insert(insert_position, 'user_id', self.user_id)
        df3_dict = df3.to_dict(orient='records')
        params = {
            'symbol': df.iloc[0]['stock'],
            'label_name': df.iloc[0]['label_name'],
            'end_of_date': end_of_date,
            'start_of_date': start_of_date,
            'user_id': self.user_id
        }
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
                result = model_collection.insert_many(df3_dict)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name,
                                     "formal_factor_evaluation_data_describe",
                                     "insert", findfilter)
                print('更新成功')
                client.close()
                return result.inserted_ids
            else:
                # 尝试插入数据到 MongoDB 集合中
                result = model_collection.insert_many(df3_dict)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name,
                                     "formal_factor_evaluation_data_describe",
                                     "insert", findfilter)
                client.close()
                return result.inserted_ids
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def formal_factor_evaluation_data_todb(self, original_df, trading_frequency):
        """
        将一次实验对应的模型数据存入mongodb中
        :param
            version_alias   版本号，唯一	string
            hash256     与版本号对应，唯一	int
            type	        参数类型    string
            params_jsonstr	原始参数，已剔除value过长的key    jsonstring
            user_id	        用户id    string
            create_time	            string
            params_jsonstr_extra	原始参数中过长的list（元素个数超过10个），非必传
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["formal_factor_evaluation_data_new"]
        df = original_df
        findfilter = {'start_of_date': df.iloc[0]['start_of_date'],
                      'end_of_date': df.iloc[0]['end_of_date'],
                      'label_name': df.iloc[0]['label_name'],
                      'symbol': df.iloc[0]['symbol'],
                      'trading_frequency': trading_frequency,
                      }
        df["create_time"] = self.time
        df['user_id'] = self.user_id
        print(df)
        document = df.to_dict(orient='records')
        # document = {
        #     'start_of_date': start_of_date,
        #     'end_of_date': end_of_date,
        #     'label_name': label_name,
        #     'symbol': symbol,
        #     'trading_frequency': trading_frequency,
        #     'factor_name': factor_name,
        #     'create_time': self.time,
        #     'update_time': self.time,
        #     "data": dict_from_df,
        # }
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
                result = model_collection.insert_many(document)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation_data",
                                     "insert", findfilter)
                print('更新成功')
                client.close()
                return result.inserted_ids
            else:
                # 尝试插入数据到 MongoDB 集合中
                result = model_collection.insert_many(document)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation_data",
                                     "insert", findfilter)
                client.close()
                return result.inserted_ids
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def formal_factor_evaluation_data_todb2(self, trading_frequency=None, stock=None, label_name=None, factor_name=None):
        """
        将一次实验对应的模型数据存入mongodb中
        :param
            version_alias   版本号，唯一	string
            hash256     与版本号对应，唯一	int
            type	        参数类型    string
            params_jsonstr	原始参数，已剔除value过长的key    jsonstring
            user_id	        用户id    string
            create_time	            string
            params_jsonstr_extra	原始参数中过长的list（元素个数超过10个），非必传
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["formal_factor_evaluation_data_new"]
        df = self.factor_evaluation_data(trading_frequency=trading_frequency, stock=stock,
                                         label_name=label_name, factor_name=factor_name)
        if trading_frequency:
            findfilter = {'start_of_date': df.iloc[0]['start_of_date'],
                          'end_of_date': df.iloc[0]['end_of_date'],
                          'label_name': df.iloc[0]['label_name'],
                          'symbol': df.iloc[0]['symbol'],
                          'trading_frequency': trading_frequency,
                          }
        else:
            findfilter = {'start_of_date': df.iloc[0]['start_of_date'],
                          'end_of_date': df.iloc[0]['end_of_date'],
                          'label_name': df.iloc[0]['label_name'],
                          'symbol': df.iloc[0]['symbol'],
                          }
        df["create_time"] = self.time
        df['user_id'] = self.user_id
        document = df.to_dict(orient='records')
        # document = {
        #     'start_of_date': start_of_date,
        #     'end_of_date': end_of_date,
        #     'label_name': label_name,
        #     'symbol': symbol,
        #     'trading_frequency': trading_frequency,
        #     'factor_name': factor_name,
        #     'create_time': self.time,
        #     'update_time': self.time,
        #     "data": dict_from_df,
        # }
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
                result = model_collection.insert_many(document)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation_data",
                                     "insert", findfilter)
                print('更新成功')
                client.close()
                return result.inserted_ids
            else:
                # 尝试插入数据到 MongoDB 集合中
                result = model_collection.insert_many(document)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation_data",
                                     "insert", findfilter)
                client.close()
                return result.inserted_ids
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def delete_indb(self, collection_name, key, value):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db[collection_name]
        query = {key: value}
        matched_document = model_collection.find_one(query)
        if matched_document is None:
            # 如果没找到匹配的文档，返回False
            client.close()
            return False
        try:
            model_collection.delete_many(query)
            print("删除成功")
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果删除过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()
            return False

    def delete_factor_indb(self, collection_name, key, value):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db[collection_name]
        query = {key: value}
        matched_document = model_collection.find_one(query)
        if matched_document is None:
            # 如果没找到匹配的文档，返回False
            client.close()
            return False
        try:
            model_collection.delete_many(query)
            print("删除成功")
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果删除过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()
            return False

    def signal_evaluation_data_delete(self, exp_id, version_alias, symbol, evaluation_type, condition, metrics):
        # 102条放一个数组里
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["signal_evaluation_data_new"]
        df = metrics
        df['date'] = pd.to_datetime(df['date'])
        date = df.iloc[0]['date']
        dict_from_df = df.to_dict(orient='list')
        document = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "symbol": symbol,
            "date": date,
            "evaluation_type": evaluation_type,
            "condition": condition,
            "update_time": self.time,
            # "metrics": flattened_array.tolist()
            "metrics": dict_from_df
        }
        matched_document = model_collection.find_one(
            {'symbol': symbol, 'exp_id': exp_id, "date": date, "evaluation_type": evaluation_type})
        if matched_document is None:
            # 如果没找到匹配的文档，返回False
            client.close()
            return False
        query = {'symbol': symbol, 'exp_id': exp_id, "date": date, "evaluation_type": evaluation_type}
        try:
            # 尝试删除数据
            model_collection.delete_many(query)
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果删除过程中发生错误，打印错误信息
            print("Error occurred while deleting data:", e)
            client.close()
            return False

    def backtest_evaluation_data_delete(self, exp_id, version_alias, symbol, strategy_name, strategy_params,
                                        backtest_evaluation_type, condition, metrics):
        # 102条放一个数组里
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["backtest_evaluation_data_new"]
        df = metrics
        df['date'] = pd.to_datetime(df['date'])
        date = df.iloc[0]['date']
        dict_from_df = df.to_dict(orient='list')
        document = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "symbol": symbol,
            "date": date,
            "strategy_name": strategy_name,
            "strategy_params": strategy_params,
            "backtest_evaluation_type": backtest_evaluation_type,
            "condition": condition,
            "update_time": self.time,
            "metrics": dict_from_df,
        }
        matched_document = model_collection.find_one(
            {'symbol': symbol, 'exp_id': exp_id, "strategy_name": strategy_name,
             "strategy_params": strategy_params,
             "backtest_evaluation_type": backtest_evaluation_type, "condition": condition})
        if matched_document is None:
            # 如果没找到匹配的文档，返回False
            client.close()
            return False
        query = {'symbol': symbol, 'exp_id': exp_id, "strategy_name": strategy_name,
                 "strategy_params": strategy_params,
                 "backtest_evaluation_type": backtest_evaluation_type, "condition": condition}
        try:
            # 尝试删除数据
            model_collection.delete_many(query)
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果删除过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()
            return False

    def load_configs(self, version_alias=None, hash256=None, params_jsonstr=None, params_jsonstr_extra=None):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["exp_params_new"]
        query = {}
        if version_alias is not None:
            query["version_alias"] = version_alias
        if hash256 is not None:
            query["hash256"] = hash256
        if params_jsonstr is not None:
            query["params_jsonstr"] = params_jsonstr
        if params_jsonstr_extra is not None:
            query["params_jsonstr_extra"] = params_jsonstr_extra
        try:
            df = pd.DataFrame(
                list(model_collection.find(query, {'version_alias': 1, 'hash256': 1, 'params_jsonstr': 1,
                                                   'params_jsonstr_extra': 1})))
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "exp_params", "load", query)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def load_user_event(self, exp_id=None, version_alias=None, operate=None, event_type=None, collection=None):
        """
        返回user_event集合中实验id对应的所有数据
        :param
            exp_id  实验id
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["user_event_new"]
        query = {}
        if exp_id is not None:
            query["exp_id"] = exp_id
        if version_alias is not None:
            query["version_alias"] = version_alias
        if operate is not None:
            query["operate"] = operate
        if event_type is not None:
            query["event_type"] = event_type
        if collection is not None:
            query["collection"] = collection
        # 投影，用来设置返回的查询中包含哪些字段
        projection = {
            'exp_id': 1,
            'user_id': 1,
            'version_alias': 1,
            'operate': 1,
            'collection': 1,
            'event_type': 1,
            'create_time': 1,
            'params': 1,
        }
        try:
            df = pd.DataFrame(list(model_collection.find(query, projection)))
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "user_event", "load", query)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def load_signal_evaluation_data(self, exp_id=None, symbol=None, version_alias=None, evaluation_type=None):
        """
        返回signal_evaluation_data集合中实验id和标的对应的所有数据
        :param
            exp_id  实验id
            symbol  标的
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["signal_evaluation_data_new"]
        query = {}
        if exp_id is not None:
            query["exp_id"] = exp_id
        if version_alias is not None:
            query["version_alias"] = version_alias
        if symbol is not None:
            query["symbol"] = symbol
        if evaluation_type is not None:
            query["evaluation_type"] = evaluation_type
        projection = {
            'exp_id': 1,
            'symbol': 1,
            'evaluation_type': 1,
            'condition': 1,
        }
        try:
            df = pd.DataFrame(list(model_collection.find(query)))
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "signal_evaluation_data", "load", query)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def load_backtest_evaluation_data(self, exp_id=None, symbol=None, version_alias=None,
                                      backtest_evaluation_type=None):
        """
        返回backtest_evaluation_data集合中实验id和标的对应的所有数据
        :param
            exp_id  实验id
            symbol  标的
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["backtest_evaluation_data_new"]
        query = {}
        if exp_id is not None:
            query["exp_id"] = exp_id
        if version_alias is not None:
            query["version_alias"] = version_alias
        if symbol is not None:
            query["symbol"] = symbol
        if backtest_evaluation_type is not None:
            query["backtest_evaluation_type"] = backtest_evaluation_type
        projection = {
            'exp_id': 1,
            'symbol': 1,
            'backtest_evaluation_type': 1,
            'condition': 1,
        }
        try:
            df = pd.DataFrame(list(model_collection.find(query)))
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "backtest_evaluation_data", "load", query)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def load_formal_factor_evaluation_data(self, label_name=None, symbol=None, trading_frequency=None,
                                           factor_name=None):
        """
        返回formal_factor_evaluation_data集合中实验id和标的对应的所有数据
        :param
            exp_id  实验id
            symbol  标的
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["formal_factor_evaluation_data_new"]
        query = {}
        if label_name is not None:
            query["label_name"] = label_name
        if symbol is not None:
            query["symbol"] = symbol
        if trading_frequency is not None:
            query["trading_frequency"] = trading_frequency
        if factor_name is not None:
            query["factor_name"] = factor_name
        projection = {
            'exp_id': 1,
            'symbol': 1,
            'backtest_evaluation_type': 1,
            'condition': 1,
        }
        try:
            df = pd.DataFrame(list(model_collection.find(query)))
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "formal_factor_evaluation_data", "load", query)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def load_formal_factor_evaluation_data_describe(self, label_name=None, symbol=None, trading_frequency=None,
                                                    factor_name=None):
        """
        返回formal_factor_evaluation_data集合中实验id和标的对应的所有数据
        :param
            exp_id  实验id
            symbol  标的
        :return:
            dataframe
        """
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["formal_factor_evaluation_data_describe_new"]
        query = {}
        if label_name is not None:
            query["label_name"] = label_name
        if symbol is not None:
            query["symbol"] = symbol
        if trading_frequency is not None:
            query["trading_frequency"] = trading_frequency
        if factor_name is not None:
            query["factor_name"] = factor_name
        projection = {
            'exp_id': 1,
            'symbol': 1,
            'backtest_evaluation_type': 1,
            'condition': 1,
        }
        try:
            df = pd.DataFrame(list(model_collection.find(query)))
            df = df.drop(["_id", "factor_name", "user_id", "start_of_date", "end_of_date", "label_name", "symbol"],
                         axis=1)
            column_names = df.columns
            df2 = pd.DataFrame(df.values.T, index=df.columns)
            # 打印结果
            print(df2)
            self.user_event_todb("-",
                                 "-", inspect.currentframe().f_code.co_name,
                                 "formal_factor_evaluation_data_describe", "load", query)
            print("success")
            client.close()
            return df2
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    # def test_todb(self, params):
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["testmodel"]
    #     data = {'name': 'John', 'age': 30, 'city': 'New York'}
    #     insert_info = {
    #         "id": 1,
    #         "exp_type": json.dumps(data),
    #         "params": params,
    #     }
    #     result = model_collection.insert_one(insert_info)
    #     print("存入成功")
    #     print(result.inserted_id)
    #     document = model_collection.find_one({})
    #     json_data = json.loads(document['exp_type'])
    #     name = json_data['name']
    #     age = json_data['age']
    #     city = json_data['city']
    #     print("Name:", name)
    #     print("Age:", age)
    #     print("City:", city)
