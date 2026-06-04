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


def trans_data_type(data_type):
    data_type_freq = {"enhanced_tick_norm": "3s",
                      "enhanced_tick":"3s",
                      "tick_l2p":"1s"}
    freq = data_type_freq.get(data_type)
    if freq is None:
        raise Exception(f"data_type：{data_type}暂无对应的freq！")
    return freq

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
        table_name_transfer['label_personal_enhanced_tick'] = ["dfs://PrivateData/EnhancedTick/" + userID,
                                                               'user_label_data']
        table_name_transfer['factor_personal_trade'] = ["dfs://PrivateData/Trade/" + userID, 'user_factor_data']
        table_name_transfer['label_personal_trade'] = ["dfs://PrivateData/Trade/" + userID, 'user_label_data']
        table_name_transfer['factor_personal_tick_l2p'] = ["dfs://PrivateData/EnhancedTickL2P/" + userID,
                                                           'user_factor_data']
        table_name_transfer['label_personal_tick_l2p'] = ["dfs://PrivateData/EnhancedTickL2P/" + userID,
                                                          'user_label_data']
        table_name_transfer['factor_personal_tick'] = ["dfs://PrivateData/Tick/" + userID, 'user_factor_data']
        table_name_transfer['label_personal_tick'] = ["dfs://PrivateData/Tick/" + userID, 'user_label_data']
        table_name_transfer['factor_personal_index_enhanced'] = ["dfs://PrivateData/IndexEnhanced/" + userID,
                                                                 'user_factor_data']
        table_name_transfer['label_personal_index_enhanced'] = ["dfs://PrivateData/IndexEnhanced/" + userID,
                                                                'user_label_data']
        table_name_transfer['factor_personal_future_tick'] = ["dfs://PrivateData/FutureTick/" + userID,
                                                              'user_factor_data']
        table_name_transfer['label_personal_future_tick'] = ["dfs://PrivateData/FutureTick/" + userID,
                                                             'user_label_data']
    table_name_transfer['factor_public_enhanced_tick'] = ["dfs://PublicData/platformdata/EnhancedTick",
                                                          'online_factor_data']
    table_name_transfer['label_public_enhanced_tick'] = ["dfs://PublicData/platformdata/EnhancedTick",
                                                         'online_label_data']
    table_name_transfer['label_public_enhanced_tick_norm'] = ["dfs://PublicData/platformdata/EnhancedTick",
                                                              'online_label_data']
    table_name_transfer['factor_public_enhanced_tick_norm'] = ["dfs://PublicData/platformdata/EnhancedTick",
                                                               'online_factor_data_new']
    table_name_transfer['real_factor_public_enhanced_tick_norm'] = ["dfs://PublicData/platformdata/EnhancedTick",
                                                                    'real_factor_data_norm']
    table_name_transfer['real_factor_public_enhanced_tick'] = ["dfs://PublicData/platformdata/EnhancedTick",
                                                               'real_factor_data']
    table_name_transfer['real_factor_public_trade'] = ["dfs://PublicData/platformdata/Trade", 'real_factor_data']
    table_name_transfer['factor_public_trade'] = ["dfs://PublicData/platformdata/Trade", 'online_factor_data']
    table_name_transfer['label_public_trade'] = ["dfs://PublicData/platformdata/Trade", 'online_label_data']
    table_name_transfer['factor_public_tick_l2p'] = ["dfs://PublicData/platformdata/EnhancedTickL2P",
                                                     'online_factor_data']
    table_name_transfer['label_public_tick_l2p'] = ["dfs://PublicData/platformdata/EnhancedTickL2P",
                                                    'online_label_data']
    table_name_transfer['factor_public_tick'] = ["dfs://PublicData/platformdata/Tick", 'online_factor_data']
    table_name_transfer['label_public_tick'] = ["dfs://PublicData/platformdata/Tick", 'online_label_data']
    table_name_transfer['factor_public_index_enhanced'] = ["dfs://PublicData/platformdata/IndexEnhanced",
                                                           'online_factor_data']
    table_name_transfer['label_public_index_enhanced'] = ["dfs://PublicData/platformdata/IndexEnhanced",
                                                          'online_label_data']
    table_name_transfer['factor_public_future_tick'] = ["dfs://PublicData/platformdata/FutureTick",
                                                        'online_factor_data']
    table_name_transfer['label_public_future_tick'] = ["dfs://PublicData/platformdata/FutureTick", 'online_label_data']

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
    factors = pt.schema().colDefs.name[4:]
    factors
    """
    factor_list = s.run(script_factor)
    # 获取标签列表

    script_label = f"""
    pt = loadTable("{label_dbName}",`{label_tbName})
    factors = pt.schema().colDefs.name[4:]
    factors
    """
    labels_list = s.run(script_label)
    return factor_list, labels_list, stocks


class MongoDB:

    def __init__(self, start_time=None, end_time=None):
        self.env_id = xquantEnv
        self.time = datetime.datetime.now()
        if start_time is None and end_time is None:
            self.end_date = self.time.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - relativedelta(
                days=1)
            self.start_date = datetime.datetime(self.time.year, self.time.month, 1) - relativedelta(months=6)
        else:
            self.end_date = datetime.datetime.strptime(end_time, "%Y%m%d")
            self.start_date = datetime.datetime.strptime(start_time, "%Y%m%d")
        self.start_of_date = self.start_date.strftime('%Y%m%d')
        self.end_of_date = self.end_date.strftime('%Y%m%d')
        # self.end_of_date = self.time.strftime('%Y%m%d')
        self.user_id = get_userid()
        self.stock_list =['688375.SH', '688082.SH', '688036.SH', '688234.SH', '688099.SH', '688819.SH', '002409.SZ', '688303.SH',
            '688012.SH', '688538.SH', '688779.SH', '002371.SZ', '688256.SH', '688390.SH', '688599.SH', '688008.SH',
            '688169.SH', '688536.SH', '688561.SH', '688295.SH', '688363.SH', '688349.SH', '688180.SH', '688385.SH',
            '688063.SH', '689009.SH', '688005.SH', '688047.SH', '688521.SH', '300373.SZ', '688728.SH', '688396.SH',
            '688114.SH', '688297.SH', '603986.SH', '688120.SH', '688220.SH', '688126.SH', '688301.SH', '688348.SH',
            '688052.SH', '300223.SZ', '688032.SH', '688777.SH', '688111.SH', '688065.SH', '688122.SH', '688223.SH',
            '688009.SH', '688187.SH', '688981.SH', '688188.SH', '000977.SZ', '688271.SH', '688041.SH', '688072.SH']
        # self.stock_list = ['688375.SH', '688082.SH']
        if self.env_id == 0:
            self.__ip = ENCRYPTED_HOSTS['mongo']['test']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['test']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "xquant_mgr"

            self.gateway_config = {"user": "xquant",
                                   "password": "Htsc&quant@test",
                                   "login": "168.63.69.110:8888",  # http://168.63.69.110:8888/v1/login
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

    def __get_fac_evaluation_data(self, label_name, data_type, factor_list=None, stock_list=None):
        from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
        fp = FactorProvider('016869')
        df = fp.load_factor_analysis_res(data_type=data_type, stock=stock_list,
                                         label_name=label_name, factor_list=factor_list,
                                         start_date=self.start_of_date, end_date=self.end_of_date)
        return df

    def __factor_evaluation_six_factor_radar_data(self, df, data_type, factor_list=None, stock_list=None):
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
            date_range = self.start_of_date + "_" + self.end_of_date
            insert_position = 1
            freq = trans_data_type(data_type)
            # 添加新列
            if data_type:
                df1.insert(insert_position, 'trading_frequency', freq)
            df1.insert(insert_position, 'symbol', "all")
            df1.insert(insert_position, 'label_name', df.iloc[0]['label_name'])
            df1.insert(insert_position, 'period', "test")
            df1.insert(insert_position, 'date_range', date_range)
            df2 = df2.drop(columns='MDDate')
            df2 = df2.drop(columns=df2.columns[1:])
            df3 = df1.merge(df2, on='factor_name', how='left')
            radar_data, df4, stock_list_from_six = six_factor_eval_and_star_rank(start_date=self.start_of_date,
                                                                        end_date=self.end_of_date,
                                                                        stock_lis=stock_list, factor_name_list=factor_list,
                                                                        trading_frequency=freq,
                                                                        label_name=df.iloc[0]['label_name'],
                                                                        factor_eval_data=df)
            # 存储雷达图数据
            self.radar_chart_data_todb(stock_list_from_six, radar_data, df.iloc[0]['label_name'], freq, factor_list)
            df4 = df4.rename(columns=lambda x: x.replace('normal_ic', '相关性'))
            df4 = df4.rename(columns=lambda x: x.replace('auto_corr_1', '自相关性'))
            df4 = df4.rename(columns=lambda x: x.replace('shift_corr', '偏移相关性衰减'))
            merged_df = pd.merge(df4, df3, on='factor_name', how="left")
            return merged_df

    def data_to_mongo(self, db_table, data_dct, findfilter, overwrite=False):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db[db_table]
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data and overwrite:
                model_collection.delete_many(findfilter)
                model_collection.insert_many(data_dct)
                print('plot_uniquekey_data_new insert success')
            elif existing_data:
                print(f'{db_table} already has same data!')
            else:
                model_collection.insert_many(data_dct)
                print(f'{db_table} insert success')
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print(f"{db_table}- Error occurred while inserting data:", e)
            client.close()
            return False

    def radar_chart_data_todb(self, stock_list, radar_data, label_name, freq, factor_names):
        # 价格，市值，波动率，换手率
        from xquant.factordata import FactorData
        s = FactorData()
        date_list = s.tradingday(self.start_of_date, self.end_of_date)
        # 波动率 annualstdevr_24m 用close求标准差
        df_m = s.get_factor_value("Basic_factor", stock_list, date_list,
                                  ["close", "mkt_cap_ard", "turn"])

        # 总市值单位：亿
        df_m["mkt_cap_ard"] = df_m["mkt_cap_ard"].apply(lambda x: x / 10000)
        df_m.index.names = ["date", "symbol"]
        df_m.reset_index(inplace=True)
        df_m["annualstdevr_24m"] = df_m["close"]
        df = df_m.groupby("symbol").agg({"close": "mean", "turn": "mean",
                                         "mkt_cap_ard": "mean", "annualstdevr_24m": "std"})
        df.reset_index(inplace=True)
        radar_data.rename(columns={"多空收益分离": "absolute_difference", "盈亏比": "profit_loss_ratio",
                                   "胜率": "win_rate", "stock": "symbol"}, inplace=True)

        radar_data = pd.merge(radar_data, df, left_on="symbol", right_on="symbol", how="left")
        radar_data.rename(columns={"auto_corr_1": "auto_corr_5", "shift_corr": "p_value"}, inplace=True)
        # normal_ic：相关性， auto_corr_5：自相关性， p_value：偏移相关性衰减， absolute_difference：多空收益分离，profit_loss_ratio：盈亏比， win_rate：胜率
        df_g = radar_data.groupby("factor_name").agg({'normal_ic': 'mean', 'auto_corr_5': 'mean', 'p_value': 'mean',
                                                      'absolute_difference': 'mean', 'profit_loss_ratio': 'mean',
                                                      'win_rate': 'mean', 'close': 'mean', 'turn': 'mean',
                                                      'mkt_cap_ard': 'mean', 'annualstdevr_24m': 'mean', })
        df_g.reset_index(inplace=True)
        # all表示所有标的得平均值
        df_g["symbol"] = "all"
        radar_data = pd.concat([radar_data, df_g])
        time_t = datetime.datetime.now()
        radar_data["date_range"] = "{}_{}".format(self.start_of_date, self.end_of_date)
        radar_data["period"] = "test"
        radar_data["freq"] = freq
        radar_data["label_name"] = label_name
        radar_data["create_time"] = time_t
        radar_data["update_time"] = time_t
        data_dct = radar_data.to_dict(orient="records")
        findfilter = {
            'date_range': radar_data.iloc[0]['date_range'],
            'label_name': label_name,
            'freq': freq,
            'symbol': {'$in': list(stock_list)},
            'factor_name': {'$in': list(factor_names)},
        }
        self.data_to_mongo(db_table="plot_radar_chart_data_new", data_dct=data_dct, findfilter=findfilter)

    def __formal_factor_evaluation_data_describe(self, df, data_type, stock_list, factor_list=None):
        if df.shape[0] == 0:
            pass
        else:
            # client = pymongo.MongoClient(self.mongo)
            # db = client[self.database]
            # model_collection = db["formal_factor_evaluation_data_describe_new"]
            column_names = df.columns.tolist()
            df1 = df.drop(['MDDate', 'label_name', 'stock'], axis=1)
            df3 = df1.groupby('factor_name').apply(lambda x: x.describe()).reset_index()
            date_range = self.start_of_date + "_" + self.end_of_date
            df3 = df3.rename(columns={'level_1': 'index'})
            findfilter = {
                'label_name': df.iloc[0]['label_name'],
                'date_range': date_range,
                "factor_name": {"$in": list(factor_list)}
            }
            insert_position = 1
            # 添加新列
            if data_type:
                freq = trans_data_type(data_type)
                findfilter["trading_frequency"] = freq
                df3.insert(insert_position, 'trading_frequency', freq)
            if type(stock_list) == str:
                findfilter["symbol"] = df.iloc[0]['stock']
                df3.insert(insert_position, 'symbol', df.iloc[0]['stock'])
            elif type(stock_list) == list:
                findfilter["symbol"] = "all"
                df3.insert(insert_position, 'symbol', "all")
            df3.insert(insert_position, 'label_name', df.iloc[0]['label_name'])
            df3.insert(insert_position, 'period', "test")
            df3.insert(insert_position, 'date_range', date_range)
            df3.insert(insert_position, 'user_id', self.user_id)
            df3_dict = df3.to_dict(orient='records')
            params = {
                'symbol': df.iloc[0]['stock'],
                'label_name': df.iloc[0]['label_name'],
                'user_id': self.user_id
            }
            self.data_to_mongo(db_table="formal_factor_evaluation_data_describe_new", data_dct=df3_dict,
                               findfilter=findfilter)

    def __formal_factor_evaluation_data_homepage(self, df,
                                                 data_type, factor_list=None):
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
            date_range = self.start_of_date + "_" + self.end_of_date
            base_dict = {
                'label_name': df.iloc[0]['label_name'],
                'date_range': date_range
                # "factor_list": {"$in": list(factor_list)}
            }
            if data_type:
                # 如果trading_frequency存在，则添加它到字典
                base_dict['trading_frequency'] = trans_data_type(data_type)
                # 如果factor_name存在，则添加它到字典
            if type(factor_list) == str:
                base_dict['factor_name'] = factor_list
            findfilter = base_dict
            df["create_time"] = self.time
            insert_position = 1
            df.insert(insert_position, 'user_id', self.user_id)
            df.insert(insert_position, 'info', ' ')
            document = df.to_dict(orient='records')
            self.data_to_mongo(db_table="formal_factor_evaluation_data_new", data_dct=document, findfilter=findfilter)

    def formal_factor_evaluation_data(self, label_name,
                                      data_type, factor_list=None, stock_list=None):
        df = self.__get_fac_evaluation_data(
            label_name=label_name, data_type=data_type, factor_list=factor_list, stock_list=stock_list)
        if df.shape[0] == 0:
            return pd.DataFrame()
        else:
            self.__formal_factor_evaluation_data_describe(df, data_type, factor_list=factor_list, stock_list=stock_list)
            data1 = self.__factor_evaluation_six_factor_radar_data(df, data_type, factor_list=factor_list, stock_list=stock_list)
            return data1

    def save_formal_factor_evaluation_data(self, df2,
                                           data_type, factor_list=None):
        # try:
        df2 = df2.sort_values("score", ascending=False)
        df2["rank"] = range(1, len(df2) + 1)
        df2["fac_num"] = str(len(df2))
        print(len(df2))
        self.__formal_factor_evaluation_data_homepage(df2, data_type=data_type, factor_list=factor_list)
        return True
        # except:
        #     # 如果插入过程中发生错误，打印错误信息
        #     print("Error while save")


    def save_formal_factor_evaluation_data_describe(self, label_name,
                                                    data_type, factor_list=None, stock_list=None):
        df = self.__get_fac_evaluation_data(
            label_name=label_name, data_type=data_type, factor_list=factor_list, stock_list=stock_list)
        self.__formal_factor_evaluation_data_describe(df, data_type, factor_list=factor_list, stock_list=stock_list)
        return True

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

    def get_stock_list_evaluation_data(self, single_factor=None):
        source_type = 'public'  # public 公共库 personal 个人私库
        data_types = ['enhanced_tick_norm']
        query = {"source_type": 'public'}
        for data_type in data_types:
            query["trading_frequency"] = trans_data_type(data_type)
            factor_list, labels_list, stocks = get_info_from_dfs(data_type, source_type)
            # try:
            if single_factor is None:
                sub_lists = [factor_list[i:i + 100] for i in range(0, len(factor_list), 100)]
                # for label in labels_list:
                label = "LabelFirstPeak_th10_120s"
                dfs = []
                for sub_list in sub_lists:
                    factor_list = list(sub_list)
                    df_data = self.formal_factor_evaluation_data(
                                                                   label_name=label,
                                                                   data_type=data_type,
                                                                   factor_list=factor_list, stock_list=self.stock_list)
                    if not df_data.empty:
                        dfs.append(df_data)
                if dfs:
                    result_df = pd.concat(dfs, ignore_index=True)
                    self.save_formal_factor_evaluation_data(result_df,
                                                        data_type=data_type,
                                                        factor_list=factor_list)
            elif single_factor is not None:
                for label in labels_list:
                    self.__save_single_factor_formal_factor_evaluation_data(
                        label_name=label, data_type=data_type,
                        single_factor = single_factor)

            print("get all fac finish")
            print(datetime.datetime.now())


    def get_one_stock_evaluation_data(self, single_factor=None, single_stock=None):
        source_type = 'public'  # public 公共库 personal 个人私库
        data_types = ['enhanced_tick_norm']
        query = {"source_type": 'public'}
        for data_type in data_types:
            freq = trans_data_type(data_type)
            query["trading_frequency"] = freq
            factor_list, labels_list, stocks = get_info_from_dfs(data_type, source_type)
            self.save_fac_label_list(factor_list, labels_list, self.stock_list, freq)
            if single_stock:
                stocks = single_stock
            elif single_stock is None:
                stocks = self.stock_list
            if single_factor is None:
                sub_lists = [factor_list[i:i + 100] for i in range(0, len(factor_list), 100)]
                for sub_list in sub_lists:
                    factor_list = list(sub_list)
                    label = "LabelFirstPeak_th10_120s"
                    #for label in labels_list:
                    for stock in stocks:
                        self.save_formal_factor_evaluation_data_describe(label_name=label,
                                                                         data_type=data_type,
                                                                         stock_list=stock, factor_list=factor_list)
            elif single_factor is not None:
                label = "LabelFirstPeak_th10_120s"
                #for label in labels_list:
                for stock in stocks:
                    self.save_formal_factor_evaluation_data_describe(label_name=label,
                                                                         data_type=data_type,
                                                                         stock_list=stock, factor_list=single_factor)
            print("get one stock_list finish")
            print(datetime.datetime.now())

    def __save_single_factor_formal_factor_evaluation_data(self, label_name,
                                                         data_type, single_factor):
        df = self.__get_fac_evaluation_data(
            label_name=label_name, data_type=data_type, factor_list=single_factor, stock_list=self.stock_list)
        data1 = self.__factor_evaluation_six_factor_radar_data(df, data_type, factor_list=single_factor, stock_list=self.stock_list)
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        date_range = self.start_of_date + "_" + self.end_of_date
        query = {
            'label_name': df.iloc[0]['label_name'],
            'date_range': date_range
        }
        model_collection = db["formal_factor_evaluation_data_new"]
        mongo_data = pd.DataFrame(list(model_collection.find(query)))
        model_collection.delete_many(query)
        client.close()
        df2 = pd.concat([mongo_data, data1])
        df2 = df2.sort_values("score", ascending=False)
        df2["rank"] = range(1, len(df2) + 1)
        df2["fac_num"] = str(len(df2))
        self.__formal_factor_evaluation_data_homepage(df2, data_type, factor_list=single_factor)
        return True

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

    def plot_uniquekey_exp_todb(self, stock, date, uniquekey, exp_name=None, version_alias=None, strategy_name=None,
                                strategy_config_alias=None, data_type=None, overwrite=False):
        data_dct = {"stock": stock,
                    "date": date,
                    "uniquekey": uniquekey,
                    "create_time": self.time
                    }
        if exp_name:
            data_dct["exp_name"] = exp_name
        else:
            data_dct["exp_name"] = ""
        if version_alias:
            data_dct["version_alias"] = version_alias
        else:
            data_dct["version_alias"] = ""
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

        findfilter = {
            'date': date,
            'stock': stock,
            'exp_name': exp_name,
            'version_alias': version_alias,
            'strategy_name': strategy_name,
            'strategy_config_alias': strategy_config_alias,
            'data_type': data_type
        }
        self.data_to_mongo("plot_uniquekey_data_exp_new", [data_dct], findfilter, overwrite=True)

    def plot_uniquekey_todb(self, stock=None, factor=None, label_name=None, date_range=None, freq=None,
                                uniquekey=None, data_source=None, overwrite=False):
        data_dct = {"stock": stock,
                    "factor": factor,
                    "label_name": label_name,
                    "freq": freq,
                    "date_range": date_range,
                    "data_source": data_source,
                    "uniquekey": uniquekey,
                    "create_time": self.time
                    }
        findfilter = {
            'date_range': date_range,
            'stock': stock,
            'factor': factor,
            'freq': freq,
            'label_name': label_name,
            'data_source': data_source,
        }
        self.data_to_mongo("plot_uniquekey_data_new", [data_dct], findfilter, overwrite=overwrite)
