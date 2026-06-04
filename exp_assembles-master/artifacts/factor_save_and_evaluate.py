import sys
sys.path.insert(0, "../")
import ray
from scipy import stats
import json
import time
import pandas as pd
import numpy as np
from artifacts.factor_metrics import FactorBacktest
from artifacts.utils import start_ray_cluster
import gc
from tqdm import tqdm
# from minepy import MINE


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
                {"type": "filesystem", "params": {"directory_path": "/tmp/"}},
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
def get_prepared(feature_label_df, label, w_size, parallel_mode = False, object_spill_path = None):
    def get_prepared_inner(normalized_df, tagger_df, w_size):
        assert len(normalized_df) == len(tagger_df)
        t = []
        x = []
        y = []
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


    factors = [v for v in feature_label_df.columns if
               v not in ["M_HTSCSecurityID", "M_HTSCSecurityID_x", "M_HTSCSecurityID_y", "R_HTSCSecurityID_x", "R_HTSCSecurityID_y", "R_HTSCSecurityID", "timestamp", "MDDate", "MDTime", label]]
    normalized_df, tagger_df = feature_label_df[factors], feature_label_df[[label]]
    normalized_df.sort_index(inplace=True)
    tagger_df.sort_index(inplace=True)

    group_df = pd.DataFrame(list(range(len(feature_label_df))), columns = ["ID"])
    print("get_prepared normalized_df shape: ", normalized_df.shape)
    group_df["MDDate"] = normalized_df.index.date
    group_idx = group_df.groupby("MDDate").agg({'ID': ["first", "last"]})["ID"]
    # print(group_idx)

    if parallel_mode == False:
        T_list, X_list, Y_list = [], [], []
        if w_size!=1:
            for date, row in tqdm(group_idx.iterrows()):
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
        else:
            T = normalized_df.index.tolist()
            X = normalized_df.values
            Y = tagger_df[label].values
    else:
        start_ray_cluster(object_spill_path=object_spill_path)
        remote_func = ray.remote(get_prepared_inner)
        tasks = [remote_func.remote(
                normalized_df.iloc[row["first"]: row["last"] + 1],
                tagger_df.iloc[row["first"]: row["last"] + 1],
                w_size) for date, row in group_idx.iterrows()]
        T_X_Y_result = ray.get(tasks)
        for task in tasks:
            ray.internal.internal_api.free(task)
            del task
        del tasks
        gc.collect()
        ray.shutdown()
        time.sleep(5)
        T = sum([v[0] for v in T_X_Y_result],[])
        X = np.concatenate([v[1] for v in T_X_Y_result])
        Y = np.concatenate([v[2] for v in T_X_Y_result])
    # Y = np.concatenate([np.sign(v[2]) for v in T_X_Y_result])
    return T, X, Y


def test_all_factor(analyzer, feature_label_df, label='Label', factor_name_list=None, object_spill_path =None):
    def clip_norm_022917(feature_df):
        arr = feature_df.values
        factor_mean = np.nanmean(arr, axis=0)
        factor_std = np.nanstd(arr, axis=0)
        clip_lower = factor_mean - 3 * factor_std
        clip_upper = factor_mean + 3 * factor_std
        cliped_df = feature_df.clip(
            lower=clip_lower, upper=clip_upper, axis=1)
        featured_df = stats.zscore(cliped_df, nan_policy='omit')
        return featured_df

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
        norm_feature_df = pd.DataFrame(clip_norm_022917(feature_df), columns=feature_df.columns,
                                       index=feature_df.index)

        for date, row in group_idx.iterrows():
            start_idx, end_idx = row["first"], row["last"]
            sub_feature_df = norm_feature_df.iloc[start_idx:end_idx + 1]
            sub_lable_df = label_df.iloc[start_idx:end_idx + 1]
            df = pd.concat([sub_feature_df, sub_lable_df], axis=1)

            if len(df) < 2000:
                cnt += 1
                continue
            df = df.dropna(how="any")

            stats_lst.append(_get_factor_stats_info_util(self, date, df, factor, label, percent_list, rolling_window,
                                                         stratified_list))
        if cnt > 0:
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

        #         t1 - time.time()
        #         mine = MINE()
        #         mine.compute_score(df[factor], df[label])
        #         result_dict['mic'] = mine.mic()
        #         result_dict['mas'] = mine.mas()
        #         result_dict['mev'] = mine.mev()
        #         result_dict['mcn'] = mine.mcn()
        #         result_dict['mcn_general'] = mine.mcn_general()
        #         result_dict['gmic'] = mine.gmic()
        #         result_dict['tic'] = mine.tic()
        #         print("mine耗时：", time.time()-t1)

        #         _ = self.calc_mutual_info(df, factor, label)
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


    start_ray_cluster(object_spill_path=object_spill_path)
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
        ray.shutdown()
        return all_factor_stats_df
    else:
        ray.shutdown()
        return pd.DataFrame()


def factor_eval_save_to_dolphindb(factor_label_df, label, factor_list, start_date, end_date, daily_avg_cnt = 2000, object_spill_path = None):
    if type(factor_list) == str:
        factor_list = [factor_list]

    start_datetime = pd.to_datetime(start_date, format='%Y%m%d')
    end_datetime = pd.to_datetime(end_date, format='%Y%m%d')
    end_datetime = end_datetime.replace(hour=23, minute=59, second=59)
    factor_label_sambol_df = factor_label_df[
        (factor_label_df.index >= start_datetime) & (factor_label_df.index <= end_datetime)]

    tagger_df = factor_label_sambol_df[label]
    factor_df = factor_label_sambol_df[factor_list]
    factor_info = factor_df.describe().loc["count"]
    trading_data_list = set(factor_df.index.strftime("%Y%m%d").tolist())

    factor_name_list = factor_info[factor_info > len(trading_data_list) * daily_avg_cnt].index.tolist()
    print("1. 原有{}个因子，条数符合评价条件的{}个因子".format(len(factor_list), len(factor_name_list)))

    sub_factor_df = factor_df[factor_name_list]
    feature_label_df = merge_factor_label(sub_factor_df, tagger_df, dropna=False)
    feature_label_df.drop(["MDDate", "MDTime"], axis=1, inplace=True)

    print("sub_factor_df:" + str(sub_factor_df.shape))
    print("feature_label_df:" + str(feature_label_df.shape))
    #             print(feature_label_df.head())
    #         l1 = len(feature_label_df)
    #         c1 = len(feature_label_df.columns)
    #         feature_label_df.dropna(axis=1, how='all', inplace=True)
    #         print("\t\t去除空值， 行：{}→{} | 列： {}→{}".format(l1, len(feature_label_df), c1, len(feature_label_df.columns)))

    t1 = time.time()
    analyzer = FactorBacktest(n_jobs=2)
    all_factor_stats_df = test_all_factor(analyzer, feature_label_df, label=label, object_spill_path = object_spill_path)
    print("4. Evaluate Factor ...", time.time() - t1)
    #     all_factor_stats_df.to_parquet(os.path.join(all_config["path_config"]["Exp_path"], "new_{}_all_factor_stats_df_{}.parquet".format(symbol, factor_group)))
    all_factor_stats_df["label"] = label
    print(all_factor_stats_df.head())

    return all_factor_stats_df


#             self.mdb.factor_evaluation_data_todb(sub_factor_name_list,symbol,label,all_factor_stats_df)
#             return all_factor_stats_df

if __name__ == "__main__":
    import os

    factor_name_list =  ["ReferenceMidPrice",
                         "FactorAlpha101World041",
                         "FactorAsk1AvgLS",
                         "FactorBearPower_n_tick10",
                         "FactorBearPower_n_tick100",
                         "FactorBearPower_n_tick30",
                         "FactorBid1AvgLS",
                         "FactorBookBuy13MoveQtyDeltaSum",
                         "FactorBookBuy15Move1QtyDelta",
                         "FactorBookBuy15Move1QtyDeltaDy0TickQtyRatio",
                         "FactorBookBuy15Move1QtyDeltaDy0TickRatio",
                         "FactorBookBuy15Move1QtyDeltaMa100",
                         "FactorBookBuy15MoveQtyDeltaSum",
                         "FactorBookBuy610Move1QtyDeltaMa100",
                         "FactorBookBuy610MoveQtyDeltaSum",
                         "FactorBookBuyMaxQtyPxDwDelta",
                         "FactorBookBuyMaxQtyPxPxRatio",
                         "FactorBookBuyQtySumQtyMaxPxMuity",
                         "FactorBookBuySell10PriceRangeDeltaNegativeQtyRatio",
                         "FactorBookBuySell10PriceRangeDeltaNegativeTickRatio",
                         "FactorBookBuySell15DeltaMa100",
                         "FactorBookBuySell5PriceRangeDeltaNegativeQtyRatio",
                         "FactorBookBuySell5PriceRangeDeltaNegativeTickRatio",
                         "FactorBookBuySell610DeltaMa100",
                         "FactorBookBuySell610QtyRatiomaxsize",
                         "FactorBookBuySumQtyLastPreRatio",
                         "FactorBookSell610Move1QtyDeltaMa100",
                         "FactorBookSell610MoveQtyDeltaSum",
                         "FactorBookSellMaxQtyPxDwDelta",
                         "FactorBookSellMaxQtyPxPxRatio",
                         "FactorBookSellMaxVolIndex10VolRatio",
                         "FactorBuyOrderQtyStd_n_tick10",
                         "FactorBuyOrderQtyStd_n_tick100",
                         "FactorBuyOrderQtyStd_n_tick60",
                         "FactorBuySellOrderQtyRatio",
                         "FactorBuySellOrderQtyRatioDiff",
                         "FactorBuyTrade2OrderQtyRatio",
                         "FactorBuyVolumeAvgLS",
                         "FactorBuyWillingByCountEn1",
                         "FactorBuyWillingByMoneyEn1",
                         "FactorBuyWillingByPrice",
                         "FactorBuyWillingByQtyEn1",
                         "FactorChangjiangAlpha1_n_tick20",
                         "FactorChangjiangAlpha4_n_tick20",
                         "FactorErAlpha_n_tick100",
                         "FactorErAlpha_n_tick20",
                         "FactorErAlpha_n_tick40",
                         "FactorFqs01_n_tick100",
                         "FactorFqs01_n_tick20",
                         "FactorFqs01_n_tick40",
                         "FactorFqs02_n_tick100",
                         "FactorFqs02_n_tick20",
                         "FactorFqs02_n_tick40",
                         "FactorFqs04",
                         "FactorGtjaAlpha013",
                         "FactorGtjaAlpha014_n_tick20",
                         "FactorGtjaAlpha015_n_tick20",
                         "FactorGtjaAlpha015_n_tick50",
                         "FactorGtjaAlpha015_n_tick90",
                         "FactorGtjaAlpha047_n_tick10",
                         "FactorGtjaAlpha047_n_tick30",
                         "FactorGtjaAlpha078",
                         "FactorGuangFaTechIndicatorAPZ_n_tick10",
                         "FactorGuangFaTechIndicatorAPZ_n_tick30",
                         "FactorGuangFaTechIndicatorENV_n_tick20",
                         "FactorGuangFaTechIndicatorTDI_n_tick20",
                         "FactorGuangFaTechIndicatorVMA_n_tick20",
                         "FactorGuangFaTechIndicatorVMA_n_tick50",
                         "FactorGuangFaTechIndicatorVMA_n_tick90",
                         "FactorMidPriceSpeed_n_tick20",
                         "FactorOrderImbalance_level1",
                         "FactorOrderImbalance_level2",
                         "FactorOrderQtyChangeEachLevelBuy_n_tick100",
                         "FactorOrderQtyChangeEachLevelBuy_n_tick20",
                         "FactorOrderQtyChangeEachLevelBuy_n_tick60",
                         "FactorOrderQtySpread",
                         "FactorSellOrderQtyStd",
                         "FactorShortTermAmp",
                         "FactorSkew1",
                         "FactorSkew1_n_tick30",
                         "FactorSkew2",
                         "FactorSkew2_n_tick30",
                         "FactorSlicePressure",
                         "FactorTechIndicatorForB3612",
                         "FactorTechIndicatorForCMF",
                         "FactorTechIndicatorForSAR_n_tick100",
                         "FactorTechIndicatorForSAR_n_tick60",
                         "FactorTechIndicatorForWR_n_tick100",
                         "FactorTechIndicatorForWR_n_tick60",
                         "FactorTianFengAlpha14_n_tick100",
                         "FactorTianFengAlpha21_n_tick20",
                         "FactorTianFengAlpha21_n_tick40",
                         "FactorTianFengAlpha21_n_tick60",
                         "FactorTianFengAlpha3_n_tick100",
                         "FactorTianFengAlpha3_n_tick20",
                         "FactorTianFengAlpha3_n_tick40",
                         "FactorTianFengAlpha3_n_tick60",
                         "FactorTradeMoneyCum1",
                         "FactorTrendStrength_n_tick20",
                         "FactorTrendStrength_n_tick40",
                         "FactorUpCount_n_tick20",
                         "FactorUpCount_n_tick40",
                         "FactorVixDownRatio_n_tick20",
                         "FactorVixDownRatio_n_tick40",
                         "FactorVixUp_n_tick20",
                         "FactorVolPriceCorr_n_tick100",
                         ]
    factor_name_list.remove("ReferenceMidPrice")
    base_dir = os.path.join("/data/user/quanttest007/013150/exp_result/002594.SZ-002594.SZ_trade_v00")
    TARGET_df_test, T_test, X_train, Y_train, X_valid, Y_valid, X_test, Y_test = pd.read_pickle(
        os.path.join(base_dir, "dataset/data.pkl"))
    Y_test_pred, Y_valid_pred = pd.read_pickle(os.path.join(base_dir, "dataset/data1.pkl"))

    feature_df = pd.DataFrame(X_test, index = T_test, columns = factor_name_list)
    label_df = pd.DataFrame(Y_test, index = T_test, columns = ["label"])
    factor_label_df = pd.merge(feature_df, label_df, left_index=True, right_index=True)
    start_date, end_date = "20230501", "20230903"
    result = factor_eval_save_to_dolphindb(factor_label_df,  label = "label", factor_list = factor_name_list[:2], start_date = start_date, end_date = end_date)
    print(result)
