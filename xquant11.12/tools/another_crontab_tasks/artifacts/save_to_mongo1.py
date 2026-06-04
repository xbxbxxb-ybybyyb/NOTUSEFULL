import pymongo
import os
import pandas as pd
import numpy as np
import datetime
from dateutil.relativedelta import relativedelta
import json
from FactorProvider.conf.DubboConf import get_userid
from artifacts.six_factor_eval_and_star_rank import six_factor_eval_and_star_rank
import inspect
import requests
from . import utils

from xquant.setXquantEnv import xquantEnv

encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_copy.json")

with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)


def create_connect(host='old'):
    import dolphindb as ddb
    s = ddb.session()
    if host == 'new':
        s.connect("168.17.249.172", 8902, 'admin', '123456')
    else:
        s.connect("168.17.250.48", 8902, 'admin', '123456')
    return s


def get_info_from_dfs(data_type, source_type, userID=None):
    # 获取标的列表
    if data_type in ['tick', 'future_tick', 'tick_l2p', 'index_enhanced']:
        host = 'new'
    else:
        host = 'old'
    s = create_connect(host)
    table_name_transfer = dict()
    if userID:
        table_name_transfer["factor_personal_enhanced_tick"] = ["dfs://PersonalData/EnhancedTick/" + userID,
                                                                'user_factor_data']
        table_name_transfer['label_personal_enhanced_tick'] = ["dfs://PersonalData/EnhancedTick/" + userID,
                                                               'user_label_data']
        table_name_transfer['factor_personal_trade'] = ["dfs://PersonalData/Trade/" + userID, 'user_factor_data']
        table_name_transfer['label_personal_trade'] = ["dfs://PersonalData/Trade/" + userID, 'user_label_data']
        table_name_transfer['factor_personal_tick_l2p'] = ["dfs://PersonalData/EnhancedTickL2P/" + userID,
                                                           'user_factor_data']
        table_name_transfer['label_personal_tick_l2p'] = ["dfs://PersonalData/EnhancedTickL2P/" + userID,
                                                          'user_label_data']
        table_name_transfer['factor_personal_index_enhanced'] = ["dfs://PersonalData/IndexEnhanced/" + userID,
                                                                 'user_factor_data']
        table_name_transfer['label_personal_index_enhanced'] = ["dfs://PersonalData/IndexEnhanced/" + userID,
                                                                'user_label_data']
        table_name_transfer['factor_personal_tick'] = ["dfs://PersonalData/Tick/" + userID, 'user_factor_data']
        table_name_transfer['label_personal_tick'] = ["dfs://PersonalData/Tick/" + userID, 'user_label_data']

    table_name_transfer['factor_public_enhanced_tick'] = ["dfs://PublicData/xquantdata/EnhancedTick",
                                                          'online_factor_data']
    table_name_transfer['label_public_enhanced_tick'] = ["dfs://PublicData/xquantdata/EnhancedTick",
                                                         'online_label_data']
    table_name_transfer['factor_public_trade'] = ["dfs://PublicData/xquantdata/Trade", 'online_factor_data']
    table_name_transfer['label_public_trade'] = ["dfs://PublicData/xquantdata/Trade", 'online_label_data']

    table_name_transfer['factor_public_tick_l2p'] = ["dfs://PublicData/xquantdata/EnhancedTickL2P",
                                                     'online_factor_data']
    table_name_transfer['label_public_tick_l2p'] = ["dfs://PublicData/xquantdata/EnhancedTickL2P", 'online_label_data']

    table_name_transfer['factor_public_tick'] = ["dfs://PublicData/xquantdata/Tick", 'online_factor_data']
    table_name_transfer['label_public_tick'] = ["dfs://PublicData/xquantdata/Tick", 'online_label_data']

    table_name_transfer['factor_public_index_enhanced'] = ["dfs://PublicData/xquantdata/IndexEnhanced",
                                                           'online_factor_data']
    table_name_transfer['label_public_index_enhanced'] = ["dfs://PublicData/xquantdata/IndexEnhanced",
                                                          'online_label_data']

    factor_dbName, factor_tbName = table_name_transfer["factor" + "_" + source_type + "_" + data_type]
    label_dbName, label_tbName = table_name_transfer["label" + "_" + source_type + "_" + data_type]

    script = f"""
    pt = loadTable("{factor_dbName}",`{factor_tbName})
    stocks = exec distinct(M_HTSCSecurityID) as stocks from pt
    stocks
    """
    stocks = s.run(script)

    # 获取因子列表
    script_factor = f"""
    pt = loadTable("{factor_dbName}",`{factor_tbName})
    factors = pt.schema().colDefs.name[3:]
    factors
    """
    factor_list = s.run(script_factor)
    # 获取标签列表

    script_label = f"""
    pt = loadTable("{label_dbName}",`{label_tbName})
    factors = pt.schema().colDefs.name[3:]
    factors
    """
    labels_list = s.run(script_label)
    return factor_list, labels_list, stocks


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
        # self.time = datetime.datetime.now()
        # self.start_date = self.time - datetime.timedelta(days=364)  # 一年前的日期作为starttime
        self.time = datetime.datetime.now()
        self.last_month = self.time.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(
            days=1)
        self.start_date = datetime.datetime(self.time.year, self.time.month, 1) - relativedelta(months=6)
        self.start_of_date = self.start_date.strftime('%Y%m%d')
        self.end_of_date = self.time.strftime('%Y%m%d')
        # self.end_of_date = self.time.strftime('%Y%m%d')
        self.user_id = get_userid()
        if self.env_id == 0:
            self.__ip = ENCRYPTED_HOSTS['mongo']['test']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['test']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "xquant_mgr"

            self.gateway_config = {"user": "xquant",
                               "password": "Htsc&quant@test",
                               "login": "168.63.69.110:8888", # http://168.63.69.110:8888/v1/login
                               "upload": "168.61.9.1:12006",
                               "download": "168.61.9.1:12006"}
        elif self.env_id == 1:
            self.__ip = ENCRYPTED_HOSTS['mongo']['prd']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['prd']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "signal_center"

            self.gateway_config = {"user": "strategy_center",
                                "login": "168.11.73.29:11022",
                                "upload": "168.11.73.67:8085",
                                "download": "168.11.73.67:8085",
                                "password": "Htsc&strategy_center@prd"}

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

    # def load_factor_evaluation_data(self, factor_name_list, symbol_list, label_list, start_time, end_time):
    #     """
    #     返回factor_evaluation_data集合中和查询条件对应的所有数据
    #     :param
    #         factor_name_list  因子名称列表
    #         symbol_list       标的列表
    #         label_list        标签列表
    #         start_time        查询开始时间
    #         end_time          查询结束时间
    #     :return:
    #         dataframe
    #     """
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     collection = db["factor_evaluation_data_new"]
    #     date_start = datetime.strptime(start_time, "%Y%m%d")
    #     date_end = datetime.strptime(end_time, "%Y%m%d")
    #     params = {
    #         "symbol_list": symbol_list,
    #         "factor_name_list": factor_name_list,
    #         "label_list": label_list,
    #         "date_start": date_start,
    #         "date_end": date_end
    #     }
    #     query = {
    #         'index.symbol': {'$in': symbol_list},
    #         'index.factor_name': {'$in': factor_name_list},
    #         'index.label': {'$in': label_list},
    #         'index.MDDatetime': {'$gte': date_start, '$lt': date_end}
    #     }
    #     try:
    #         df = pd.DataFrame(list(collection.find(query)))
    #         self.user_event_todb("-",
    #                              "-", inspect.currentframe().f_code.co_name,
    #                              "factor_evaluation_data", "load", params)
    #         print("success")
    #         client.close()
    #         return df
    #     except pymongo.errors.PyMongoError as e:
    #         print("Error occurred while finding data:", e)
    #         client.close()

    def exp_params_todb(self, exp_id, version_alias, hash256, exp_type, params_jsonstr, info=None,
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
        insert_info = {
            "version_alias": version_alias,
            "hash256": hash256,
            "exp_type": exp_type,
            "info": info,
            "params_jsonstr": params_jsonstr,
            "params_jsonstr_extra": params_jsonstr_extra,
            "user_id": self.user_id,
            "create_time": create_time,
            "update_time": self.time,
        }

        if params_jsonstr_extra:
            insert_info['params_jsonstr_extra'] = params_jsonstr_extra
        if info:
            insert_info['info'] = info
        try:
            existing_data = model_collection.find_one(
                {'version_alias': insert_info['version_alias'], 'hash256': insert_info['hash256']})
            if existing_data:
                update_info = {
                    "version_alias": version_alias,
                    "hash256": hash256,
                    "exp_type": exp_type,
                    "info": info,
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
            # print("DEBUG: user_event_todb 存入成功!")
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
        params = {
            "symbol": symbol
        }
        df = metrics
        grouped = df.groupby('date')
        for date, group in grouped:
            # 将日期作为文档的唯一标识符，插入MongoDB
            group['date'] = pd.to_datetime(group['date'])
            date = group.iloc[0]['date']
            dict_from_df = group.to_dict(orient='list')
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
            existing_data = model_collection.find_one({
                'symbol': symbol, 'exp_id': exp_id, "date": date, "condition": condition,
                "evaluation_type": evaluation_type})
            if existing_data:
                query = {'symbol': symbol, 'exp_id': exp_id, "date": date, "condition": condition,
                         "evaluation_type": evaluation_type}
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
            except pymongo.errors.PyMongoError as e:
                # 如果插入过程中发生错误，打印错误信息
                print("Error occurred while inserting data:", e)
                client.close()
                return False
        client.close()
        return True

    # def backtest_evaluation_data_todb(self, exp_id, version_alias, symbol, strategy_name, strategy_params,
    # backtest_evaluation_type, condition, metrics, signal_path):
    def backtest_evaluation_data_todb(self, exp_id, version_alias, symbol, strategy_name, strategy_alias,
                                      backtest_evaluation_type, condition, metrics, is_operation):
        # 102条放一个数组里
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        if is_operation:
            db_table = "online_transaction_performance_data_new"
        else:
            db_table = "offline_transaction_performance_data_new"
        # model_collection = db["backtest_evaluation_data_new"]
        model_collection = db[db_table]
        df = metrics
        params = {
            "strategy_name": strategy_name,
        }
        grouped = df.groupby('date')
        for date, group in grouped:
            # 将日期作为文档的唯一标识符，插入MongoDB
            # group['date'] = pd.to_datetime(group['date'])
            date = group.iloc[0]['date']
            if "-" in date:
                date = date.replace("-", "")
            dict_from_df = group.to_dict(orient='list')
            document = {
                "exp_id": exp_id,
                "version_alias": version_alias,
                "symbol": symbol,
                "date": date,
                "strategy_name": strategy_name,
                "strategy_alias": strategy_alias,
                "backtest_evaluation_type": backtest_evaluation_type,
                "condition": condition,
                "create_time": self.time,
                "metrics": dict_from_df,
                # "signal_path": signal_path
            }
            existing_data = model_collection.find_one({
                'symbol': symbol, 'exp_id': exp_id, "date": date, "condition": condition,
                "strategy_name": strategy_name, "strategy_alias": strategy_alias,
                "backtest_evaluation_type": backtest_evaluation_type})
            if existing_data:
                query = {'symbol': symbol, 'exp_id': exp_id, "date": date, "condition": condition,
                         "strategy_name": strategy_name, "strategy_alias": strategy_alias,
                         "backtest_evaluation_type": backtest_evaluation_type
                         }
                model_collection.delete_many(query)
                self.user_event_todb(exp_id, version_alias,
                                     inspect.currentframe().f_code.co_name,
                                     db_table,
                                     "delete", params)
            try:
                # 尝试插入数据到 MongoDB 集合中
                model_collection.insert_one(document)
                self.user_event_todb(exp_id,
                                     version_alias, inspect.currentframe().f_code.co_name,
                                     db_table, "insert", params)
            except pymongo.errors.PyMongoError as e:
                # 如果插入过程中发生错误，打印错误信息
                print("Error occurred while inserting data:", e)
                client.close()
                return False
        client.close()
        return True

    # def factor_evaluation_data_todb(self, factor_name, symbol, label, evaluation_df):
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["factor_evaluation_data_new"]
    #     df = evaluation_df
    #     df['MDDatetime'] = pd.to_datetime(df['MDDate'])
    #     data_list = df.to_dict(orient='records')
    #     params = {
    #         "factor_name": factor_name,
    #     }
    #     print(data_list)
    #     for row in data_list:
    #         insert_index = {
    #             "factor_name": factor_name,
    #             "label": label,
    #             "symbol": symbol,
    #             'MDDatetime': row['MDDatetime'],
    #         }
    #         try:
    #             result = model_collection.insert_one({
    #                 "index": insert_index,
    #                 "factor_name": factor_name,
    #                 'data': row,  # 将元组转换为字典，字典的键是列的名字，值是列的值
    #                 "update_time": self.time,
    #             })
    #         except pymongo.errors.PyMongoError as e:
    #             # 如果插入过程中发生错误，打印错误信息
    #             print("Error occurred while inserting data:", e)
    #             client.close()
    #             return False
    #     self.user_event_todb("-",
    #                          "-", inspect.currentframe().f_code.co_name,
    #                          "factor_evaluation_data", "insert", params)
    #     print("存入成功")
    #     client.close()
    #     return True

    # def __get_fac_evaluation_data(self, label_name, trading_frequency, factor_name=None, stock=None):
    #     fp = FactorProvider('016869')
    #     data_type = None
    #     # 定义日期
    #     end_date = self.last_month  # 获取上月最后一天时间
    #     now_str = end_date.strftime('%Y%m%d')
    #     start_date = self.start_date  # 一年前的日期作为starttime
    #     # 计算日期差
    #     delta = end_date - start_date
    #     days = delta.days
    #     periods = days // 182
    #     # remaining_days = days % 182
    #     dfs = []
    #     if trading_frequency == '1s':
    #         data_type = 'tick_l2p'
    #     if trading_frequency == '3s':
    #         data_type = 'enhanced_tick'
    #     for i in range(periods):
    #         # 打印开始和结束时间
    #         start_of_date = start_date.strftime('%Y%m%d')
    #         end_of_date = end_date.strftime('%Y%m%d')
    #         df = fp.load_factor_analysis_res(data_type=data_type, stock=stock,
    #                                          label_name=label_name, factor_list=factor_name,
    #                                          start_date=start_of_date, end_date=end_of_date)
    #         df.name = f"df_{i}"  # 设置DataFrame的名称
    #         dfs.append(df)
    #         #     if remaining_days > 0:
    #         # end_of_date = end_date.strftime('%Y%m%d')
    #         # start_of_date = date.strftime('%Y%m%d')
    #         # df = fp.load_factor_analysis_res(data_type=data_type, stock=stock,
    #         #                                  label_name=label_name, factor_list=factor_name,
    #         #                                  start_date=start_of_date, end_date=end_of_date)
    #         # df.name = f"df_{periods}"  # 设置DataFrame的名称
    #         # dfs.append(df)
    #
    #         start_date -= datetime.timedelta(days=182)
    #         end_date -= datetime.timedelta(days=182)
    #     return dfs

    def __get_fac_evaluation_data(self, label_name, trading_frequency, factor_name=None, stock=None):
        from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
        fp = FactorProvider('016869')
        data_type = None
        # 定义日期
        end_date = self.last_month  # 获取上月最后一天时间
        now_str = end_date.strftime('%Y%m%d')
        start_date = self.start_date  # 半年前的日期作为starttime
        if trading_frequency == '1s':
            data_type = 'tick_l2p'
        if trading_frequency == '3s':
            data_type = 'enhanced_tick'
        start_of_date = start_date.strftime('%Y%m%d')
        end_of_date = end_date.strftime('%Y%m%d')
        df = fp.load_factor_analysis_res(data_type=data_type, stock=stock,
                                         label_name=label_name, factor_list=factor_name,
                                         start_date=start_of_date, end_date=end_of_date)
        return df

    def __factor_evaluation_data(self, df, trading_frequency, factor_name=None, stock=None):
        if df.shape[0] == 0:
            return df
        else:
            column_names = df.columns.tolist()
            # 创建一个空的聚合函数字典
            agg_dict = {}
            for col in column_names:
                # 需要计算均值的列添加到聚合函数字典中
                if col not in ['factor_name', 'MDDate', 'label_name', 'stock']:
                    agg_dict[col] = np.mean
            # 聚合
            df1 = df.groupby('factor_name').agg(agg_dict).reset_index()
            df2 = df.groupby('factor_name').head(1)
            end_date = self.last_month
            start_date = self.start_date
            start_of_date = start_date.strftime('%Y%m%d')
            end_of_date = end_date.strftime('%Y%m%d')
            date_range = start_of_date + "_" + end_of_date
            insert_position = 1

            # 添加新列
            if trading_frequency:
                df1.insert(insert_position, 'trading_frequency', trading_frequency)
            if stock:
                df1.insert(insert_position, 'symbol', df.iloc[0]['stock'])
            elif stock is None:
                df1.insert(insert_position, 'symbol', "all")
            df1.insert(insert_position, 'label_name', df.iloc[0]['label_name'])
            # df1.insert(insert_position, 'end_of_date', end_of_date)
            # df1.insert(insert_position, 'start_of_date', start_of_date)
            df1.insert(insert_position, 'period', "test")
            df1.insert(insert_position, 'date_range', date_range)
            # df1['start_of_date'] = start_of_date
            # df1['end_of_date'] = end_of_date
            # df1['label_name'] = df.iloc[0]['label_name']
            # df1['symbol'] = df.iloc[0]['stock']
            df2 = df2.drop(columns='MDDate')
            df2 = df2.drop(columns=df2.columns[1:])
            df3 = df1.merge(df2, on='factor_name', how='left')
            df4 = six_factor_eval_and_star_rank(start_date=start_of_date, end_date=end_of_date,
                                                stock=stock, factor_list=factor_name,
                                                trading_frequency=trading_frequency, label_name=df.iloc[0]['label_name'])
            df4 = df4.rename(columns=lambda x: x.replace('normal_ic', '相关性'))
            df4 = df4.rename(columns=lambda x: x.replace('auto_corr_5', '自相关性'))
            df4 = df4.rename(columns=lambda x: x.replace('p_value', '收益率显著性'))
            merged_df = pd.merge(df4, df3, on='factor_name', how="left")
            return merged_df

    def __formal_factor_evaluation_data_describe(self, df, trading_frequency,
                                                 factor_name=None, stock=None):
        if df.shape[0] == 0:
            pass
        else:
            client = pymongo.MongoClient(self.mongo)
            db = client[self.database]
            model_collection = db["formal_factor_evaluation_data_describe_new"]
            column_names = df.columns.tolist()
            df1 = df.drop(['MDDate', 'label_name', 'stock'], axis=1)
            df3 = df1.groupby('factor_name').apply(lambda x: x.describe()).reset_index()
            end_of_date = self.last_month
            start_of_date = self.start_date
            start_date = start_of_date.strftime('%Y%m%d')
            end_date = end_of_date.strftime('%Y%m%d')
            date_range = start_date + "_" + end_date
            df3 = df3.rename(columns={'level_1': 'index'})
            findfilter = {
                'label_name': df.iloc[0]['label_name'],
                'date_range': date_range
            }
            # max_min_dates = pd.DataFrame({'start_of_date': start_of_date,
            #                              'end_of_date': end_of_date})
            # 将结果添加到原始的DataFrame中
            insert_position = 1
            # 添加新列
            if trading_frequency:
                findfilter["trading_frequency"] = trading_frequency
                df3.insert(insert_position, 'trading_frequency', trading_frequency)
            if stock:
                findfilter["symbol"] = df.iloc[0]['stock']
                df3.insert(insert_position, 'symbol', df.iloc[0]['stock'])
            elif stock is None:
                findfilter["symbol"] = "all"
                df3.insert(insert_position, 'symbol', "all")
            df3.insert(insert_position, 'label_name', df.iloc[0]['label_name'])
            # df3.insert(insert_position, 'end_of_date', end_of_date)
            # df3.insert(insert_position, 'start_of_date', start_of_date)
            df3.insert(insert_position, 'period', "test")
            df3.insert(insert_position, 'date_range', date_range)
            df3.insert(insert_position, 'user_id', self.user_id)
            df3_dict = df3.to_dict(orient='records')
            params = {
                'symbol': df.iloc[0]['stock'],
                'label_name': df.iloc[0]['label_name'],
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
                    client.close()
                    return result.inserted_ids
            except pymongo.errors.PyMongoError as e:
                # 如果插入过程中发生错误，打印错误信息
                print("Error occurred while inserting data:", e)
                client.close()

    # def formal_factor_evaluation_data_todb(self, original_df, trading_frequency):
    #     """
    #     将一次实验对应的模型数据存入mongodb中
    #     :param
    #         version_alias   版本号，唯一	string
    #         hash256     与版本号对应，唯一	int
    #         type	        参数类型    string
    #         params_jsonstr	原始参数，已剔除value过长的key    jsonstring
    #         user_id	        用户id    string
    #         create_time	            string
    #         params_jsonstr_extra	原始参数中过长的list（元素个数超过10个），非必传
    #     :return:
    #         dataframe
    #     """
    #     client = pymongo.MongoClient(self.mongo)
    #     db = client[self.database]
    #     model_collection = db["formal_factor_evaluation_data_new"]
    #     df = original_df
    #     findfilter = {'start_of_date': df.iloc[0]['start_of_date'],
    #                   'end_of_date': df.iloc[0]['end_of_date'],
    #                   'label_name': df.iloc[0]['label_name'],
    #                   'symbol': df.iloc[0]['symbol'],
    #                   'trading_frequency': trading_frequency,
    #                   }
    #     df["create_time"] = self.time
    #     df['user_id'] = self.user_id
    #     print(df)
    #     document = df.to_dict(orient='records')
    #     # document = {
    #     #     'start_of_date': start_of_date,
    #     #     'end_of_date': end_of_date,
    #     #     'label_name': label_name,
    #     #     'symbol': symbol,
    #     #     'trading_frequency': trading_frequency,
    #     #     'factor_name': factor_name,
    #     #     'create_time': self.time,
    #     #     'update_time': self.time,
    #     #     "data": dict_from_df,
    #     # }
    #     try:
    #         existing_data = model_collection.find_one(findfilter)
    #         if existing_data:
    #             model_collection.delete_many(findfilter)
    #             result = model_collection.insert_many(document)
    #             self.user_event_todb("-",
    #                                  "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation_data",
    #                                  "insert", findfilter)
    #             print('更新成功')
    #             client.close()
    #             return result.inserted_ids
    #         else:
    #             # 尝试插入数据到 MongoDB 集合中
    #             result = model_collection.insert_many(document)
    #             self.user_event_todb("-",
    #                                  "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation_data",
    #                                  "insert", findfilter)
    #             client.close()
    #             return result.inserted_ids
    #     except pymongo.errors.PyMongoError as e:
    #         # 如果插入过程中发生错误，打印错误信息
    #         print("Error occurred while inserting data:", e)
    #         client.close()

    def __formal_factor_evaluation_data_todb(self, df,
                                             trading_frequency, factor_name=None, stock=None):
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
        if df.shape[0] == 0:
            pass
        else:
            client = pymongo.MongoClient(self.mongo)
            db = client[self.database]
            model_collection = db["formal_factor_evaluation_data_new"]
            end_of_date = self.last_month
            start_of_date = self.start_date
            start_date = start_of_date.strftime('%Y%m%d')
            end_date = end_of_date.strftime('%Y%m%d')
            date_range = start_date + "_" + end_date
            base_dict = {
                'label_name': df.iloc[0]['label_name'],
                'date_range': date_range
            }
            if trading_frequency:
                # 如果trading_frequency存在，则添加它到字典
                base_dict['trading_frequency'] = trading_frequency
                # 如果factor_name存在，则添加它到字典
            if factor_name:
                base_dict['factor_name'] = factor_name
            if stock:
                base_dict["symbol"] = df.iloc[0]['symbol']
            elif stock is None:
                base_dict["symbol"] = "all"

            findfilter = base_dict
            df["create_time"] = self.time
            insert_position = 1
            df.insert(insert_position, 'user_id', self.user_id)
            df.insert(insert_position, 'info', ' ')
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
                    print('更新成功')
                    client.close()
                    return result.inserted_ids
                else:
                    # 尝试插入数据到 MongoDB 集合中
                    result = model_collection.insert_many(document)
                    client.close()
                    return result.inserted_ids
            except pymongo.errors.PyMongoError as e:
                # 如果插入过程中发生错误，打印错误信息
                print("Error occurred while inserting data:", e)
                client.close()

    # def formal_factor_evaluation_data_todb(self, label_name,
    #                                        trading_frequency, factor_name=None, stock=None):
    #     try:
    #         all_dfs = self.__get_fac_evaluation_data(
    #             label_name=label_name, trading_frequency=trading_frequency, factor_name=factor_name, stock=stock)
    #         result1 = pd.concat([all_dfs[0], all_dfs[1]])
    #         result2 = pd.concat([result1, all_dfs[2], all_dfs[3]])
    #         result3 = pd.concat([result2, all_dfs[4], all_dfs[5]])
    #         result4 = result3.copy(deep=True)
    #         for i in range(6, len(all_dfs)):
    #             result4 = pd.concat([result4, all_dfs[i]])
    #         data0 = self.__factor_evaluation_data(all_dfs[0], trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_todb(data0, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_describe(all_dfs[0], trading_frequency, stock=stock)
    #         data1 = self.__factor_evaluation_data(result1, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_todb(data1, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_describe(result1, trading_frequency, stock=stock)
    #         data2 = self.__factor_evaluation_data(result2, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_todb(data2, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_describe(result2, trading_frequency, stock=stock)
    #         data3 = self.__factor_evaluation_data(result3, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_todb(data3, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_describe(result3, trading_frequency, stock=stock)
    #         data4 = self.__factor_evaluation_data(result4, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_todb(data4, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_describe(result4, trading_frequency, stock=stock)
    #         if stock is None:
    #             data1 = self.__factor_evaluation_data(result1, trading_frequency, stock=stock)
    #             self.__formal_factor_evaluation_data_todb(data1, trading_frequency, stock=stock)
    #         self.__formal_factor_evaluation_data_describe(result1, trading_frequency, stock=stock)
    #         print("get fac success")
    #         return True
    #     except:
    #         # 如果插入过程中发生错误，打印错误信息
    #         print("Error while save:")

    def formal_factor_evaluation_data_todb(self, label_name,
                                           trading_frequency, factor_name=None, stock=None):
        try:
            df = self.__get_fac_evaluation_data(
                label_name=label_name, trading_frequency=trading_frequency, factor_name=factor_name, stock=stock)
            if stock is None:
                data1 = self.__factor_evaluation_data(df, trading_frequency, factor_name=factor_name, stock=stock)
                self.__formal_factor_evaluation_data_todb(data1, trading_frequency, stock=stock)
            self.__formal_factor_evaluation_data_describe(df, trading_frequency, stock=stock)
            print("get fac success")
            return True
        except:
            # 如果插入过程中发生错误，打印错误信息
            print("Error while save:")

    def save_fac_label_list(self, factor_list, labels_list, stocks, trading_frequency):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["factor_label_stock_list_new"]
        df1 = pd.DataFrame({
            "list": factor_list,
            "type": "factor_list",
            "trading_frequency": trading_frequency,
            "update_time": self.time,
        })
        df2 = pd.DataFrame({
            "list": labels_list,
            "type": "labels_list",
            "trading_frequency": trading_frequency,
            "update_time": self.time,
        })
        df3 = pd.DataFrame({
            "list": stocks,
            "type": "stocks",
            "trading_frequency": trading_frequency,
            "update_time": self.time,
        })
        df = pd.concat([df1, df2, df3])
        data_dict = df.to_dict(orient='records')
        findfilter = {
            'trading_frequency': trading_frequency
        }
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
            result = model_collection.insert_many(data_dict)
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            client.close()

    def get_all_fac_evaluation_data(self, factor_name=None):
        source_type = 'public'  # public 公共库 personal 个人私库
        data_types = ['enhanced_tick', 'tick_l2p']
        query = {"source_type": 'public'}
        for data_type in data_types:
            if data_type == 'enhanced_tick':
                trading_frequency = '3s'
                query["trading_frequency"] = '3s'
            elif data_type == 'tick_l2p':
                trading_frequency = '1s'
                query["trading_frequency"] = '1s'
            factor_list, labels_list, stocks = get_info_from_dfs(data_type, source_type)
            try:
                self.save_fac_label_list(factor_list, labels_list, stocks, trading_frequency)
                for label in labels_list:
                    self.formal_factor_evaluation_data_todb(
                        label_name=label, trading_frequency=trading_frequency, factor_name=factor_name)
                    for stock in stocks:
                        self.formal_factor_evaluation_data_todb(
                            label_name=label, trading_frequency=trading_frequency, stock=stock, factor_name=factor_name)
                self.user_event_todb("-",
                                     "-", inspect.currentframe().f_code.co_name, "formal_factor_evaluation",
                                     "insert", query)
                print("get all fac finish")
                print(datetime.datetime.now())
            except:
                print("Error occurred while get data")

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

    def backtest_evaluation_data_delete(self, exp_id, version_alias, symbol, strategy_name, strategy_alias,
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
            "strategy_alias": strategy_alias,
            "backtest_evaluation_type": backtest_evaluation_type,
            "condition": condition,
            "update_time": self.time,
            "metrics": dict_from_df,
        }
        matched_document = model_collection.find_one(
            {'symbol': symbol, 'exp_id': exp_id, "strategy_name": strategy_name,
             "strategy_alias": strategy_alias,
             "backtest_evaluation_type": backtest_evaluation_type, "condition": condition})
        if matched_document is None:
            # 如果没找到匹配的文档，返回False
            client.close()
            return False
        query = {'symbol': symbol, 'exp_id': exp_id, "strategy_name": strategy_name,
                 "strategy_alias": strategy_alias,
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
                                                   'params_jsonstr_extra': 1, 'info': 1})))
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
                                      backtest_evaluation_type=None, is_operation=False):
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
        if is_operation:
            db_table = "online_transaction_performance_data_new"
        else:
            db_table = "offline_transaction_performance_data_new"
        # model_collection = db["backtest_evaluation_data_new"]
        model_collection = db[db_table]
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
                                 db_table, "load", query)
            print("success")
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print("Error occurred while finding data:", e)
            client.close()

    def load_formal_factor_evaluation_data(self, label_name=None, symbol=None, trading_frequency=None,
                                           factor_name=None, query_str=None):
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
        fit_current_condition = []
        conditions = []
        if label_name is not None:
            fit_current_condition.append({"label_name": {"$eq": label_name}})
        if symbol is not None:
            fit_current_condition.append({"symbol": {"$eq": symbol}})
        if symbol is None:
            fit_current_condition.append({"symbol": {"$eq": "all"}})
        if trading_frequency is not None:
            fit_current_condition.append({"trading_frequency": {"$eq": trading_frequency}})
        if factor_name is not None:
            fit_current_condition.append({"factor_name": {"$eq": factor_name}})
        conditions.append({"$and": fit_current_condition})
        # 将查询字符串按空格分割，并将每个条件构造成一个字典
        if query_str:
            conditions = []
            current_condition = []
            or_strs = query_str.split(' OR ')
            for or_str in or_strs:
                and_strs = or_str.split(' AND ')
                if label_name is not None:
                    current_condition.append({"label_name": {"$eq": label_name}})
                if symbol is not None:
                    current_condition.append({"symbol": {"$eq": symbol}})
                if trading_frequency is not None:
                    current_condition.append({"trading_frequency": {"$eq": trading_frequency}})
                if factor_name is not None:
                    current_condition.append({"factor_name": {"$eq": factor_name}})
                for and_str in and_strs:
                    tokens = and_str.split()
                    if len(tokens) != 3:
                        print("长度异常")
                    # 提取name、operator和value
                    name, operator, value = tokens
                    try:
                        value = float(value)
                    except ValueError:
                        pass
                    if operator == '=':
                        current_condition.append({name: {"$eq": value}})
                    elif operator == '<':
                        current_condition.append({name: {"$lt": value}})
                    elif operator == ">":
                        current_condition.append({name: {"$gt": value}})
                    elif operator == ">=":
                        current_condition.append({name: {"$gte": value}})
                    elif operator == "<=":
                        current_condition.append({name: {"$lte": value}})
                    elif operator == "!=":
                        current_condition.append({name: {"$ne": value}})
                    else:
                        raise ValueError(f'Unsupported operator: {operator}')
                if current_condition:  # 如果current_condition不为空，则添加到conditions中
                    conditions.append({'$and': current_condition})
                current_condition = []  # 重置current_condition以便下一个循环
            if current_condition:  # 如果最后一个循环中的current_condition不为空，则添加到conditions中
                conditions.append({'$and': current_condition})
        try:
            # df = pd.DataFrame(list(model_collection.find(query)))
            df = pd.DataFrame(model_collection.find({'$or': conditions}))
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
        fit_current_condition = []
        conditions = []
        if label_name is not None:
            fit_current_condition.append({"label_name": {"$eq": label_name}})
        if symbol is not None:
            fit_current_condition.append({"symbol": {"$eq": symbol}})
        if symbol is None:
            fit_current_condition.append({"symbol": {"$eq": "all"}})
        if trading_frequency is not None:
            fit_current_condition.append({"trading_frequency": {"$eq": trading_frequency}})
        if factor_name is not None:
            fit_current_condition.append({"factor_name": {"$eq": factor_name}})
        conditions.append({"$and": fit_current_condition})
        projection = {
            'exp_id': 1,
            'symbol': 1,
            'backtest_evaluation_type': 1,
            'condition': 1,
        }
        try:
            df = pd.DataFrame(model_collection.find({'$or': conditions}))
            # df = pd.DataFrame(list(model_collection.find(query)))
            df = df.drop(["_id", "factor_name", "user_id", "start_of_date", "end_of_date", "label_name", "symbol"],
                         axis=1)
            column_names = df.columns
            df2 = pd.DataFrame(df.values.T, index=df.columns)
            df2 = df2.drop(columns=0)
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

    def online_trasaction_data_todb(self, trade_df):
        if "index" in trade_df.columns:
            trade_df.drop("index", axis=1, inplace=True)
        trade_df["tradeDate"] = trade_df["tradeDate"].apply(
            lambda x: datetime.datetime.strftime(datetime.datetime.strptime(x, "%Y-%m-%d"), "%Y%m%d"))
        trade_df["createDate"] = trade_df["createDate"].astype(str)
        trade_df["createDate"] = trade_df["createDate"].apply(lambda x: x.replace("T", " "))
        trade_df["filledDate"] = trade_df["filledDate"].astype(str)
        trade_df["filledDate"] = trade_df["filledDate"].apply(lambda x: x.replace("T", " "))
        trade_df["create_time"] = self.time
        trade_df["update_time"] = self.time
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["online_transaction_data_new"]
        data_dct = trade_df.to_dict(orient="records")
        findfilter = {
            'tradeDate': trade_df.iloc[0]['tradeDate'],
            'symbol': trade_df.iloc[0]['symbol'],
            'strategy_config_alias': trade_df.iloc[0]['strategy_config_alias'],
            'strategy_name': trade_df.iloc[0]['strategy_name'],
            'label_name': trade_df.iloc[0]['label_name'],
        }
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
                model_collection.insert_many(data_dct)
                print('online_transaction_data insert success')
            else:
                model_collection.insert_many(data_dct)
                print('online_transaction_data insert success')
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("online_trasaction_data_todb - Error occurred while inserting data:", e)
            client.close()
            return False

    # 登录
    def login(self):
        username = self.gateway_config["user"]
        password = self.gateway_config["password"]

        url = 'http://{}/v1/login'.format(self.gateway_config["login"])
        header = {'Content-Type': 'application/json;charset=UTF-8'}
        data = {
            'identityType': '1',
            'resourceId': '000357',
            'level': 1,
            'credential': {
                'type': 'username_password',
                'username': username,
                'password': password
            }
        }
        jsondata = json.dumps(data)
        r = requests.post(url, data=jsondata, headers=header, verify=True).json()
        token = r['result']['token']
        return token

    # 同步上传
    def UploadFile(self, filename, filepath):

        username = self.gateway_config["user"]
        password = self.gateway_config["password"]

        token = self.login()
        headers = {'Connection': 'keep-alive',
                   'User-Agent': 'Apache-HttpClient/4.5.12 (Java/1.8.0_271)'}
        url = 'http://{}/syncauth/upload/{}'.format(self.gateway_config["upload"], username)
        data = {'filename': filename,
                'token': token}
        files = {'in': (filename, open(filepath, 'rb'), 'multipart/form-data')}
        res = requests.post(url=url, headers=headers, data=data, files=files, verify=False)
        return res

    def plot_uniquekey_todb(self, stock=None, factor=None, label_name=None, date=None,freq=None,
                            strategy_name=None, strategy_config_alias=None,
                            data_type=None, uniquekey=None, source=None):
        data_dct = {"stock": stock,
                    "date": date,
                    "uniquekey":uniquekey,
                    "create_time": self.time
                    }
        if factor:
            data_dct["factor"] = factor
        else:
            data_dct["factor"] = ""
        if freq:
            data_dct["freq"] = freq
        else:
            data_dct["freq"] = ""
        if strategy_name:
            data_dct["strategy_name"] = strategy_name
        else:
            data_dct["strategy_name"] = ""
        if strategy_config_alias:
            data_dct["strategy_config_alias"] = strategy_config_alias
        else:
            data_dct["strategy_config_alias"] = ""
        if data_type:
            data_dct["data_type"] = data_type
        else:
            data_dct["data_type"] = ""
        if label_name:
            data_dct["label_name"] = label_name
        else:
            data_dct["label_name"] = ""

        if source == "ic":
            findfilter = {
                        'date': date,
                        'stock': stock,
                        'factor': factor,
                        'freq':freq,
                        'label_name': label_name
                        }
        elif source == "trade":
            findfilter = {
                        'date': date,
                        'stock': stock,
                        'strategy_name': strategy_name,
                        'strategy_config_alias': strategy_config_alias,
                        'data_type': data_type
                        }
        else:
            raise Exception("只支持存储ic与运营分析图的uniquekey")

        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["plot_uniquekey_data_new"]
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
                model_collection.insert_one(data_dct)
                print('plot_uniquekey_data insert success')
            else:
                model_collection.insert_one(data_dct)
                print('plot_uniquekey_data insert success')
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("plot_uniquekey_todb - Error occurred while inserting data:", e)
            client.close()
            return False









