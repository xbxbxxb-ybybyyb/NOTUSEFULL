import os
import gc
import datetime
import sys
import shutil
from xgboost import XGBRegressor, XGBClassifier
import numpy as np
import pandas as pd
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from sklearn.metrics import mean_squared_error as mse
import ray
from artifacts import exp_artifacts, model_save_and_evaluate, parse_format, backtest_save_and_evaluate, model_plot
from artifacts.run.parallel_xbrain_backtest import parallel_run
from artifacts.factor_save_and_evaluate import get_prepared

import time
import json
pd.set_option('display.max_colwidth', 200)
pd.set_option('display.max_rows', 50)

import os
import pickle
from tqdm import tqdm
import polars as pl


def __select_factor_by_analysis(fp, data_type, symbol, start_date, end_date, tagger_name_list, thres_limit):
    res_list = []
    for year in range(int(start_date[:4]), int(end_date[:4]) + 1):
        year_start = max("{}0101".format(year), start_date)
        year_end = min("{}1231".format(year), end_date)
        print("__select_factor_by_analysis", year_start, year_end)
        res = fp.load_factor_analysis_res(data_type=data_type, stock=symbol, start_date=year_start, end_date=year_end,
                                          label_name=tagger_name_list[0])
        res_list.append(res)
    res = pd.concat(res_list, axis=0)
    print("factor analysis dateframe shape: ", res.shape)

    valid_count = res["valid_count"].quantile(0.1)
    factor_res = res[res["valid_count"] >= valid_count].groupby("factor_name").mean()

    # 删选因子数据
    thres_1, thres_2 = thres_limit
    factor_res_filter = factor_res[(factor_res["normal_ic"] >= thres_2) | (factor_res["normal_ic"] <= thres_1)]
    factor_res_filter = factor_res_filter[~np.isnan(factor_res_filter["tratified_short_p_value_10"])]
    print("select_factor_res_filter shape: ", factor_res_filter.shape)
    select_factors = list(set(factor_res_filter.index.tolist()))
    fac = fp.load_info_from_dfs(factor_type="factor", source_type="public", data_type="tick_l2p")
    select_factors = set(select_factors) & set(fac)
    select_factors = list(select_factors)
    #     print("select_factors", select_factors)
    return select_factors, factor_res_filter


def factor_process(model_config, factor_label_df, label_name, w_size, parallel_mode=False):
    # 将DataFrame转换为numpy数组
    feature_label_df_train = factor_label_df[
        (factor_label_df.index >= pd.to_datetime(model_config["train_start_time"])) &
        (factor_label_df.index <= pd.to_datetime(model_config["train_end_time"]))]
    feature_label_df_valid = factor_label_df[
        (factor_label_df.index >= pd.to_datetime(model_config["valid_start_time"])) &
        (factor_label_df.index <= pd.to_datetime(model_config["valid_end_time"]))]
    feature_label_df_test = factor_label_df[
        (factor_label_df.index >= pd.to_datetime(model_config["test_start_time"])) &
        (factor_label_df.index <= pd.to_datetime(model_config["test_end_time"]))]

    T_train, X_train, Y_train = get_prepared(feature_label_df_train, label_name,
                                             w_size, parallel_mode=parallel_mode)
    print("T_train, X_train, Y_train: ", len(T_train), X_train.shape, Y_train.shape)
    T_valid, X_valid, Y_valid = get_prepared(feature_label_df_valid, label_name,
                                             w_size, parallel_mode=parallel_mode)
    print("T_valid, X_valid, Y_valid: ", len(T_valid), X_valid.shape, Y_valid.shape)
    T_test, X_test, Y_test = get_prepared(feature_label_df_test, label_name,
                                          w_size,
                                          parallel_mode=parallel_mode)
    print("T_test, X_test, Y_test: ", len(T_test), X_test.shape, Y_test.shape)

    if parallel_mode:
        X_train = X_train[:, 0]
        Y_train = Y_train[:, 0]
        X_valid = X_valid[:, 0]
        Y_valid = Y_valid[:, 0]
        X_test = X_test[:, 0]
        Y_test = Y_test[:, 0]

    return T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test


def __factor_process_filter_by_flying(model_config, factor_label_df, flying_factor_df, label_name, w_size,
                                      object_spill_path="/dfs/user/013150/tmp/", parallel_mode=False):
    # 将DataFrame转换为numpy数组
    feature_label_df_train = factor_label_df[
        (factor_label_df.index >= pd.to_datetime(model_config["train_start_time"])) &
        (factor_label_df.index <= pd.to_datetime(model_config["train_end_time"]))]
    feature_label_df_valid = factor_label_df[
        (factor_label_df.index >= pd.to_datetime(model_config["valid_start_time"])) &
        (factor_label_df.index <= pd.to_datetime(model_config["valid_end_time"]))]
    feature_label_df_test = factor_label_df[
        (factor_label_df.index >= pd.to_datetime(model_config["test_start_time"])) &
        (factor_label_df.index <= pd.to_datetime(model_config["test_end_time"]))]
    
    ###################################################
    flying_factor = model_config["data_config"]["flying_factor"]
    target_columns = factor_label_df.columns.to_list() + flying_factor
    merge_df = pd.merge(feature_label_df_train, flying_factor_df, left_index=True, right_index=True, how = "left")#耗时长
    merge_df = merge_df[merge_df["open_flying"]!=0]
    
    new_feature_label_df_train = merge_df.reindex(columns = target_columns)
    print("feature_label_df_train: ",feature_label_df_train.shape, ", new_feature_label_df_train: ", new_feature_label_df_train.shape)
        
    T_train, X_train, Y_train = get_prepared(new_feature_label_df_train, label_name,
                                             w_size, parallel_mode=parallel_mode)
    print("T_train, X_train, Y_train: ", len(T_train), X_train.shape, Y_train.shape)

    ###################################################
    merge_df = pd.merge(feature_label_df_valid, flying_factor_df, left_index=True, right_index=True, how="left")
    merge_df = merge_df[merge_df["open_flying"] != 0]
    new_feature_label_df_valid = merge_df.reindex(columns=target_columns)
    print("feature_label_df_valid: ", feature_label_df_valid.shape, ", new_feature_label_df_valid: ",
          new_feature_label_df_valid.shape)

    T_valid, X_valid, Y_valid = get_prepared(new_feature_label_df_valid, label_name,
                                             w_size, parallel_mode=parallel_mode)
    print("T_valid, X_valid, Y_valid: ", len(T_valid), X_valid.shape, Y_valid.shape)
    ###################################################
    merge_df = pd.merge(feature_label_df_test, flying_factor_df, left_index=True, right_index=True, how="left")
    merge_df = merge_df[merge_df["open_flying"] != 0]
    new_feature_label_df_test = merge_df.reindex(columns=target_columns)
    print("feature_label_df_test: ", feature_label_df_test.shape, ", new_feature_label_df_test: ",
          new_feature_label_df_test.shape)
    T_test, X_test, Y_test = get_prepared(new_feature_label_df_test, label_name,
                                          w_size,
                                          parallel_mode=parallel_mode)
    print("T_test, X_test, Y_test: ", len(T_test), X_test.shape, Y_test.shape)

    if parallel_mode:
        X_train = X_train[:, 0]
        Y_train = Y_train[:, 0]
        X_valid = X_valid[:, 0]
        Y_valid = Y_valid[:, 0]
        X_test = X_test[:, 0]
        Y_test = Y_test[:, 0]

    return T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test


def load_factor_label(fp, data_type, start_date, end_date, stock, factor_list, label_list, tagger_limit):
    # factor_list_all = list(self.fp.load_info_from_dfs('factor', 'public', self.data_type))
    if True:
        factor_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=factor_list[:],
                                                     start_time=start_date,
                                                     end_time=end_date, factor_type='factor',
                                                     data_type=data_type)
        factor_df_all = factor_df_all.set_index('timestamp')

        label_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=label_list,
                                                    start_time=start_date,
                                                    end_time=end_date, factor_type='label',
                                                    data_type=data_type)
        label_df_all = label_df_all.set_index('timestamp')
        for label_name in label_list:
            # 过滤极值
            label_df_all = label_df_all[
                abs(label_df_all[label_name]) <= tagger_limit]
        print("factor_df_all shape:", factor_df_all.shape, "label_df_all shape:", label_df_all.shape)
        source_factor_label_df = pd.merge(factor_df_all, label_df_all, left_index=True, right_index=True)
        print("source_factor_label_df shape: ", source_factor_label_df.shape)
        return source_factor_label_df
        # source_factor_label_df.to_parquet(os.path.join(self.exp_path, "dataset/factor_label_df.parquet"))
    else:
        source_factor_label_df = pd.read_parquet(os.path.join(exp_path, "dataset/factor_label_df.parquet"))
        print("source_factor_label_df shape: ", source_factor_label_df.shape)
        return source_factor_label_df


def clip_norm(feature_arr, factor_mean=None, factor_std=None):
    arr = feature_arr  # feature_df.values
    if not factor_mean:
        factor_mean = np.nanmean(arr, axis=0)
    if not factor_std:
        factor_std = np.nanstd(arr, axis=0)
    clip_lower = factor_mean - 3 * factor_std
    clip_upper = factor_mean + 3 * factor_std
    cliped_arr = np.clip(arr, clip_lower, clip_upper)
    featured_arr = (cliped_arr - factor_mean) / factor_std  # stats.zscore(cliped_df, nan_policy='omit')
    return featured_arr


## 盘口即时特征删选时间段
def load_flying_factors(symbol, dates=None, use_pandas=True):
    def resample_flying_factors(edf, use_pandas=True):
        if use_pandas:
            how_method_dict = {
                'ActivePriceVolume': "sum",
                'BreakingP0NumOrders': 'sum',
                'OneBigOrder': 'sum',
                'CumOrdersNetVolOverV0': 'sum',
                'PriceSpread': 'sum',
                'LevelOneChange': 'sum',
            }
            how_method_dict = {k: v for k, v in how_method_dict.items() if k in edf.columns}

            edf_resample = edf.resample(rule='1s', closed='right', label='right').agg(how_method_dict)
            edf_resample = edf_resample.rolling(5).agg({
                'ActivePriceVolume': "mean",
                'BreakingP0NumOrders': "mean",
                'OneBigOrder': "mean",
                'CumOrdersNetVolOverV0': "mean",
                'PriceSpread': "mean",
                'LevelOneChange': lambda x: x.iloc[-1],
            })
            # print("edf_resample:", edf_resample.groupby("MDDate")["ActivePriceVolume"].count().iloc[0])

            edf_resample["open_flying"] = (abs(edf_resample["PriceSpread"]) >= 0.2 ) |                                           (abs(edf_resample["BreakingP0NumOrders"]) >=0.2 ) |                                           (abs(edf_resample["OneBigOrder"])>=0.2) |                                           (abs(edf_resample["CumOrdersNetVolOverV0"])>=0.2
                                           #                                            (edf_resample["ActivePriceVolume"]!=0)
                                           )
            edf_resample["close_flying"] = (edf_resample["LevelOneChange"] != 0)
        #             edf_resample = edf_resample[((edf_resample["MDTime"] >= 93000000) & (edf_resample["MDTime"] <= 113000000)) | ((edf_resample["MDTime"] >= "130000000") & (edf_resample["MDTime"] <= "150000000"))]
        else:
            # Define the aggregation methods for resampling
            how_method_dict = {
                'ActivePriceVolume': pl.col('ActivePriceVolume').sum(),
                'BreakingP0NumOrders': pl.col('BreakingP0NumOrders').sum(),
                'OneBigOrder': pl.col('OneBigOrder').sum(),
                'CumOrdersNetVolOverV0': pl.col('CumOrdersNetVolOverV0').sum(),
                'PriceSpread': pl.col('PriceSpread').sum(),
                'LevelOneChange': pl.col('LevelOneChange').sum(),
            }
            how_method_dict = {k: v for k, v in how_method_dict.items() if k in edf.columns}
            if len(edf)==0:
                return pl.DataFrame()

            # Resample (downsample) the DataFrame
            # polars的resample不会补全缺失的秒
            edf_resample = edf.with_columns(pl.col("DateTime").set_sorted()).                group_by_dynamic(index_column = 'DateTime', every='1s', closed="right", label = "right").agg(**how_method_dict)

#              # Apply rolling window operations
#             ###########################指数滑动平均效果不好##############################
#             # 且polars的resample不会补全缺失的秒，导致rolling_mean结果和pandas不一致
#             edf_resample = edf_resample.lazy(). \
#                             with_columns(pl.Series(name="id", values=list(range(len(edf_resample)))).set_sorted()). \
#                             rolling(index_column = "DateTime",period = '5s').agg(
#                             pl.col('ActivePriceVolume').last().alias('ActivePriceVolume'),
#                             pl.col('BreakingP0NumOrders').mean().alias('BreakingP0NumOrders'),
#                             pl.col('OneBigOrder').last().alias('OneBigOrder'),
#                             pl.col('CumOrdersNetVolOverV0').mean().alias('CumOrdersNetVolOverV0'),
#                             pl.col('PriceSpread').mean().alias('PriceSpread'),
#                             pl.col('LevelOneChange').last().alias('LevelOneChange'),
#                             pl.col('Timestamp').last().alias('Timestamp'),
#                             pl.col('MDDate').last().alias('MDDate'),
#                             pl.col('MDTime').last().alias('MDTime')
#                 ).collect()
#             edf_resample = edf_resample.lazy(). \
#                 with_columns(pl.Series(name="id", values=list(range(len(edf_resample)))).set_sorted()). \
#                 rolling(index_column="DateTime", period='4s').agg(
#                 pl.col('ActivePriceVolume').ewm_mean(alpha=0.4).last().alias('ActivePriceVolume'),
#                 pl.col('BreakingP0NumOrders').ewm_mean(alpha=0.4).last().alias('BreakingP0NumOrders'),
#                 pl.col('OneBigOrder').ewm_mean(alpha=0.4).last().alias('OneBigOrder'),
#                 pl.col('CumOrdersNetVolOverV0').ewm_mean(alpha=0.4).last().alias('CumOrdersNetVolOverV0'),
#                 pl.col('PriceSpread').ewm_mean(alpha=0.4).last().alias('PriceSpread'),
#                 pl.col('LevelOneChange').last().alias('LevelOneChange'),
#             ).collect()
            # Compute 'open_flying' and 'close_flying' columns
            open_flying = (pl.col('PriceSpread').abs() >= 1) | \
                          (pl.col('BreakingP0NumOrders').abs() >= 1) | \
                          (pl.col('OneBigOrder').abs() >= 1) | \
                          (pl.col('CumOrdersNetVolOverV0').abs() >= 1)
            close_flying = pl.col('LevelOneChange') != 0
            edf_resample = edf_resample.with_columns([
                open_flying.alias('open_flying'),
                close_flying.alias('close_flying')
            ])
            # length = len(edf_resample)
            # extend_window = 5
            # open_flying_extend = np.zeros(length)
            # # 每个事件往后多看5条数据
            # for ridx, row in enumerate(edf_resample.select("open_flying").iter_rows()):
            #     if row[0] and ridx<length-extend_window:
            #         for i in range(extend_window):
            #             open_flying_extend[ridx+i] = 1
            # edf_resample = edf_resample.with_columns(pl.Series("open_flying_extend", open_flying_extend))
        return edf_resample
    

    ###########################################
    if not dates:
        from xquant.factordata import FactorData
        fa = FactorData()
        start_date = model_config["train_start_time"]
        end_date = model_config["test_end_time"]
        dates = fa.tradingday(start_date, end_date)
    flying_base_dir = "/dfs/group/800657/library/l3_event/event_data"
    data_list = []
    ###########################################
    if use_pandas:
        for date in tqdm(dates):
            sub_edf = pd.read_parquet(os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date)))
            sub_edf = sub_edf.set_index('DateTime')
            try:
                if not sub_edf.empty:
                    sub_edf_resample = resample_flying_factors(sub_edf)
                    data_list.append(sub_edf_resample)
            except Exception as e:
                print(e, "sub_edf_resample error: ",symbol ," ", date)
        edf_resample = pd.concat(data_list)
        print("edf_resample:", edf_resample.shape)
        # 用polars读取速度快10倍
        # edf_resample.to_parquet(os.path.join(flying_base_dir, "{}.pqt".format(symbol)))
    else:
        for date in tqdm(dates):
            try:
                sub_edf = pl.read_parquet(os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date)))
            except:
                time.sleep(3)
                sub_edf = pl.read_parquet(os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date)))
            sub_edf = sub_edf.with_columns(pl.col("LevelOneChange").cast(pl.Float32))
            sub_edf_resample = resample_flying_factors(sub_edf, use_pandas = use_pandas)
            if not len(sub_edf) == 0:
                data_list.append(sub_edf_resample)
        edf_resample = pl.concat(data_list)
        #         edf_resample = edf_resample.to_pandas()
        #         edf_resample.set_index("DateTime", inplace = True)
        print("edf_resample", edf_resample.shape)
        # edf_resample.write_parquet(os.path.join(flying_base_dir, "{}.pqt".format(symbol)))
    return edf_resample


def merge_flying_factor(T_train, X_train, Y_train, edf_resample, flying_factor, use_pandas = False):
    if use_pandas:
        ttrain_df = pd.DataFrame(T_train, columns = ["DateTime"])

        open_flying_df = ttrain_df.join(edf_resample, on = "DateTime")
        open_flying_df = open_flying_df[open_flying_df["open_flying"]!=0]
        valid_idx = ttrain_df['DateTime'].isin(open_flying_df["DateTime"])
        valid_idx = valid_idx.values.flatten()
        
        T_train_resample = np.array(T_train)[valid_idx]
        X_train_resample = X_train[valid_idx]
        Y_train_resample = Y_train[valid_idx]
        F_train_resample = open_flying_df.select(flying_factor).to_numpy()
        
        assert F_train_resample.shape[0] == X_train_resample.shape[0]
        print("X_train shape: ",X_train.shape, ", new_X_train shape: ", X_train_resample.shape)
        return T_train_resample, X_train_resample, Y_train_resample, F_train_resample

    else:
        ttrain_df = pl.from_pandas(pd.DataFrame(T_train, columns = ["DateTime"])).with_columns(
            pl.Series("id", list(range(len(T_train)))),
        #     pl.col("DateTime").dt.strftime(format="%Y%m%d%H%M%S")
        )
        open_flying_df = ttrain_df.join(edf_resample, on = "DateTime").filter(pl.col("open_flying")!=0)
        valid_idx = ttrain_df.select(pl.col('DateTime').is_in(open_flying_df["DateTime"])).to_numpy()
        valid_idx = valid_idx.flatten()
        
        T_train_resample = np.array(T_train)[valid_idx]
        X_train_resample = X_train[valid_idx]
        Y_train_resample = Y_train[valid_idx]
        F_train_resample = open_flying_df.select(flying_factor).to_numpy()
        
        assert F_train_resample.shape[0] == X_train_resample.shape[0]
        print("X_train shape: ",X_train.shape, ", new_X_train shape: ", X_train_resample.shape)
        return T_train_resample, X_train_resample, Y_train_resample, F_train_resample

    
def id_category(symbol_id,T_train,X_train,Y_train,T_valid,X_valid,Y_valid,T_test,X_test,Y_test):
    X_train_ = pd.DataFrame(X_train)
    X_train_["id"] = symbol_id
    X_train_["id"] = X_train_["id"].astype("category")
    
    X_valid_ = pd.DataFrame(X_valid)
    X_valid_["id"] = symbol_id
    X_valid_["id"] = X_valid_["id"].astype("category")
    
    X_test_ = pd.DataFrame(X_test)
    X_test_["id"] = symbol_id
    X_test_["id"] = X_test_["id"].astype("category")
    
    return T_train,X_train_,Y_train,T_valid,X_valid_,Y_valid,T_test,X_test_,Y_test

def generate_split_dataset(model_config, open_flying_df, type = "train"):
    if type == "train":
        start_date = model_config["train_start_time"]
        end_date = model_config["train_end_time"]
    elif type == "valid":
        start_date = model_config["valid_start_time"]
        end_date = model_config["valid_end_time"]
    elif type == "test":
        start_date = model_config["test_start_time"]
        end_date = model_config["test_end_time"]
    else:
        raise Exception()
        
    open_flying_df_train = open_flying_df.filter(
        (pl.col("DateTime") >= pl.lit(start_date).str.to_datetime("%Y%m%d")) &
        (pl.col("DateTime") <= pl.lit(end_date).str.to_datetime("%Y%m%d")))
    
    
    flying_factor = model_config["data_config"]["flying_factor"]
    select_factors = model_config["factor_name_list"]
    label_list = model_config["tagger_name_list"]

    T_train = open_flying_df_train.select(["DateTime"]).to_numpy().flatten()
    F_train = open_flying_df_train.select(flying_factor).to_numpy()
    X_train = open_flying_df_train.select(select_factors).to_numpy()
    Y_train = open_flying_df_train.select(label_list).to_numpy().flatten()
    
    #     T_train1,X_train1,Y_train1,T_valid1,X_valid1,Y_valid1,T_test1,X_test1,Y_test1 = id_category(
    #         symbol,T_train,X_train,Y_train,T_valid,X_valid,Y_valid,T_test,X_test,Y_test
    #     )
    mask_train = abs(Y_train)<=model_config["data_config"]["tagger_limit"]        
    X_train = np.concatenate((X_train, F_train), axis = 1)
    
    T_train,X_train, F_train, Y_train =  T_train[mask_train], X_train[mask_train], F_train[mask_train], Y_train[mask_train]

    return T_train,X_train, F_train, Y_train


def select_factors_multi(expa, model_config, fp):
    # # 加载因子数据
    factor_save_path = os.path.join(expa.path_of_exp_version(), "saved_models/factors.csv")
    if os.path.exists(factor_save_path):
        # # 加载因子数据
        select_factors = pd.read_csv(factor_save_path, header=None)[0].tolist()
        print("【Warning】已有因子筛选结果，将直接从文件加载...:")
        print("select_factors :", len(select_factors))
        print(select_factors)
        model_config["factor_name_list"] = select_factors
    else:
        data_type = model_config["data_config"]["data_type"]
        select_factors_dict = {}
        factor_res_filter_dict = {}
        for symbol in tqdm(model_config["symbol_list"]):
            print("symbol select_factor:", symbol)
            select_factors, factor_res_filter = __select_factor_by_analysis(fp, data_type,
                                                          symbol,
                                                          model_config["train_start_time"],
                                                          model_config["valid_end_time"],
                                                          model_config["tagger_name_list"],
                                                          model_config["data_config"]["thres"]
                                                          )
            select_factors_dict[symbol] = select_factors
            factor_res_filter_dict[symbol] = factor_res_filter

            from collections import defaultdict
            factor_count = defaultdict(int)
            valid_stock_count = {}
            for symbol in select_factors_dict:
                if not select_factors_dict[symbol]:
                    continue
                else:
                    valid_stock_count[symbol] = len(select_factors_dict[symbol])
                    for factor in select_factors_dict[symbol]:
                        factor_count[factor] = factor_count[factor] + 1

            print("每个标的的有效因子数valid_stock_count:", valid_stock_count)
            print("总因子数total_factor_count length:", len(factor_count))
            # 删选条件，被至少一半标的选中的因子
            downbound = min(len(valid_stock_count), max(int(len(valid_stock_count) / 4 * 1), 2))
            print("因子出现次数的下限: ", downbound)
            select_factors = [f for f, c in factor_count.items() if c >= downbound]
            print("select_factors length: ", len(select_factors))
            # select_factors
            model_config["factor_name_list"] = select_factors
            expa.model_factorlist_save(overwrite=True)
            print("factor_count:", factor_count)
            print(valid_stock_count)
    return select_factors


class L2PXGBoostRegPack:
    def __init__(self, exp_name, model_config, version_alias):
        self.data_type = "tick_l2p"
        self.expa = exp_artifacts.ExpArtifacts(exp_name=exp_name, exp_base="/dfs/group/800657/exp_results/")
        self.exp_path = self.expa.exp_path
        self.expa.activate_version_to_save(model_config, version_alias=version_alias)
        self.version_alias = version_alias
        self.model_config = model_config
        self.factor_name_list = model_config["factor_name_list"]
        self.tagger_name_list = model_config["tagger_name_list"]
        self.symbol_list = model_config["symbol_list"]
        self.exp_version_path = self.expa.path_of_exp_version()
        self.fp = FactorProvider('016884')



    def prepare_data(self, data_params):
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.select_factors = select_factors
        self.model_config["factor_name_list"] = select_factors
        model_config = self.model_config
        exp_path = self.exp_path
        fp =self.fp
        use_pandas = False
        factor_descibe_dict = {}
        label_list = model_config["tagger_name_list"]
        for symbol in model_config["symbol_list"]:
            source_data_path = os.path.join("/dfs/group/800657/exp_results/kc_dataset/{}_data.parquet".format(symbol))
            if not os.path.exists(source_data_path):
                factor_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=select_factors,
                                                             start_time=model_config["train_start_time"],
                                                             end_time=model_config["test_end_time"], factor_type='factor',
                                                             data_type=model_config["data_config"]["data_type"])
                factor_df_all = factor_df_all.set_index("timestamp")
                factor_df_all.reindex(columns = select_factors, copy = False)
                if not factor_df_all.empty:
        #                 factor_descibe_dict[symbol] = factor_label_df.describe()
                    factor_config = {}
                    factor_df_all_train = factor_df_all[
                        (factor_df_all.index >= pd.to_datetime(model_config["train_start_time"])) &
                        (factor_df_all.index <= pd.to_datetime(model_config["train_end_time"]))]
                    for factor_name in select_factors:
                        mean = factor_df_all_train[factor_name].mean()
                        std = factor_df_all_train[factor_name].std()
                        factor_config[factor_name] = {"mean":mean, "std":std}
                    with open(os.path.join(os.path.dirname(source_data_path), "{}_factor_config.json".format(symbol)), "w") as f:
                        json.dump(factor_config, f, indent=4)
                    norm_results = []
                    ########耗时2min左右#######
                    for f_name in tqdm(select_factors):
                        sub_result = clip_norm(factor_df_all[[f_name]].values, factor_config[f_name]["mean"], factor_config[f_name]["std"])
                        norm_results.append(sub_result)
                    normal_factor_arr = np.concatenate(norm_results, axis=1)
                    X_all = normal_factor_arr
                    T_all = factor_df_all.index.values
                    factor_norm_df_all = pl.from_numpy(X_all,schema = select_factors).with_columns(pl.Series(T_all).alias("DateTime"))
                    factor_norm_df_all.write_parquet(source_data_path)


            if not use_pandas:
                #######################合并数据##########################
                factor_norm_df_all = pl.read_parquet(source_data_path)
                label_df_all = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=label_list,
                                                                 start_time=model_config["train_start_time"],
                                                                 end_time=model_config["test_end_time"], factor_type='label',
                                                                 data_type=model_config["data_config"]["data_type"])
                label_df_all = label_df_all[["timestamp"]+label_list]
                label_df_all = pl.from_pandas(label_df_all).rename({"timestamp":"DateTime"})
                edf_resample_df_all = load_flying_factors(symbol, use_pandas = False)

                factor_label_df_all = factor_norm_df_all.join(label_df_all, on = "DateTime")
                # 筛选事件数据
                open_flying_df = factor_label_df_all.join(edf_resample_df_all, on = "DateTime").filter(pl.col("open_flying")!=0)
                if not os.path.exists(exp_path + "/dataset/"):
                    os.makedirs(exp_path + "/dataset/")
                open_flying_df.write_parquet(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol)))
                print(symbol, " : factor_label_df_all shape: ",factor_label_df_all.shape, ", open_flying_df shape: ", open_flying_df.shape)
                #########################################################



    def train_loop(self, model_params):
        exp_path = self.exp_path
        symbol_list = model_config["symbol_list"]
        flying_factor = model_config["data_config"]["flying_factor"]
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.model_config["factor_name_list"] = select_factors

        T_train_list,X_train_list,Y_train_list,T_valid_list = [], [], [], []
        X_valid_list,Y_valid_list,T_test_list,X_test_list,Y_test_list = [], [], [], [], []

        for symbol in symbol_list:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol))):
                print("无该标的数据：", symbol)
                continue
            open_flying_df = pl.read_parquet(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol)))
            ########################划分训练测试集################################
            T_train, X_train, F_train, Y_train = generate_split_dataset(model_config, open_flying_df, type = "train")
            T_valid, X_valid, F_valid, Y_valid = generate_split_dataset(model_config, open_flying_df, type = "valid")
            T_test, X_test, F_test, Y_test = generate_split_dataset(model_config, open_flying_df, type = "test")

        #     X_train = X_train.astype(np.float32)
        #     X_valid = X_valid.astype(np.float32)
        #     X_test = X_test.astype(np.float32)

            print("mask shape:", symbol, T_train.shape, Y_train.flatten())
            T_train_list.append(T_train[-1200000:])
            X_train_list.append(X_train[-1200000:])
            Y_train_list.append(Y_train[-1200000:])
            T_valid_list.append(T_valid)
            X_valid_list.append(X_valid)
            Y_valid_list.append(Y_valid)
            T_test_list.append(T_test)
            X_test_list.append(X_test)
            Y_test_list.append(Y_test)


        T_train_all = np.concatenate(T_train_list)
        X_train_all = np.concatenate(X_train_list)
        Y_train_all = np.concatenate(Y_train_list)
        T_valid_all = np.concatenate(T_valid_list)
        X_valid_all = np.concatenate(X_valid_list)
        Y_valid_all = np.concatenate(Y_valid_list)
        T_test_all = np.concatenate(T_test_list)
        X_test_all = np.concatenate(X_test_list)
        Y_test_all = np.concatenate(Y_test_list)
        del T_train_list
        del X_train_list
        del Y_train_list
        del T_valid_list
        del X_valid_list
        del Y_valid_list
        del T_test_list
        del X_test_list
        del Y_test_list
        gc.collect()

        self.model_config["xgb_config"]["n_estimators"] = 2000
        self.model_config["xgb_config"]['tree_method'] = 'gpu_hist'
        xgb_regressor = XGBRegressor(**self.model_config["xgb_config"], n_jobs=30)
        xgb_regressor.fit(X_train_all, Y_train_all,
              eval_set = [(X_train_all, Y_train_all),(X_valid_all, Y_valid_all)], #xgb_model = xgb_regressor_semiconductor,
              early_stopping_rounds = 8,
              verbose = True)

        # 模型文件存储
        self.expa.model_file_save(model_obj=xgb_regressor, mode=["pkl"], overwrite=True)
        importance_ = xgb_regressor.feature_importances_
        factor_importance = pd.DataFrame({'factor': select_factors+flying_factor, 'importance': importance_})
        factor_importance = factor_importance.sort_values(by='importance', ascending=False)
        print("factor_importance:", factor_importance.head(20))
        self.xgb_regressor = xgb_regressor


    def predict_signal(self, xgb_regressor):
        # 加载模型
        exp_path = self.exp_path
        model_config = self.model_config
        select_factors = select_factors_multi(self.expa, self.model_config, self.fp)
        self.model_config["factor_name_list"] = select_factors
        fp = self.fp
        expa = self.expa
        fp = FactorProvider('016884')

        for symbol in model_config["symbol_list"]:
            if not os.path.exists(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol))):
                print("无该标的数据：", symbol)
                continue
            open_flying_df = pl.read_parquet(os.path.join(exp_path, "dataset/{}_flying_data.parquet".format(symbol)))
            T_test, X_test, F_test, Y_test = generate_split_dataset(model_config, open_flying_df, type = "test")
            print(X_test.shape, Y_test.shape)
            factor_df = fp.load_public_data_from_dfs(symbol=[symbol], factor_list=["ReferenceMidPrice"],
                                                          start_time=model_config["test_start_time"],
                                                          end_time=model_config["test_end_time"], factor_type='factor',
                                                          data_type=model_config["data_config"]["data_type"])
            factor_df = factor_df.set_index("timestamp")
            target_values = factor_df["ReferenceMidPrice"].loc[T_test].values
            # 预测信号
            Y_test_pred = xgb_regressor.predict(X_test)
            # Y_test_pred = (2*Y_test_pred+Y_test_pred_lgbm)/3
            print("test rmse", np.sqrt(mse(Y_test_pred, Y_test)))

            # 合成并存储标准信号数据
            signal_df = expa.model_signal_save(label_name=model_config["tagger_name_list"][0],
                                               symbol=symbol,
                                               tm_values=list(T_test), yhat_values=Y_test_pred, y_values=Y_test,
                                               target_values=target_values, period=120, target_type="mid")
            expa.model_signal_process_long_short_pred_th_classify(model_config["tagger_name_list"][0], symbol, pred_th_up = 1.5, pred_th_dw = -1.5)
            print("signal_df shape: ", signal_df.shape)


    def analysis_ic(self):
        for symbol_name in self.model_config["symbol_list"]:
            signal_df_load = self.expa.model_signal_load(version_alias=self.version_alias, symbol=symbol_name,
                                                    label_name=self.model_config["tagger_name_list"][0])
            print(symbol_name)
            print(signal_df_load[["PREDICTED", "LABEL_VALUE"]].corr())

    def analysis_signal_winloss(self, start_date="2023-12-06", end_date="2024-02-06"):
        def winloss_func(source_signal_df, long_pred_th, short_pred_th, start_date="2023-12-06", end_date="2024-02-06"):
            from artifacts.model_save_and_evaluate import model_signal_evaluation_winloss_stop_table_daily
            res_dict = model_signal_evaluation_winloss_stop_table_daily(source_signal_df,
                                                                        long_pred_th=long_pred_th,
                                                                        short_pred_th=short_pred_th,
                                                                        win_limits=[0.0015, 0.002],
                                                                        loss_limits=[0.002],
                                                                        t_sta="09:33:00"
                                                                        )
            res_df = res_dict[(0.0015, 0.002)]
            res_df = res_df[(res_df.index >= start_date) & (res_df.index <= end_date)]

            up_win_tol = round(res_df["涨信号止盈个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
            up_eq_tol = round(res_df["涨信号平个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
            up_loss_tol = round(res_df["涨信号止损个数"].sum() / res_df["涨信号个数"].sum(), 3) if res_df["涨信号个数"].sum() else 0
            up_num_tol = round(res_df["涨信号个数"].sum(), 3)
            up_win_day = round(res_df.mean()["涨信号止盈率"], 3)
            up_loss_day = round(res_df.mean()["涨信号止损率"], 3)
            up_eq_day = round(res_df.mean()["涨信号平率"], 3)
            up_num_day = round(res_df.mean()["涨信号个数"], 3)

            dw_win_tol = round(res_df["跌信号止盈个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
            dw_eq_tol = round(res_df["跌信号平个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
            dw_loss_tol = round(res_df["跌信号止损个数"].sum() / res_df["跌信号个数"].sum(), 3) if res_df["跌信号个数"].sum() else 0
            dw_num_tol = round(res_df["跌信号个数"].sum(), 3)
            dw_win_day = round(res_df.mean()["跌信号止盈率"], 3)
            dw_loss_day = round(res_df.mean()["跌信号止损率"], 3)
            dw_eq_day = round(res_df.mean()["跌信号平率"], 3)
            dw_num_day = round(res_df.mean()["跌信号个数"], 3)

            print(f"涨信号【总体】：信号个数: {up_num_tol}， 止盈率：{up_win_tol}, 平率： {up_eq_tol}， 止损率： {up_loss_tol}")
            print(f"跌信号【总体】：信号个数: {dw_num_tol}，止盈率：{dw_win_tol}, 平率： {dw_eq_tol}， 止损率： {dw_loss_tol}")
            print(f"涨信号日均：信号个数: {up_num_day}，止盈率：{up_win_day}，平率：{up_eq_day}, 止损率：{up_loss_day}")
            print(f"跌信号日均：信号个数: {dw_num_day}，止盈率：{dw_win_day}，平率：{dw_eq_day}, 止损率：{dw_loss_day}")
            eva_dict = {"涨信号总体": {"信号个数": up_num_tol, "止盈率": up_win_tol, "平率": up_eq_tol, "止损率": up_loss_tol},
                        "跌信号总体": {"信号个数": dw_num_tol, "止盈率": dw_win_tol, "平率": dw_eq_tol, "止损率": dw_loss_tol},
                        "涨信号日均": {"信号个数": up_num_day, "止盈率": up_win_day, "平率": up_eq_day, "止损率": up_loss_day},
                        "跌信号日均": {"信号个数": dw_num_day, "止盈率": dw_win_day, "平率": dw_eq_day, "止损率": dw_loss_day}}
            #     eva_dict = {"涨总信号个数": up_num_tol, "涨总止盈率":up_win_tol, "涨总平率": up_eq_tol, "涨总止损率": up_loss_tol,
            #         "涨信号个数": dw_num_tol,"涨总止盈率":dw_win_tol,"涨总平率": dw_eq_tol, "涨总止损率": dw_loss_tol,
            #         "涨总信号个数": up_num_day,"涨总止盈率":up_win_day,"涨日均平率":up_eq_day, "涨日均止损率":up_loss_day,
            #         "跌日信号个数": dw_num_day,"跌日均止盈率":dw_win_day,"跌日均平率":dw_eq_day, "跌日均止损率":dw_loss_day}
            return eva_dict

        for symbol_name in self.model_config["symbol_list"]:
            #     if symbol_name!="688012.SH":
            #         continue
            long_pred_th = 1.5
            short_pred_th = -1.5
            print(
                "=====================" + symbol_name + ":" + f"[{long_pred_th}, {short_pred_th}]" + "=====================")
            label_name = self.model_config["tagger_name_list"][0]
            source_signal_df = self.expa.model_signal_load(version_alias, label_name, symbol_name)
            res_df = winloss_func(source_signal_df.copy(), long_pred_th, short_pred_th,
                                  start_date=start_date, end_date=end_date)
            print(res_df)
        #     res_dict[(0.0015, 0.002)].to_csv(os.path.join(exp_version_path,
        #                                "pred_th_win_loss_{}_{}_{}.csv".format(1,5, model_config["test_start_time"], model_config["test_end_time"])))
        #     display(res_dict[(0.0015, 0.002)][res_dict[(0.0015, 0.002)].index<"2024-02-06"].mean())

    def dyanamic_evaluate(self):
        self.analysis_ic()
        self.analysis_signal_winloss(start_date=self.model_config["test_start_time"], end_date="2024-02-16")

    def xbrain_backtest(self):
        ray.init(num_cpus=30, ignore_reinit_error=True, local_mode=False,
                 _system_config={"object_spilling_config": json.dumps(
                     {"type": "filesystem", "params": {"directory_path": "/data/user/013150/tmp/"}, })})
        for th1 in [1.2, 1.4]:
            for probs_up in [0.64, 0.66]:
                # th1 = 1.2
                # probs_up = 0.62
                signal_process_dir = self.expa.path_of_signal_process_save(
                            label_name=self.model_config["tagger_name_list"][0],
                            symbol=self.model_config["symbol_list"][0],
                            label_th1=th1,
                            label_th2=2,
                            probs_up=probs_up,
                            probs_dw=probs_up)
                plot_save_dir = signal_process_dir.replace("signal_files_processed", "StrategySignalT0")
                print("signal_process_dir:", signal_process_dir)
                print("plot_save_dir: ", plot_save_dir)
                parallel_run(signal_process_dir, plot_save_dir, self.model_config["symbol_list"][0], th1=th1, prob1=probs_up)



def main(exp_name, model_config, version_alias , train_mode = True):
    # assert model_config!=None, "model_config不可为None！"
    instance = L2PXGBoostRegPack(exp_name=exp_name,
                                            model_config = model_config,
                                            version_alias=version_alias
                                            )
    if train_mode == True:
        instance.prepare_data(data_params={})
        instance.train_loop(model_params={})
        # instance.xgb_regressor = pd.read_pickle(os.path.join(instance.exp_version_path, "saved_models/tmp_model.pickle.dat"))
        instance.predict_signal(instance.xgb_regressor)
        instance.dyanamic_evaluate()
    else:
        # 只评价信号，不训练
        # instance.dyanamic_evaluate()
        instance.xbrain_backtest()


if __name__ == "__main__":
    #######################################################################
    model_config = {
        # 数据段配置
        "symbol_list": [],
        "train_start_time": "20210701",
        "train_end_time": "20230930",
        "valid_start_time": "20231001",
        "valid_end_time": "20231215",
        "test_start_time": "20231216",
        "test_end_time": "20240229",
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": [],

        "data_config": {
            "data_type": "tick_l2p",
            "w_size": 1,
            "n_job": 2,
            "transform": True,
            "clip_type": "3sigma",
            "scaler_type": "z-score",
            "quantile": [0.02, 0.98],
            "tagger_limit": 40,
            "raw_name_list": [],
            "thres": [-0.020, 0.020],
            "other_factor_list": "",
            # 因子列表， 为空的话为全量
            "factor_json_path": ""
        },
        # 模型段配置
        "xgb_config": {
            'objective': 'reg:squarederror',
            'booster': 'gbtree',
            'tree_method': 'hist',
            'gamma': 0.5,
            'learning_rate': 0.01,
            'lambda': 2,
            'subsample': 0.7,
            'colsample_bytree': 0.7,
            'max_depth': 13,
            'n_estimators': 1300,
            'seed': 4,
        },
        "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                    "reg_eval_th": 0.5},
        "model_save_mode": ["pkl", "onnx"],
    }
    SYMBOL_LIST = [
        "688981.SH",
        "688041.SH",
        "688271.SH",
        "688111.SH",
        "688012.SH",
        "688036.SH",
        "688008.SH",
        "688599.SH",
        "688256.SH",
        "688126.SH",
        "688169.SH",
        "688396.SH",
        "688777.SH",
        "688223.SH",
        "688303.SH",
        "688122.SH",
        "688099.SH",
        "688072.SH",
        "688120.SH",
        "688114.SH",
        "688047.SH",
        "688180.SH",
        "688188.SH",
        "688390.SH",
        "688728.SH",
        "688363.SH",
        "688301.SH",
        "688521.SH",
        "688220.SH",
        "688065.SH",
        "688063.SH",
        "688052.SH",
        #     "688032.SH",
        "688187.SH",
        "688005.SH",
        "688561.SH",
        "688234.SH",
        "688536.SH",
        "688385.SH",
        "688082.SH",
        "688349.SH",
        "688297.SH",
        #     "688348.SH",
        #     "688506.SH",
        #     "688819.SH",
        #     "688295.SH",
        #     "688375.SH"
    ]
    model_config["symbol_list"] = SYMBOL_LIST
    model_config["train_start_time"] = "20210101"
    model_config["train_end_time"] = "20231015"
    model_config["valid_start_time"] = "20231016"
    model_config["valid_end_time"] = "20231214"
    model_config["test_start_time"] = "20231215"
    model_config["test_end_time"] = "20240320"
    # model_config["train_start_time"] = "20240101"
    # model_config["train_end_time"] = "20240131"
    # model_config["valid_start_time"] = "20240201"
    # model_config["valid_end_time"] = "20240210"
    # model_config["test_start_time"] = "20240211"
    # model_config["test_end_time"] = "20240228"
    exp_name = "tmp"
    model_config["tagger_name_list"] = [] #"LabelFirstPeak_th10_60s"
    version_alias = "xgboost_base"
    flying_factor = ["PriceSpread", "OneBigOrder", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "LevelOneChange"]
    model_config["data_config"]["flying_factor"] = flying_factor
    ###################################################
    # /data/user/013150/online_scripts/shen/DolphindbFactors/labels/InfoTech/Factors
    for label_name, exp_name in [
            # ("LabelFirstPeakLongShort_th10_60s", "exp_l3_kc50_ls_th10_60s"),
            ("LabelLongOneMin", "exp_l3_kc50_ls_60s"),
            ("LabelFirstPeakSmooth_5_th10_60s", "exp_l3_kc50_smooth5_th10_60s"),
            ("LabelFirstPeak_th10_60s", "exp_l3_kc50_th10_60s"),
            ( "LabelLongTwoMin", "exp_l3_kc50_ls_120s"),
    ]:
        model_config["tagger_name_list"] = [label_name] #"LabelFirstPeak_th10_60s"
        if ray.is_initialized():
            ray.shutdown()
        try:
            ray.init(local_mode=True)
            base_dir = f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}"
            factor_path = f"{base_dir}/saved_models/factors.csv"
            if not os.path.exists(factor_path):
                os.makedirs(f"/dfs/group/800657/exp_results/{exp_name}/{version_alias}/saved_models")
                shutil.copyfile("/dfs/group/800657/exp_results/exp_l3_kc50_60s/xgboost_base/saved_models/factors.csv", factor_path)
        except Exception as e:
            print("ERRRO:", e)
        sys.stdout = open(f"/dfs/group/800657/exp_results/{exp_name}/{exp_name}_{datetime.datetime.now().strftime('%Y%m%d')}.txt", 'w')
        # sys.stderr = open(f"/dfs/group/800657/exp_results/{exp_name}/{exp_name}_{datetime.datetime.now().strftime('%Y%m%d')}.txt", 'w')
        t1 = time.time()
        main(exp_name=exp_name, model_config = model_config, version_alias = version_alias, train_mode = True)
        print("本次试验耗时：", time.time() - t1)

