import pymongo
import os
import pandas as pd
from datetime import datetime
import json
from . import utils
from xquant.setXquantEnv import xquantEnv

encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_copy.json")

with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)


class MongoDB:

    def __init__(self):
        self.env_id = xquantEnv
        # now = datetime.now()
        # formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
        # self.time = formatted_now
        self.time = datetime.now()
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

    def signal_evaluation_data_todb1(self, exp_id, version_alias, symbol, evaluation_type, condition, metrics,
                                     create_time):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["signal_evaluation_data"]
        df = pd.DataFrame()
        df2 = metrics
        list_of_dicts = df2.to_dict(orient='records')
        print(list_of_dicts)
        df['DATE'] = pd.to_datetime(df2['date'])
        df["exp_id"] = exp_id
        df["symbol"] = symbol
        df["version_alias"] = version_alias
        df["evaluation_type"] = evaluation_type
        df["create_time"] = create_time
        df['metrics'] = list_of_dicts
        fixed_dict_list = [condition] * len(df)
        df['condition'] = fixed_dict_list
        documents = df.to_dict(orient='records')
        time0 = datetime.now()
        # insert_info = {
        #     "exp_id": exp_id,
        #     "version_alias": version_alias,
        #     "symbol": symbol,
        #     # "date": date,
        #     "evaluation_type": evaluation_type,
        #     # "condition": condition,
        #     # "metrics": metrics,
        #     "create_time": create_time,
        #     "update_time": self.time,
        # }
        try:
            existing_data = model_collection.find_one({'symbol': symbol, 'exp_id': exp_id})
            if existing_data:
                query = {'symbol': symbol, 'exp_id': exp_id}
                model_collection.delete_many(query)
                time1 = datetime.now()
                delete_time = time1 - time0
                print("删除时间")
                print(delete_time)
                result = model_collection.insert_many(documents)
                print('插入成功，耗时')
                print(datetime.now() - time1)
                return result.inserted_ids
            else:
                # 尝试插入数据到 MongoDB 集合中
                result = model_collection.insert_many(documents)
                print("插入耗时")
                print(datetime.now() - time0)
                return result.inserted_ids
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)

    def signal_evaluation_data_todb2(self, exp_id, version_alias, symbol, evaluation_type, condition, metrics,
                                     create_time):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["signal_evaluation_data"]
        df = metrics
        df['DATE'] = pd.to_datetime(df['DATE'])
        data_list = df.to_dict(orient='records')
        print(data_list)
        existing_data = model_collection.find_one({'index.symbol': symbol, 'index.exp_id': exp_id})
        if existing_data:
            time0 = datetime.now()
            query = {'index.symbol': symbol, 'index.exp_id': exp_id}
            model_collection.delete_many(query)
            time1 = datetime.now() - time0
            print("删除时间")
            print(time1)
        time2 = datetime.now()
        for row in data_list:
            insert_index = {
                "exp_id": exp_id,
                "version_alias": version_alias,
                "symbol": symbol,
                'DATE': row['DATE'],
            }
            try:
                # 尝试插入数据到 MongoDB 集合中
                model_collection.insert_one({
                    "index": insert_index,
                    "evaluation_type": evaluation_type,
                    "condition": condition,
                    "create_time": create_time,
                    'data': row,  # 将元组转换为字典，字典的键是列的名字，值是列的值
                    "update_time": self.time,
                })
            except pymongo.errors.PyMongoError as e:
                # 如果插入过程中发生错误，打印错误信息
                print("Error occurred while inserting data:", e)
                return False
        time3 = datetime.now() - time2
        print("插入耗时")
        print(time3)
        return True

    def signal_evaluation_data_todb3(self, exp_id, version_alias, symbol, evaluation_type, condition, metrics,
                                     create_time):
        # 102条放一个数组里
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db["signal_evaluation_data"]
        df = metrics
        flattened_array = df.values.flatten()
        document = {
            "exp_id": exp_id,
            "version_alias": version_alias,
            "symbol": symbol,
            "evaluation_type": evaluation_type,
            "condition": condition,
            "create_time": create_time,
            "update_time": self.time,
            "metrics": flattened_array.tolist()}
        existing_data = model_collection.find_one({'symbol': symbol, 'exp_id': exp_id})
        if existing_data:
            time0 = datetime.now()
            query = {'symbol': symbol, 'exp_id': exp_id}
            model_collection.delete_many(query)
            time1 = datetime.now() - time0
            print("删除时间")
            print(time1)
        try:
            # 尝试插入数据到 MongoDB 集合中
            time2 = datetime.now()
            model_collection.insert_one(document)
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print("Error occurred while inserting data:", e)
            return False
        time3 = datetime.now() - time2
        print("插入耗时")
        print(time3)
        return True
