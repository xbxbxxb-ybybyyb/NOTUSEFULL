import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from scipy import stats
import seaborn as sns
import textwrap
from tquant.psfactor import PsFactorData
from .backtest_toolbox import get_ic, plt_distribution, plt_scatter
from joblib import Parallel, delayed
from statsmodels.stats.multitest import multipletests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib.colors import *
from reportlab.lib import colors
from io import BytesIO
import datetime
from reportlab.lib.pagesizes import letter
import os


# def vif_process(data, col, thres):
#     data = data.loc[:, col]  # 读取对应列标数据
#     vif = [variance_inflation_factor(data.values, i) for i in range(data.shape[1])][1:]
#     if max(vif) >= thres:
#         index = np.argmax(vif) + 1  # 得到最大值的标号
#         del col[index]  # 删除vif值最大的一项
#         return vif_process(data, col, thres)  # 递归过程
#     else:
#         vif = [variance_inflation_factor(data.values, i) for i in range(data.shape[1])][1:]
#         return col, vif
class FactorBacktest(object):
    """
    检测多因子的类，分析单因子，并筛选
    """

    def __init__(self, n_jobs=4):
        """
        构造函数，指定n_jobs， 设置阈值和相关因子检查的配置
        :param n_jobs:
        """
        self.n_jobs = n_jobs
        self.reset_option()

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
            'vif_thres': 10
        }
        assert len(self.factor_test['auto_corr_minute_threshold_list']) == len(
            self.factor_test['auto_corr_x_minute_list'])

    def set_factor_test_option(self, dct: dict):
        """
        重置参数
        :param dct:
        :return:
        """
        for key in dct.keys():
            self.factor_test[key] = dct[key]
        self._set_check_list()

    def prepare_factor_value(self, library_name, mddate_list, security_id, factor_list=None, label=None):
        """
        传入DatasetPipline, 还原数据
        :param library_name:
        :param mddate_list:
        :param security_id
        :param factor_list
        :param label : str
        :return: list  每个元素是一个DataFrame index : MDTime columns: MDDate,Label,Factor1 Factor2..
        """
        # 从因子库中获取因子值，并加上label
        tps = PsFactorData()
        security_dict = tps.get_factor_value(library_name=library_name, mddate_list=mddate_list,
                                             security_list=[security_id], factor_list=factor_list, sort=True)
        df = security_dict[security_id].set_index(['MDTime'])
        # 修改指定列为因子列
        df.rename(columns={label: 'Label'}, inplace=True)
        # 正式版不加这个处理
        df = df.replace([np.inf, np.NaN, -np.inf, np.nan], 0)
        factor_label_list = []
        for index, (name, group) in enumerate(df.groupby('MDDate')):
            factor_label_list.append(group)
        return factor_label_list

    def prepare_factor_value1(self, security_list, mddate_list, label=None):

        tps = PsFactorData()
        df_dict = {}
        for lib, secu in security_list.items():
            security_dict = tps.get_factor_value(library_name=lib, mddate_list=mddate_list,
                                                 security_list=[secu], sort=True)
            for key in security_dict.keys():
                df_dict[key] = security_dict[key]
        df_lst_by_security = []
        for key, values in df_dict.items():
            df_1 = df_dict[key]
            # 去掉不属于自己的特征
            df_1.dropna(axis=1, how='all', inplace=True)
            df_1.dropna(axis=0, how='any', inplace=True)
            df_1['DateTime'] = df_1.apply(lambda x: x['MDDate'] + x['MDTime'], axis=1)
            df_1.drop(columns=['MDDate', 'MDTime'], inplace=True)
            # 为所有的标签都带上自己的识别号
            df_1.set_index('DateTime', inplace=True)
            df_1.columns = df_1.columns.map(lambda x: x[0:] + '_' + key)
            df_lst_by_security.append(df_1)
        df_concat = pd.concat(df_lst_by_security, axis=1)
        df_concat.dropna(axis=0, how='any', inplace=True)
        print(df_concat.index.names)
        df_concat.reset_index(inplace=True)
        df_concat['MDDate'] = df_concat['DateTime'].apply(lambda x: x[:8])
        df_concat.sort_index(inplace=True)
        del df_concat['DateTime']
        df_concat.rename(columns={label: 'Label'}, inplace=True)
        factor_label_list = []
        for index, (name, group) in enumerate(df_concat.groupby('MDDate')):
            factor_label_list.append(group)
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
            stats_dict['stratified_trade_long_return_{}'.format(n_bins)] = df_long.mean()
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
        result_dict['MDDate'] = df.ix[0, 'MDDate']
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
            stats_df[p_val_name] = pval_correction(stats_df, p_val_name, self.factor_test['long_pval_threshold'])
        stats_df.set_index('MDDate', drop=True, inplace=True)
        return stats_df

    def test_all_factor(self, df_list, label='Label', factor_name_list=None, percent_list=[], rolling_window=None,
                        stratified_list=[]):
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
        all_factor_stats_list = Parallel(n_jobs=self.n_jobs, verbose=10)(
            delayed(self._get_single_factor_stats_info)(n, df_list, factor, label, percent_list, rolling_window,
                                                        stratified_list) for n, factor in enumerate(f_name))
        all_factor_stats_df = pd.concat(all_factor_stats_list)
        return all_factor_stats_df

    def _analyse_one_tsinghua(self):
        pass

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
        axes[0, 0].set_xticklabels(axes[0, 0].get_xticklabels(), rotation=45, fontsize=fontsize)
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
        fig.suptitle("Analysis for Factor {}".format(factor), fontsize=fontsize)
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
        cond1 = all_pre_filter['corr'] >= self.factor_test['corr_threshold']
        cond2 = pd.Series([False] * len(cond1), index=cond1.index)
        for i, auto_corr in enumerate(self.auto_corr_list):
            cond2 = cond2 | (all_pre_filter[auto_corr] >= self.factor_test['auto_corr_minute_threshold_list'][i])
        cond3 = (all_pre_filter['kurt'] <= self.factor_test['kurt_threshold']) & (
                all_pre_filter['skew'] <= self.factor_test['skew_threshold'])
        cond4 = pd.Series([False] * len(cond1), index=cond1.index)
        for percent in self.factor_test['percent']:
            long_cond = all_pre_filter['long_p_value_{}'.format(percent)] <= self.factor_test['long_pval_threshold']
            short_cond = all_pre_filter['short_p_value_{}'.format(percent)] <= self.factor_test['short_pval_threshold']
            cond4 = cond4 | (long_cond & short_cond)
        for percent in self.factor_test['percent']:
            long_cond = all_pre_filter['long_p_value_{}'.format(percent)] >= 0.99
            short_cond = all_pre_filter['short_p_value_{}'.format(percent)] >= 0.99
            cond4 = cond4 | (long_cond & short_cond)
        cond5 = (all_pre_filter['rank_ic'] >= self.factor_test['rank_ic']) & (
                all_pre_filter['normal_ic'] >= self.factor_test['normal_ic'])
        cond = cond1 & cond2 & cond3 & cond4 & cond5
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
        return fig

    def calc_factors_corr(self, factors_data, metric=None, plot=True):
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

    def get_rc_stage2filter(self, factor_label_list: list, all_pre_filter: pd.DataFrame, columns: list,
                            metric_xy: str = 'rank_ic', metric_xx: str = 'pearson',
                            threshold: float = 0.0, method: str = "rc"):
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
        if method == 'rc':
            metric = all_pre_filter[metric_xy].sort_values(ascending=False)
            # 拼接 tick 数据
            factors_pre_data = pd.concat(factor_label_list, axis=0)
            # 去掉不需要的列
            factors_corr_info = factors_pre_data.drop(['Label', 'MDDate'], axis=1)
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
        # 计算过程很慢
        # elif method == 'vif':
        #     factors_pre_data = pd.concat(factor_label_list, axis=0)
        #     factors_pre_data = factors_pre_data[columns]
        #     factors_pre_data = sm.add_constant(factors_pre_data, prepend=True, has_constant='add')
        #     col, vif = vif_process(factors_pre_data, columns, self.factor_test['vif_thres'])
        #
        #     factors_co = factors_pre_data[col]
        #     print("=============Get vif stage2filter end============")
        #     factors_co = self.calc_factors_corr(factors_co, plot=True)
        #
        #     return {"final_passed": col, "vif": vif}


class RunFactorBacktest():
    def __init__(self, n_jobs=4):
        self.fb = FactorBacktest(n_jobs)

    def get_factor_passed(self, all_pre_filter):
        '''
        重写自己的筛选函数
        :param all_pre_filter:
        :return:
        '''
        pass

    def summary_table(self, df,  security_id, label, factor_name='', filter_strategy='', back_type='single'):
        factor_date_list = df.index.tolist()

        test_date = factor_date_list[0] + ' - ' + factor_date_list[-1]
        date_num = len(factor_date_list)
        if back_type == 'single':
            sum_index = ['Factor Name', 'Test Period', 'Security ID', 'Date Count', 'Label']
            sum_val_str = [str(i) for i in [factor_name, test_date, security_id, date_num, label]]
        elif back_type == 'multi':
            sum_index = ['Test Period', 'Security ID', 'Date Count', 'Label', 'Filter strategy']
            sum_val_str = [str(i) for i in [test_date, security_id, date_num, label, filter_strategy]]
        sum_df = pd.DataFrame(sum_val_str, index=sum_index)
        sum_df.columns = ['Basic_Info']
        return sum_df.T

    def dataframe2str(self, df):
        """get dataframe column, return string with format"""
        # df = df.T
        df_col = df.columns.tolist()
        df_row = df.index.tolist()
        df_str = [''] + df_row
        for col in df_col:
            data = ['\n'.join(textwrap.wrap(col, width=11))] + df[col].values.tolist()
            df_str = np.vstack([df_str, data])
        df_str = df_str.T.tolist()
        return df_str

    def generate_image(self, fig, width, heigh):
        imgdata = BytesIO()
        fig.savefig(imgdata, format='png')
        imgdata.seek(0)  # rewind the data
        return Image(imgdata, width=width * inch, height=heigh * inch)

    def generate_table(self, df, fontsize):
        df_str = self.dataframe2str(df=df)
        t = Table(df_str)
        mytable = TableStyle([('BACKGROUND', (0, 0), (-1, 0), HexColor('#d5dae6')),  # 设置第一行背景颜色
                              ('BACKGROUND', (0, 0), (0, -1), HexColor('#d5dae6')),  # 设置第一列背景颜色
                              ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                              ('FONTSIZE', (0, 0), (-1, -1), fontsize),
                              ('GRID', (0, 0), (-1, -1), 0.2, colors.grey),
                              ('TOPPADDING', (0, 0), (-1, -1), 1),
                              ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
                              ('LEFTPADDING', (0, 0), (-1, -1), 1),
                              ('RIGHTPADDING', (0, 0), (-1, -1), 1),
                              ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # 对齐
                              ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # 对齐
                              ])
        t.setStyle(mytable)

        return t

    def generate_pdf(self, contents, factor_name=''):
        version_number = 1.0
        output_folder = '/app/mount/project_data/'
        current_time = datetime.datetime.today()
        pdf_styles = getSampleStyleSheet()
        report_version = Paragraph('Version: %s' % (version_number), pdf_styles['Normal'])
        report_date = Paragraph(current_time.strftime('%Y%m%d'), pdf_styles['Normal'])
        contents.insert(0, report_version)
        contents.insert(0, report_date)
        if factor_name == '':
            report_name = 'FactorsBacktest_%s' % (current_time.strftime('%Y%m%d_%H%M%S'))
        else:
            report_name = 'SingleFactorBacktest_%s_%s' % (str(factor_name), current_time.strftime('%Y%m%d_%H%M%S'))

        pdf_name = os.path.join(output_folder, report_name + '.pdf')
        doc = SimpleDocTemplate(pdf_name,
                                pagesize=letter,
                                topMargin=0.8 * inch,
                                bottomMargin=0.8 * inch)
        doc.build(contents)

    def run_single_factor_backtest(self, library_name=None, date_list=None, security_id=None, factor_name=None,
                                   label=None, percent_list=None, rolling_window=20, stratified_list=None):
        """
        :param : library_name: str
        :param : date_list: list
        :param : security_id: str
        :param : factor_name: str
        :param : label: str
        :return :  plt画的图
        """
        # 校验参数

        if stratified_list is None:
            stratified_list = [4]
        if percent_list is None:
            percent_list = [0.1, 0.5]
        self.fb.factor_test.update(
            {'percent': percent_list, 'stratified': stratified_list, 'rolling_win': rolling_window})
        self.fb._set_check_list()

        # 加载需要回测的因子数据
        factor_label_list = self.fb.prepare_factor_value(library_name=library_name, mddate_list=date_list,
                                                         security_id=security_id, factor_list=[factor_name, label],
                                                         label=label)
        # 绘图(单因子分布 单因子与标签的分布关系)
        fig1 = self.fb.analyze_one(factor_label_list, factor=factor_name)
        factor_label_img = self.generate_image(fig1, 7.5, 2.5)
        all_factor_stats_df = self.fb.test_all_factor(factor_label_list, percent_list=percent_list,
                                                      rolling_window=rolling_window, stratified_list=stratified_list)

        summary_info_df = self.summary_table(all_factor_stats_df, factor_name=factor_name, security_id=security_id,
                                             label=label)
        summary_info_table = self.generate_table(summary_info_df, 8)

        # 绘图（单因子的无法计算收益的统计结果，分层测试累计收益，因子相关指标的统计信息）
        _, _, fig2 = self.fb._analyse_single_factor(all_factor_stats_df, factor=factor_name)
        factor_stat_img = self.generate_image(fig2, 7.5, 5)
        # 回测因子的统计结果
        all_pre_filter = self.fb._analyse_all_factor_stat(all_factor_stats_df)
        factor_stats_table = self.generate_table(all_pre_filter, 4)
        # 图表之间的空格
        interval_space = Spacer(240, 10)  # 添加空白，长度240，宽10
        # 图表之间增加标题说明
        pdf_styles = getSampleStyleSheet()
        heading_size = pdf_styles['Heading4']

        summary_info_par = Paragraph("Factor Summary Info", heading_size)
        factor_label_img_par = Paragraph('Factor Distribution and Factor_Label Scatter', heading_size)
        factor_stat_img_par = Paragraph('Analysis of factor statistics', heading_size)
        factor_stats_table_par = Paragraph('Factor evaluation indicators', heading_size)
        # list pdf中需要展示的图表
        contents = [summary_info_par, summary_info_table, factor_label_img_par, factor_label_img, interval_space,
                    factor_stat_img_par, factor_stat_img, PageBreak(),
                    factor_stats_table_par, factor_stats_table]
        self.generate_pdf(factor_name=factor_name, contents=contents)
        return all_pre_filter

    def run_factors_backtest(self, library_name=None, date_list=None, security_id=None, label=None, percent_list=None,
                             rolling_window=20, stratified_list=None, security_list=None,
                             metric_xx='pearson', metric_xy='rank_ic', threshold=0.5):
        if stratified_list is None:
            stratified_list = [4]
        if percent_list is None:
            percent_list = [0.1]
        self.fb.factor_test.update(
            {'percent': percent_list, 'stratified': stratified_list, 'rolling_win': rolling_window})
        self.fb._set_check_list()
        # factor_label_list = self.fb.prepare_factor_value1(security_list=security_list, mddate_list=date_list, label=label)
        factor_label_list = self.fb.prepare_factor_value(library_name=library_name, mddate_list=date_list,
                                                         security_id=security_id, label=label)
        factors_pre_data = pd.concat(factor_label_list, axis=0)
        factors_corr_info = factors_pre_data.drop(['Label', 'MDDate'], axis=1)
        # 计算因子的互相关性，并绘制热力图(筛选前)
        _, fig = self.fb.calc_factors_corr(factors_corr_info, metric=metric_xx, plot=True)
        factors_heat_img = self.generate_image(fig, heigh=7.5, width=7.5)

        all_factor_stats_df = self.fb.test_all_factor(factor_label_list, percent_list=percent_list,
                                                      rolling_window=rolling_window,
                                                      stratified_list=stratified_list)

        # 筛选标准
        filter_strategy = 'Corr:{0} - Threshold:{1}'.format(metric_xx,threshold)
        # 回测报告的基本信息
        summary_info_df = self.summary_table(all_factor_stats_df, security_id=security_id, label=label,
                                             back_type='multi', filter_strategy=filter_strategy)
        summary_info_table = self.generate_table(summary_info_df, fontsize=8)

        # 图表增加标题说明
        pdf_styles = getSampleStyleSheet()
        heading_size = pdf_styles['Heading4']

        # 因子的在回测区间的统计结果，制成表格
        all_pre_filter = self.fb._analyse_all_factor_stat(all_factor_stats_df)
        factor_stats_table = self.generate_table(all_pre_filter, fontsize=4)

        # 按因子间的互相关系数的阈值对因子进行筛选，筛去相关性高的因子。并对剩下来的因子并绘制热力图
        factors_corr_info_after_sel = self.fb.get_rc_stage2filter(factor_label_list=factor_label_list,
                                                                  all_pre_filter=all_pre_filter,
                                                                  columns=all_pre_filter.index.tolist(),
                                                                  metric_xy=metric_xy, metric_xx='pearson',
                                                                  threshold=threshold, method="rc")
        _, fig2 = self.fb.calc_factors_corr(factors_corr_info_after_sel, metric=metric_xx, plot=True)
        factors_heat_img_after_sel = self.generate_image(fig2, heigh=7, width=7)

        #各图表的标题
        summary_info_table_par = Paragraph('Report Basic Info',heading_size)
        factor_stats_table_par = Paragraph('Factors evaluation indicators', heading_size)
        factors_heat_img_par = Paragraph('Factors HeatMap', heading_size)
        factors_heat_img_after_sel_par = Paragraph(
            'Factors HeatMap After Selection {}-Threshold:{}'.format(metric_xy, threshold), heading_size)

        # 评价报告的开头

        contents = [summary_info_table_par, summary_info_table, factors_heat_img_par, factors_heat_img, PageBreak(), factors_heat_img_after_sel_par,
                    factors_heat_img_after_sel, PageBreak(),
                    factor_stats_table_par, factor_stats_table]

        self.generate_pdf(contents=contents)
        return all_pre_filter


if __name__ == '__main__':
    # 实例化
    factor_test = FactorBacktest(n_jobs=4)
    # 加载需要回测的因子数据
    factor_label_list = factor_test.prepare_factor_value('b20180808', ['20201102', '20201103'], '159968.SZ')
    # 因子的分布密度，因子与标签的分布散点图
    factor_test.analyze_one(factor_label_list, 'pxchange_interval_seconds60_tick_interval_seconds3')
    plt.show()
    # 画热力图
    factors_pre_data = pd.concat(factor_label_list, axis=0)
    # 去掉不需要的列
    factors_corr_info = factors_pre_data.drop(['Label', 'MDDate'], axis=1)
    factor_test.calc_factors_corr(factors_corr_info, metric='pearson', plot=True)
    # 计算相关的因子统计信息 ， 并画出 指定因子的 无法计算收益的天数统计图，累计收益图，相关指标的统计信息，P_value
    all_factor_stats_df = factor_test.test_all_factor(factor_label_list)
    factor_test._analyse_single_factor(all_factor_stats_df, 'px_to_preclose_premium_discount')
    # 按天聚合，并做均值，中位数，取绝对值等处理 获得 index: 因子 columns： 指标的DataFrame
    all_pre_filter = factor_test._analyse_all_factor_stat(all_factor_stats_df)
    # 重新设置factor_test中的筛选条件，针对按天聚合后的因子指标 按照指定的条件进行因子筛选
    update_dict = {'auto_corr_minute_threshold_list': [0.00, 0.0, 0.0], "long_pval_threshold": 0,
                   "short_pval_threshold": 0}
    factor_test.set_factor_test_option(update_dict)
    passed_list = factor_test.get_factor_passed(all_pre_filter)
