# -*- coding: utf-8 -*-
"""
Created on 2018/8/28 16:04

@author: 006547
"""
from DataAPI.AddressManagement import AddressManagement
import numpy as np
import pandas as pd
import DataAPI.DataToolkit as Dtk
import datetime as dt
from Utils.HelperFunctions import outlier_filter_for_label, fillna_with_industry_mean_forlabel, neutralizer_for_label, z_score_standardizer, demean
from DataAPI.FactorTestloader import *
import re


addressManagement = AddressManagement()
root_666889 = addressManagement.get_root('666889')


def load_label(start_date, end_date, complete_stock_list, label_type='twap', holding_period=1, time_interval=None):
    basic_daily_path = '/data/user/012620/AlphaDataCenter/Basic/daily/'
    if label_type == 'interval_twap_30_5_excess_median':
        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        data_df = Dtk.get_panel_interval_pv_df(complete_stock_list, start_date, valid_end_date,
                                               pv_type='interval_twap_30_5', adj_type='FORWARD',
                                               interval_time=time_interval)
        return_rate_df = data_df.shift(-holding_period) / data_df - 1  # 计算收益率
        return_rate_median = return_rate_df.median(axis=1)
        excess_return_df = return_rate_df.sub(return_rate_median, axis=0)
        excess_return_df = Dtk.convert_df_index_type(excess_return_df, 'date_int', 'timestamp')
        return excess_return_df
    elif label_type == 'vwap_re':
        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        daily_vwap = pd.read_pickle(basic_daily_path + 'vwap.pkl')
        daily_vwap.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in daily_vwap.index]
        daily_vwap = daily_vwap.loc[start_date:valid_end_date, :]
        adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl')
        adjfactor.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in adjfactor.index]
        adjfactor = adjfactor.reindex(daily_vwap.index)

        data_vwap = daily_vwap * adjfactor  # 计算后复权的vwap
        return_rate_df = data_vwap.shift(-holding_period) / data_vwap - 1
        return_rate_df = return_rate_df.loc[start_date:end_date]

        is_valid_df = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
        is_valid_df.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in is_valid_df.index]
        is_valid_df = is_valid_df.shift(1).loc[start_date:end_date]
        is_valid_stack = is_valid_df.stack(dropna=False)
        return_rate_stack = return_rate_df.stack(dropna=False)
        return_rate_stack_filtered = return_rate_stack[is_valid_stack == 1]
        return_rate_df = return_rate_stack_filtered.unstack()
        return_rate_df = outlier_filter_for_label(return_rate_df)
        return_rate_df = z_score_standardizer(return_rate_df)
        return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        return return_rate_df.fillna(0)

    elif label_type == 'vwap_NoExtremum_re':
        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        daily_vwap = pd.read_pickle(basic_daily_path + 'vwap.pkl')
        daily_vwap.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in daily_vwap.index]
        daily_vwap = daily_vwap.loc[start_date:valid_end_date, :]
        adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl')
        adjfactor.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in adjfactor.index]
        adjfactor = adjfactor.reindex(daily_vwap.index)
        data_vwap = daily_vwap * adjfactor  # 计算后复权的vwap
        return_rate_df = data_vwap.shift(-holding_period) / data_vwap - 1
        return_rate_df = return_rate_df.loc[start_date:end_date]
        is_valid_df = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
        is_valid_df.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in is_valid_df.index]
        is_valid_df = is_valid_df.shift(1).loc[start_date:end_date]
        is_valid_stack = is_valid_df.stack(dropna=False)
        return_rate_stack = return_rate_df.stack(dropna=False)
        return_rate_stack_filtered = return_rate_stack[is_valid_stack == 1]
        return_rate_df = return_rate_stack_filtered.unstack()

        return_rate_df = outlier_filter_for_label(return_rate_df)  # 因子去除极值
        return_rate_df = z_score_standardizer(return_rate_df)
        return_rate_df = return_rate_df.loc[start_date:end_date]
        return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        return return_rate_df

    elif label_type == 'neu_vwap_re':
        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        daily_vwap = pd.read_pickle(basic_daily_path + 'vwap.pkl')
        daily_vwap.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in daily_vwap.index]
        daily_vwap = daily_vwap.loc[start_date:valid_end_date, :]
        adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl')
        adjfactor.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in adjfactor.index]
        adjfactor = adjfactor.reindex(daily_vwap.index)
        data_vwap = daily_vwap * adjfactor  # 计算后复权的vwap
        data_vwap = data_vwap.reindex(columns=complete_stock_list)

        industry_df_sw = pd.read_pickle(basic_daily_path + 'industry_code_all.pkl')
        industry_df_sw.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in industry_df_sw.index]
        industry_df_sw = industry_df_sw.shift(1).loc[start_date:end_date]
        industry_df_sw = industry_df_sw.reindex(columns=complete_stock_list)
        mkt_cap_ard_df = pd.read_pickle(basic_daily_path + 'mkt_cap_ard.pkl')
        mkt_cap_ard_df.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in mkt_cap_ard_df.index]
        mkt_cap_ard_df = mkt_cap_ard_df.shift(1).loc[start_date:end_date]
        mkt_cap_ard_df = np.log(mkt_cap_ard_df)  # 对市值取对数
        mkt_cap_ard_df = mkt_cap_ard_df.reindex(columns=complete_stock_list)
        is_valid_df = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
        is_valid_df.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in is_valid_df.index]
        is_valid_df = is_valid_df.shift(1).loc[start_date:end_date]
        is_valid_df = is_valid_df.reindex(columns=complete_stock_list).fillna(0)

        return_rate_df = data_vwap.shift(-holding_period) / data_vwap - 1
        return_rate_df = return_rate_df.loc[start_date:end_date]

        return_rate_stack = return_rate_df.stack(dropna=False)
        industry_df_sw_stack = industry_df_sw.stack(dropna=False)
        mkt_cap_ard_df_stack = mkt_cap_ard_df.stack(dropna=False)
        is_valid_stack = is_valid_df.stack(dropna=False)

        return_rate_stack_filtered = return_rate_stack[is_valid_stack == 1]
        industry_df_sw_stack_filtered = industry_df_sw_stack[is_valid_stack == 1]
        mkt_cap_ard_df_stack_filtered = mkt_cap_ard_df_stack[is_valid_stack == 1]

        return_rate_df = return_rate_stack_filtered.unstack()
        industry_df_sw = industry_df_sw_stack_filtered.unstack()
        mkt_cap_ard_df = mkt_cap_ard_df_stack_filtered.unstack()
        return_rate_df = fillna_with_industry_mean_forlabel(return_rate_df, industry_df_sw)
        return_rate_df = demean(return_rate_df)
        mkt_cap_ard_df = outlier_filter_for_label(mkt_cap_ard_df)
        mkt_cap_ard_df = z_score_standardizer(mkt_cap_ard_df)
        return_rate_df = neutralizer_for_label(return_rate_df, mkt_cap_ard_df, industry_df_sw)
        return_rate_df = z_score_standardizer(return_rate_df)
        return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        return return_rate_df
    elif label_type == 'interval_vwap_re_30':

        def sub_sum_data(min_data, time_interval, interval_length):
            match_series = pd.Series(1, index=min_data.index)
            match_cumsum = match_series.cumsum()
            date_sets = list(set([dt.datetime.strftime(i, '%Y%m%d') for i in min_data.index]))
            date_sets = sorted(date_sets)
            cut_points = [pd.Timestamp(date + time_interval + '00') for date in date_sets]
            count_perday = match_cumsum - match_cumsum.loc[cut_points].reindex(match_cumsum.index).fillna(
                method='ffill')
            target_idx = count_perday[count_perday < interval_length].index.tolist()
            target_data = min_data.loc[target_idx]
            match_date_series = pd.Series([dt.datetime.strftime(i, '%Y%m%d') for i in target_data.index],
                                          index=target_data.index)
            daily_data = target_data.groupby(match_date_series).sum()
            return daily_data

        def z_score_standardizer_temp(value_df):
            factor_mean = value_df.mean(axis=1)
            factor_std = value_df.std(axis=1)
            value_df = value_df.sub(factor_mean, axis=0)
            value_df = value_df.div(factor_std, axis=0)
            return value_df

        stock_list = complete_stock_list
        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        amt = Dtk.get_panel_min_data('amt', start_date, valid_end_date, stock_list)
        volume = Dtk.get_panel_min_data('volume', start_date, valid_end_date, stock_list)
        interval_amt_sum = sub_sum_data(amt, time_interval, 30)
        interval_volume_sum = sub_sum_data(volume, time_interval, 30)
        interval_vwap = pd.DataFrame(interval_amt_sum.values / interval_volume_sum.values, index=interval_amt_sum.index,
                                     columns=interval_amt_sum.columns)
        interval_vwap.index = [int(i) for i in interval_vwap.index]

        adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl')
        adjfactor.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in adjfactor.index]
        adjfactor = adjfactor.reindex(interval_vwap.index)
        data_vwap = interval_vwap * adjfactor  # 计算后复权的vwap
        return_rate_df = data_vwap.shift(-holding_period) / data_vwap - 1  # 计算收益率
        return_rate_df = return_rate_df.loc[start_date:end_date, stock_list]
        return_rate_df = z_score_standardizer_temp(return_rate_df)
        return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')

        return return_rate_df
    elif label_type == 'interval_neu_vwap_re_30':
        def sub_sum_data(min_data, time_interval, interval_length):
            match_series = pd.Series(1, index=min_data.index)
            match_cumsum = match_series.cumsum()
            date_sets = list(set([dt.datetime.strftime(i, '%Y%m%d') for i in min_data.index]))
            date_sets = sorted(date_sets)
            cut_points = [pd.Timestamp(date + time_interval + '00') for date in date_sets]
            count_perday = match_cumsum - match_cumsum.loc[cut_points].reindex(match_cumsum.index).fillna(
                method='ffill')
            target_idx = count_perday[count_perday < interval_length].index.tolist()
            target_data = min_data.loc[target_idx]
            match_date_series = pd.Series([dt.datetime.strftime(i, '%Y%m%d') for i in target_data.index],
                                          index=target_data.index)
            daily_data = target_data.groupby(match_date_series).sum()
            return daily_data

        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        amt = Dtk.get_panel_min_data('amt', start_date, valid_end_date, complete_stock_list)
        volume = Dtk.get_panel_min_data('volume', start_date, valid_end_date, complete_stock_list)
        interval_amt_sum = sub_sum_data(amt, time_interval, 30)
        interval_volume_sum = sub_sum_data(volume, time_interval, 30)
        interval_vwap = pd.DataFrame(interval_amt_sum.values / interval_volume_sum.values, index=interval_amt_sum.index,
                                     columns=interval_amt_sum.columns)
        interval_vwap.index = [int(i) for i in interval_vwap.index]

        adjfactor = pd.read_pickle(basic_daily_path + 'adjfactor.pkl')
        adjfactor.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in adjfactor.index]
        adjfactor = adjfactor.reindex(index=interval_vwap.index, columns=complete_stock_list)
        data_vwap = interval_vwap * adjfactor  # 计算后复权的vwap
        return_rate_df = data_vwap.shift(-holding_period) / data_vwap - 1  # 计算收益率
        return_rate_df = return_rate_df.loc[start_date:end_date, complete_stock_list]

        industry_df_sw = pd.read_pickle(basic_daily_path + 'industry_code_all.pkl')
        industry_df_sw.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in industry_df_sw.index]
        industry_df_sw = industry_df_sw.shift(1).loc[start_date:end_date]
        industry_df_sw = industry_df_sw.reindex(columns=complete_stock_list)
        mkt_cap_ard_df = pd.read_pickle(basic_daily_path + 'mkt_cap_ard.pkl')
        mkt_cap_ard_df.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in mkt_cap_ard_df.index]
        mkt_cap_ard_df = mkt_cap_ard_df.shift(1).loc[start_date:end_date]
        mkt_cap_ard_df = np.log(mkt_cap_ard_df)  # 对市值取对数
        mkt_cap_ard_df = mkt_cap_ard_df.reindex(columns=complete_stock_list)
        is_valid_df = pd.read_pickle(basic_daily_path + 'is_valid.pkl')
        is_valid_df.index = [int(dt.datetime.strftime(i, '%Y%m%d')) for i in is_valid_df.index]
        is_valid_df = is_valid_df.shift(1).loc[start_date:end_date]
        is_valid_df = is_valid_df.reindex(columns=complete_stock_list).fillna(0)

        return_rate_stack = return_rate_df.stack(dropna=False)
        industry_df_sw_stack = industry_df_sw.stack(dropna=False)
        mkt_cap_ard_df_stack = mkt_cap_ard_df.stack(dropna=False)
        is_valid_stack = is_valid_df.stack(dropna=False)

        return_rate_stack_filtered = return_rate_stack[is_valid_stack == 1]
        industry_df_sw_stack_filtered = industry_df_sw_stack[is_valid_stack == 1]
        mkt_cap_ard_df_stack_filtered = mkt_cap_ard_df_stack[is_valid_stack == 1]

        return_rate_df = return_rate_stack_filtered.unstack()
        industry_df_sw = industry_df_sw_stack_filtered.unstack()
        mkt_cap_ard_df = mkt_cap_ard_df_stack_filtered.unstack()
        return_rate_df = fillna_with_industry_mean_forlabel(return_rate_df, industry_df_sw)
        # return_rate_df = outlier_filter(return_rate_df)
        return_rate_df = demean(return_rate_df)
        mkt_cap_ard_df = outlier_filter_for_label(mkt_cap_ard_df)
        mkt_cap_ard_df = z_score_standardizer(mkt_cap_ard_df)
        return_rate_df = neutralizer_for_label(return_rate_df, mkt_cap_ard_df, industry_df_sw)
        return_rate_df = z_score_standardizer(return_rate_df)
        return_rate_df = Dtk.convert_df_index_type(return_rate_df, 'date_int', 'timestamp')
        return return_rate_df


def load_intra_all_factor_suanfa(start_date, end_date, time_interval, complete_stock_list, factor_list,
                                 path_intra=root_666889 + "/Apollo/DepartmentIntraFactor/DepartmentStandardIntraFactor2/",
                                 path_dep=root_666889 + "/Apollo/DepartmentDailyFactor/DepartmentDailyStandardFactor2/",
                                 path_team=root_666889 + "/Apollo/DepartmentDailyFactor/DepartmentDailyStandardFactor2_Team/",
                                 index_type='timestamp'):
    original_factor_data_df = {}

    start_date_datetime = Dtk.convert_date_or_time_int_to_datetime(Dtk.get_n_days_off(start_date, -2)[0])
    end_date_datetime = Dtk.convert_date_or_time_int_to_datetime(end_date) + dt.timedelta(hours=23)

    is_valid_path = '/data/user/012620/AlphaDataCenter/Basic/daily/'
    is_valid = pd.read_pickle(is_valid_path + 'is_valid.pkl')
    is_valid_day = is_valid.shift()
    is_valid_day = is_valid_day.reindex(columns=complete_stock_list, fill_value=0)
    is_valid_day_temp = is_valid_day.loc[start_date_datetime:end_date_datetime, :]

    for factor_name in factor_list:
        # print('loading ' + factor_name)
        if re.match(r"^Fix\d+_.*", factor_name):
            temp_factor = load_factor(factor_name, complete_stock_list, start_date_datetime, end_date_datetime, path_intra)
            temp_factor[pd.DataFrame(is_valid_day_temp.values == 0, index=temp_factor.index, columns=temp_factor.columns)] = np.nan
            temp_factor.drop(index=[temp_factor.index[0]], inplace=True)
        else:
            file_name = "{}/{}.h5".format(path_dep, factor_name)
            if not os.path.isfile(file_name):
                path = path_team
            else:
                path = path_dep
            temp_factor = load_factor(factor_name, complete_stock_list, start_date_datetime, end_date_datetime, path)
            temp_factor = temp_factor.shift(1)
            temp_factor[pd.DataFrame(is_valid_day_temp.values == 0, index=temp_factor.index, columns=temp_factor.columns)] = np.nan
            temp_factor.drop(index=[temp_factor.index[0]], inplace=True)
            temp_factor.index = temp_factor.index + int((int(time_interval) / 100)) * 3600 + (int(time_interval) % 100) * 60
        if index_type == 'datetime':
            temp_factor.index = [dt.datetime.fromtimestamp(x) for x in list(temp_factor.index)]
        original_factor_data_df.update({factor_name: temp_factor})

    return original_factor_data_df


def load_intra_day_factor_suanfa(start_date, end_date, complete_stock_list, factor_list,
                                 path=root_666889 + "/Apollo/DepartmentIntraFactor/DepartmentStandardIntraFactor2/",
                                 index_type='timestamp'):
    original_day_factor_data_df = {}
    start_date_datetime = Dtk.convert_date_or_time_int_to_datetime(start_date)
    end_date_datetime = Dtk.convert_date_or_time_int_to_datetime(end_date) + dt.timedelta(hours=23)
    print('loading intra_day fixed factor')

    is_valid_path = '/data/user/012620/AlphaDataCenter/Basic/daily/'
    is_valid = pd.read_pickle(is_valid_path + 'is_valid.pkl')
    is_valid_day = is_valid.shift()
    is_valid_day = is_valid_day.reindex(columns=complete_stock_list, fill_value=0)
    is_valid_day_temp = is_valid_day.loc[start_date_datetime:end_date_datetime, :]

    for intra_day_factor_name in factor_list:
        print('loading ' + intra_day_factor_name)
        temp_factor = load_factor(intra_day_factor_name, complete_stock_list, start_date_datetime, end_date_datetime, path)
        temp_factor[pd.DataFrame(is_valid_day_temp.values == 0, index=temp_factor.index, columns=temp_factor.columns)] = np.nan
        if index_type == 'datetime':
            temp_factor.index = [dt.datetime.fromtimestamp(x) for x in list(temp_factor.index)]
        original_day_factor_data_df.update({intra_day_factor_name: temp_factor})

    return original_day_factor_data_df


def load_day_factor_2_intra_suanfa(start_date, end_date, time_interval, complete_stock_list, factor_list,
                                   path_dep=root_666889 + "/Apollo/DepartmentDailyFactor/DepartmentDailyStandardFactor2/",
                                   path_team=root_666889 + "/Apollo/DepartmentDailyFactor/DepartmentDailyStandardFactor2_Team/",
                                 index_type='timestamp'):
    original_day_factor_data_df = {}

    start_date_datetime = Dtk.convert_date_or_time_int_to_datetime(Dtk.get_n_days_off(start_date, -2)[0])
    end_date_datetime = Dtk.convert_date_or_time_int_to_datetime(end_date)

    start_date_new = Dtk.get_n_days_off(start_date, -2)[0]
    start_date_new_datetime = Dtk.convert_date_or_time_int_to_datetime(start_date_new)
    is_valid_path = '/data/user/012620/AlphaDataCenter/Basic/daily/'
    is_valid = pd.read_pickle(is_valid_path + 'is_valid.pkl')
    is_valid_day = is_valid.shift()
    is_valid_day = is_valid_day.reindex(columns=complete_stock_list, fill_value=0)
    is_valid_day_temp = is_valid_day.loc[start_date_new_datetime:end_date_datetime, :]

    # print('loading day factor')
    for day_factor_name in factor_list:
        # print('loading ' + day_factor_name)
        file_name = "{}/{}.h5".format(path_dep, day_factor_name)
        if not os.path.isfile(file_name):
            path = path_team
        else:
            path = path_dep
        temp_factor = load_factor(day_factor_name, complete_stock_list, start_date_datetime, end_date_datetime, path)
        temp_factor = temp_factor.shift(1)
        temp_factor[pd.DataFrame(is_valid_day_temp.values == 0, index=temp_factor.index, columns=temp_factor.columns)] = np.nan
        temp_factor.drop(index=[temp_factor.index[0]], inplace=True)
        temp_factor.index = temp_factor.index + int((int(time_interval) / 100)) * 3600 + (int(time_interval) % 100) * 60
        # print("shift day_factor_name: " + day_factor_name)
        if index_type == 'datetime':
            temp_factor.index = [dt.datetime.fromtimestamp(x) for x in list(temp_factor.index)]
        original_day_factor_data_df.update({day_factor_name: temp_factor})

    return original_day_factor_data_df


def load_day_factor(start_date, end_date, complete_stock_list, factor_list,
                    path_dep=root_666889 + "/Apollo/DepartmentDailyFactor/DepartmentDailyStandardFactor2/",
                    path_team=root_666889 + "/Apollo/DepartmentDailyFactor/DepartmentDailyStandardFactor2_Team/",
                    index_type='timestamp'):
    original_day_factor_data_df = {}
    end_date_datetime = Dtk.convert_date_or_time_int_to_datetime(end_date)

    # start_date_new = Dtk.get_n_days_off(start_date, -2)[0]
    start_date_new_datetime = Dtk.convert_date_or_time_int_to_datetime(start_date)
    is_valid_path = '/data/user/012620/AlphaDataCenter/Basic/daily/'
    is_valid = pd.read_pickle(is_valid_path + 'is_valid.pkl')
    is_valid_day = is_valid
    is_valid_day = is_valid_day.reindex(columns=complete_stock_list, fill_value=0)
    is_valid_day.index = [x.year * 10000 + x.month * 100 + x.day for x in is_valid_day.index]
    is_valid_day_temp = is_valid_day.loc[start_date:end_date, :]
    is_valid_day_temp.index = [Dtk.convert_date_or_time_int_to_datetime(x) for x in is_valid_day_temp.index]

    # print('loading factor')
    for day_factor_name in factor_list:
        # print('loading ' + day_factor_name)
        file_name = "{}/{}.h5".format(path_dep, day_factor_name)
        if not os.path.isfile(file_name):
            path = path_team
        else:
            path = path_dep
        temp_factor = load_factor(day_factor_name, complete_stock_list, start_date_new_datetime, end_date_datetime, path)
        # print('@Sample:', start_date, end_date)
        temp_factor[pd.DataFrame(is_valid_day_temp.values == 0, index=temp_factor.index, columns=temp_factor.columns)] = np.nan
        if index_type == 'datetime':
            temp_factor.index = [dt.datetime.fromtimestamp(x) for x in list(temp_factor.index)]
        original_day_factor_data_df.update({day_factor_name: temp_factor})
    return original_day_factor_data_df


def remove_void_data(data_list: list):
    temp_judge = np.isnan(data_list[0])
    temp_judge = np.hstack((temp_judge, data_list[0] == np.inf))
    temp_judge = np.hstack((temp_judge, data_list[0] == -np.inf))
    if data_list.__len__() > 1:
        for i in range(1, data_list.__len__()):
            temp_judge = np.hstack((temp_judge, np.isnan(data_list[i])))
            temp_judge = np.hstack((temp_judge, data_list[i] == np.inf))
            temp_judge = np.hstack((temp_judge, data_list[i] == -np.inf))
    judge = temp_judge.any(1)
    data_list_filtration = []
    judge_reverse = judge == False
    for i in range(0, data_list.__len__()):
        data_list_filtration.append(data_list[i][judge_reverse, :])
    return data_list_filtration, judge


def remove_void_data_suanfa(data_list: list):
    temp_judge = np.isnan(data_list[0]) 
    temp_judge = np.hstack((temp_judge, data_list[0] == np.inf))
    temp_judge = np.hstack((temp_judge, data_list[0] == -np.inf))
    if data_list.__len__() > 1:
        for i in range(1, data_list.__len__()):
            temp_judge = np.hstack((temp_judge, np.isnan(data_list[i])))
            temp_judge = np.hstack((temp_judge, data_list[i] == np.inf))
            temp_judge = np.hstack((temp_judge, data_list[i] == -np.inf))
    judge = temp_judge.any(1)
    data_list_filtration = []
    judge_reverse = judge == False
    for i in range(0, data_list.__len__()-1):
        data_list_filtration.append(data_list[i][judge_reverse, :])
    return data_list_filtration, judge


def fill_void_data(data_list: list, fill: str):
    if fill == '0':
        for i in range(data_list.__len__()):
            temp = data_list[i].copy()
            temp[np.isnan(temp)] = 0
            temp[temp == np.inf] = 0
            temp[temp == -np.inf] = 0
    elif fill == 'mean':
        for i in range(data_list.__len__()):
            temp = data_list[i]

            temp[temp == np.inf] = np.nan
            temp[temp == -np.inf] = np.nan
            nan_mean = np.nanmean(temp, axis=0)
            is_nan = np.isnan(temp)
            for j in range(temp.shape[1]):
                temp[is_nan[:, j], j] = nan_mean[j]
    return data_list


def factor_excess_mean_select(factor_list, date_start, date_end, del_ratio, time_interval):
    # factor_list = [x+'.h5' for x in factor_list]
    if time_interval != 2400:
        address = '/data/user/666889/Apollo/IntraTopNavHistory/Cost0/'
        address0 = '/data/user/666889/Apollo/IntraTopNavHistory_dpt/Cost0/'
        factor_list = [x + '.h5' for x in factor_list]
    else:
        address = '/data/user/666889/Apollo/DepartmentFactorTopGroupNav/Cost0/'
    if time_interval != 2400:
        file = pd.read_csv(address+str(time_interval)+'_ExceedMean.csv', index_col=0)
        file0 = pd.read_csv(address0 + str(time_interval) + '_ExceedMean.csv', index_col=0)
        file = pd.concat([file, file0], axis=1)
    else:
        file = pd.read_csv(address + 'ExceedMean.csv', index_col=0)
        file = file.shift(1)
    target_data = file.loc[date_start:date_end, factor_list]
    factor_list_sort = list(target_data.mean().sort_values().index)
    factor_list_select = factor_list_sort[int(factor_list_sort.__len__()*del_ratio):]
    if time_interval != 2400:
        factor_list_select = [x[:-3] for x in factor_list_select]
    return factor_list_select


def factor_excess_mean_select2(factor_list, date_start, date_end, del_ratio, time_interval):
    # factor_list = [x+'.h5' for x in factor_list]
    if time_interval != 2400:
        address = '/data/user/666889/Apollo/ResearchData/tmp/exceedmean_checkwithlly/recalc_with_selltwap_benchmarktwap/fix_adjweight/Cost0/'
        factor_list = [x + '.h5' for x in factor_list]
    else:
        address = '/data/user/666889/Apollo/ResearchData/tmp/exceedmean_checkwithlly/recalc_with_selltwap_benchmarktwap/daily_adjweight/'
    if time_interval != 2400:
        file = pd.read_csv(address+str(time_interval)+'_ExceedMean.csv', index_col=0)
    else:
        file = pd.read_csv(address+'ExceedMean.csv', index_col=0)
        file = file.shift(1)
    target_data = file.loc[date_start:date_end, factor_list]

    if time_interval != 2400:
        factor_list = np.array(list(target_data.mean().index))
        factor_list_select = factor_list[target_data.mean().values > 0.0001]
    else:
        factor_list = np.array(list(target_data.mean().index))
        factor_list_select = factor_list[target_data.mean().values > 0.0001]

    if time_interval != 2400:
        factor_list_select = [x[:-3] for x in factor_list_select]
    return factor_list_select


def factor_excess_mean_select3(factor_list, date_start, date_end, del_ratio, time_interval):
    # factor_list = [x+'.h5' for x in factor_list]
    if time_interval != 2400:
        address = '/data/user/666889/Apollo/ResearchData/tmp/exceedmean_checkwithlly/recalc_with_selltwap_benchmarktwap/fix_adjweight/Cost0/'
        factor_list = [x + '.h5' for x in factor_list]
    else:
        address = '/data/user/666889/Apollo/ResearchData/tmp/exceedmean_checkwithlly/recalc_with_selltwap_benchmarktwap/daily_adjweight/'
    if time_interval != 2400:
        file = pd.read_csv(address+str(time_interval)+'_ExceedMean.csv', index_col=0)
    else:
        file = pd.read_csv(address+'ExceedMean.csv', index_col=0)
        file = file.shift(1)
    target_data = file.loc[date_start:date_end, factor_list]

    factor_list_sort = list(target_data.mean().sort_values().index)
    factor_list_select = factor_list_sort[int(factor_list_sort.__len__()*del_ratio):]
    if time_interval != 2400:
        factor_list_select = [x[:-3] for x in factor_list_select]
    return factor_list_select
