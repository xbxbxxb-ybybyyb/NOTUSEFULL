import pymongo
import os
import pandas as pd
import numpy as np
import datetime as dt
from dateutil.relativedelta import relativedelta
import json
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from xquant.factordata import FactorData
from xquant.funddata import FundData
from xquant.marketdata import MarketData
from . import utils
from artifacts.save_to_mongo import get_info_from_dfs, trans_data_type, MongoDB
from xquant.setXquantEnv import xquantEnv
import ray

encrypt_path = os.path.join('/'.join(os.path.abspath(__file__).split('/')[:-1]), "encrypted_copy.json")

with open(encrypt_path, 'rb') as f:
    ENCRYPTED_HOSTS = json.load(f)

mdb = MongoDB()


def get_factor_label_data(stock, factors, start_date, end_date, user_id, label_name, data_type):
    fp = FactorProvider(user_id)
    # 获取因子值
    factor_value = fp.load_public_data_from_dfs(symbol=[stock], factor_list=factors,
                                                factor_type='factor', start_time=start_date,
                                                end_time=end_date, data_type=data_type)
    if factor_value.empty:
        return pd.DataFrame()
    factor_value.drop("R_HTSCSecurityID", axis=1, inplace=True)
    factor_value.rename(columns={"M_HTSCSecurityID": "symbol"}, inplace=True)
    factor_value.set_index(["timestamp", "symbol"], inplace=True)
    df_list = []
    for factor in factors:
        df_p = factor_value[[factor]]
        df_p["factor_name"] = factor
        df_p.rename(columns={factor: "factor_value"}, inplace=True)
        df_list.append(df_p)
    df_factor = pd.concat(df_list)
    if df_factor.empty:
        return pd.DataFrame()
    # 获取标签值
    factor_label = fp.load_public_data_from_dfs(symbol=[stock], factor_list=label_name,
                                                factor_type='label', start_time=start_date,
                                                end_time=end_date, data_type=data_type)
    factor_label.rename(columns={label_name: "label_value", "M_HTSCSecurityID": "symbol"}, inplace=True)
    factor_label.set_index(["timestamp", "symbol"], inplace=True)
    df = pd.merge(df_factor, factor_label, left_index=True, right_index=True, how="inner")
    if df.empty:
        return pd.DataFrame()
    df.reset_index(inplace=True)

    df["timestamp"] = df["timestamp"].astype(str)
    df["date"] = df["timestamp"].apply(lambda x: x[:10].replace("-", ""))
    df["label_name"] = label_name
    df["freq"] = trans_data_type(data_type)
    df = df[["date", "timestamp", "symbol", "factor_name", "factor_value", "label_name", "label_value", "freq"]]
    return df


def label_distribution_data_todb(factors, factor_label_df, start_date, end_date):
    time = dt.datetime.now()
    factor_label_df["create_time"] = time
    factor_label_df["update_time"] = time
    data_dct = factor_label_df.to_dict(orient="records")
    findfilter = {
        'label_name': factor_label_df.iloc[0]['label_name'],
        'date': {'$gte': start_date, '$lte': end_date},
        'freq': factor_label_df.iloc[0]['freq'],
        'symbol': factor_label_df.iloc[0]['symbol'],
        'factor_name': {'$in': factors},
    }
    mdb.data_to_mongo(db_table="plot_factor_label_distribution_data_new",
                      data_dct=data_dct, findfilter=findfilter)


def calc_top_bottom_yield(factor_label_data):
    """
    BottomYield 因子与标签数据，按因子值升序排序取前20%得数据，然后对标签值求均值，
    TopYield 因子与标签数据，按因子值降序排序取前20%得数据，然后对标签值求均值
    :param factor_label_data:
    :return:
    """
    import math
    factor_label_data = factor_label_data[["date", "factor_value", "label_value"]]
    top_n = max(math.floor(len(factor_label_data) * 0.2), 1)
    yield_data = factor_label_data.sort_values(by="factor_value", ascending=False)
    top_yield_data = yield_data.iloc[:top_n]
    # bottom_yield_data = factor_label_data.sort_values(by="factor_value", ascending=True)
    bottom_yield_data = yield_data.iloc[-top_n:]
    top_yield = np.mean(top_yield_data["label_value"])
    bottom_yield = np.mean(bottom_yield_data["label_value"])
    return top_yield, bottom_yield


def long_short_data_todb(symbol, label_name, data_type, start_date, end_date, factors, factor_label_data):
    if len(factor_label_data) == 0:
        print("factor_label_data为空DataFrame")
        return
    freq = trans_data_type(data_type)
    dates = list(set(factor_label_data["date"].tolist()))
    dates.sort()
    long_short_data = pd.DataFrame(columns=["date", "stock", "factor_name", "label_name", "freq",
                                            "bottom_yield", "top_yield"])

    for factor in factors:
        for date in dates:
            tmp_data = factor_label_data[(factor_label_data["symbol"] == symbol) &
                                         (factor_label_data["factor_name"] == factor) &
                                         (factor_label_data["date"] == date)]
            if tmp_data.empty:
                continue
            top_yield, bottom_yield = calc_top_bottom_yield(tmp_data)
            long_short_data.loc[len(long_short_data.index)] = [date, symbol, factor, label_name,
                                                               freq, bottom_yield, top_yield]
    # print("long_short_data:\n",long_short_data)
    time = dt.datetime.now()
    long_short_data["create_time"] = time
    long_short_data["update_time"] = time
    data_dct = long_short_data.to_dict(orient="records")
    findfilter = {
        'date': {'$gte': start_date, '$lte': end_date},
        'label_name': long_short_data.iloc[0]['label_name'],
        'freq': long_short_data.iloc[0]['freq'],
        'stock': long_short_data.iloc[0]['stock'],
        'factor_name': {'$in': factors},
    }
    mdb.data_to_mongo(db_table="plot_long_short_data_new", data_dct=data_dct, findfilter=findfilter)


@ray.remote
def short_data_label_data_todb(stock, start_date, end_date, user_id, label_name, data_type, factors, category):
    factor_label_df = get_factor_label_data(stock=stock, factors=factors, start_date=start_date,
                                            end_date=end_date, user_id=user_id, label_name=label_name,
                                            data_type=data_type)
    if len(factor_label_df) == 0:
        print("factor_label_df为空DataFrame")
        return
    else:
        if category == "long_short":
            print(f"标的：{stock} long_short_data开始写入因子。")
            long_short_data_todb(stock, label_name, data_type, start_date, end_date, factors, factor_label_df)
        elif category == "factor_label":
            print(f"标的：{stock} factor_label_distribution_data开始写入因子。")
            label_distribution_data_todb(factors, factor_label_df, start_date, end_date)


def long_short_data_label_distribution_data_parallel(stock, start_date, end_date, user_id, label_name,
                                                     data_type, factors=None, category="long_short"):
    # factors为None时 更新库中所有因子数据，并发读写，factors为指定因子列表时单进程读写
    if factors is None:
        factor_name_list, _, _ = get_info_from_dfs(data_type, source_type="public")
        factor_name_list = list(factor_name_list)
        if not ray.is_initialized():
            ray.init(num_cpus=15, _system_config={
                "object_spilling_config": json.dumps(
                    {"type": "filesystem", "params": {"directory_path": "/dfs/user/013150"}},
                )}
                     )
        # 因子&标签分布
        fac_num = len(factor_name_list)
        factors_list = [factor_name_list[i: i + 1] for i in range(0, fac_num, 1)]
        tasks = [short_data_label_data_todb.remote(stock, start_date, end_date, user_id, label_name, data_type,
                                                   factors, category) for factors in factors_list]
        ray.get(tasks)
    else:
        assert isinstance(factors, list), "factors参数为list类型"
        factor_label_df = get_factor_label_data(stock=stock, factors=factors, start_date=start_date,
                                                end_date=end_date, user_id=user_id, label_name=label_name,
                                                data_type=data_type)
        if len(factor_label_df) == 0:
            print("factor_label_df为空DataFrame")
            return
        else:
            if category == "long_short":
                print(f"标的：{stock} long_short_data开始写入因子。")
                long_short_data_todb(stock, label_name, data_type, start_date, end_date, factors, factor_label_df)
            elif category == "factor_label":
                print(f"标的：{stock} label_distribution_data开始写入因子。")
                label_distribution_data_todb(factors, factor_label_df, start_date, end_date)


class PlotData:

    def __init__(self, user_id, label_name, symbol, start_date, end_date, data_type="enhanced_tick_norm"):
        self.env_id = xquantEnv
        self.time = dt.datetime.now()
        self.start_date = start_date
        self.end_date = end_date

        self.user_id = user_id
        self.label_name = label_name
        self.period = "test"

        self.symbol = symbol
        self.fp = FactorProvider(self.user_id)
        self.s = FactorData()
        self.fd = FundData()
        self.data_type = data_type
        self.freq = trans_data_type(data_type)
        if self.env_id == 0:
            self.__ip = ENCRYPTED_HOSTS['mongo']['test']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['test']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "xquant_mgr"
        elif self.env_id == 1:
            self.__ip = ENCRYPTED_HOSTS['mongo']['prd']['ip']
            self.__password = utils.decrypt(ENCRYPTED_HOSTS['mongo']['prd']['ciphertext'])
            self.mongo = 'mongodb://xquant_mgr:' + self.__password + self.__ip
            self.database = "signal_center"

        self.date_list = self.s.tradingday(self.start_date, self.end_date)
        self.factor_name_list = None

    def set_stocks_factors(self):
        if not self.factor_name_list:
            self.factor_name_list, _, _ = get_info_from_dfs(self.data_type, source_type="public")
            self.factor_name_list = list(self.factor_name_list)


    def __get_daliy_K(self, stock):
        """ 拿到画K线的必要数据 """
        df = self.s.get_factor_value("Basic_factor", [stock], self.date_list,
                                     ["close", "low", "high", "open", "amt"])
        df.reset_index(inplace=True)
        df.rename(columns={"mddate": "date"}, inplace=True)
        return df

    def __get_daily_fitness(self, stock, freq, factor_list):
        """ 调用DolphinDB，得到每天的评价 (IC, RankIC)"""
        if isinstance(factor_list, list):
            tmp = self.fp.load_factor_analysis_res(data_type=self.data_type, factor_list=factor_list,
                                                   start_date=self.start_date, end_date=self.end_date,
                                                   stock=stock, label_name=self.label_name)
        else:
            tmp_list = []
            fac_num = len(self.factor_name_list)
            if fac_num > 100:
                for i in range(fac_num // 100 + 1):
                    factors = self.factor_name_list[i * 100: (i + 1) * 100]
                    tmp_i = self.fp.load_factor_analysis_res(data_type=self.data_type, factor_list=factors,
                                                             start_date=self.start_date, end_date=self.end_date,
                                                             stock=stock, label_name=self.label_name)
                    if not tmp_i.empty:
                        tmp_list.append(tmp_i)
            else:
                factors = self.factor_name_list
                tmp_i = self.fp.load_factor_analysis_res(data_type=self.data_type, factor_list=factors,
                                                         start_date=self.start_date, end_date=self.end_date,
                                                         stock=stock, label_name=self.label_name)
                if not tmp_i.empty:
                    tmp_list.append(tmp_i)
            if tmp_list:
                tmp = pd.concat(tmp_list)
            else:
                return pd.DataFrame()
        tmp = tmp[["MDDate", "stock", "normal_ic", "rank_ic", "factor_name"]]
        try:
            tmp["MDDate"] = tmp["MDDate"].apply(lambda x: dt.datetime.strftime(x, "%Y%m%d"))
        except:
            tmp["MDDate"] = tmp["MDDate"].apply(
                lambda x: dt.datetime.strftime(dt.datetime.strptime(x, "%Y-%m-%d"), "%Y%m%d"))
        tmp = tmp[(tmp["MDDate"] >= self.start_date) & (tmp["MDDate"] <= self.end_date)]
        tmp.rename(columns={"MDDate": "date"}, inplace=True)
        tmp["freq"] = freq
        return tmp

    def __get_ic_rankic_data(self, stock, factors):
        daily_k = self.__get_daliy_K(stock)
        tmp = self.__get_daily_fitness(stock, freq=self.freq, factor_list=factors)
        if tmp.empty:
            print("因子评价数据为空！IC&RankIC存储失败！")
            return pd.DataFrame()
        data_p = pd.merge(daily_k, tmp, left_on=["date", "stock"], right_on=["date", "stock"])
        return data_p

    def ic_rankic_data_todb(self, factors=None):
        # factors传因子列表时，更新指定因子的数据，否则更新全库因子
        self.set_stocks_factors()
        data = self.__get_ic_rankic_data(self.symbol, factors)
        if data.empty:
            print("ic_rankic_data is empty!!")
            return
        data["label_name"] = self.label_name
        data["create_time"] = self.time
        data["update_time"] = self.time
        data_dct = data.to_dict(orient="records")
        findfilter = {
            'date': {'$gte': self.start_date, '$lte': self.end_date},
            'label_name': data.iloc[0]['label_name'],
            'freq': data.iloc[0]['freq'],
            'stock': data.iloc[0]['stock'],
        }
        mdb.data_to_mongo(db_table="plot_ic_rankic_k_data_new", data_dct=data_dct, findfilter=findfilter)

    def get_ic_rankic_data(self, factor, stock):
        conditions = [{"date": {"$gte": self.start_date}}, {"date": {"$lte": self.end_date}},
                      {"stock": {"$eq": stock}}, {"freq": {"$eq": self.freq}},
                      {"label_name": {"$eq": self.label_name}}, {"factor_name": {"$eq": factor}}]
        df = self.__query_func("plot_ic_rankic_k_data_new", conditions)
        return df

    def __calc_factor_corr(self, df):
        df_corr = df.corr()
        df_corr = pd.DataFrame(df_corr.stack())
        df_corr.index.names = ["factor_name1", "factor_name2"]
        df_corr.columns = ["factor_corr"]
        df_corr.reset_index(inplace=True)
        return df_corr

    def factor_corr_data_todb(self, stock_list):
        # 因子相关性-热力图数据
        # 因子相关性：取测试区间数据，【因子，标的，因子值，时间戳】，遍历标的的计算时间段内两两因子的相关性，然后计算所有标的相关性的均值
        self.set_stocks_factors()
        date_range = "{}_{}".format(self.start_date, self.end_date)
        df_corr_list = []
        for stock in stock_list:
            df_fac_label = self.fp.load_public_data_from_dfs(symbol=[stock], factor_list=self.factor_name_list,
                                                             factor_type='factor', start_time=self.start_date,
                                                             end_time=self.end_date, data_type=self.data_type)
            if df_fac_label.empty:
                return pd.DataFrame()
            df_fac_label.drop("R_HTSCSecurityID", axis=1, inplace=True)
            df_fac_label.rename(columns={"M_HTSCSecurityID": "symbol"}, inplace=True)
            if not df_fac_label.empty:
                df_fac_label.drop(["timestamp", "symbol"], axis=1, inplace=True)
                df_corr_s = self.__calc_factor_corr(df_fac_label)
                if not df_corr_s.empty:
                    df_corr_list.append(df_corr_s)
        df_corr_1 = pd.concat(df_corr_list)
        df_corr = df_corr_1.groupby(["factor_name1", "factor_name2"])["factor_corr"].mean()
        df_corr = pd.DataFrame(df_corr)
        df_corr.reset_index(inplace=True)

        df_corr["label_name"] = self.label_name
        df_corr["period"] = self.period
        df_corr["date_range"] = date_range
        df_corr["freq"] = self.freq
        df_corr["create_time"] = self.time
        df_corr["update_time"] = self.time
        data_dct = df_corr.to_dict(orient="records")

        findfilter = {
            'date_range': df_corr.iloc[0]['date_range'],
            'period': df_corr.iloc[0]['period'],
            'label_name': df_corr.iloc[0]['label_name'],
        }
        mdb.data_to_mongo(db_table="plot_factor_correlation_data_new", data_dct=data_dct, findfilter=findfilter)

    def __query_func(self, db_table, conditions):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db[db_table]
        try:
            df = pd.DataFrame(
                list(model_collection.find({"$and": conditions})))
            client.close()
            return df
        except pymongo.errors.PyMongoError as e:
            print(f"{db_table} Error occurred while finding data: {e}")
            client.close()
            return pd.DataFrame()

    def query_longshort_data(self, date=None, stock=None, factor_name=None, label_name=None, freq=None):
        conditions = []
        if date:
            conditions.append({"date": {"$eq": date}})
        if stock:
            conditions.append({"stock": {"$eq": stock}})
        if factor_name:
            conditions.append({"factor_name": {"$eq": factor_name}})
        if label_name:
            conditions.append({"label_name": {"$eq": label_name}})
        if freq:
            conditions.append({"freq": {"$eq": freq}})
        res = self.__query_func("plot_long_short_data_new", conditions)
        return res

    def query_factor_label_data(self, date=None, symbol=None, factor_name=None, label_name=None, freq=None):
        conditions = []
        if date:
            conditions.append({"date": {"$eq": date}})
        if symbol:
            conditions.append({"symbol": {"$eq": symbol}})
        if factor_name:
            conditions.append({"factor_name": {"$eq": factor_name}})
        if label_name:
            conditions.append({"label_name": {"$eq": label_name}})
        if freq:
            conditions.append({"freq": {"$eq": freq}})
        res = self.__query_func("plot_factor_label_distribution_data_new", conditions)
        return res

    def query_radar_data(self, symbol=None, factor_name=None, label_name=None, freq=None,
                         date_range=None):
        conditions = []
        if symbol:
            conditions.append({"symbol": {"$eq": symbol}})
        if factor_name:
            conditions.append({"factor_name": {"$eq": factor_name}})
        if label_name:
            conditions.append({"label_name": {"$eq": label_name}})
        if freq:
            conditions.append({"freq": {"$eq": freq}})
        if date_range:
            conditions.append({"date_range": {"$eq": date_range}})
        res = self.__query_func("plot_radar_chart_data_new", conditions)
        return res

    def query_ic_rankic_data(self, date=None, stock=None, factor_name=None, label_name=None, freq=None):
        conditions = []
        if date:
            conditions.append({"date": {"$eq": date}})
        if stock:
            conditions.append({"stock": {"$eq": stock}})
        if factor_name:
            conditions.append({"factor_name": {"$eq": factor_name}})
        if label_name:
            conditions.append({"label_name": {"$eq": label_name}})
        if freq:
            conditions.append({"freq": {"$eq": freq}})
        res = self.__query_func("plot_ic_rankic_k_data_new", conditions)
        return res

    def query_factor_correlation_data(self, label_name=None, freq=None, date_range=None,
                                      factor_name1=None, factor_name2=None):
        conditions = []
        if label_name:
            conditions.append({"label_name": {"$eq": label_name}})
        if freq:
            conditions.append({"freq": {"$eq": freq}})
        if date_range:
            conditions.append({"date_range": {"$eq": date_range}})
        if factor_name1:
            conditions.append({"factor_name1": {"$eq": factor_name1}})
        if factor_name2:
            conditions.append({"factor_name2": {"$eq": factor_name2}})
        res = self.__query_func("plot_factor_correlation_data_new", conditions)
        return res

    def query_transaction_data(self, symbol=None, strategy_name=None, strategy_config_alias=None,
                               label_name=None, tradeDate=None, is_operation=True):
        conditions = []
        if symbol:
            conditions.append({"symbol": {"$eq": symbol}})
        if strategy_name:
            conditions.append({"strategy_name": {"$eq": strategy_name}})
        if strategy_config_alias:
            conditions.append({"strategy_config_alias": {"$eq": strategy_config_alias}})
        if label_name:
            conditions.append({"label_name": {"$eq": label_name}})
        if tradeDate:
            conditions.append({"tradeDate": {"$eq": tradeDate}})
        if is_operation:
            db_table = "online_transaction_data_new"
        else:
            db_table = "offline_transaction_data_new"
        res = self.__query_func(db_table, conditions)
        return res

    def query_transaction_performance_data(self, exp_id=None, version_alias=None, symbol=None,
                                           date=None, strategy_name=None, strategy_alias=None,
                                           T0=None, is_operation=True):
        conditions = []
        if exp_id:
            conditions.append({"exp_id": {"$eq": exp_id}})
        if version_alias:
            conditions.append({"version_alias": {"$eq": version_alias}})
        if symbol:
            conditions.append({"symbol": {"$eq": symbol}})
        if date:
            conditions.append({"date": {"$eq": date}})
        if strategy_name:
            conditions.append({"strategy_name": {"$eq": strategy_name}})
        if strategy_alias:
            conditions.append({"strategy_alias": {"$eq": strategy_alias}})
        if T0:
            conditions.append({"T0": {"$eq": T0}})
        if is_operation:
            db_table = "online_transaction_performance_data_new"
        else:
            db_table = "offline_transaction_performance_data_new"
        res = self.__query_func(db_table, conditions)
        return res

    def __delete_data(self, db_table, findfilter):
        client = pymongo.MongoClient(self.mongo)
        db = client[self.database]
        model_collection = db[db_table]
        try:
            existing_data = model_collection.find_one(findfilter)
            if existing_data:
                model_collection.delete_many(findfilter)
                print(f'{db_table} data delete success')
            client.close()
            return True
        except pymongo.errors.PyMongoError as e:
            # 如果插入过程中发生错误，打印错误信息
            print(f"{db_table} - Error occurred while delete data:", e)
            client.close()
            return False

    def delete_radar_data(self, date_range, label_name=None, factor_name=None, symbol=None, freq=None):
        findfilter = {"date_range": date_range}
        if label_name:
            findfilter["label_name"] = label_name
        if factor_name:
            findfilter["factor_name"] = factor_name
        if symbol:
            findfilter["symbol"] = symbol
        if freq:
            findfilter["freq"] = freq

        self.__delete_data("plot_radar_chart_data_new", findfilter)

    def delete_longshort_data(self, freq, date=None, stock=None, factor_name=None, label_name=None):
        findfilter = {"freq": freq}
        if date:
            findfilter["date"] = date
        if stock:
            findfilter["stock"] = stock
        if factor_name:
            findfilter["factor_name"] = factor_name
        if label_name:
            findfilter["label_name"] = label_name

        self.__delete_data("plot_long_short_data_new", findfilter)

    def delete_ic_rankic_data(self, freq, date=None, stock=None, factor_name=None, label_name=None):
        findfilter = {"freq": freq}
        if date:
            findfilter["date"] = date
        if stock:
            findfilter["stock"] = stock
        if factor_name:
            findfilter["factor_name"] = factor_name
        if label_name:
            findfilter["label_name"] = label_name

        self.__delete_data("plot_ic_rankic_k_data_new", findfilter)

    def delete_factor_correlation_data(self, freq, label_name=None, date_range=None):
        findfilter = {"freq": freq}
        if label_name:
            findfilter["label_name"] = label_name
        if date_range:
            findfilter["date_range"] = date_range

        self.__delete_data("plot_factor_correlation_data_new", findfilter)

    def delete_factor_label_data(self, freq, symbol=None, label_name=None, factor_name=None):
        findfilter = {"freq": freq}
        if symbol:
            findfilter["symbol"] = symbol
        if label_name:
            findfilter["label_name"] = label_name
        if factor_name:
            findfilter["factor_name"] = factor_name
        self.__delete_data("plot_factor_label_distribution_data_new", findfilter)
