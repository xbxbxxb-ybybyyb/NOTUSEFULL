# coding : utf-8
from xfactor.test.test_data_loader import *
from dateutil.relativedelta import relativedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from sklearn.metrics import roc_auc_score
import datetime
import time
from typing import List
import numpy as np
import warnings

warnings.filterwarnings('ignore')


class FactorTestAlgorithm:
    def __init__(self, factor_name, factor_value, start_date='20160101', end_date='20191231', res_folder=r"./",
                 price_type='vwap', rho=4e-4, top_range=0.1, neutralize=True, turnover_mode=True, ret_weight=False,
                 is_day_factor=True, vwap_13_type=0, local=True):
        self.factor_name = factor_name
        factor_value = factor_value.loc[start_date:end_date, :]
        factor_value.index = [str(i) for i in factor_value.index]
        start_date, end_date = int(start_date), int(end_date)
        self.factor_value = factor_value
        self.start_date = start_date
        self.end_date = end_date
        self.price_type = price_type
        self.rho = rho
        self.neutralize = neutralize
        self.turnover_mode = turnover_mode
        self.top_range = top_range
        self.ret_weight = ret_weight
        self.is_day_factor = is_day_factor
        self.vwap_13_type = vwap_13_type
        self.real_price_type = self.price_type
        self.label_df = None
        self.label_NL_df = None
        if self.is_day_factor:
            self.real_price_type = self.price_type
        else:
            fix_time = self.factor_name[3:7]
            if fix_time[-2:] == '00':
                vwap_period = fix_time + '_' + fix_time[:2] + '30'
            else:
                vwap_period = fix_time + '_' + str(int(fix_time[:2]) + 1) + '00'

            if (fix_time == '1300') & (self.vwap_13_type == 1):
                vwap_period = '1300_1500'
            self.real_price_type = self.price_type + "_" + vwap_period
        self.local = local
        if self.local:
            self.test_end_date = end_date
        else:
            # 样本内外时间分割点
            self.test_end_date = dt.datetime.strptime(str(end_date), '%Y%m%d') - relativedelta(months=6)
            self.test_end_date = int(self.test_end_date.strftime("%Y%m%d"))
            self.test_end_date = Dtk.get_n_days_off(self.test_end_date, -2)[-1]
        self.orth_factors_path = orth_factors_path
        self.factors_speIC_path = factors_spe_IC_path
        self.label_path_for_NonLinearIC = label_path_for_NonLinearIC
        self.orth_factors_used = ['OB_ret_vol20_day', 'OB_liquidity5_day', 'OB_reverse1_day', 'OB_reverse5_day']
        self.orth_factors_dict = dict(zip(self.orth_factors_used, [None] * len(self.orth_factors_used)))
        self.stock_list = Dtk.get_complete_stock_list()
        self.load_daily_label(self.start_date, self.end_date)
        self.load_label_for_NonLinearIC()
        self.data_buffer = {}

        # 待检测因子ic值序列
        self.ic = None

        # 保存待检测因子中性化后的因子值
        self.neutralized_factor_value = None

        self.report_address = os.path.join(res_folder, self.factor_name)

        self.report_timestamp = dt.datetime.now()
        self.exempt_date = [20160107, 20160225]

    def load_daily_label(self, start_date, end_date):
        valid_start_date = Dtk.get_n_days_off(start_date, -2)[0]
        valid_end_date = Dtk.get_n_days_off(end_date, 3)[-1]
        buy_price_df = Dtk.get_panel_daily_pv_df(self.stock_list, valid_start_date,
                                                 valid_end_date, pv_type='buy_twap',
                                                 adj_type='FORWARD')
        sell_price_df = Dtk.get_panel_daily_pv_df(self.stock_list, valid_start_date,
                                                  valid_end_date, pv_type='twap',
                                                  adj_type='FORWARD')
        return_rate_df = sell_price_df.shift(-1) / buy_price_df - 1
        return_rate_df = return_rate_df.shift(-1)
        return_rate_df = return_rate_df.loc[start_date:end_date]
        self.label_df = return_rate_df

    def load_label_for_NonLinearIC(self):
        label_NL_df = pd.read_pickle(self.label_path_for_NonLinearIC + 'neu_vwap_re_5d.pkl')
        label_NL_df = label_NL_df.loc[self.start_date:self.end_date, self.stock_list]
        self.label_NL_df = label_NL_df

    def load_orth_factors(self):
        for singlestylefactor in self.orth_factors_used:
            factor_value_singlestyle = pd.read_hdf(self.orth_factors_path + singlestylefactor + '.h5', 'factor')
            factor_value_singlestyle_dt = Dtk.convert_df_index_type(factor_value_singlestyle, 'timestamp', 'date_int')
            factor_value_singlestyle_dt = factor_value_singlestyle_dt.reindex(columns=self.stock_list)
            self.orth_factors_dict.update({singlestylefactor: factor_value_singlestyle_dt})

    def get_neu_factor_spe_IC_series(self, neu_factors):
        factors_spe_IC = pd.read_pickle(self.factors_speIC_path)
        factors_spe_IC = factors_spe_IC.loc[self.start_date:self.test_end_date, neu_factors]
        nan_check = factors_spe_IC.count(axis=1)
        if (nan_check == 0).sum() > 0:
            raise Exception('error in test_data:IC')
        return factors_spe_IC

    def factors_regged_by_orth_factors(self):

        # 加载因子数据
        target_factor_value_dt = self.neutralized_factor_value
        trading_dates = target_factor_value_dt.index.tolist()
        # target_factor_value_dt = target_factor_value_dt.rank(pct=True,axis=1)
        # 进行剔除取残差
        residual_dict = {}
        b_dict = {}
        detailed_projections = dict(zip(self.orth_factors_used, [{} for i in self.orth_factors_used]))
        for single_date in trading_dates:
            style_factor_values_singledate_dict = {}
            try:
                for singlestylefactor in self.orth_factors_dict:
                    singlestylefactorvalue = self.orth_factors_dict[singlestylefactor]
                    style_factor_values_singledate_dict.update(
                        {singlestylefactor: singlestylefactorvalue.loc[int(single_date)]})
                style_factor_values_singledate_df = pd.DataFrame(style_factor_values_singledate_dict)
            except:
                continue
            target_factor_value_dt_singledate = target_factor_value_dt.loc[single_date]
            x0 = style_factor_values_singledate_df.values
            y0 = target_factor_value_dt_singledate.values
            y0_isnan = np.isnan(y0)
            x0_isnan = np.isnan(np.max(x0, axis=1))
            y0_isvalid = 1 - y0_isnan
            x0_isvalid = 1 - x0_isnan
            valid_rows = x0_isvalid * y0_isvalid
            valid_stock_list = [self.stock_list[i] for i in range(self.stock_list.__len__()) if valid_rows[i] == 1]
            x0_valid = x0[valid_rows == 1]
            y0_valid = y0[valid_rows == 1]
            x0_valid = x0_valid - np.mean(x0_valid, axis=0)
            if x0_valid.__len__() > 0:
                b = np.linalg.inv(x0_valid.T.dot(x0_valid)).dot(x0_valid.T).dot(y0_valid)
                projection = x0_valid.dot(b)

                b_tile = np.repeat(b.reshape([1, b.shape[0]]), x0_valid.shape[0], 0)
                detailed_projection = x0_valid * b_tile
                detailed_projection_df = pd.DataFrame(detailed_projection, index=valid_stock_list,
                                                      columns=style_factor_values_singledate_df.columns)
                residual = y0_valid - projection  # 求残差
                residual_series = pd.Series(residual, index=valid_stock_list)
                b_series = pd.Series(b, index=style_factor_values_singledate_df.columns)
                b_dict.update({single_date: b_series})
                residual_dict.update({single_date: residual_series})
                for singlestylefactor in detailed_projections:
                    detailed_projections[singlestylefactor].update(
                        {single_date: detailed_projection_df[singlestylefactor]})

        residual_df = pd.DataFrame(residual_dict).T
        b_df = pd.DataFrame(b_dict).T
        reverse_RS = residual_df.var(axis=1) / target_factor_value_dt.var(axis=1)
        reverse_RS_mean = reverse_RS.mean()

        data_for_factor_test = {
            'residual': residual_df,
            'b': b_df,
            'reverse_RS': reverse_RS_mean
        }
        return data_for_factor_test

    def get_IC_series(self, factor_df, label_df):
        IC_series = factor_df.corrwith(label_df, axis=1)
        return IC_series

    def get_insample_corr(self):
        ic_is = self.ic.loc[self.start_date:self.test_end_date]
        ic_corr = self.neu_factors_spe_IC_all.corrwith(ic_is, axis=0)
        return ic_corr

    def prepare_data_buffer(self):
        industry_df_sw = pd.read_pickle(
            '/data/group/800002/alpha_factor/test/depend_data/day/basic_data/industry_code_all.pkl')
        industry_df_sw.index = [int(datetime.datetime.strftime(i, '%Y%m%d')) for i in industry_df_sw.index]
        industry_df_sw = industry_df_sw.loc[self.start_date:self.end_date]
        industry_df_sw = Dtk.convert_df_index_type(industry_df_sw, 'date_int', 'timestamp')
        industry_df_sw = industry_df_sw.reindex(columns=self.stock_list)
        mkt_cap_ard_df = pd.read_pickle(
            '/data/group/800002/alpha_factor/test/depend_data/day/basic_data/mkt_cap_ard.pkl')
        mkt_cap_ard_df.index = [int(datetime.datetime.strftime(i, '%Y%m%d')) for i in mkt_cap_ard_df.index]
        mkt_cap_ard_df = mkt_cap_ard_df.loc[self.start_date:self.end_date]
        mkt_cap_ard_df = Dtk.convert_df_index_type(mkt_cap_ard_df, 'date_int', 'timestamp')
        mkt_cap_ard_df = np.log(mkt_cap_ard_df)  # 对市值取对数
        mkt_cap_ard_df = mkt_cap_ard_df.reindex(columns=self.stock_list)
        is_valid_df = pd.read_pickle('/data/group/800002/alpha_factor/test/depend_data/day/basic_data/is_valid.pkl')
        is_valid_df.index = [int(datetime.datetime.strftime(i, '%Y%m%d')) for i in is_valid_df.index]
        is_valid_df = is_valid_df.loc[self.start_date:self.end_date]
        is_valid_df = Dtk.convert_df_index_type(is_valid_df, 'date_int', 'timestamp')
        is_valid_df = is_valid_df.reindex(columns=self.stock_list).fillna(0)
        universe_df = Dtk.get_panel_daily_info(self.stock_list, self.start_date, self.end_date, 'alpha_universe')
        valid_end_date = Dtk.get_n_days_off(self.end_date, 2)[-1]
        buyfillrate_df = Dtk.get_panel_daily_pv_df(self.stock_list, self.start_date, valid_end_date,
                                                   pv_type='buy_twap_fill_rate')
        buyfillrate_df = buyfillrate_df.shift(-1).loc[self.start_date:self.end_date]
        self.data_buffer.update({
            'industry_df_sw': industry_df_sw,
            'mkt_cap_ard_df': mkt_cap_ard_df,
            'is_valid_df': is_valid_df,
            'universe_df': universe_df,
            'buyfillrate_df': buyfillrate_df
        })

    def load_factor(self, stock_list: List[str] = ..., start_date: datetime = None,
                    end_date: datetime = None) -> pd.DataFrame:
        result = self.factor_value
        result = result.loc[start_date.strftime('%Y%m%d'): end_date.strftime('%Y%m%d')]
        result.index = [int(i) for i in result.index]
        result2 = result.reindex(columns=stock_list)
        result2 = result2.astype('float64')
        return result2

    @staticmethod
    def fillna_with_industry_mean(raw_factor_df, ind_df):
        # 用当天的行业中位数填充因子中遇到的nan值
        # 算法原理是：
        #     计算31个行业的因子值的中位数，构造31个矩阵，每个矩阵都先用行业中位数填充所有的nan值，再将非本行业的股票的值
        #     设为0；再将上述31个矩阵直接叠加；最后再 * ind_df / ind_df，使得没有行业的股票的值为nan.
        # univ_df = Dtk.convert_df_index_type(univ_df, 'date_int', 'timestamp')
        # ind_df = Dtk.convert_df_index_type(ind_df, 'date_int', 'timestamp')
        factor_df_na_filled = raw_factor_df.copy()
        factor_df_na_filled[:] = 0
        for i in np.unique(ind_df.stack().dropna().values).tolist():
            if i == 6123:
                a = 1
            i_industry_df = pd.DataFrame(ind_df.values == i, index=ind_df.index,
                                         columns=ind_df.columns)  # a matrix full of True/False
            # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
            factor_ind_i = raw_factor_df * i_industry_df / i_industry_df
            # 计算本行业的因子值的中位数
            factor_ind_i_median = factor_ind_i.mean(axis=1)
            # 将形状为(n, )的series的形状转为(n, 1)
            factor_ind_i_median_reshaped = np.reshape(factor_ind_i_median.values, (factor_ind_i_median.__len__(), 1))
            # 把本行业的中位数的series拓展为矩阵
            factor_ind_i_median_matrix = pd.DataFrame(
                np.tile(factor_ind_i_median_reshaped, [1, ind_df.shape[1]]),
                index=ind_df.index, columns=ind_df.columns)
            # 用行业中位数填充所有的NaN
            factor_ind_i[np.isnan] = factor_ind_i_median_matrix
            # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
            factor_ind_i = factor_ind_i * i_industry_df / i_industry_df
            # 如是本行业的、则值为因子值，如不是本行业的、值为0
            factor_ind_i[pd.DataFrame(i_industry_df.values == False, index=i_industry_df.index,
                                      columns=i_industry_df.columns)] = 0
            factor_df_na_filled = factor_df_na_filled + factor_ind_i
        # 再以industry_df过滤，若没有行业的股票值为nan
        factor_df_na_filled[pd.DataFrame(np.isnan(ind_df.values), index=ind_df.index, columns=ind_df.columns)] = np.nan
        return factor_df_na_filled

    @staticmethod
    def outlier_filter(value_df, scale=5):
        """
        本函数以MAD的方式去除极端值
        """
        # 在20160104和20160107这两天，全市场熔断，那么先删除全市场都是nan的数据
        value_df_raw = value_df.copy()
        diversion_series = value_df.apply(lambda x: len(np.unique(x.dropna())), axis=1) / value_df.count(axis=1)

        factor_max = value_df.max(axis=1)
        # factor_max = factor_max.dropna()
        value_df = value_df.reindex(factor_max.index)
        factor_median = value_df.median(axis=1)
        factor_deviation_from_median = value_df.sub(factor_median, axis=0)
        factor_deviation_from_median[
            pd.DataFrame(factor_deviation_from_median.values == 0, index=factor_deviation_from_median.index,
                         columns=factor_deviation_from_median.columns)] = np.nan
        factor_mad = factor_deviation_from_median.abs().median(axis=1)

        lower_limit = factor_median - scale * factor_mad
        upper_limit = factor_median + scale * factor_mad
        lower_limit = lower_limit.fillna(method='ffill')
        upper_limit = upper_limit.fillna(method='ffill')

        lower_limit_plus1 = factor_median - (scale + 1) * factor_mad
        upper_limit_plus1 = factor_median + (scale + 1) * factor_mad
        lower_limit_plus1 = lower_limit_plus1.fillna(method='ffill')
        upper_limit_plus1 = upper_limit_plus1.fillna(method='ffill')

        lower_limit_plus2 = factor_median - (scale + 2) * factor_mad
        upper_limit_plus2 = factor_median + (scale + 2) * factor_mad
        lower_limit_plus2 = lower_limit_plus2.fillna(method='ffill')
        upper_limit_plus2 = upper_limit_plus2.fillna(method='ffill')

        extreme_count = (value_df.sub(upper_limit, axis=0) > 0) | (value_df.sub(lower_limit, axis=0) < 0)
        extreme_count = extreme_count.sum(axis=1)
        nan_count = value_df.count(axis=1)
        extreme_rate = extreme_count / nan_count

        value_df[((diversion_series > 0.1) & (diversion_series <= 1)) == False] = value_df_raw[
            ((diversion_series > 0.1) & (diversion_series <= 1)) == False]
        value_df[(((diversion_series > 0.1) & (diversion_series <= 1)) == True) & (extreme_rate <= 0.1)] = \
            value_df.clip_lower(lower_limit, axis='index').clip_upper(upper_limit, axis='index')[
                (((diversion_series > 0.1) & (diversion_series <= 1)) == True) & (extreme_rate <= 0.1)]
        value_df[(((diversion_series > 0.1) & (diversion_series <= 1)) == True) & (extreme_rate > 0.1) & (
                extreme_rate <= 0.2)] = \
            value_df.clip_lower(lower_limit_plus1, axis='index').clip_upper(upper_limit_plus1, axis='index')[
                (((diversion_series > 0.1) & (diversion_series <= 1)) == True) & (extreme_rate > 0.1) & (
                        extreme_rate <= 0.2)]
        value_df[(((diversion_series > 0.1) & (diversion_series <= 1)) == True) & (extreme_rate > 0.2)] = \
            value_df.clip_lower(lower_limit_plus2, axis='index').clip_upper(upper_limit_plus2, axis='index')[
                (((diversion_series > 0.1) & (diversion_series <= 1)) == True) & (extreme_rate > 0.2)]
        return value_df

    @staticmethod
    def z_score_standardizer(value_df):
        factor_mean = value_df.mean(axis=1)
        factor_std = value_df.std(axis=1)
        value_df = value_df.sub(factor_mean, axis=0)
        value_df = value_df.div(factor_std, axis=0)
        return value_df

    @staticmethod
    def factor_neutralizer(factor_df, mkt_cap_ard_df, industry_df):
        # 初版为了方便，只写了size和industry中性；后续应该开发一个能支持更多因子正交化的函数
        residual_list = []
        residual_date_list = []
        for j, i_date in enumerate(list(factor_df.index)):
            if j % 50 == 0:
                print("factor neutralizing, {} / {} days".format(j, list(factor_df.index).__len__()))
            y = factor_df.loc[i_date]
            x = pd.get_dummies(industry_df.loc[i_date])  # 将1*N的行业信息变为N*31的虚拟变量矩阵（dataframe）
            x = x.join(mkt_cap_ard_df.loc[i_date], on=None, how='left')  # 加入市值信息
            y = y.dropna()  # 去na、使矩阵non-singular，后续才能做回归
            x = x.dropna()
            index_intersect = list(set(y.index).intersection(x.index))  # 要取x和y都有值的
            y = y.reindex(index_intersect)
            x = x.reindex(index_intersect)
            ind_checker = x.sum()  # 再次检查是否有行业缺失，如有的话删除这个dummy variable，以保证矩阵non-singular
            for i in range(ind_checker.__len__()):
                if ind_checker.iloc[i] == 0:
                    x = x.drop(ind_checker.index[i], axis=1)
            if index_intersect.__len__() > 0:
                b = np.linalg.inv(x.T.dot(x)).dot(x.T).dot(y)  # OLS 求回归系数，这里要用到求逆，有点慢
                residual = y - x.dot(b)  # 求残差
                residual_list.append(residual)  # 将残差保存下来
                residual_date_list.append(i_date)

        # 将残差list一次性转变为DataFrame
        neutralized_factor_df = pd.DataFrame(residual_list, index=residual_date_list)
        neutralized_factor_df = neutralized_factor_df.reindex(factor_df.index)
        neutralized_factor_df = neutralized_factor_df.sort_index(axis=1)
        return neutralized_factor_df

    def get_neu_factor_value(self):
        start_date_datetime = Dtk.convert_date_or_time_int_to_datetime(self.start_date)
        end_date_datetime = Dtk.convert_date_or_time_int_to_datetime(self.end_date)
        industry_df_sw = self.data_buffer['industry_df_sw']
        mkt_cap_ard_df = self.data_buffer['mkt_cap_ard_df']
        is_valid_df = self.data_buffer['is_valid_df']
        temp_factor = self.load_factor(self.stock_list, start_date_datetime, end_date_datetime)
        temp_factor = Dtk.convert_df_index_type(temp_factor, 'date_int', 'timestamp')
        temp_factor_stack = temp_factor.stack(dropna=False)
        industry_df_sw_stack = industry_df_sw.stack(dropna=False)
        mkt_cap_ard_df_stack = mkt_cap_ard_df.stack(dropna=False)
        is_valid_stack = is_valid_df.stack(dropna=False)

        temp_factor_stack_filtered = temp_factor_stack[is_valid_stack == 1]
        industry_df_sw_stack_filtered = industry_df_sw_stack[is_valid_stack == 1]
        mkt_cap_ard_df_stack_filtered = mkt_cap_ard_df_stack[is_valid_stack == 1]

        temp_factor = temp_factor_stack_filtered.unstack()
        industry_df_sw = industry_df_sw_stack_filtered.unstack()
        mkt_cap_ard_df = mkt_cap_ard_df_stack_filtered.unstack()

        # 进行行业均值填充
        temp_factor = self.fillna_with_industry_mean(temp_factor, industry_df_sw)
        # 进行异常值处理
        temp_factor = self.outlier_filter(temp_factor)  # 因子去除极值
        # 进行标准化
        temp_factor = self.z_score_standardizer(temp_factor)
        # 行业市值中性化
        mkt_cap_ard_df = self.outlier_filter(mkt_cap_ard_df)
        mkt_cap_ard_df = self.z_score_standardizer(mkt_cap_ard_df)
        temp_factor = self.factor_neutralizer(temp_factor, mkt_cap_ard_df, industry_df_sw)
        # 标准化
        temp_factor = self.outlier_filter(temp_factor)  # 因子去除极值
        temp_factor = self.z_score_standardizer(temp_factor)  # 因子标准化
        temp_factor = temp_factor.reindex(columns=self.stock_list).fillna(0)
        temp_factor_dt = Dtk.convert_df_index_type(temp_factor, 'timestamp', 'date_int')
        return temp_factor_dt

    def get_em(self):
        df_int = self.neutralized_factor_value.copy()
        universe_df = self.data_buffer['universe_df'].copy()
        label_df = self.label_df.copy()
        label_df = label_df * universe_df / universe_df
        buyfillrate_df = self.data_buffer['buyfillrate_df'].copy()
        buyfillrate_df2 = self.data_buffer['buyfillrate_df'].copy()
        df_int = df_int * universe_df / universe_df
        df_infer_rank = df_int.rank(axis=1, ascending=True, pct=True)
        df_topgrp = pd.DataFrame(df_infer_rank.values >= 0.9, index=df_infer_rank.index, columns=df_infer_rank.columns)
        df_topgrp_nan = df_topgrp[df_topgrp == 1]
        df_topgrp_nan[(label_df.isnull() == True)] = np.nan
        df_topgrp_nan_count = df_topgrp_nan.count(axis=1)
        topmeanweight = pd.Series(1 / df_topgrp_nan_count.values, index=df_topgrp_nan_count.index)
        topmeanweight_tile = pd.DataFrame(np.tile(topmeanweight, [df_topgrp_nan.shape[1], 1]).T,
                                          index=df_topgrp_nan.index, columns=df_topgrp_nan.columns)
        topmeanweight_tile = topmeanweight_tile[df_topgrp_nan.isnull() == False]
        topmeanweight_tile = topmeanweight_tile.fillna(0)
        stock_holdlist_weight = topmeanweight_tile
        buyfillrate_df = buyfillrate_df[df_topgrp_nan.isnull() == False]
        adj_stock_holdlist_weight = stock_holdlist_weight * buyfillrate_df
        adj_stock_holdlist_weight_sum = adj_stock_holdlist_weight.sum(axis=1)
        adj_stock_holdlist_weight_sum_tile = pd.DataFrame(
            np.tile(adj_stock_holdlist_weight_sum, [adj_stock_holdlist_weight.shape[1], 1]).T,
            index=adj_stock_holdlist_weight.index, columns=adj_stock_holdlist_weight.columns)
        adj_stock_holdlist_weight = pd.DataFrame(
            adj_stock_holdlist_weight.values / adj_stock_holdlist_weight_sum_tile.values,
            index=adj_stock_holdlist_weight.index, columns=adj_stock_holdlist_weight.columns)
        ov = (label_df * adj_stock_holdlist_weight).sum(axis=1)
        label_count = label_df.count(axis=1)
        mktmeanweight = pd.Series(1 / label_count.values, index=label_count.index)
        mktmeanweight_tile = pd.DataFrame(np.tile(mktmeanweight, [label_df.shape[1], 1]).T,
                                          index=label_df.index, columns=label_df.columns)
        mktmeanweight_tile = mktmeanweight_tile[
            pd.DataFrame(label_df.isnull().values == False, index=label_df.index, columns=label_df.columns)]
        index_weight_df = mktmeanweight_tile
        buyfillrate_df2 = buyfillrate_df2[
            pd.DataFrame(label_df.isnull().values == False, index=label_df.index,
                         columns=label_df.columns)]
        adj_index_weight_df = pd.DataFrame(index_weight_df.values * buyfillrate_df2.values,
                                           index=index_weight_df.index, columns=index_weight_df.columns)
        adj_index_weight_df_sum = adj_index_weight_df.sum(axis=1)
        adj_index_weight_df_sum_tile = pd.DataFrame(
            np.tile(adj_index_weight_df_sum, [adj_index_weight_df.shape[1], 1]).T,
            index=adj_index_weight_df.index, columns=adj_index_weight_df.columns)
        adj_index_weight_df = pd.DataFrame(
            adj_index_weight_df.values / adj_index_weight_df_sum_tile.values,
            index=adj_index_weight_df.index, columns=adj_index_weight_df.columns)
        markt_mean_df = (label_df * adj_index_weight_df).sum(axis=1)
        em = ov - markt_mean_df
        exempt_dates_in_em = [i for i in self.exempt_date if i in em.index]
        em.loc[exempt_dates_in_em] = 0
        return em

    def factor_ic_adj(self):
        ic = self.get_IC_series(self.neutralized_factor_value, self.label_df)
        icmean_is = ic.loc[self.start_date:self.end_date].mean()
        if icmean_is < 0:
            self.neutralized_factor_value = -self.neutralized_factor_value

    def linear_test(self, neu_factors):
        # 将中性化值对正交基进行拆分（加入对正交基的拆分）
        self.load_orth_factors()
        data_for_factor_test = self.factors_regged_by_orth_factors()

        # 计算待检测因子的特质IC序列
        factors_spe = data_for_factor_test['residual']
        self.ic = self.get_IC_series(factors_spe, self.label_df)
        IC_is_mean = self.ic.loc[self.start_date:self.test_end_date].mean()
        if IC_is_mean < 0:
            self.ic = -self.ic
        nan_ratio = self.ic.count() / self.ic.shape[0]
        # nan_ratio = nancheck/self.ic.shape[0]
        if nan_ratio < 0.1:
            raise Exception('error in factor ic')
        in_sample_icmean = self.ic.loc[self.start_date:self.test_end_date].mean()

        # 读取库内因子特质IC序列
        self.neu_factors_spe_IC_all = self.get_neu_factor_spe_IC_series(neu_factors)

        # 样本内测试条件1：特质的样本内IC均值大于0.004
        in_flag1 = in_sample_icmean > 0.004

        # 样本内测试条件2：特质的样本内IC相关性最大值小于0.7
        insample_iccorr = self.get_insample_corr()
        in_flag2 = insample_iccorr.max() < 0.7

        # 样本内测试条件3：特质的样本内IC相关性均值小于0.085
        in_flag3 = insample_iccorr.mean() < 0.085

        # 样本内测试条件4：单因子的特质部分的波动占比大于0.8，或在基因子上暴露的时序波动均值<0.06
        beta_df = data_for_factor_test['b']
        reverse_RS = data_for_factor_test['reverse_RS']
        if (reverse_RS > 0.8) or (beta_df.std().mean() < 0.06):
            in_flag4 = True
        else:
            in_flag4 = False

        flag = in_flag1 & in_flag2 & in_flag3 & in_flag4
        details = {
            'in_flag1': in_flag1,
            'in_flag2': in_flag2,
            'in_flag3': in_flag3,
            'in_flag4_1': reverse_RS > 0.8,
            'in_flag4_2': beta_df.std().mean() < 0.06
        }
        details_num = {
            'in_flag1': in_sample_icmean,
            'in_flag2': insample_iccorr.max(),
            'in_flag3': insample_iccorr.mean(),
            'in_flag4_1': reverse_RS,
            'in_flag4_2': beta_df.std().mean(),
        }
        details_name = {
            'in_flag1': 'SpeICMean',
            'in_flag2': 'SpeICCorrMax',
            'in_flag3': 'SpeICCorrMean',
            'in_flag4_1': 'SpeExp',
            'in_flag4_2': 'BetaStd',
        }

        flag_stat = {
            'flag': flag,
            'details': details,
            'details_num': details_num,
            'details_name': details_name
        }
        return flag_stat

    def calc_nonlinearic(self):
        nfv = self.neutralized_factor_value.copy()
        nfv[pd.DataFrame(nfv.values < 0, index=nfv.index, columns=nfv.columns)] = np.nan
        nl_ic_series = nfv.corrwith(self.label_NL_df, axis=1)
        return nl_ic_series

    def calc_auc(self):
        label_df = self.label_df.copy()
        nfv = self.neutralized_factor_value.copy()
        label_df_demean = label_df.sub(label_df.mean(axis=1), axis=0)
        label_df_class = label_df_demean.copy()
        label_df_class[
            pd.DataFrame(label_df_class.values > 0, index=label_df_class.index, columns=label_df_class.columns)] = 1
        label_df_class[
            pd.DataFrame(label_df_class.values <= 0, index=label_df_class.index, columns=label_df_class.columns)] = 0

        auc_score = {}
        for date in nfv.index.tolist():
            y_true = label_df_class.loc[date]
            y_true[np.isinf(y_true)] = np.nan
            y_true.fillna(0, inplace=True)
            y_pred = nfv.loc[date]
            y_pred[np.isinf(y_pred)] = np.nan
            y_pred.fillna(0, inplace=True)
            auc_sd = roc_auc_score(y_true, y_pred)
            auc_score.update({date: auc_sd})
        auc_score_series = pd.Series(auc_score)
        return auc_score_series

    def nonlinear_test(self):
        nl_ic_series = self.calc_nonlinearic()
        auc_score_series = self.calc_auc()
        in_sample_aucmean = auc_score_series.loc[self.start_date:self.test_end_date].mean()
        in_sample_nlicstd = nl_ic_series.loc[self.start_date:self.test_end_date].std()

        # 样本内测试条件1：样本内AUC均值大于0.51
        in_flag1 = in_sample_aucmean > 0.51

        # 样本内测试条件2：非线性IC波动率大于0.035
        in_flag2 = in_sample_nlicstd > 0.035

        # inflag = in_flag1|in_flag2

        flag1 = in_flag1
        flag2 = in_flag2
        flag = flag1 | flag2

        details = {
            'in_flag1': in_flag1,
            'in_flag2': in_flag2,
        }
        details_num = {
            'in_flag1': in_sample_aucmean,
            'in_flag2': in_sample_nlicstd,
        }
        details_name = {
            'in_flag1': 'AUCMean',
            'in_flag2': 'RELUICStd',

        }
        flag_stat = {
            'flag': flag,
            'flag1': flag1,
            'flag2': flag2,
            'details': details,
            'details_num': details_num,
            'details_name': details_name
        }
        return flag_stat

    def _dic2list_ltr(self, for_rp_stat):
        result = []
        ltr_dct = for_rp_stat['part_linear_test_res_dct']
        ltr_details = ltr_dct['details']
        ltr_detailsnum = ltr_dct['details_num']
        ltr_detailsname = ltr_dct['details_name']
        keys = list(ltr_details.keys())
        result.append([' ', 'deltailed results', 'deltailed number'])
        for item in keys:
            result.append(
                [ltr_detailsname[item],
                 ltr_details[item],
                 ltr_detailsnum[item]]
            )
        result.append(['ExceedMeanRet', for_rp_stat['em_res_dct']['flag'], for_rp_stat['em_res_dct']['num']])
        return result

    def _dic2list_nlr(self, for_rp_stat):
        result = []
        pnlr_dct = for_rp_stat['part_nonlinear_test_res_dct']
        pltr_dct = for_rp_stat['part_linear_test_res_dct']
        pnlr_details = pnlr_dct['details']
        pnlr_detailsnum = pnlr_dct['details_num']
        pnlr_detailsname = pnlr_dct['details_name']
        keys = list(pnlr_details.keys())
        result.append([' ', 'deltailed results', 'deltailed number'])
        for item in keys:
            result.append(

                [

                    pnlr_detailsname[item],
                    pnlr_details[item],
                    pnlr_detailsnum[item]

                ]
            )
        result.append([pltr_dct['details_name']['in_flag2'], pltr_dct['details']['in_flag2'],
                       pltr_dct['details_num']['in_flag2']])
        result.append(['ExceedMeanRet', for_rp_stat['em_res_dct']['flag'], for_rp_stat['em_res_dct']['num']])
        return result

    @staticmethod
    def _table_model(data):
        inch = 72.0
        width = 5.2
        col_widths = (width / len(data[0])) * inch
        dis_list = []
        for x in data:
            dis_list.append(x)
        component_table = Table(dis_list, colWidths=col_widths)
        return component_table

    def generate_report(self, for_rp_stat):
        abs_address = self.report_address
        if not os.path.exists(abs_address):
            os.makedirs(abs_address)
        doc = SimpleDocTemplate(abs_address + '/' + self.factor_name + '_' + str(
            self.report_timestamp.strftime("%Y%m%d_%H%M%S")) + '.pdf', rightMargin=40, leftMargin=20, topMargin=50,
                                bottomMargin=20)
        story = []
        style_type = getSampleStyleSheet()
        style_type.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        story.append(Paragraph(self.factor_name + ' test', style_type['Title']))
        story.append(Spacer(1, 24))
        text_data = '<font size=9.5>%s</font>' % time.ctime()
        text_data = 'Report date : ' + text_data
        story.append(Paragraph(text_data, style_type['Normal']))
        story.append(Spacer(1, 48))
        text_data = 'Factor Information'
        story.append(Paragraph(text_data, style_type['Justify']))
        story.append(Spacer(1, 12))
        dic = {
            'Factor Name': self.factor_name,
            'Test Period': str(self.start_date) + ' --> ' + str(self.test_end_date),
            'Date Count': Dtk.get_trading_day(self.start_date, self.end_date).__len__(),
            'Final Result': for_rp_stat['final_flag'],
            'Linear Test Result': for_rp_stat['ltr_flag'],
            'Nonlinear Test Result': for_rp_stat['ntr_flag'],
        }

        for item in dic.keys():
            story.append(Paragraph(item.rjust(20) + ' : ' + str(dic[item]), style_type['Normal']))
            story.append(Spacer(1, 6))
        story.append(Spacer(1, 24))
        story.append(Paragraph('Linear Test Details:', style_type['Justify']))
        story.append(Spacer(1, 6))
        data_ltr = self._dic2list_ltr(for_rp_stat)
        tb_ltr = self._table_model(data_ltr)
        story.append(tb_ltr)

        story.append(Spacer(1, 24))
        story.append(Paragraph('Nonlinear Test Details:', style_type['Justify']))
        data_nlr = self._dic2list_nlr(for_rp_stat)
        tb_nlr = self._table_model(data_nlr)
        story.append(tb_nlr)
        story.append(Spacer(1, 24))
        doc.build(story)
        pass

    def launch_test(self):
        # 计算待检测因子中性化后的因子值
        self.prepare_data_buffer()
        self.neutralized_factor_value = self.get_neu_factor_value()
        self.factor_ic_adj()
        factor_em = self.get_em()

        df = pd.read_pickle(day_inlib_factors_path)
        neu_factors = df.query("isInLib==1").index.tolist()

        part_linear_test_res_dct = self.linear_test(neu_factors)
        part_nonlinear_test_res_dct = self.nonlinear_test()

        pltr_flag = part_linear_test_res_dct['flag']
        pntr_flag = part_nonlinear_test_res_dct['flag']
        corrmax_res = part_linear_test_res_dct['details']['in_flag2']
        corrmean_res = part_linear_test_res_dct['details']['in_flag3']
        em_res = factor_em.loc[self.start_date:self.test_end_date].mean() > 0
        ntr_flag = pntr_flag & corrmax_res & corrmean_res & em_res
        ltr_flag = pltr_flag & em_res

        final_flag = ltr_flag | ntr_flag
        em_res_dct = {
            'flag': em_res,
            'num': factor_em.mean()
        }

        for_rp_stat = {
            'final_flag': final_flag,
            'ltr_flag': ltr_flag,
            'ntr_flag': ntr_flag,
            'part_linear_test_res_dct': part_linear_test_res_dct,
            'part_nonlinear_test_res_dct': part_nonlinear_test_res_dct,
            'em_res_dct': em_res_dct
        }
        self.generate_report(for_rp_stat)
        return final_flag, None


# 测试用
if __name__ == "__main__":
    import xfactor.test.symbol_team.DataAPI.DataToolkit as Dtk
    import pandas as pd
    import numpy as np

    factor_name = 'ADSC'

    complete_stock_list = Dtk.get_complete_stock_list()
    factor_value = pd.read_pickle('/data/group/800002/alpha_factor/lib/x_factor_lib/ADSC.pkl')
    factor_value = factor_value.loc['20160101':'20200331', complete_stock_list]
    factor_value.index = [int(i) for i in factor_value.index]
    factor_test_class = FactorTestAlgorithm(factor_name, factor_value, 20160101, 20191231, "/data/user/999999/")

    test_result = factor_test_class.launch_test()
    print("factor_test_algorithm: ", factor_name, " finished")
