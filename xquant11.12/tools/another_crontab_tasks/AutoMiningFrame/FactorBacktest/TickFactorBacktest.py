import datetime
import time
import pandas as pd
from scipy import stats
import ray
from joblib import Parallel, delayed
from statsmodels.stats.multitest import multipletests
from AutoMiningFrame.FactorBacktest.data.data_prepare import ClipCalculator, NormCalculator
from .backtest_toolbox import *
import copy
from itertools import product
from xquant.factordata import FactorData

def filter_valid_data(df):
    now_time = df.index[0]
    am_start_time = datetime.datetime(now_time.year, now_time.month, now_time.day, 9, 30)
    am_end_time = datetime.datetime(now_time.year, now_time.month, now_time.day, 11, 30)
    pm_start_time = datetime.datetime(now_time.year, now_time.month, now_time.day, 13, 00)
    pm_end_time = datetime.datetime(now_time.year, now_time.month, now_time.day, 14, 57)
    condition = ((df.index >= am_start_time) & (df.index <= am_end_time)) | (
                (df.index >= pm_start_time) & (df.index <= pm_end_time))
    return df[condition]

def fileter_invalid_data_by_tradingday(df, trading_date_list):
    df["MDDate"] = [i.strftime("%Y%m%d") for i in df.index.date]
    df = df[df.MDDate.isin(trading_date_list)]
    df.drop(columns=["MDDate"], inplace=True)
    return df


def data_prepare_preprocess(feature_df_list_id, idx,  transform,clip_type='3sigma', quantile=[0.02, 0.98], scaler_type='z-score'):
    clip_calculator = ClipCalculator(clip_type, quantile)
    norm_calculator = NormCalculator(scaler_type)
    calc_list = [clip_calculator, norm_calculator]

    normalized_df = feature_df_list_id[idx]
    if transform:
        for calc in calc_list:
            normalized_df = calc.train_transform(normalized_df)
    return normalized_df


def data_prepare_preprocess_batch(feature_df_list, calc_list):
    feature_df = pd.concat(feature_df_list, axis=0)
    for i, calc in enumerate(calc_list):
        if i==0:
            res = calc.train_transform(feature_df)
        else:
            res = calc.train_transform(res)
    return res


class FactorBacktest(object):
    """
    检测多因子的类，分析单因子，并筛选
    """

    def __init__(self, n_jobs=1):
        """
        构造函数，指定n_jobs， 设置阈值和相关因子检查的配置
        :param n_jobs:
        """
        self.n_jobs = n_jobs
        self.reset_option()
        self._set_check_list()

    # 初始化时调用
    def _set_check_list(self):
        self.p_val_list = []
        self.ret_related = []
        self.auto_corr_list = []
        for x in self.factor_test['auto_corr_x_minute_list']:
            self.auto_corr_list.append('auto_corr_{}'.format(x))
        for percent in self.factor_test['percent']:
            self.p_val_list.append('long_p_value_{}'.format(percent))
            self.p_val_list.append('short_p_value_{}'.format(percent))
            self.ret_related.append('trade_long_return_{}'.format(percent))
            self.ret_related.append('trade_short_return_{}'.format(percent))

    def reset_option(self):
        """
        设置阈值和相关因子检查的配置
        :return:
        """
        self.factor_test = {
            ## 基础信息配置 ##
            'tick_interval': 3,
            'auto_corr_x_minute_list': [1, 3, 5],
            ## 统计信息 ##
            # label 与 factor的相关性
            'corr_threshold': 0.005,
            # factor 自相关性
            'auto_corr_minute_threshold_list': [0.85, 0.80, 0.7],
            # factor 峰度
            'kurt_threshold': 20,
            # factor 偏度
            'skew_threshold': 3,
            # MI
            'mutual_infomation': None,
            # Normal_IC
            'normal_ic': 0.06,
            # Rank IC
            'rank_ic': 0.06,
            ## 交易相关, 即简单回测 ##
            'percent': [0.1, 0.5],
            'stratified': [5],
            'rolling_win': 20,
            'long_return_threshold': 0.00015,
            'short_return_threshold': 0.00015,
            'long_pval_threshold': 0.1,
            'short_pval_threshold': 0.1,
            # 因子筛选时的互相关系数
            # 'factor_label_corr_threshold': 0.5
        }

    def set_factor_test_option(self, dct: dict):
        """
        重置参数
        :param dct:
        :return:
        """
        for key in dct.keys():
            self.factor_test[key] = dct[key]
        self._set_check_list()

    def prepare_factor_label(self, dp, label="Label", use_normalized=False):

        assert len(dp.train_dataset.feature_df_list) == len(dp.train_dataset.label_df_list)

        factor_label_list = []
        for i, (feature, label) in enumerate(zip(dp.train_dataset.feature_df_list, dp.train_dataset.label_df_list)):
            feature["MDDate"] = feature.index.date
            feature.sort_index(inplace=True)
            label.sort_index(inplace=True)
            tmp_df = feature.merge(label, how='inner', left_index=True, right_index=True)
            factor_label_list.append(tmp_df)
        return factor_label_list


    def prepare_factor_label_by_dataframe(self, factor_df, label_df, factor_name_list, tagger_name_list,
                                          clip_type='3sigma', quantile=[0.02, 0.98], scaler_type='z-score',
                                          need_all_date_ic=False):
        factor_df = factor_df.sort_index()
        start_time = factor_df.index.date[0].strftime("%Y%m%d")
        end_time = factor_df.index.date[-1].strftime("%Y%m%d")
        fd = FactorData()
        factor_df = fileter_invalid_data_by_tradingday(factor_df, fd.tradingday(start_time, end_time))
        label_df = fileter_invalid_data_by_tradingday(label_df, fd.tradingday(start_time, end_time))
        factor_label = pd.merge(factor_df, label_df, left_index=True, right_index=True)
        factor_label["MDDate"] = factor_label.index.date
        factor_label["MDTime"] = factor_label.index.time
        factor_label.dropna(how="any", axis=0, inplace=True)
        keep_column_list = factor_name_list + tagger_name_list + ["MDDate", "MDTime"]
        factor_label = factor_label[keep_column_list]

        factor_label.replace([np.inf, -np.inf], np.NaN, inplace=True)
        factor_label.dropna(axis=1, how='all', inplace=True)
        factor_label.dropna(axis=0, how='any', inplace=True)
        feature_df_list = []
        label_df_list = []
        am_start_time = pd.to_datetime("09:30").time()
        am_end_time = pd.to_datetime("11:30").time()
        pm_start_time = pd.to_datetime("13:00").time()
        pm_end_time = pd.to_datetime("14:57").time()
        condition = ((factor_label["MDTime"] >= am_start_time) & (factor_label["MDTime"] <= am_end_time)) | (
                    (factor_label["MDTime"] >= pm_start_time) & (factor_label["MDTime"] <= pm_end_time))
        factor_label = factor_label[condition]
        for index, (name, group) in enumerate(factor_label.groupby('MDDate')):
            feature_df_list.append(group[factor_name_list])
            label_df_list.append(group[tagger_name_list])
        feature_df_list = [i for i in feature_df_list if not i.empty]
        label_df_list = [i for i in label_df_list if not i.empty]

        # 按天标准化
        # ray.init(num_cpus=10)
        # feature_df_list_id = ray.put(feature_df_list)
        # remote_func = ray.remote(data_prepare_preprocess)
        # tasks = [remote_func.remote(feature_df_list_id, idx, True, clip_type='3sigma', quantile=[0.02, 0.98], scaler_type='z-score') for idx in range(len(feature_df_list))]
        # normalized_data_list = ray.get(tasks)
        # ray.shutdown()
        # 统一标准化
        clip_calculator = ClipCalculator(clip_type, quantile)
        norm_calculator = NormCalculator(scaler_type)
        calc_list = [clip_calculator, norm_calculator]
        normalized_data_list = []
        normalized_data = data_prepare_preprocess_batch(feature_df_list, calc_list)
        normalized_data = normalized_data.reset_index()
        normalized_data['MDDate'] = normalized_data['timestamp'].apply(lambda x: x.strftime("%Y%m%d"))
        normalized_data = normalized_data.set_index('timestamp')
        for index, (name, group) in enumerate(normalized_data.groupby('MDDate')):
            normalized_data_list.append(group[factor_name_list])

        factor_label_list = []
        for i, (feature, label) in enumerate(zip(normalized_data_list, label_df_list)):
            feature["MDDate"] = feature.index.date
            feature.sort_index(inplace=True)
            label.sort_index(inplace=True)
            tmp_df = feature.merge(label, how='inner', left_index=True, right_index=True)
            factor_label_list.append(tmp_df)
        if need_all_date_ic:
            remote_get_ic = ray.remote(get_ic)
            normalized_data.sort_index(inplace=True)
            label_df.sort_index(inplace=True)
            tmp_df = normalized_data.merge(label_df, how='inner', left_index=True, right_index=True)
            df_copy_id = ray.put(tmp_df)
            factor_normal_ic_per_fac = ray.get([remote_get_ic.remote(df_copy_id, factor, ret=label, ic_type='normal',need_factor_name=True)
                                                for factor, label in product(factor_name_list, tagger_name_list)])
            factor_rank_ic_per_fac = ray.get([remote_get_ic.remote(df_copy_id, factor, ret=label, ic_type='rank',need_factor_name=True)
                                              for factor, label in product(factor_name_list, tagger_name_list)])

            return factor_label_list, factor_normal_ic_per_fac, factor_rank_ic_per_fac
        else:
            return factor_label_list

    def calc_factor_label_corr(self, df, factor: str, label: str):
        """
        计算因子与 label 的相关度
        :param df:
        :param factor:
        :param label:
        :return:
        """
        df_factor = df[factor]
        s_label = df[label]
        assert isinstance(df_factor, pd.Series)
        assert isinstance(s_label, pd.Series)
        return df_factor.corr(s_label)

    def calc_mutual_info(self, df, factor: str, label: str):
        """
        计算因子与label的分布关系
        :param df:
        :param factor:
        :param label:
        :return:
        """
        df_factor = df[factor]
        df_label = df[label]
        pass

    def calc_factor_label_ic(self, df, factor: str, label: str):
        """
        :param df:
        :param factor:
        :param label:
        :return:
        """
        factor_normal_ic = get_ic(df, factor, ret=label, ic_type='normal')
        factor_rank_ic = get_ic(df, factor, ret=label, ic_type='rank')
        return factor_normal_ic, factor_rank_ic

    def calc_factor_skew(self, df, factor: str):
        """
        计算偏度
        :param df:
        :param factor:
        :return:
        """
        df_factor = df[factor]
        return df_factor.skew()

    def calc_factor_kurt(self, df, factor: str):
        """
        计算峰度
        :param df:
        :param factor:
        :return:
        """
        df_factor = df[factor]
        return df_factor.kurt()

    def calc_std(self, df, factor: str):
        """
        标准差
        :param df:
        :param factor:
        :return:
        """
        df_factor = df[factor]
        return df_factor.std()

    def calc_factor_auto_corr(self, df, factor: str):
        """
        计算因子自身相关性, 滑动1min, 3min ,5min
        :param df:
        :param factor:
        :return:
        """
        df_factor = df[factor]
        assert isinstance(df_factor, pd.Series)
        x_ticks = [i * 60 // self.factor_test['tick_interval'] for i in self.factor_test['auto_corr_x_minute_list']]
        results = {}
        for ix, shift_tick in enumerate(x_ticks):
            results['auto_corr_{}'.format(self.factor_test['auto_corr_x_minute_list'][ix])] = df_factor.corr(
                df_factor.shift(shift_tick))
        return results

    def calc_profit_stats_by_stratified(self, df, factor, label, n_bins):
        """
        因子分层收益率检验
        :param df:
        :param factor:
        :param label:
        :param n_bins:
        :return:
        """
        group_label = ['stratified_{}'.format(i + 1) for i in range(0, n_bins)]
        df_label_factor = df.loc[:, [label, factor]]
        stats_dict = {}
        try:
            df_label_factor['stratified_cut'] = pd.qcut(df_label_factor[factor], n_bins, labels=group_label,
                                                        precision=3,
                                                        duplicates='raise')
            df_long = df_label_factor.loc[
                df_label_factor['stratified_cut'] == 'stratified_{}'.format(n_bins), label]
            df_short = df_label_factor.loc[df_label_factor['stratified_cut'] == 'stratified_{}'.format(1), label]
            stats_dict['stratified_N{}'.format(n_bins)] = df_long.mean()
            stats_dict['stratified_trade_short_return_{}'.format(n_bins)] = -df_short.mean()
            long_n = len(df_long)
            short_n = len(df_short)
            stats_dict['stratified_long_p_value_{}'.format(n_bins)] = stats.t.sf(
                (df_long.mean() / df_long.std()) * np.sqrt(long_n),
                long_n - 1)
            stats_dict['stratified_short_p_value_{}'.format(n_bins)] = stats.t.sf(
                (-df_short.mean() / df_short.std()) * np.sqrt(short_n),
                short_n - 1)
        except:
            stats_dict['stratified_trade_long_return_{}'.format(n_bins)] = np.nan
            stats_dict['stratified_trade_short_return_{}'.format(n_bins)] = np.nan
            stats_dict['stratified_long_p_value_{}'.format(n_bins)] = np.nan
            stats_dict['stratified_short_p_value_{}'.format(n_bins)] = np.nan
        return stats_dict

    def calc_profit_stats_by_percent(self, df, factor, label, percent: float, rolling_win=20):
        """
        分位数收益率检验
        :param df:
        :param factor:
        :param label:
        :param percent:
        :param rolling_win:
        :return:
        """
        df_factor = df[factor]
        df_label = df[label]
        long_thres = df_factor.rolling(rolling_win).quantile(percent)
        short_thres = df_factor.rolling(rolling_win).quantile(1 - percent)
        df_long = df_label[df_factor >= long_thres]
        df_short = df_label[df_factor <= short_thres]
        stats_dict = {}
        df_long.dropna(inplace=True)
        df_short.dropna(inplace=True)
        stats_dict['trade_long_return_{}'.format(percent)] = df_long.mean()
        stats_dict['trade_short_return_{}'.format(percent)] = -df_short.mean()
        long_n = len(df_long)
        short_n = len(df_short)
        try:
            stats_dict['long_p_value_{}'.format(percent)] = stats.t.sf(
                (df_long.mean() / df_long.std()) * np.sqrt(long_n),
                long_n - 1)
            stats_dict['short_p_value_{}'.format(percent)] = stats.t.sf(
                (-df_short.mean() / df_short.std()) * np.sqrt(short_n),
                short_n - 1)
        except:
            stats_dict['long_p_value_{}'.format(percent)] = np.nan
            stats_dict['short_p_value_{}'.format(percent)] = np.nan
        return stats_dict

    def _get_factor_stats_info_util(self, n, df, factor, label, percent_list, rolling_window, stratified_list):
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
        result_dict['MDDate'] = df.iloc[0]['MDDate']

        result_dict['test_factor'] = factor
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
        _ = self.calc_mutual_info(df, factor, label)
        for percent in percent_list:
            stats_dict = self.calc_profit_stats_by_percent(df, factor, label, percent=percent,
                                                           rolling_win=rolling_window)
            result_dict.update(stats_dict)
        for n_bins in stratified_list:
            stats_dict_stratified = self.calc_profit_stats_by_stratified(df, factor, label, n_bins)
            result_dict.update(stats_dict_stratified)
        return result_dict

    def _get_single_factor_stats_info(self, n, df_list, factor, label, percent_list, rolling_window, stratified_list):
        """
        单因子多日检测
        :param n:
        :param df_list:
        :param factor:
        :param label:
        :return:
        """
        stats_lst = Parallel(n_jobs=self.n_jobs)(
            delayed(self._get_factor_stats_info_util)(n, df, factor, label, percent_list, rolling_window,
                                                      stratified_list)
            for n, df in enumerate(df_list))
        stats_df = pd.DataFrame(stats_lst)

        # 修正p_value, multiple test: Benjamini and Hochberg / Bonferroni
        def pval_correction(df, p_val_col, alpha):
            _, pvals_corrected, _, _ = multipletests(df[p_val_col].values, alpha=alpha, method='fdr_bh',
                                                     is_sorted=False)
            return pvals_corrected

        for p_val_name in self.p_val_list:
            stats_df[p_val_name] = pval_correction(stats_df, p_val_name, 0.1)
        stats_df.set_index('MDDate', drop=True, inplace=True)
        return stats_df

    def test_all_factor(self, df_list, label='Label', factor_name_list=None):
        """
        多因子多日检测
        :param df_list:
        :param label:
        :param factor_name_list:
        :param percent_list:
        :param rolling_window:
        :param stratified_list:
        :return:
        """
        if factor_name_list is not None:
            f_name = factor_name_list
        else:
            f_name = list(df_list[0])
            if 'Label' in f_name:
                f_name.remove('Label')
            if 'MDDate' in f_name:
                f_name.remove('MDDate')
        all_factor_stats_list = Parallel(n_jobs=self.n_jobs, verbose=0)(
            delayed(self._get_single_factor_stats_info)(
                n,
                df_list,
                factor,
                label,
                self.factor_test["percent"],
                self.factor_test["rolling_win"],
                self.factor_test["stratified"]
            ) for n, factor in enumerate(f_name))
        all_factor_stats_df = pd.concat(all_factor_stats_list)
        return all_factor_stats_df

    def filter_factors(self, dp, label='labelEQendtaggertypeEQmidpricedsizeEQ300'):
        factor_label_list = self.prepare_factor_label(dp, label)
        all_factor_stats_df = self.test_all_factor(
            factor_label_list,
            label=label
        )
        all_pre_filter = self._analyse_all_factor_stat(all_factor_stats_df)
        # self.get_factor_passed(all_pre_filter)
        passed_list = self.get_factor_passed(all_pre_filter)
        # 过滤高相关性的因子
        self.passed_list_final = self.get_rc_stage2filter(
            factor_label_list, all_pre_filter, passed_list, label=label, threshold=0.85)

    def _analyse_single_factor(self, all_factor_stats_df, factor):
        """
        单因子结果分析，
        :param all_factor_stats_df:
        :param factor:
        :return:
        """
        curr_factor = all_factor_stats_df[all_factor_stats_df['test_factor'] == factor]
        fig, axes = plt.subplots(2, 2, figsize=(20, 20))
        ### 单因子，各个指标NA天数统计
        fontsize = 20
        count_nan = pd.DataFrame(len(curr_factor) - curr_factor.count()).T
        sns.barplot(ax=axes[0, 0], data=count_nan)
        axes[0, 0].set_title('Missing NA(days)', fontsize=fontsize)
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=90, fontsize=fontsize)
        axes[0, 0].set_ylabel("Days", fontsize=fontsize)
        ### 因子ret类评价指标显著性统计
        curr_factor_stat = curr_factor.loc[:, self.p_val_list]
        # curr_factor_stat.describe()
        p_10 = (curr_factor_stat <= 0.1).sum() / len(curr_factor)
        p_5 = (curr_factor_stat <= 0.05).sum() / len(curr_factor)
        # 转为图片
        significance_pd = pd.DataFrame([p_10, p_5], index=['p<0.1 占比', 'p<0.05 占比'])
        for col_name in list(curr_factor_stat):
            g = sns.distplot(curr_factor_stat[col_name], ax=axes[0, 1], kde=False, label=col_name,
                             bins=np.arange(0, 1, 0.05))
        # ax.set_xaxis([2,4,6,8)
        axes[0, 1].set_xticks(np.arange(0, 1, 0.05))
        axes[0, 1].set_xlabel('p_value', fontsize=fontsize)
        axes[0, 1].legend()
        axes[0, 1].set_title('RV(P_val)', fontsize=fontsize)
        ### ret 类
        curr_factor_stat = curr_factor.loc[:, self.ret_related]
        # print("无法计算收益的天数")
        # print(curr_factor_stat[curr_factor_stat.isnull().T.any()].index)
        cum_sum = curr_factor_stat.cumsum()
        cum_sum.fillna(method='ffill', inplace=True)
        cum_sum.dropna(inplace=True)
        cum_sum.plot(kind='line', ax=axes[1, 0])
        # sns.lineplot(data=cum_sum, ax=axes[1, 0], linewidth=2.5)
        axes[1, 0].set_xlabel('Date', fontsize=fontsize)
        axes[1, 0].set_ylabel('Accum_ret(1/1000)', fontsize=fontsize)
        axes[1, 0].set_xticklabels(axes[1, 0].get_xticklabels(), rotation=70, fontsize=fontsize)
        axes[1, 0].set_title('Accumulate_ret', fontsize=fontsize)
        # 统计值
        ic_cate = pd.DataFrame(
            curr_factor.mean()[['normal_ic', 'rank_ic', 'skew', 'kurt', 'corr'] + self.auto_corr_list])
        ret_cate = pd.DataFrame(curr_factor.mean()[self.ret_related])
        pval_cate = pd.DataFrame(curr_factor.median()[self.p_val_list])
        pre_filter = pd.concat([ic_cate, ret_cate, pval_cate], axis=0)
        text = []
        for x in pre_filter.index:
            text.append("{}: {:.4f}".format(x, pre_filter.loc[x].values[0]))
        axes[1, 1].text(0.15, 0.95, '\n'.join(text),
                        fontsize=20,
                        bbox={'facecolor': 'white', 'alpha': 1, 'pad': 5},
                        verticalalignment='top', )
        axes[1, 1].set_title("Analysis for Factor {}".format(factor), fontsize=fontsize)

        # plt.show()
        fig.tight_layout()
        return curr_factor, significance_pd, fig

    def _analyse_all_factor_stat(self, all_factor_stats_df):
        """
        多因子结果分析
        :param all_factor_stats_df:
        :return:
        """
        ic_cate = all_factor_stats_df.groupby('test_factor').mean().abs()[
            ['normal_ic', 'rank_ic', 'skew', 'kurt', 'corr'] + self.auto_corr_list]
        ret_cate = all_factor_stats_df.groupby('test_factor').mean().abs()[self.ret_related]
        pval_cate = all_factor_stats_df.groupby('test_factor').median()[self.p_val_list]

        def std_corr(df):
            return df['factor_std'].corr(df['label_std'], method='spearman')

        std_corr_cat = pd.DataFrame(all_factor_stats_df.groupby('test_factor').apply(std_corr).abs(),
                                    columns=['f_ret_std_corr'])
        # 每个因子、按天汇总（）检测下的结果。 因子A _> (指标1， 指标2， 指标3.。。。。。。。。。。。。。)
        all_pre_filter = pd.concat([ret_cate, ic_cate, pval_cate, std_corr_cat], axis=1)
        return all_pre_filter.round(5)

    def get_factor_passed(self, all_pre_filter):
        """
        筛选因子， 可继承overwrite，筛选的第一步
        :param all_pre_filter:
        :return:
        """
        # cond1 = all_pre_filter['corr'] >= self.factor_test['corr_threshold']
        # cond2 = pd.Series([False] * len(cond1), index=cond1.index)
        # for i, auto_corr in enumerate(self.auto_corr_list):
        #     cond2 = cond2 | (all_pre_filter[auto_corr] >= self.factor_test['auto_corr_minute_threshold_list'][i])
        # cond3 = (all_pre_filter['kurt'] <= self.factor_test['kurt_threshold']) & (
        #         all_pre_filter['skew'] <= self.factor_test['skew_threshold'])
        # cond4 = pd.Series([False] * len(cond1), index=cond1.index)
        # for percent in self.factor_test['percent']:
        #     long_cond = all_pre_filter['long_p_value_{}'.format(percent)] <= self.factor_test['long_pval_threshold']
        #     short_cond = all_pre_filter['short_p_value_{}'.format(percent)] <= self.factor_test['short_pval_threshold']
        #     cond4 = cond4 | (long_cond & short_cond)
        # for percent in self.factor_test['percent']:
        #     long_cond = all_pre_filter['long_p_value_{}'.format(percent)] >= 0.99
        #     short_cond = all_pre_filter['short_p_value_{}'.format(percent)] >= 0.99
        #     cond4 = cond4 | (long_cond & short_cond)
        cond5 = (all_pre_filter['rank_ic'] >= self.factor_test['rank_ic']) & (
                all_pre_filter['normal_ic'] >= self.factor_test['normal_ic'])
        cond = cond5
        passed_list = cond[cond == True]
        try:
            return passed_list.index.tolist()
        except:
            return passed_list.index.to_list()

    def analyze_one(self, factor_label_list, factor, label="Label"):
        """
        画factor和label的所有值的散点图、factor的分布图
        :param factor_label_listl:
        :param factor:
        :param label:
        :return:
        """
        df = pd.concat([df[[factor, label]] for df in factor_label_list], axis=0)
        fig, axes = plt.subplots(1, 2, figsize=(32, 9))
        plt_distribution(df, factor, ax=axes[0])
        plt_scatter(df, factor, label, ax=axes[1])
        # return fig

    def calc_factors_corr(self, factors_data, metric=None, plot=False):
        """
        :param factors_data:
        :param metric:
        :param plot:
        :return:
        """
        if metric == None:
            result = factors_data.corr()
        else:
            result = factors_data.corr(metric)
        # 是否保存相关性热力图
        if plot:
            fig, axes = plt.subplots(1, 1, figsize=(32, 20))
            sns.heatmap(result, annot=False)
        return result.abs(), fig

    def get_rc_stage2filter(self, factor_label_list: list, all_pre_filter: pd.DataFrame, columns: list, label: str,
                            metric_xx: str = 'pearson', threshold: float = 0.0):
        '''
        因子之间冗余性筛选
        :param factor_label_list:
        :param all_pre_filter:
        :param columns:
        :param metric_xy: str: x与y 辅助排序的metric
        :param metric_xx: str: x与x correlation的metric
        :param threshold: Cov(x,x)的阈值
        :return:
        '''
        # 按 metric 取出所有因子的指标
        metric = all_pre_filter['rank_ic'].sort_values(ascending=False)
        # 拼接 tick 数据
        factors_pre_data = pd.concat(factor_label_list, axis=0)
        # 去掉不需要的列
        factors_corr_info = factors_pre_data.drop([label, 'MDDate'], axis=1)
        # 取出 columns 对应 metric 并排序
        metric = pd.Series(metric, index=columns).sort_values(ascending=False)
        # 获取第一步筛选出来的列
        columns = metric.index.tolist()
        factors_corr_info = pd.DataFrame(factors_corr_info, columns=columns)
        # 计算相关性
        factors_co, _ = self.calc_factors_corr(factors_corr_info, metric=metric_xx, plot=True)
        # 矩阵处理
        np.fill_diagonal(factors_co.values, 0)
        factors_co = pd.DataFrame(np.tril(factors_co.values), index=columns, columns=columns)
        # 根据阈值筛选冗余因子
        for i in range(len(factors_co)):
            factor_index = np.where(factors_co > threshold)[0]
            if len(factor_index) > 0:
                factor_index = factor_index[0]
                # print(columns[factor_index])
                factors_co = factors_co.drop(index=columns[factor_index], columns=columns[factor_index])
                columns.remove(columns[factor_index])
        return factors_corr_info[columns]
