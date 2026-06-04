# -*- coding: utf-8 -*-
"""
Created on 2018/8/9 16:00
@author: 006547
revised by 006566 on 2019/3/4
revised by 013050 on 2019/6/11
revised by 013050 on 2019/9/26
"""
from DataAPI.AddressManagement import AddressManagement
from DataAPI.FactorTestloader import *
import platform
import re
from ModelSystem.Tools import load_intra_day_factor_suanfa, load_day_factor_2_intra_suanfa, load_day_factor, load_label
import pandas as pd
import datetime as dt
addressManagement = AddressManagement()
root_666889 = addressManagement.get_root('666889')
platform_name = addressManagement.get_platform()


class Model:
    def __init__(self, para_model, model_name, model_management):
        self.complete_stock_list = Dtk.get_complete_stock_list()
        self.para_model = para_model
        self.model_name = model_name
        self.model_management = model_management
        self.trading_day = model_management.trading_day
        self.mode = model_management.mode
        if self.mode == 'production':
            self.alpha_universe = model_management.data_buffer.latest_universe
            self.factor_value = model_management.data_buffer.factor_value
            self.volume_df = model_management.data_buffer.volume_df

    def train(self, date):
        pass

    def infer(self, date):
        pass

    def load_label(self, start_date, end_date, label_type='twap', holding_period=1, time_interval=None):
        if self.mode == 'production':
            return None
        return_rate_df = load_label(start_date, end_date, self.complete_stock_list, label_type=label_type, holding_period=holding_period, time_interval=time_interval)
        return return_rate_df

    def load_intra_day_factor_suanfa(self, start_date: int, end_date: int):
        original_day_factor_data_df = load_intra_day_factor_suanfa(start_date, end_date, self.complete_stock_list, self.para_model['test_intra_day_factor'])
        return original_day_factor_data_df

    def load_day_factor_2_intra_suanfa(self, start_date, end_date, time_interval):
        original_day_factor_data_df = load_day_factor_2_intra_suanfa(start_date, end_date, time_interval, self.complete_stock_list, self.para_model['test_day_factor'])
        return original_day_factor_data_df  

    def load_day_factor(self, start_date, end_date):
        original_day_factor_data_df = load_day_factor(start_date, end_date, self.complete_stock_list, self.para_model['test_day_factor'])
        return original_day_factor_data_df                

    @staticmethod
    def outlier_filter(value_df):
        """
        本函数以MAD的方式去除极端值
        """
        # 在20160104和20160107这两天，全市场熔断，那么先删除全市场都是nan的数据
        factor_max = value_df.max(axis=1)
        factor_max = factor_max.dropna()
        value_df = value_df.reindex(factor_max.index)
        factor_median = value_df.median(axis=1)
        factor_deviation_from_median = value_df.sub(factor_median, axis=0)
        factor_mad = factor_deviation_from_median.abs().median(axis=1)
        lower_limit = factor_median - 3.14826 * factor_mad
        upper_limit = factor_median + 3.14826 * factor_mad
        lower_limit = lower_limit.fillna(method='ffill')
        upper_limit = upper_limit.fillna(method='ffill')
        value_df = value_df.clip_lower(lower_limit, axis='index')
        value_df = value_df.clip_upper(upper_limit, axis='index')
        return value_df

    @staticmethod
    def z_score_standardizer(value_df):
        factor_mean = value_df.mean(axis=1)
        factor_std = value_df.std(axis=1)
        value_df = value_df.sub(factor_mean, axis=0)
        value_df = value_df.div(factor_std, axis=0)
        return value_df

    @staticmethod
    def factor_neutralizer(factor_df, start_date, end_date):
        # 初版为了方便，只写了size和industry中性；后续应该开发一个能支持更多因子正交化的函数

        valid_start_date = Dtk.get_n_days_off(start_date, -2)[0]
        stock_list = list(factor_df.columns)
        industry_df = Dtk.get_panel_daily_info(stock_list, valid_start_date, end_date, 'industry3', 'timestamp')
        industry_df = industry_df.shift(1)  # 日级别信息要取前一天的
        mkt_cap_ard_df = Dtk.get_panel_daily_info(stock_list, valid_start_date, end_date, 'mkt_cap_ard', 'timestamp')
        mkt_cap_ard_df = np.log(mkt_cap_ard_df)  # 对市值取对数
        mkt_cap_ard_df = mkt_cap_ard_df.shift(1)  # 日级别信息要取前一天的
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

        return neutralized_factor_df
