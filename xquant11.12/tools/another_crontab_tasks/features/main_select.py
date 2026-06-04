import ray
# from backtest_scripts import *
import matplotlib.pyplot as plt
from datetime import datetime
import os
import sys
import json
from xquant.factordata import FactorData
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
import time
from star_model.src.utils.utils import Args, fileter_invalid_data_by_tradingday
import pandas as pd
import numpy as np
from tqdm import tqdm
from star_model.analyzer.TickFactorBacktest import *
from star_model.src.data.calculator import *
from minepy import MINE

symbol = "ALL_SYMBOL"
exp_name = symbol
exp_path = "/data/user/013150/exp_result/" + exp_name + "/"
if not os.path.exists(exp_path):
    os.makedirs(exp_path)

if not os.path.exists(exp_path + "saved_models/"):
    os.makedirs(exp_path + "saved_models/")

label_name = "labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1"

all_config = {
    "data_config": {
        "symbol": symbol,
        "train_start_time": "20200101",
        "train_end_time": "20220831",
        "valid_start_time": "20220901",
        "valid_end_time": "20230201",
        "test_start_time": "20230202",
        "test_end_time": "20230915",
        "main_stocks": symbol,
        "w_size": 1,
        "n_job": 2,
        "transform": True,
        "clip_type": "3sigma",
        "scaler_type": "z-score",
        "quantile": [0.02, 0.98],
        "factor_name_list": [],  # 按条数筛选后写入
        "tagger_name_list": ["labelEQtriplebarriertaggerv2pricetypeEQmidpricedsizeEQ120barrierEQ1"],
        "tagger_limit": 50,
        "raw_name_list": [],
        "model_dir": os.path.join(exp_path, "saved_models/"),
        "thres": [0.02, 0.02],
        # 因子候选集, factor_select 是在这里的因子选
        # "factor_pool": "/data/user/019771/star_project/exp_result/688223.SH_trade_v1.1/factor_pool.csv",
        # 也可是public或personal
        "data_source": "{}_factor_df.parquet".format(symbol[:-3]),
        "label_source": "label_{}.parquet".format(symbol),
        # 不以Factor开头但是也能放进来的列表
        "other_factor_list": "",
        # 因子列表， 为空的话为全量
        "factor_json_path": "",
        # 因子黑名单列表，不能用的因子
        "exclude_json_path": "/data/user/013150/online_scripts/Signal_Pipeline/factor_exclude.json"},
    # 模型段配置
    "xgb_config": {
        'objective': 'reg:squarederror',
        'booster': 'gbtree',
        'tree_method': 'gpu_hist',
        'gamma': 0.5,
        'learning_rate': 0.01,
        'lambda': 2,
        'subsample': 0.7,
        'colsample_bytree': 0.7,
        'max_depth': 12,
        'n_estimators': 3000,
        'seed': 4},
    "metrics": {"reg_eval_abs_limits": [1.0, 3.0],
                "reg_eval_th": 0.5},
    "model": {"name": "mlp"},
    "optimizer": {"name": "adam", "lr": 0.001, },
    "criterion": {"name": "mse"},
    "model_dir": os.path.join(exp_path, "saved_models/"),
    "Model_save_mode": ["pkl", "onnx"],
    "n_jobs_model": 32,

    "path_config": {
        "Exp_path": exp_path,
        "model_saved_path": os.path.join(exp_path, "saved_models/"),
        "dataset_saved_path": os.path.join(exp_path, "dataset"),
        "signal_saved_path": os.path.join(exp_path, "signal_files/"),
        "signal_saved_txt_path": os.path.join(exp_path, "signal_files_txt/"),
        "plot_saved_path": os.path.join(exp_path, "plot_files"),
        "backtest_saved_path": os.path.join(exp_path, "backtest")
    }
}

model_saved_path = os.path.join(exp_path, "saved_models/")
dataset_saved_path = os.path.join(exp_path, "dataset")
signal_saved_path = os.path.join(exp_path, "signal_files/")
signal_saved_txt_path = os.path.join(exp_path, "signal_files_txt/")
plot_saved_path = os.path.join(exp_path, "plot_files")

all_config["path_config"]["Exp_path"] = exp_path
all_config["path_config"]["model_saved_path"] = model_saved_path
all_config["path_config"]["dataset_saved_path"] = dataset_saved_path
all_config["path_config"]["signal_saved_path"] = signal_saved_path
all_config["path_config"]["signal_saved_txt_path"] = signal_saved_txt_path
all_config["path_config"]["plot_saved_path"] = plot_saved_path
all_config["model_dir"] = model_saved_path

all_config["data_config"]["symbol"] = symbol
all_config["data_config"]["main_stocks"] = symbol
all_config["data_config"]["model_dir"] = model_saved_path
all_config["data_config"]["data_source"] = os.path.join(dataset_saved_path, "{}_factor_df.parquet".format(symbol))
all_config["data_config"]["factor_json_path"] = os.path.join(all_config["path_config"]["Exp_path"],
                                                             f"_{all_config['data_config']['symbol']}_{str(all_config['data_config']['thres'][0]).replace('.', '')}.json")

print("exp_name:", exp_name)


def _load_factor(data_config, start_time, end_time, save=True):
    """
    获取因子集
    """
    # 公库获取因子
    if data_config.data_source == "public":
        print("\t\tLoad {} factors from public".format(len(data_config.factor_name_list)))
        factor_df = factor_oi.load_public_data_from_dfs(
            symbol=data_config.symbol,
            factor_list=data_config.factor_name_list,
            start_time=start_time,
            end_time=end_time,
            factor_type="factor"
        )
    # 私库获取因子
    elif data_config.data_source == "personal":
        print("\t\tLoad {} factors from personal".format(len(data_config.factor_name_list)))
        factor_df = factor_oi.load_personal_data_from_dfs(
            symbol=data_config.symbol,
            factor_list=data_config.factor_name_list,
            start_time=start_time,
            end_time=end_time,
            factor_type="factor"
        )
    else:
        if os.path.exists(data_config.data_source) and data_config.factor_name_list:
            factor_df = pd.read_parquet(data_config.data_source, engine="pyarrow", use_threads=True)
            if data_config.factor_json_path != "":
                factor_df = factor_df[
                    data_config.factor_name_list + ["timestamp", "M_HTSCSecurityID", "R_HTSCSecurityID"]]
                assert len(factor_df.columns) == len(
                    data_config.factor_name_list + ["timestamp", "M_HTSCSecurityID", "R_HTSCSecurityID"])
            print("\t\tLoad {} factors from parquet".format(len(data_config.factor_name_list)))
        else:
            print("暂无因子数据{} {}，将从公库加载。".format(data_config,symbol, data_config.data_source))
            print("data_config.factor_name_list:", data_config.factor_name_list)
            factor_df = factor_oi.load_public_data_from_dfs(
                symbol=data_config.symbol,
                factor_list=data_config.factor_name_list,
                start_time=start_time,
                end_time=end_time,
                factor_type="factor"
            )
            factor_df["timestamp1"] = factor_df["timestamp"]
            factor_df = factor_df.set_index("timestamp1", drop=True)
            if data_config.factor_json_path != "":
                factor_df = factor_df[
                    data_config.factor_name_list + ["timestamp", "M_HTSCSecurityID", "R_HTSCSecurityID"]]
                assert len(factor_df.columns) == len(
                    data_config.factor_name_list + ["timestamp", "M_HTSCSecurityID", "R_HTSCSecurityID"])
            if save == True:
                pass
                # factor_df.to_parquet(data_config.data_source)
                # print("因子数据已保存至：{}".format(data_config.data_source))

        sta = str(start_time[0:4]) + "-" + str(start_time[4:6]) + "-" + str(start_time[6:8])
        end = str(end_time[0:4]) + "-" + str(end_time[4:6]) + "-" + str(end_time[6:8]) + " 23:59:59"
        print("\t\t时间范围：{}~{}, 数据列数（含key）:{}".format(sta, end, len(list(factor_df.columns))))
        factor_df = factor_df[(factor_df["timestamp"] >= pd.Timestamp(sta)) &
                              (factor_df["timestamp"] <= pd.Timestamp(end))]

    ck1 = len(factor_df)
    factor_df = factor_df.drop_duplicates(subset=["timestamp"]).set_index("timestamp", drop=True)
    trading_date_list = FactorData().tradingday(start_time, end_time)
    factor_df = fileter_invalid_data_by_tradingday(factor_df, trading_date_list)
    print("\t\t 因子长度{} → 去重清洗后长度{}:".format(ck1, len(factor_df)))
    return factor_df


def _load_tagger(data_config, start_time, end_time, tagger_limit=100):
    """
    tagger 里面可能会遇到的问题是，tagger值本身没有对齐。这个在保存的时候，应该就处理好。
    即用户拿到的就是对齐好的标签数据。
    """
    t1 = time.time()
    tagger_df = factor_oi.load_personal_data_from_dfs(
        symbol=data_config.symbol,
        factor_list=data_config.tagger_name_list,
        start_time=start_time,
        end_time=end_time,
        factor_type="label"
    )
    print("load tag time: ", time.time() - t1)
    ck1 = len(tagger_df)
    tagger_df = tagger_df.set_index("timestamp", drop=True)
    trading_date_list = FactorData().tradingday(start_time, end_time)
    if tagger_limit:
        tagger_df = tagger_df[(tagger_df[data_config.tagger_name_list] <= tagger_limit) & (
                tagger_df[data_config.tagger_name_list] >= -tagger_limit)]
    ck2 = len(tagger_df)
    tagger_df = fileter_invalid_data_by_tradingday(tagger_df, trading_date_list)
    print("\t\t 标签长度{} → 去除异常标签值后的数据长度 {} → 去重清洗后长度{}".format(ck1, ck2, len(tagger_df)))
    return tagger_df


def merge_factor_label(factor_df, tagger_df, keep_column_list=None, dropna=True):
    """
    dropna: 合并后是否去除nan值
    """
    l = factor_df.shape[0]
    factor_label = pd.merge(factor_df, tagger_df, left_index=True, right_index=True)
    factor_label["MDDate"] = factor_label.index.date
    factor_label["MDTime"] = factor_label.index.time
    if dropna:
        factor_label.dropna(how="any", axis=0, inplace=True)
    if keep_column_list:
        #         keep_column_list =  [v for v in data_config.factor_name_list if v.startswith("Factor")
        #                         ] + data_config.tagger_name_list + data_config.raw_name_list+["MDDate","MDTime"]
        keep_column_list = factor_label.columns()
        keep_column_list.remove("")
        print("\t\t数据列长度：", len(keep_column_list))
        factor_label = factor_label[keep_column_list]
    factor_label = factor_label[~factor_label.index.duplicated(keep="first")]
    print("\t\t 因子数据长度：{} → 因子标签合并数据长度: {}".format(l, factor_label.shape[0]))
    return factor_label


def train_transformer(feature_df, calc_lst):
    for i, calc in enumerate(calc_lst):
        if i == 0:
            res = calc.train_transform(feature_df)
        else:
            res = calc.train_transform(res)


def get_transformed(feature_df, calc_list, transform=True, batch_num=50):
    def process_innter(feature_df, calc_list, transform):
        normalized_df = feature_df
        if transform:
            for calc in calc_list:
                normalized_df = calc.transform(normalized_df)
        return normalized_df

    if ray.is_initialized():
        ray.shutdown()
        ray.init(_system_config={
            "object_spilling_config": json.dumps(
                {"type": "filesystem", "params": {"directory_path": "/data/user/013150/tmp/"}},
            )}
        )
    print("========get_transformed==========")
    per_batch = len(feature_df) // 20 + 1
    remote_func = ray.remote(process_innter)
    tasks = [remote_func.remote(feature_df.iloc[i * per_batch:(i + 1) * per_batch], calc_list, transform) for i in
             range(20)]

    normalized_df_list = ray.get(tasks)
    normalized_df = pd.concat(normalized_df_list, axis=0)
    ray.shutdown()
    return normalized_df


# 将DataFrame转换为numpy数组
def get_prepared(feature_label_df, label, w_size):
    def get_prepared_inner(normalized_df, tagger_df, w_size):
        assert len(normalized_df) == len(tagger_df)
        t = []
        x = []
        y = []
        normalized_df.sort_index(inplace=True)
        tagger_df.sort_index(inplace=True)
        # 为有重叠窗口的数据处理做准备
        for i in range(len(normalized_df)):
            if i + w_size > len(normalized_df):
                break
            x_span = normalized_df[i:i + w_size]
            if x_span.index[-1] not in tagger_df.index:
                continue
            else:
                t.append(x_span.index[-1])
                x.append(x_span.values)
                y.append(tagger_df.loc[x_span.index[-1]].values)
        return t, np.array(x), np.array(y)

    T_list, X_list, Y_list = [], [], []

    factors = [v for v in feature_label_df.columns if
               v not in ["M_HTSCSecurityID", "R_HTSCSecurityID", "timestamp", "MDDate", "MDTime"]]
    normalized_df, tagger_df = feature_label_df[factors], feature_label_df[[label]]
    group_df = pd.DataFrame(list(range(len(feature_label_df))), columns = ["ID"])
    group_df["MDDate"] = normalized_df.index.date
    group_idx = group_df.groupby("MDDate").agg({'ID': ["first", "last"]})["ID"]
    # print(group_idx)

    for date, row in group_idx.iterrows():
        start_idx, end_idx = row["first"], row["last"]
        sub_normalized_df = normalized_df.iloc[start_idx: end_idx + 1]
        sub_tagger_df = tagger_df.iloc[start_idx: end_idx + 1]
        sub_result = get_prepared_inner(sub_normalized_df, sub_tagger_df, w_size)
        T_list.append(sub_result[0])
        X_list.append(sub_result[1])
        Y_list.append(sub_result[2])

    T = sum(T_list, [])
    X = np.concatenate(X_list)
    Y = np.concatenate(Y_list)
    # Y = np.concatenate([np.sign(v[2]) for v in T_X_Y_result])
    return T, X, Y


def test_all_factor(analyzer, feature_label_df, label='Label', factor_name_list=None):
    def _get_single_factor_stats_info_inner(self, n, feature_df, label_df, group_idx, factor, label, percent_list,
                                            rolling_window,
                                            stratified_list):
        """
        单因子多日检测
        :param n:
        :param factor:
        :param label:
        :return:
        """
        stats_lst = []
        cnt = 0
        for date, row in group_idx.iterrows():
            start_idx, end_idx = row["first"], row["last"]
            sub_feature_df = feature_df.iloc[start_idx:end_idx + 1]
            sub_lable_df = label_df.iloc[start_idx:end_idx + 1]

            df = pd.concat([sub_feature_df, sub_lable_df], axis=1)
            if len(df) < 2000:
                cnt += 1
                continue
            df = df.dropna(how = "any")
            stats_lst.append(_get_factor_stats_info_util(self, date, df, factor, label, percent_list, rolling_window,
                                                         stratified_list))
        if cnt>0:
            print("\t\tfactor{}按日统计去除异常天， 异常天共{}天".format(factor, cnt))

        stats_df = pd.DataFrame(stats_lst)
        #     stats_df.set_index('MDDate', drop=True, inplace=True)
        #         print("stats_df:", stats_df)
        return stats_df

    def _get_factor_stats_info_util(self, date, df, factor, label, percent_list, rolling_window, stratified_list):
        """
        获取单个因子日内统计值指标
        :param n:
        :param df:
        :param factor:
        :param label:
        :return:
        """
        result_dict = {}
        # 保留一些信息
        # result_dict['MDDate'] = df.ix[0, 'MDDate']
        result_dict['MDDate'] = date
        # 有效的因子个数
        df = df.dropna(how="any", axis=0)
        result_dict['test_factor'] = factor
        result_dict["valid_count"] = df.shape[0]
        # 计算各个因子的偏度
        result_dict['skew'] = self.calc_factor_skew(df, factor)
        # 计算各个因子的峰度
        result_dict['kurt'] = self.calc_factor_kurt(df, factor)
        result_dict['factor_std'] = self.calc_std(df, factor)
        result_dict['label_std'] = self.calc_std(df, label)
        # IC
        result_dict['normal_ic'], result_dict['rank_ic'] = self.calc_factor_label_ic(df, factor, label)
        # 因子自相关
        result_corr = self.calc_factor_auto_corr(df, factor)
        result_dict.update(result_corr)
        # 各个因子与 Label 的相关性
        result_dict['corr'] = self.calc_factor_label_corr(df, factor, label)

        # t1 - time.time()
        # mine = MINE()
        # mine.compute_score(df[factor], df[label])
        # result_dict['mic'] = mine.mic()
        # result_dict['mas'] = mine.mas()
        # result_dict['mev'] = mine.mev()
        # result_dict['mcn'] = mine.mcn()
        # result_dict['mcn_general'] = mine.mcn_general()
        # result_dict['gmic'] = mine.gmic()
        # result_dict['tic'] = mine.tic()
        # print("mine耗时：", time.time()-t1)

        # _ = self.calc_mutual_info(df, factor, label)
        for percent in percent_list:
            stats_dict = self.calc_profit_stats_by_percent(df, factor, label, percent=percent,
                                                           rolling_win=rolling_window)
            result_dict.update(stats_dict)
        for n_bins in stratified_list:
            stats_dict_stratified = self.calc_profit_stats_by_stratified(df, factor, label, n_bins)
            result_dict.update(stats_dict_stratified)
        return result_dict

    if factor_name_list is not None:
        f_name = factor_name_list
    else:
        f_name = feature_label_df.columns
        f_name = [v for v in f_name if
                  v not in ["M_HTSCSecurityID", "R_HTSCSecurityID", "timestamp", "MDDate", "MDTime", label]]
    print("开始评价因子, 共计{}个".format(len(f_name)))
    print(f_name)

    feature_label_df = feature_label_df.sort_index(axis=0)
    feature_label_df["timestamp"] = feature_label_df.index
    feature_label_df["group"] = feature_label_df["timestamp"].apply(lambda x: int(x.strftime("%Y%m%d")))
    feature_label_df["ID"] = list(range(len(feature_label_df)))
    tagger_df = feature_label_df[[label]]
    group_idx = feature_label_df[["ID", "group"]].reset_index().groupby("group").agg({'ID': ["first", "last"]})["ID"]
    feature_label_df = feature_label_df.drop(columns=["group", "ID"])
    # print("group_idx: ", group_idx)

    if ray.is_initialized():
        ray.shutdown()
        ray.init(_system_config={
            "object_spilling_config": json.dumps(
                {"type": "filesystem", "params": {"directory_path": "/data/user/013150/tmp/"}},
            )})

    tagger_df_id = ray.put(tagger_df)
    remote_func = ray.remote(_get_single_factor_stats_info_inner)

    tasks = []
    for n, factor in enumerate(f_name):
        df_factor = feature_label_df[[factor]]
        tasks.append(remote_func.remote(
            analyzer,
            n,
            df_factor,
            tagger_df_id,
            group_idx,
            factor,
            label,
            analyzer.factor_test["percent"],
            analyzer.factor_test["rolling_win"],
            analyzer.factor_test["stratified"]
        ))

    all_factor_stats_list = ray.get(tasks)
    for task in tasks:
        ray.internal.internal_api.free(task)
        del task
    if all_factor_stats_list:
        all_factor_stats_df = pd.concat(all_factor_stats_list)
        return all_factor_stats_df
    else:
        return pd.DataFrame()


def factor_select_by_IC(data_config, feature_label_df, label_name, output_path, thres=[0.2, 0.2]):
    """通过IC & RankIC 筛选因子
    params:
       data_config: dict, 数据流水线配置
       label_name:  str, label名称
       n_jobs:      str, 并发核数
       thres: list, 两个元素，第一个为IC阈值，第二个为RankIC阈值
    return:
       chosen_factor_config_dict: list, 满足条件的因子名集合
    """
    if not os.path.exists(data_config["model_dir"]):
        os.makedirs(data_config["model_dir"])
    t1 = time.time()
    analyzer = FactorBacktest(n_jobs=2)
    all_factor_stats_df = test_all_factor(analyzer, feature_label_df, label=label_name)

    if not all_factor_stats_df.empty:
        factor_info = all_factor_stats_df.groupby(
            all_factor_stats_df.test_factor).apply(np.mean)[["normal_ic", "rank_ic", "valid_count"]].fillna(0)
        factor_info.to_csv(
            output_path + "_{}_{}.csv".format(data_config["symbol"], str(data_config["thres"][0]).replace(".", "")))
        chosen_factor = factor_info[(abs(factor_info.normal_ic) >= thres[0]) | (abs(factor_info.rank_ic) >= thres[1])]
    else:
        print("warning: 因子评价结果为空！")

    print("评价因子耗时：", time.time() - t1)
    return all_factor_stats_df


if __name__ == "__main__":
    target_securities = [
        '688599.SH','688012.SH','688303.SH',
        '688521.SH','688385.SH','688036.SH',
        '689009.SH','688598.SH','688536.SH',
        '688111.SH','688017.SH','688981.SH',
        '688116.SH','688223.SH','688777.SH',
        '688008.SH','688256.SH','688271.SH',
        '688009.SH','688561.SH','688126.SH',
        '688297.SH','688220.SH','688187.SH',
        '688772.SH','688390.SH','688567.SH',
        '688005.SH','688122.SH','688006.SH',
        '688819.SH','688728.SH','688126.SH',
        '688208.SH','688778.SH','688070.SH',
        '688234.SH','688375.SH','688350.SH',
        '688598.SH','688198.SH','688396.SH',
        '688099.SH','688161.SH','688065.SH',
        '688169.SH','688082.SH','688180.SH',
        '688499.SH','688041.SH','688105.SH',
        '688047.SH','688052.SH','688114.SH',
        '688538.SH','688348.SH','688295.SH',
        '688779.SH','688178.SH','688349.SH',
        '688219.SH',
        '688029（l2p）.SH',
        '688012(l2p).SH',
    ]

    factor_oi = FactorProvider("016884")
    # 先读取公共库中已存在的因子列表
    fac = list(factor_oi.load_info_from_dfs("factor", source_type="public"))
    start_date = "20200101"
    end_date = "20230930"

    data_config = all_config["data_config"]
    data_config["train_start_time"] = start_date
    data_config["train_end_time"] = end_date
    data_config = Args(**data_config)
    if False:
        factor_name_list = factor_select_by_cnt(config, symbol, config["train_start_time"], config["train_end_time"],
                                                daily_avg_cnt=4200)
    else:
        factor_name_list = list(factor_oi.load_info_from_dfs('factor', source_type='public'))
    print("Filter Factors by cnt, Left {}".format(len(factor_name_list)))

    # 将1000个因子分为4组
    factor_group_num = 8
    per_group_num = len(factor_name_list) // factor_group_num + 1
    for symbol in [sys.argv[1]]:
        for factor_group in [int(sys.argv[2])]:#range(factor_group_num):
            sub_factor_name_list = factor_name_list[per_group_num * factor_group: per_group_num * (factor_group + 1)]
            data_config["factor_name_list"] = sub_factor_name_list
            data_config.symbol = symbol
            factor_df = _load_factor(data_config, data_config.train_start_time, data_config.train_end_time)
            tagger_df = _load_tagger(data_config, data_config.train_start_time, data_config.train_end_time,
                                     data_config.tagger_limit)

            if len(factor_df) == 0 or len(tagger_df)==0:
                print("warning: symbol {} data length is zero!".format(symbol))
                continue

            clip_calculator = ClipCalculator(data_config.clip_type, data_config.quantile)
            norm_calculator = NormCalculator(data_config.scaler_type)
            # 保存了标准化信息
            transformer_list = [clip_calculator, norm_calculator]
            label_name = data_config.tagger_name_list[0]
            factors = [v for v in data_config.factor_name_list if
                       v not in ["M_HTSCSecurityID", "R_HTSCSecurityID", "timestamp", "MDDate", "MDTime", label_name]]
            feature_df = factor_df[factors]
            t1 = time.time()
            train_transformer(feature_df, transformer_list)
            print("train_transformer:", time.time() - t1)
            normalized_df = get_transformed(feature_df, transformer_list, data_config.transform)
            print("2. Normalize Feature Data ...", time.time() - t1)
            t1 = time.time()
            feature_label_df = merge_factor_label(normalized_df, tagger_df, dropna=False)
            l1 = len(feature_label_df)
            c1 = len(feature_label_df.columns)
            feature_label_df.dropna(axis=1, how='all', inplace=True)
            print("\t\t去除空值， 行：{}→{} | 列： {}→{}".format(l1, len(feature_label_df), c1, len(feature_label_df.columns)))

            # T, X, Y = get_prepared(feature_label_df, label_name, data_config.w_size)
            # print("3. Prepare Dataset ...", time.time() - t1)

            t1 = time.time()
            all_factor_stats_df = factor_select_by_IC(data_config, feature_label_df, label_name, all_config["path_config"]["Exp_path"],
                                                thres=data_config.thres)
            print("4. Evaluate Factor ...", time.time() - t1)
            all_factor_stats_df.to_parquet(os.path.join(all_config["path_config"]["Exp_path"], "new_{}_all_factor_stats_df_{}.parquet".format(symbol, factor_group)))
