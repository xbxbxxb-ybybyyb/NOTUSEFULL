import numpy as np
import pandas as pd
import os
from tqdm import tqdm
import copy
import polars as pl
from artifacts.factor_save_and_evaluate import get_prepared
from artifacts.model_metrics import *
from artifacts.parse_format import *
from artifacts.dataload_utils import *
from xquant.factordata import FactorData
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider


def load_factor_label(fp, data_type, start_date, end_date, stock, factor_list, label_list, tagger_limit, verbose = 1, factor_type = 'factor', factor_only = False):
    """
    :param fp:
    :param data_type:
    :param start_date:
    :param end_date:
    :param stock:
    :param factor_list:
    :param label_list:
    :param tagger_limit:
    :param verbose:
    :param factor_type:
    :param factor_only: 为True只加载银子，标签数据置为0
    :return:
    """
    # factor_list_all = list(self.fp.load_info_from_dfs('factor', 'public', self.data_type))
    if True:
        factor_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=factor_list[:],
                                                     start_time=start_date,
                                                     end_time=end_date, factor_type=factor_type,
                                                     data_type=data_type)
        factor_df_all = factor_df_all.set_index('timestamp')
        try:
            label_df_all = fp.load_public_data_from_dfs(symbol=[stock], factor_list=label_list,
                                                        start_time=start_date,
                                                        end_time=end_date, factor_type='label',
                                                        data_type=data_type)
            label_df_all = label_df_all.set_index('timestamp')
            label_df_all[label_list] = label_df_all[label_list].fillna(0.0)
            for label_name in label_list:
                # 过滤极值
                label_df_all[label_df_all[label_name] >= tagger_limit][label_name] = tagger_limit
                label_df_all[label_df_all[label_name] <= -tagger_limit][label_name] = -tagger_limit

        except RuntimeError:
            # 从polars 加载标签数据
            label_df_all = load_polars_label(stock, start_date, end_date, label_list[0])
            label_df_all = label_df_all.with_columns(pl.col(label_list[0]).fill_nan(0.0).alias(label_list[0]))
            # ############## 去除上市首月的数据, 避免极端行情的影响
            label_df_all = label_df_all.select(["DateTime", label_list[0]]).filter(pl.col(label_list[0]) <= tagger_limit)
            label_df_all = label_df_all.rename({"DateTime":"timestamp"}).to_pandas().set_index("timestamp")
        if len(label_df_all) > 0:
            # 合并因子和标签数据
            source_factor_label_df = pd.merge(factor_df_all, label_df_all, left_index=True, right_index=True)
        else:
            if factor_only:
                # 当没有标签数据时，标签置为0
                source_factor_label_df = factor_df_all
                source_factor_label_df[label_list[0]] = 0.0
        if verbose>0:
            print("factor_df_all shape:", factor_df_all.shape, "label_df_all shape:", label_df_all.shape, "source_factor_label_df shape: ", source_factor_label_df.shape)
        return source_factor_label_df
        # source_factor_label_df.to_parquet(os.path.join(self.exp_path, "dataset/factor_label_df.parquet"))
    else:
        source_factor_label_df = pd.read_parquet(os.path.join(exp_path, "dataset/factor_label_df.parquet"))
        print("source_factor_label_df shape: ", source_factor_label_df.shape)
        return source_factor_label_df


def select_factor_by_analysis(fp, data_type, symbol, start_date, end_date, tagger_name_list, thres_limit):
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


def select_factors_multi(expa, model_config, fp):
    # # 加载因子数据
    # factor_save_path = os.path.join(expa.path_of_exp_version(), "saved_models/factors.csv")
    # if os.path.exists(factor_save_path):
    #     # # 加载因子数据
    #     select_factors = pd.read_csv(factor_save_path, header=None)[0].tolist()
    #     print("【Warning】已有因子筛选结果，将直接从文件加载...:")
    #     print("select_factors :", len(select_factors))
    #     print(select_factors)
    #     model_config["factor_name_list"] = select_factors
    if model_config["factor_name_list"]:
        print("【Warning】已有因子筛选结果，将直接从model_config加载...:")
        select_factors = model_config["factor_name_list"]
    else:
        data_type = model_config["data_config"]["data_type"]
        select_factors_dict = {}
        factor_res_filter_dict = {}
        for symbol in tqdm(model_config["symbol_list"]):
            print("symbol select_factor:", symbol)
            select_factors, factor_res_filter = select_factor_by_analysis(fp, data_type,
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
    print("T_train, X_train, Y_train: ", len(T_train), X_train.shape, Y_train.shape, end = ", ")
    T_valid, X_valid, Y_valid = get_prepared(feature_label_df_valid, label_name,
                                             w_size, parallel_mode=parallel_mode)
    print("T_valid, X_valid, Y_valid: ", len(T_valid), X_valid.shape, Y_valid.shape, end = ", ")
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


def resample_edf_1s(edf_ms, event_list = [], sample_method = "sum"):
    """
    对毫秒级别的edf采样为1s，先合并同一毫秒的数据，求最大或最小值，再对1s内的数据求和
    :param edf_ms: 毫秒级别的edf
    :param event_list: 事件列
    :return:
    """
    ###################同一时刻只保留最大或最小值####################
    duplicate_how_method_dict = {}
    for col in edf_ms.columns:
        if col.startswith("Fac") or col in event_list:
            duplicate_how_method_dict[col] = pl.when(pl.col(col).max() > 0).then(pl.col(col).max()).otherwise(
                pl.col(col).min())
    edf_ms = edf_ms.fill_null(0.0)
    edf_ms = edf_ms.group_by("DateTime", maintain_order=True).agg(
        **duplicate_how_method_dict
        )#.sort("DateTime")
    ###################对1s内的数据求和#############################
    how_method_dict = {}

    for col in edf_ms.columns:
        if col in event_list:
            how_method_dict[col] = pl.col(col).sum()
        if col.startswith("Fac") and col not in event_list:
            if sample_method == "sum":
                how_method_dict[col] = pl.col(col).sum()
            elif sample_method == "minmax":
                how_method_dict[col] = pl.when(pl.col(col).sum() > 0).then(pl.col(col).max()).otherwise(
                    pl.col(col).min())
            else:
                raise Exception("sample_method仅支持sum和minmax方法！")
    # polars的resample不会补全缺失的秒
    edf_resample_1s = edf_ms.with_columns(pl.col("DateTime").set_sorted()). \
        group_by_dynamic(index_column='DateTime', every='1s', closed="left", label="right").agg(
        **how_method_dict)
    return edf_resample_1s


## 盘口即时特征删选时间段
def load_flying_factors(symbol, dates=None, model_config = None, flying_factor = None, sample_method = "sum",
                        flying_base_dir="/dfs/group/800657/library/l3_event/event_data", verbose = 0):
    """
    读取事件数据，并采样为1s
    :param symbol:
    :param dates:
    :param model_config:
    :param flying_factor:
    :param flying_base_dir:
    :return:
    """
    def resample_flying_factors(edf, sample_method = "sum"):
        if len(edf) == 0:
            return pl.DataFrame()
        event_list = ["PriceSpread", "CumOrdersNetVolOverV0", "BreakingP0NumOrders", "OneBigOrder", "OneBigOrderExtend", 'LevelOneChange']
        event_list = [ee for ee in event_list if ee in edf.columns]

        # 去除前50秒的数据和最后三分钟的数据
        edf_resample = resample_edf_1s(edf, event_list, sample_method = sample_method)
        date = edf_resample["DateTime"][0].strftime("%Y-%m-%d")
        edf_resample = edf_resample.filter((pl.col("DateTime") >= pd.to_datetime("{} 09:31:00".format(date))) & (
                    pl.col("DateTime") <= pd.to_datetime("{} 14:50:00".format(date))))
        # ###########################指数滑动平均效果不好##############################
        # polars的resample不会补全缺失的秒，导致rolling_mean结果和pandas不一致
        # edf_resample = edf_resample.lazy(). \
        #                 with_columns(pl.Series(name="id", values=list(range(len(edf_resample)))).set_sorted()). \
        #                 rolling(index_column = "DateTime",period = '5s').agg(
        #                 pl.col('ActivePriceVolume').last().alias('ActivePriceVolume'),
        #                 pl.col('BreakingP0NumOrders').mean().alias('BreakingP0NumOrders'),
        #                 pl.col('OneBigOrder').last().alias('OneBigOrder'),
        #                 pl.col('CumOrdersNetVolOverV0').mean().alias('CumOrdersNetVolOverV0'),
        #                 pl.col('PriceSpread').mean().alias('PriceSpread'),
        #                 pl.col('LevelOneChange').last().alias('LevelOneChange'),
        #                 pl.col('Timestamp').last().alias('Timestamp'),
        #                 pl.col('MDDate').last().alias('MDDate'),
        #                 pl.col('MDTime').last().alias('MDTime')
        #     ).collect()
        # edf_resample = edf_resample.lazy(). \
        #     with_columns(pl.Series(name="id", values=list(range(len(edf_resample)))).set_sorted()). \
        #     rolling(index_column="DateTime", period='4s').agg(
        #     pl.col('ActivePriceVolume').ewm_mean(alpha=0.4).last().alias('ActivePriceVolume'),
        #     pl.col('BreakingP0NumOrders').ewm_mean(alpha=0.4).last().alias('BreakingP0NumOrders'),
        #     pl.col('OneBigOrder').ewm_mean(alpha=0.4).last().alias('OneBigOrder'),
        #     pl.col('CumOrdersNetVolOverV0').ewm_mean(alpha=0.4).last().alias('CumOrdersNetVolOverV0'),
        #     pl.col('PriceSpread').ewm_mean(alpha=0.4).last().alias('PriceSpread'),
        #     pl.col('LevelOneChange').last().alias('LevelOneChange'),
        # ).collect()

        # Compute 'open_flying' and 'close_flying' columns
        open_flying = None
        open_event_list = copy.deepcopy(event_list)
        open_event_list.remove("LevelOneChange")
        for eidx, ee in enumerate(open_event_list):
            if eidx == 0:
                open_flying = (pl.col(ee).abs() >= 1)
            else:
                open_flying = open_flying | (pl.col(ee).abs() >= 1)

        close_flying = pl.col('LevelOneChange') != 0
        edf_resample = edf_resample.with_columns([
            open_flying.alias('open_flying').cast(pl.Int32),
            close_flying.alias('close_flying').cast(pl.Int32),
            # pl.lit(0).alias("CumOrdersNetVolOverV0"),
            # pl.lit(0).alias("OneBigOrder"),
            # pl.lit(0).alias("PriceSpread"),
            # pl.lit(0).alias("BreakingP0NumOrders"),

            # pl.when(pl.col("CumOrdersNetVolOverV0")>0).then(pl.lit(1)).
            #     when(pl.col("CumOrdersNetVolOverV0")<0).then(pl.lit(-1)).
            #     otherwise(pl.lit(0)).alias("CumOrdersNetVolOverV0"),
            # pl.when(pl.col("OneBigOrder") > 0).then(pl.lit(1)).
            #     when(pl.col("OneBigOrder") < 0).then(pl.lit(-1)).
            #     otherwise(pl.lit(0)).alias("OneBigOrder"),
            # pl.when(pl.col("PriceSpread") > 0).then(pl.lit(1)).
            #     when(pl.col("PriceSpread") < 0).then(pl.lit(-1)).
            #     otherwise(pl.lit(0)).alias("PriceSpread"),
            # pl.when(pl.col("BreakingP0NumOrders") > 0).then(pl.lit(1)).
            #     when(pl.col("BreakingP0NumOrders") < 0).then(pl.lit(-1)).
            #     otherwise(pl.lit(0)).alias("BreakingP0NumOrders")
        ])
        # 确保列的顺序
        if flying_factor:
            edf_resample = edf_resample.select(["DateTime"] + flying_factor+["open_flying", "close_flying"])
        return edf_resample

    ###########################################
    if not dates:
        from xquant.factordata import FactorData
        fa = FactorData()
        start_date = model_config["train_start_time"]
        end_date = model_config["test_end_time"]
        dates = fa.tradingday(start_date, end_date)
    data_list = []
    ###########################################
    needed_colnames = None
    for date in dates:
        try:
            sub_edf = pl.read_parquet(os.path.join(flying_base_dir, "{}/{}-{}.pqt".format(symbol, symbol, date)))
            sub_edf = sub_edf.with_columns(pl.col("LevelOneChange").cast(pl.Float32))
            sub_edf_resample = resample_flying_factors(sub_edf, sample_method=sample_method)
            if not needed_colnames:
                needed_colnames = sub_edf_resample.columns
            if not len(sub_edf) == 0:
                data_list.append(sub_edf_resample.select(needed_colnames))#保持列的顺序一致
        except Exception as e:
            # import traceback
            # print(symbol, date, traceback.print_exc())
            print("resample_flying_factors error: ", symbol, date, e)
    if not len(data_list)==0:
        try:
            edf_resample = pl.concat(data_list).sort("DateTime")
        except:
            import traceback
            print(symbol, traceback.print_exc())
            new_data_list = []
            for d in data_list:
                print(d.shape)
                if d.columns == needed_colnames:
                    new_data_list.append(d)
                else:
                    print(d.columns)
                    print("columns does not match: {}, {}".format(symbol, d["DateTime"][0]))
            edf_resample = pl.concat(new_data_list, how="vertical")
    else:
        edf_resample = pl.DataFrame()
    if verbose>0:
        print("edf_resample", edf_resample.shape)
    return edf_resample


def sample_by_sort(df, label_name, group_num = 10, sample_ratio = 0.2, time_column = "DateTime"):
    """
    将dataframe分段采样，比如df总长度为10000，按照标签值从小到大排列分成10组，每组采样20%，最后再按time_column排列
    :param df:
    :param label_name:
    :param group_num: 分组采样组数
    :param sample_ratio: 采样比率
    :param time_column: 时间列
    :return:
    """
    df = df.sort(label_name)#.with_row_count()
    per_group_num = len(df)/group_num
    groups = np.array(list(range(len(df))))/per_group_num
    groups = groups.astype(int)
    df = df.with_columns(groups = groups)
    # aa.with_columns(pl.col("row_nr").shuffle().over("group").alias("num")).filter(pl.col("num")<group_num)
    result_df = df.filter(pl.int_range(pl.len()).shuffle(seed = 2024).over("groups")<per_group_num*sample_ratio)
    result_df = result_df.sort(time_column).drop("groups")
    return result_df


def group_by_sort(df, label_name, group_num = 10):
    """
    将dataframe分段采样，比如df总长度为10000，按照标签值从小到大排列分成10组，每组采样20%，最后再按time_column排列
    :param df:
    :param label_name:
    :param group_num: 分组采样组数
    :return:
    """
    df = df.sort(label_name)#.with_row_count()
    per_group_num = len(df)/group_num
    groups = np.array(list(range(len(df))))/per_group_num
    groups = groups.astype(int)
    df = df.with_columns(groups = groups)
    # aa.with_columns(pl.col("row_nr").shuffle().over("group").alias("num")).filter(pl.col("num")<group_num)
    # result_df = df.sort(time_column)#.drop("groups")
    return df


def merge_norm_flying_factor(symbol, start_date, end_date, factor_name_list,label_name, flying_factor, factor_config_path, tagger_limit = 60,
                             data_type = "tick_l2p", flying_base_dir = "/dfs/group/800657/library/l3_event/event_data", closing_flag = False):
    """
    读取事件数据，
    :param symbol:
    :param start_date:
    :param end_date:
    :param factor_name_list:
    :param label_name:
    :param tagger_limit:
    :param data_type:
    :param flying_base_dir:
    :param closing_flag: 是否将levelOneChange加入到样本中
    :return:
    """
    fa = FactorData()
    dates = fa.tradingday(start_date, end_date)
    fp = FactorProvider("016869")
    # ########################生成采样数据###########################
    feature_label_df = load_factor_label(
                                      fp,
                                      data_type,
                                      start_date,
                                      end_date,
                                      symbol,
                                      factor_name_list,
                                      [label_name],
                                      tagger_limit,
                                      verbose=0
    )
    flying_factor_df = load_flying_factors(symbol, dates = dates, flying_factor = flying_factor, flying_base_dir = flying_base_dir)
    if len(flying_factor_df)==0:
        if not closing_flag:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        else:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    flying_factor_df = flying_factor_df.to_pandas()
    flying_factor_df = flying_factor_df.set_index("DateTime")

    merge_df = pd.merge(feature_label_df, flying_factor_df, left_index=True, right_index=True, how = "inner")
    new_feature_label_df = merge_df[factor_name_list + [label_name]+flying_factor]
    if new_feature_label_df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    T_test, X_test, Y_test = get_prepared(new_feature_label_df, label_name, w_size=1, parallel_mode=False)
    X_test = X_test#[:, 0]
    Y_test = Y_test.flatten()
    print("feature_label_df: ",feature_label_df.shape, ", new_feature_label_df: ", new_feature_label_df.shape, "T_test, X_test, Y_train: ", len(T_test), X_test.shape, Y_test.shape)
    # ########################标准化因子###########################
    open_flying_df = pd.DataFrame(X_test, columns = factor_name_list + flying_factor, index = new_feature_label_df.index)
    factor_config = pd.read_json(factor_config_path)
    for j in range(len(factor_name_list)):
        factor_mean = factor_config[factor_name_list[j]].loc['mean']
        factor_std = factor_config[factor_name_list[j]].loc['std']
        clip_lower = factor_mean - 3 * factor_std
        clip_upper = factor_mean + 3 * factor_std
        cliped_df = open_flying_df[factor_name_list[j]].clip(
            lower=clip_lower, upper=clip_upper)
        open_flying_df[factor_name_list[j]] = (cliped_df.values - factor_mean) / factor_std
    open_flying_label_df = pd.DataFrame(Y_test, index = new_feature_label_df.index)
    if not closing_flag:
        return open_flying_df, open_flying_label_df, merge_df[["open_flying"]]
    else:
        return open_flying_df, open_flying_label_df, merge_df[["open_flying"]], merge_df["close_flying"]


def id_category(symbol_id, T_train, X_train, Y_train, T_valid, X_valid, Y_valid, T_test, X_test, Y_test):
    X_train_ = pd.DataFrame(X_train)
    X_train_["id"] = symbol_id
    X_train_["id"] = X_train_["id"].astype("category")

    X_valid_ = pd.DataFrame(X_valid)
    X_valid_["id"] = symbol_id
    X_valid_["id"] = X_valid_["id"].astype("category")

    X_test_ = pd.DataFrame(X_test)
    X_test_["id"] = symbol_id
    X_test_["id"] = X_test_["id"].astype("category")

    return T_train, X_train_, Y_train, T_valid, X_valid_, Y_valid, T_test, X_test_, Y_test


def generate_split_dataset(model_config, open_flying_df, tagger_limit, type="train", include_flying_factor = True):
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
    mask_train = abs(Y_train) <= tagger_limit
    if include_flying_factor:
        X_train = np.concatenate((X_train, F_train), axis=1)

    T_train, X_train, F_train, Y_train = T_train[mask_train], X_train[mask_train], F_train[mask_train], Y_train[
        mask_train]

    return T_train, X_train, F_train, Y_train


def generate_split_dataset_pl(model_config, open_flying_df, tagger_limit, type="train", include_flying_factor = True):
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
    F_train_pl = open_flying_df_train.select(flying_factor)
    X_train_pl = open_flying_df_train.select(select_factors)
    Y_train = open_flying_df_train.select(label_list).to_numpy().flatten()

    #     T_train1,X_train1,Y_train1,T_valid1,X_valid1,Y_valid1,T_test1,X_test1,Y_test1 = id_category(
    #         symbol,T_train,X_train,Y_train,T_valid,X_valid,Y_valid,T_test,X_test,Y_test
    #     )
    mask_train = abs(Y_train) <= tagger_limit
    if include_flying_factor:
        X_train_pl = pl.concat([X_train_pl, F_train_pl], how="horizontal")

    mask_train_pl = pl.DataFrame({"mask" : mask_train})["mask"]==True
    T_train, X_train_pl, F_train_pl, Y_train = T_train[mask_train], X_train_pl.filter(mask_train_pl), F_train_pl.filter(mask_train_pl), Y_train[
        mask_train]

    return T_train, X_train_pl, F_train_pl, Y_train


def generate_split_dataset_valid(model_config, open_flying_df, tagger_limit, type="train", include_flying_factor=True,
                               T_valid=None):
    if type == "train":
        start_date = model_config["train_start_time"]
        end_date = model_config["valid_end_time"]
    elif type == "valid":
        start_date = model_config["train_start_time"]
        end_date = model_config["valid_end_time"]
    elif type == "test":
        start_date = model_config["test_start_time"]
        end_date = model_config["test_end_time"]
    else:
        raise Exception()

    if type == "valid":
        from xquant.factordata import FactorData
        fa = FactorData()
        date_train_valid = fa.tradingday(start_date, end_date)
        # 确定验证集的长度
        m = len(date_train_valid)
        valid_length = len(date_train_valid) // 6

        # 取样，从头每隔三个取一个，从尾每隔三个取两个

        # 初始化两个空列表来存储从前往后和从后往前的取样结果
        forward_samples = []
        backward_samples = []

        # 从前往后取样，每三个取一个
        for i in range(0, m - 2, 3):  # 减2是为了避免在最后一个元素时索引越界
            if len(forward_samples) < valid_length // 3:  # 只取三分之一的数量
                forward_samples.append(date_train_valid[i])

                # 计算从后往前取样时需要取的总数（三分之二的数量）
        two_thirds_sample_count = valid_length - len(forward_samples)
        # 每遍历到三个元素中的第一个和第二个时取它们 ,而不需要一个额外的跳过标记
        backward_samples = []
        count = 0  # 用于计数已经取了多少个元素（从后往前看的“三个”中的哪一个）
        for i in range(m - 1, -1, -1):
            if len(backward_samples) < two_thirds_sample_count:
                # 每三个取两个，即从后往前看，取第1个和第2个（索引为m-1, m-2, 然后跳过m-3, 取m-4, m-5, ...）
                if count < 2:
                    backward_samples.append(date_train_valid[i])
                count = (count + 1) % 3  # 更新计数，如果达到3则重置为0（但实际上我们不会取到第3个）

        # 合并结果
        sampled_list = forward_samples + backward_samples
        # print(sampled_list)
        # print(open_flying_df)
        # print(len(open_flying_df))
        # sampled_list = [pl.lit(dt).str.to_datetime("%Y%m%d") for dt in sampled_list]
        open_flying_df_train = open_flying_df.filter(
            (pl.col("DateTime").dt.strftime("%Y%m%d").is_in(sampled_list)))
        # print(len(open_flying_df_train))

    elif type == "train":
        print(T_valid)
        open_flying_df_train = open_flying_df.filter(
            (pl.col("DateTime") >= pl.lit(start_date).str.to_datetime("%Y%m%d")) &
            (pl.col("DateTime") <= pl.lit(end_date).str.to_datetime("%Y%m%d")))
        print("+" * 200)
        print(len(open_flying_df_train))
        open_flying_df_train = open_flying_df_train.filter(~
                                                           (pl.col("DateTime").is_in(T_valid)))
        print(len(open_flying_df_train))
    else:
        open_flying_df_train = open_flying_df.filter(
            (pl.col("DateTime") >= pl.lit(start_date).str.to_datetime("%Y%m%d")) &
            (pl.col("DateTime") <= pl.lit(end_date).str.to_datetime("%Y%m%d")))

    # open_flying_df_train = open_flying_df.filter(
    #     (pl.col("DateTime") >= pl.lit(start_date).str.to_datetime("%Y%m%d")) &
    #     (pl.col("DateTime") <= pl.lit(end_date).str.to_datetime("%Y%m%d")))

    flying_factor = model_config["data_config"]["flying_factor"]
    select_factors = model_config["factor_name_list"]
    label_list = model_config["tagger_name_list"]

    T_train = open_flying_df_train.select(["DateTime"]).to_numpy().flatten()
    F_train_pl = open_flying_df_train.select(flying_factor)
    X_train_pl = open_flying_df_train.select(select_factors)
    Y_train = open_flying_df_train.select(label_list).to_numpy().flatten()

    #     T_train1,X_train1,Y_train1,T_valid1,X_valid1,Y_valid1,T_test1,X_test1,Y_test1 = id_category(
    #         symbol,T_train,X_train,Y_train,T_valid,X_valid,Y_valid,T_test,X_test,Y_test
    #     )
    mask_train = abs(Y_train) <= tagger_limit
    if include_flying_factor:
        X_train_pl = pl.concat([X_train_pl, F_train_pl], how="horizontal")

    mask_train_pl = pl.DataFrame({"mask" : mask_train})["mask"]==True
    T_train, X_train_pl, F_train_pl, Y_train = T_train[mask_train], X_train_pl.filter(mask_train_pl), F_train_pl.filter(mask_train_pl), Y_train[
        mask_train]

    return T_train, X_train_pl, F_train_pl, Y_train

