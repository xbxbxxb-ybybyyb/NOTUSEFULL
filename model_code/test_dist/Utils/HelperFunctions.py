"""
常用函数
"""
import numpy as np
import pandas as pd
import scipy.stats as sps
import datetime as dt
import DataAPI.DataToolkit as Dtk
import pickle
import os


def factor_distribution_calc(factor_value_df):
    factor_np = factor_value_df.values.flatten()
    factor_val = factor_np[np.isfinite(factor_np)]
    factor_min = np.nanmin(factor_val)
    factor_max = np.nanmax(factor_val)
    factor_mean = np.nanmean(factor_val)
    factor_median = np.nanmedian(factor_val)
    factor_std = np.nanstd(factor_val)
    factor_skewness = sps.skew(factor_val)
    factor_kurtosis = sps.kurtosis(factor_val)
    stat_item = ['Skewness', 'Kurtosis', 'Median', 'Mean', 'Max', 'Min', 'Std']
    factor_distribution = pd.DataFrame(
        [factor_skewness, factor_kurtosis, factor_median, factor_mean, factor_max, factor_min, factor_std],
        index=stat_item, columns=['factor_distribution'])
    return factor_distribution


def factor_distribution_calc2(factor_value_df):
    factor_np = factor_value_df.values.flatten()
    factor_val = factor_np[np.isfinite(factor_np)]
    factor_min = np.nanmin(factor_val)
    factor_max = np.nanmax(factor_val)
    factor_mean = np.nanmean(factor_val)
    factor_median = np.nanmedian(factor_val)
    factor_025 = np.percentile(factor_val, 25)
    factor_075 = np.percentile(factor_val, 75)
    factor_std = np.nanstd(factor_val)
    factor_skewness = sps.skew(factor_val)
    factor_kurtosis = sps.kurtosis(factor_val)
    stat_item = ['025', 'Median', '075', 'Mean', 'Max', 'Min', 'Std', 'Skewness', 'Kurtosis']
    factor_distribution = pd.DataFrame(
        [factor_025, factor_median, factor_075, factor_mean, factor_max, factor_min, factor_std, factor_skewness,
         factor_kurtosis],
        index=stat_item, columns=['factor_distribution'])
    return factor_distribution


def outlier_filter(value_df, method="MAD", parameter=3.14826, lower_clip=True, upper_clip=True):
    if method == "3Std":
        factor_mean = value_df.mean(axis=1)
        factor_std = value_df.std(axis=1)
        upper_limit = factor_mean + 3 * factor_std
        lower_limit = factor_mean - 3 * factor_std
    else:
        # 如有全为nan的行，则drop之
        factor_max = value_df.max(axis=1)
        factor_max = factor_max.dropna()
        value_df = value_df.reindex(factor_max.index)
        factor_median = value_df.median(axis=1)
        factor_deviation_from_median = value_df.sub(factor_median, axis=0)
        factor_mad = factor_deviation_from_median.abs().median(axis=1)
        lower_limit = factor_median - parameter * factor_mad
        upper_limit = factor_median + parameter * factor_mad
    lower_limit = lower_limit.fillna(method='ffill')
    upper_limit = upper_limit.fillna(method='ffill')
    if lower_clip:
        value_df = value_df.clip_lower(lower_limit, axis='index')
    if upper_clip:
        value_df = value_df.clip_upper(upper_limit, axis='index')
    return value_df


def outlier_filter2(limite_status, value_df, method="MAD", parameter=3.14826, lower_clip=True, upper_clip=True):
    #  考虑了涨跌停时刻的因子值的异常性
    #  在进行统计的时候除去了涨跌停时刻的因子
    clean_value_df = value_df * limite_status / limite_status
    if method == "3Std":
        factor_mean = clean_value_df.mean(axis=1)
        factor_std = clean_value_df.std(axis=1)
        upper_limit = factor_mean + 3 * factor_std
        lower_limit = factor_mean - 3 * factor_std
    else:
        # 如有全为nan的行，则drop之
        factor_max = clean_value_df.max(axis=1)
        factor_max = factor_max.dropna()
        clean_value_df = clean_value_df.reindex(factor_max.index)
        factor_median = clean_value_df.median(axis=1)
        factor_deviation_from_median = clean_value_df.sub(factor_median, axis=0)
        factor_mad = factor_deviation_from_median.abs().median(axis=1)
        lower_limit = factor_median - parameter * factor_mad
        upper_limit = factor_median + parameter * factor_mad
    lower_limit = lower_limit.fillna(method='ffill')
    upper_limit = upper_limit.fillna(method='ffill')
    if lower_clip:
        value_df = value_df.clip_lower(lower_limit, axis='index')
    if upper_clip:
        value_df = value_df.clip_upper(upper_limit, axis='index')
    return value_df


def z_score_standardizer(value_df):
    factor_mean = value_df.mean(axis=1)
    factor_std = value_df.std(axis=1)
    value_df = value_df.sub(factor_mean, axis=0)
    value_df = value_df.div(factor_std, axis=0)
    return value_df


def z_score_standardizer2(limite_status, value_df):
    #  考虑了涨跌停时刻的因子值的异常性
    #  在进行统计的时候除去了涨跌停时刻的因子
    clean_value_df = value_df * limite_status / limite_status
    factor_mean = clean_value_df.mean(axis=1)
    factor_std = clean_value_df.std(axis=1)
    value_df = value_df.sub(factor_mean, axis=0)
    value_df = value_df.div(factor_std, axis=0)
    return value_df


def demean(value_df):
    return value_df.sub(value_df.mean(axis=1),axis=0)


def make_one_hot(input_data):
    # 将输入的向量改造成one-hot矩阵
    # 例如：输入x=np.array([1, 2, 4])，shape是(3,)；输出一个(3,5)的矩阵，其中3和3对应，5对应的是max(x)+1
    # array([[0, 1, 0, 0, 0],
    #        [0, 0, 1, 0, 0],
    #        [0, 0, 0, 0, 1]])
    max_value = np.max(input_data) + 1
    result = (np.arange(max_value) == input_data[:, None]).astype(np.int)
    return result


def extend_index_to_intraday(df, freq=30, index_type_timestamp=True):
    # 将dataframe从日频index延展为日内频率，数据是直接复制
    min_list = np.array(Dtk.get_complete_minute_list()[1:-1])
    rep_num = 240 / freq
    min_list_used = min_list[list(range(0, 240, freq))]
    if index_type_timestamp:
        new_df = Dtk.convert_df_index_type(df, 'timestamp', 'date_int')
    else:
        new_df = df.copy()
    new_index = np.repeat(np.array(new_df.index), rep_num) * 1000000 + np.tile(min_list_used, df.shape[0]) * 100
    new_df = pd.DataFrame(np.repeat(new_df.values, rep_num, 0), index=new_index, columns=new_df.columns)
    if index_type_timestamp:
        new_df = Dtk.convert_df_index_type(new_df, 'date_int', 'timestamp')
    return new_df


def compress_intraday_index_to_daily(df, index_type_timestamp=False):
    # 将索引为日内（14位整形）的日频df或series转化为索引为8位整形日期的日频df或series
    new_df = df.copy()
    if_input_series = False
    if isinstance(df, pd.Series):
        if_input_series = True
        new_df = new_df.to_frame()
    if index_type_timestamp:
        new_df = Dtk.convert_df_index_type(new_df, 'timestamp', 'date14_int')
    new_df.index.name = 'index'
    intraday_index_list = list(new_df.index)
    daily_index_list = [divmod(x, 1000000)[0] for x in intraday_index_list]
    new_df['dt'] = daily_index_list
    new_df = new_df.reset_index()
    new_df = new_df.set_index(['dt'])
    new_df = new_df.drop('index', axis=1)
    if index_type_timestamp:
        new_df = Dtk.convert_df_index_type(new_df, 'date_int', 'timestamp')
    if if_input_series:
        new_df = new_df[0]
    return new_df


def get_intraday_moment_df(df, moment):
    index_datetime_list = list(df.index)
    key_idx_list = []
    for i, i_datetime in enumerate(index_datetime_list):
        _, i_time = divmod(i_datetime, 1000000)
        if i_time == moment:
            key_idx_list.append(i)
    new_df = df.iloc[key_idx_list].copy()
    return new_df


def factor_neutralizer(factor_df, start_date, end_date, neutral_factor_set={'size', 'industry3'},
                       neutral_regressor_backward_shift=True):
    """
    注释 - neutral_regressor_backward_shift: 中性化因子（行业、市值）是否要取前一天的
    """
    if neutral_factor_set == {'size', 'industry3'} or neutral_factor_set == {'size'}:
        pass
    else:
        neutralized_factor_df = factor_df
        return neutralized_factor_df
    valid_start_date = Dtk.get_n_days_off(start_date, -22)[0]  # 向前多取一段时间，以便后续shift的话有足够的值
    stock_list = list(factor_df.columns)
    factor_date_list = list(factor_df.index)
    industry_df = Dtk.get_panel_daily_info(stock_list, valid_start_date, end_date, 'industry3', 'timestamp')
    if neutral_regressor_backward_shift:
        industry_df = industry_df.shift(1)
    mkt_cap_ard_df = Dtk.get_panel_daily_info(stock_list, valid_start_date, end_date, 'mkt_cap_ard', 'timestamp')
    mkt_cap_ard_df = np.log(mkt_cap_ard_df)  # 对市值取对数
    if neutral_regressor_backward_shift:
        mkt_cap_ard_df = mkt_cap_ard_df.shift(1)

    # 确保industry和mkt_cap_ard与factor_df的index一致，这样才能正确回归
    industry_df = industry_df.reindex(factor_df.index)
    mkt_cap_ard_df = mkt_cap_ard_df.reindex(factor_df.index)

    if neutral_factor_set == {'size', 'industry3'}:
        t1 = dt.datetime.now()
        factor_start_line = list(mkt_cap_ard_df.index).index(factor_df.index[0])
        factor_end_line = list(mkt_cap_ard_df.index).index(factor_df.index[-1])
        # 要生成一个从factor_start_line 到 factor_end_line的自然数数列，前后双闭；range是前闭后开，因此区间后半部分要+1
        repeat_lines_list = list(range(factor_start_line, factor_end_line + 1))
        factor_array = factor_df.values
        industry_df2 = industry_df.fillna(0)  # 将行业的缺失值替换为0，以方便后续用np创造one_hot矩阵
        industry_array = industry_df2.values
        mkt_cap_ard_array = mkt_cap_ard_df.values
        stock_col_num = stock_list.__len__()
        residual_list = []
        residual_date_list = []
        if repeat_lines_list.__len__() > 10000:
            division_multiplier = 1000
        elif repeat_lines_list.__len__() > 5000:
            division_multiplier = 500
        else:
            division_multiplier = 100
        for j, i_line in enumerate(repeat_lines_list):
            if j % division_multiplier == 0:
                print("factor neutralizing, {} / {} lines".format(j, list(factor_df.index).__len__()))
            y0 = factor_array[j]
            x1_0 = industry_array[i_line].astype(np.int)
            x1_0 = make_one_hot(x1_0)  # 构造one_hot矩阵
            x1_0 = x1_0[:, 1:]  # 去掉第0列，也就是去掉原来无行业的值
            x2_0 = mkt_cap_ard_array[i_line]
            x2_0 = x2_0.reshape([stock_col_num, 1])
            x0 = np.hstack([x1_0, x2_0])
            y0_isnan = np.isnan(y0)
            x0_isnan = np.isnan(np.max(x0, axis=1))
            y0_isvalid = 1 - y0_isnan
            x0_isvalid = 1 - x0_isnan
            valid_rows = x0_isvalid * y0_isvalid
            valid_stock_list = [stock_list[i] for i in range(stock_list.__len__()) if valid_rows[i] == 1]
            x0_valid = x0[valid_rows == 1]
            y0_valid = y0[valid_rows == 1]
            ind_check = np.sum(x0_valid, axis=0)
            empty_industry = []
            for i_col in range(x1_0.shape[1]):
                if ind_check[i_col] < 1:
                    empty_industry.append(i_col)
            if empty_industry.__len__() > 0:
                x0_valid = np.delete(x0_valid, empty_industry, 1)
            if x0_valid.__len__() > 0:
                b = np.linalg.inv(x0_valid.T.dot(x0_valid)).dot(x0_valid.T).dot(y0_valid)
                residual = y0_valid - x0_valid.dot(b)  # 求残差
                residual_dict = dict(zip(valid_stock_list, residual))  # 将残差与股票代码关联起来
                residual_list.append(residual_dict)
                residual_date_list.append(factor_date_list[j])
        # 将残差list一次性转变为DataFrame
        neutralized_factor_df = pd.DataFrame(residual_list, index=residual_date_list)
        t2 = dt.datetime.now()
        print("neutralizing costs", t2 - t1)
        return neutralized_factor_df
    elif neutral_factor_set == {'size'}:
        t1 = dt.datetime.now()
        factor_start_line = list(mkt_cap_ard_df.index).index(factor_df.index[0])
        factor_end_line = list(mkt_cap_ard_df.index).index(factor_df.index[-1])
        # 要生成一个从factor_start_line 到 factor_end_line的自然数数列，前后双闭；range是前闭后开，因此区间后半部分要+1
        repeat_lines_list = list(range(factor_start_line, factor_end_line + 1))
        factor_array = factor_df.values
        mkt_cap_ard_array = mkt_cap_ard_df.values
        stock_col_num = stock_list.__len__()
        residual_list = []
        residual_date_list = []
        if repeat_lines_list.__len__() > 10000:
            division_multiplier = 1000
        elif repeat_lines_list.__len__() > 5000:
            division_multiplier = 500
        else:
            division_multiplier = 100
        for j, i_line in enumerate(repeat_lines_list):
            if j % division_multiplier == 0:
                print("factor neutralizing, {} / {} lines".format(j, list(factor_df.index).__len__()))
            y0 = factor_array[j]
            x0 = mkt_cap_ard_array[i_line]
            x0 = x0.reshape([stock_col_num, 1])
            y0_isnan = np.isnan(y0)
            x0_isnan = np.isnan(np.max(x0, axis=1))
            y0_isvalid = 1 - y0_isnan
            x0_isvalid = 1 - x0_isnan
            valid_rows = x0_isvalid * y0_isvalid
            valid_stock_list = [stock_list[i] for i in range(stock_list.__len__()) if valid_rows[i] == 1]
            x0_valid = x0[valid_rows == 1]
            y0_valid = y0[valid_rows == 1]
            empty_industry = []
            if empty_industry.__len__() > 0:
                x0_valid = np.delete(x0_valid, empty_industry, 1)
            if x0_valid.__len__() > 0:
                b = np.linalg.inv(x0_valid.T.dot(x0_valid)).dot(x0_valid.T).dot(y0_valid)
                residual = y0_valid - x0_valid.dot(b)  # 求残差
                residual_dict = dict(zip(valid_stock_list, residual))  # 将残差与股票代码关联起来
                residual_list.append(residual_dict)
                residual_date_list.append(factor_date_list[j])
        # 将残差list一次性转变为DataFrame
        neutralized_factor_df = pd.DataFrame(residual_list, index=residual_date_list)
        t2 = dt.datetime.now()
        print("neutralizing costs", t2 - t1)
        return neutralized_factor_df


def factor_neutralizer2(limite_status, factor_df, start_date, end_date, neutral_factor_set={'size', 'industry3'},
                        neutral_regressor_backward_shift=True):
    """
    注释 - neutral_regressor_backward_shift: 中性化因子（行业、市值）是否要取前一天的
    #  考虑了涨跌停时刻的因子值的异常性
    #  在计算beta的时候剔除了涨跌停时刻因子 若某行业全部股票都涨停or跌停 则加入
    #  用beta计算残差时考虑了全部因子
    """
    clean_factor_df = factor_df * limite_status / limite_status
    if neutral_factor_set == {'size', 'industry3'} or neutral_factor_set == {'size'}:
        pass
    else:
        neutralized_factor_df = factor_df
        return neutralized_factor_df
    valid_start_date = Dtk.get_n_days_off(start_date, -22)[0]  # 向前多取一段时间，以便后续shift的话有足够的值
    stock_list = list(factor_df.columns)
    factor_date_list = list(factor_df.index)
    industry_df = Dtk.get_panel_daily_info(stock_list, valid_start_date, end_date, 'industry3', 'timestamp')
    if neutral_regressor_backward_shift:
        industry_df = industry_df.shift(1)
    mkt_cap_ard_df = Dtk.get_panel_daily_info(stock_list, valid_start_date, end_date, 'mkt_cap_ard', 'timestamp')
    mkt_cap_ard_df = np.log(mkt_cap_ard_df)  # 对市值取对数
    if neutral_regressor_backward_shift:
        mkt_cap_ard_df = mkt_cap_ard_df.shift(1)

    # 确保industry和mkt_cap_ard与factor_df的index一致，这样才能正确回归
    industry_df = industry_df.reindex(factor_df.index)
    mkt_cap_ard_df = mkt_cap_ard_df.reindex(factor_df.index)
    clean_factor_array = clean_factor_df.values
    factor_array = factor_df.values
    mkt_cap_ard_array = mkt_cap_ard_df.values

    if neutral_factor_set == {'size', 'industry3'}:
        t1 = dt.datetime.now()
        factor_start_line = list(mkt_cap_ard_df.index).index(factor_df.index[0])
        factor_end_line = list(mkt_cap_ard_df.index).index(factor_df.index[-1])
        # 要生成一个从factor_start_line 到 factor_end_line的自然数数列，前后双闭；range是前闭后开，因此区间后半部分要+1
        repeat_lines_list = list(range(factor_start_line, factor_end_line + 1))
        industry_df2 = industry_df.fillna(0)  # 将行业的缺失值替换为0，以方便后续用np创造one_hot矩阵
        industry_array = industry_df2.values
        stock_col_num = stock_list.__len__()
        residual_list = []
        residual_date_list = []
        if repeat_lines_list.__len__() > 10000:
            division_multiplier = 1000
        elif repeat_lines_list.__len__() > 5000:
            division_multiplier = 500
        else:
            division_multiplier = 100
        for j, i_line in enumerate(repeat_lines_list):
            if j % division_multiplier == 0:
                print("factor neutralizing, {} / {} lines".format(j, list(factor_df.index).__len__()))
            y0_test = factor_array[j]
            y0_train = clean_factor_array[j]

            stock2industry = industry_array[i_line].astype(np.int)
            x1_0 = make_one_hot(stock2industry)  # 构造one_hot矩阵
            x1_0 = x1_0[:, 1:]  # 去掉第0列，也就是去掉原来无行业的值
            x2_0 = mkt_cap_ard_array[i_line]
            x2_0 = x2_0.reshape([stock_col_num, 1])
            x0 = np.hstack([x1_0, x2_0])
            y0_test_isnan = np.isnan(y0_test)
            y0_train_isnan = np.isnan(y0_train)
            x0_isnan = np.isnan(np.max(x0, axis=1))
            y0_test_isvalid = 1 - y0_test_isnan
            y0_train_isvalid = 1 - y0_train_isnan
            x0_isvalid = 1 - x0_isnan
            test_valid_rows = x0_isvalid * y0_test_isvalid
            test_valid_stock_list = [stock_list[i] for i in range(stock_list.__len__()) if test_valid_rows[i] == 1]
            x0_test_valid = x0[test_valid_rows == 1]
            y0_test_valid = y0_test[test_valid_rows == 1]
            train_valid_rows = x0_isvalid * y0_train_isvalid
            # train_valid_stock_list = [stock_list[i] for i in range(stock_list.__len__()) if train_valid_rows[i] == 1]
            x0_train_valid = x0[train_valid_rows == 1]
            y0_train_valid = y0_train[train_valid_rows == 1]
            test_ind_check = np.sum(x0_test_valid, axis=0)
            train_ind_check = np.sum(x0_train_valid, axis=0)
            # train_empty_industry = []
            empty_industry = []
            restore_industry = []
            for i_col in range(x1_0.shape[1]):
                if test_ind_check[i_col] < 1 and train_ind_check[i_col] < 1:
                    empty_industry.append(i_col)
                elif train_ind_check[i_col] < 1 and test_ind_check[i_col] >= 1:
                    restore_industry.append(i_col)
            if empty_industry.__len__() > 0:
                x0_train_valid = np.delete(x0_train_valid, empty_industry, 1)
                x0_test_valid = np.delete(x0_test_valid, empty_industry, 1)
            if restore_industry.__len__() > 0:
                for i in np.arange(len(stock2industry)):
                    if stock2industry[i] - 1 in restore_industry:
                        y0_train[i] = y0_test[i]
                y0_train_isnan = np.isnan(y0_train)
                y0_train_isvalid = 1 - y0_train_isnan
                train_valid_rows = x0_isvalid * y0_train_isvalid
                x0_train_valid = x0[train_valid_rows == 1]
                y0_train_valid = y0_train[train_valid_rows == 1]
            if x0_train_valid.__len__() > 0:
                b = np.linalg.inv(x0_train_valid.T.dot(x0_train_valid)).dot(x0_train_valid.T).dot(y0_train_valid)
                residual = y0_test_valid - x0_test_valid.dot(b)  # 求残差
                residual_dict = dict(zip(test_valid_stock_list, residual))  # 将残差与股票代码关联起来
                residual_list.append(residual_dict)
                residual_date_list.append(factor_date_list[j])
        # 将残差list一次性转变为DataFrame
        neutralized_factor_df = pd.DataFrame(residual_list, index=residual_date_list)
        t2 = dt.datetime.now()
        print("neutralizing costs", t2 - t1)
        return neutralized_factor_df
    elif neutral_factor_set == {'size'}:
        t1 = dt.datetime.now()
        factor_start_line = list(mkt_cap_ard_df.index).index(factor_df.index[0])
        factor_end_line = list(mkt_cap_ard_df.index).index(factor_df.index[-1])
        # 要生成一个从factor_start_line 到 factor_end_line的自然数数列，前后双闭；range是前闭后开，因此区间后半部分要+1
        repeat_lines_list = list(range(factor_start_line, factor_end_line + 1))
        stock_col_num = stock_list.__len__()
        residual_list = []
        residual_date_list = []
        if repeat_lines_list.__len__() > 10000:
            division_multiplier = 1000
        elif repeat_lines_list.__len__() > 5000:
            division_multiplier = 500
        else:
            division_multiplier = 100
        for j, i_line in enumerate(repeat_lines_list):
            if j % division_multiplier == 0:
                print("factor neutralizing, {} / {} lines".format(j, list(factor_df.index).__len__()))
            y0_test = factor_array[j]
            y0_train = clean_factor_array[j]
            x0 = mkt_cap_ard_array[i_line]
            x0 = x0.reshape([stock_col_num, 1])
            y0_test_isnan = np.isnan(y0_test)
            y0_train_isnan = np.isnan(y0_train)
            x0_isnan = np.isnan(np.max(x0, axis=1))
            y0_test_isvalid = 1 - y0_test_isnan
            y0_train_isvalid = 1 - y0_train_isnan
            x0_isvalid = 1 - x0_isnan
            test_valid_rows = x0_isvalid * y0_test_isvalid
            test_valid_stock_list = [stock_list[i] for i in range(stock_list.__len__()) if test_valid_rows[i] == 1]
            x0_test_valid = x0[test_valid_rows == 1]
            y0_test_valid = y0_test[test_valid_rows == 1]
            train_valid_rows = x0_isvalid * y0_train_isvalid
            x0_train_valid = x0[train_valid_rows == 1]
            y0_train_valid = y0_train[train_valid_rows == 1]
            if x0_train_valid.__len__() > 0:
                b = np.linalg.inv(x0_train_valid.T.dot(x0_train_valid)).dot(x0_train_valid.T).dot(y0_train_valid)
                residual = y0_test_valid - x0_test_valid.dot(b)  # 求残差
                residual_dict = dict(zip(test_valid_stock_list, residual))  # 将残差与股票代码关联起来
                residual_list.append(residual_dict)
                residual_date_list.append(factor_date_list[j])
        # 将残差list一次性转变为DataFrame
        neutralized_factor_df = pd.DataFrame(residual_list, index=residual_date_list)
        t2 = dt.datetime.now()
        print("neutralizing costs", t2 - t1)
        return neutralized_factor_df


def equally_wt_fast_nav(stock_dict_input, trading_date_list, deal_price_df, close_price_df, stock_cost_rate):
    """等权重组合；不考虑对冲；在调仓日，新股票全部买入、旧股票全部卖出
    stock_dict_input的key是调仓日，value是股票代码的list
    """
    deal_price_df = deal_price_df.fillna(method='ffill')
    close_price_df = close_price_df.fillna(method='ffill')
    close_price_df = close_price_df.reindex(columns=deal_price_df.columns)

    stock_column_dict = {}
    for index, stock_code in enumerate(deal_price_df.columns):
        stock_column_dict.update({stock_code: index})

    buy_array = np.zeros((deal_price_df.shape[0], deal_price_df.shape[1]))  # 买入股票数量的array
    sell_array = np.zeros((deal_price_df.shape[0], deal_price_df.shape[1]))  # 卖出股票数量的array
    hold_array = np.zeros((deal_price_df.shape[0], deal_price_df.shape[1]))  # 不调仓股票数量的array
    diff_array = np.zeros((deal_price_df.shape[0], deal_price_df.shape[1]))  # 换仓股票数量的array
    net_sell_array = np.zeros((deal_price_df.shape[0], deal_price_df.shape[1]))  # 净卖股票数量的array
    eod_holding_array = np.zeros((deal_price_df.shape[0], deal_price_df.shape[1]))  # 日末持仓股票数量的array

    last_buy_day_row = None
    for i_row, i_date in enumerate(trading_date_list):
        if i_date in stock_dict_input.keys():
            if last_buy_day_row is not None:
                sell_array[i_row] = buy_array[last_buy_day_row]
            stock_list_to_buy_temp = stock_dict_input[i_date]
            weight_scalar = 1 / stock_list_to_buy_temp.__len__()
            for stock_code in stock_list_to_buy_temp:
                # 这里假设不知道要买多少股票，而是按 【1亿元 * weight / twap价格】算出全天的可成交量
                buy_array[i_row, stock_column_dict[stock_code]] = weight_scalar * 100000000 / deal_price_df.iat[
                    i_row, stock_column_dict[stock_code]]
            last_buy_day_row = i_row
            temp_diff_array = sell_array[i_row] - buy_array[i_row]  # 实际换仓的股票数量 （负为买入，正为卖出）
            temp_diff_array[np.isnan(temp_diff_array)] = 0
            diff_array[i_row] = temp_diff_array
            net_sell_array[i_row] = diff_array[i_row] * (diff_array[i_row] > 0)  # 净卖出的股票数量
            eod_holding_array[i_row] = buy_array[i_row]  # 日末持仓的股票数量
        else:
            if last_buy_day_row is not None:
                hold_array[i_row] = buy_array[last_buy_day_row]  # 不调仓的股票数量
                eod_holding_array[i_row] = hold_array[i_row]  # 日末持仓的股票数量

    buy_vol_df = pd.DataFrame(buy_array, deal_price_df.index, deal_price_df.columns)  # 买入股票数量的df
    hold_vol_df = pd.DataFrame(hold_array, deal_price_df.index, deal_price_df.columns)  # 不调仓股票数量的df
    sell_vol_df = pd.DataFrame(sell_array, deal_price_df.index, deal_price_df.columns)  # 卖出股票数量的df
    eod_holding_vol_df = pd.DataFrame(eod_holding_array, deal_price_df.index, deal_price_df.columns)
    net_sell_vol_df = pd.DataFrame(net_sell_array, deal_price_df.index, deal_price_df.columns)  # 净卖出股数

    hold_income_df = close_price_df - close_price_df.shift(1)
    hold_income_df = hold_income_df.fillna(0)  # 持仓股票的收益金额
    buy_income_df = close_price_df - deal_price_df  # 当天买入的股票的收益金额
    sell_income_df = deal_price_df - close_price_df.shift(1)
    sell_income_df = sell_income_df.fillna(0)  # 当天卖出股票的收益金额
    net_sell_amt_df = net_sell_vol_df * deal_price_df  # 当天净卖出的股票的交易额
    cost_df = net_sell_amt_df.mul(stock_cost_rate)  # 交易成本的金额 = 净卖出金额 * 交易成本费率
    eod_holding_amt_df = eod_holding_vol_df * close_price_df  # 日末持仓市值

    turnover_series = net_sell_amt_df.sum(axis=1) / eod_holding_amt_df.sum(axis=1).shift(1)
    avg_turnover_rate = np.nanmean(turnover_series)
    total_income_df = buy_vol_df * buy_income_df + hold_vol_df * hold_income_df + sell_vol_df * sell_income_df
    daily_income = total_income_df.sum(axis=1) - cost_df.sum(axis=1)
    cumsum_income = daily_income.cumsum() + 100000000
    nav = cumsum_income / 100000000
    annulized_return_rate = ((nav.values[-1]) - 1) / (nav.values.__len__() / 244)
    return nav, annulized_return_rate, avg_turnover_rate


def fast_long_short_nav(long_nav_series, short_nav_series):
    long_pct_chg_list = long_nav_series.diff()
    short_pct_chg_list = short_nav_series.diff()
    long_short_pct_chg = long_pct_chg_list - short_pct_chg_list
    long_short_pct_chg.iloc[0] = 0.0
    long_short_nav = np.cumsum(long_short_pct_chg) + 1
    long_short_nav = pd.Series(long_short_nav, index=long_short_nav.index)
    long_short_annualized_return = np.cumsum(long_short_nav.values)[-1] / (
            long_short_nav.__len__() / 244)
    return long_short_nav, long_short_annualized_return


def nav_series_annually_stat(nav_series, benchmark):
    """输入净值Series, index是日期（int），按年输出收益率（不满一年的不做年化处理）"""
    index_date = list(nav_series.index)
    date_year_list = [i // 10000 for i in index_date]
    year_list = list(set(date_year_list))
    year_list.sort()
    year_begin_idx = {}  # 记录每年首日在index_date中的位置索引
    year_idx = 0
    year_begin_idx.update({year_list[year_idx]: 0})
    year_end_idx = {}  # 记录每年末日在index_date中的位置索引
    for j, i_date in enumerate(date_year_list):
        if date_year_list[j] > year_list[year_idx]:
            year_end_idx.update({year_list[year_idx]: j - 1})
            year_idx += 1
            year_begin_idx.update({year_list[year_idx]: j})
        if j == date_year_list.__len__() - 1:
            year_end_idx.update({year_list[year_idx]: j})
    year_dates_count = {}  # 记录回测期间每年的交易日天数
    for i_year in year_begin_idx.keys():
        year_dates_count.update({i_year: year_end_idx[i_year] - year_begin_idx[i_year] + 1})
    return_each_year = {}
    return_each_year_daily = {}
    if year_dates_count[year_list[0]] < 30:  # 如果第1年的交易日小于30天，那么第1年的年化收益就没有计算的必要
        for j, i_year in enumerate(year_begin_idx.keys()):
            if j > 0:
                return_each_year.update(
                    {str(i_year) + "-" + benchmark: nav_series.iloc[year_end_idx[i_year]] -
                                                    nav_series.iloc[year_end_idx[i_year - 1]]})
                daily_return = (nav_series.iloc[year_end_idx[i_year]] - nav_series.iloc[year_end_idx[i_year - 1]]) / \
                               year_dates_count[i_year]
                daily_return = "%.2f%%" % (daily_return * 100)
                return_each_year_daily.update({str(i_year) + "-" + benchmark + "-daily": daily_return})
    else:
        for j, i_year in enumerate(year_begin_idx.keys()):
            if j == 0:
                return_each_year.update(
                    {str(i_year) + "-" + benchmark: nav_series.iloc[year_end_idx[i_year]] -
                                                    nav_series.iloc[year_begin_idx[i_year]]})
                daily_return = (nav_series.iloc[year_end_idx[i_year]] - nav_series.iloc[year_begin_idx[i_year]]) / \
                               year_dates_count[i_year]
                daily_return = "%.2f%%" % (daily_return * 100)
                return_each_year_daily.update({str(i_year) + "-" + benchmark + "-daily": daily_return})
            else:
                return_each_year.update(
                    {str(i_year) + "-" + benchmark: nav_series.iloc[year_end_idx[i_year]] -
                                                    nav_series.iloc[year_end_idx[i_year - 1]]})
                daily_return = (nav_series.iloc[year_end_idx[i_year]] - nav_series.iloc[year_end_idx[i_year - 1]]) / \
                               year_dates_count[i_year]
                daily_return = "%.2f%%" % (daily_return * 100)
                return_each_year_daily.update({str(i_year) + "-" + benchmark + "-daily": daily_return})
    return return_each_year, return_each_year_daily


def load_label(stock_list, start_date, end_date, label_type, holding_period, output_index_type='date_int',
               forward_shift=True):
    """
    注 -  forward_shift:  标签是否要向后shift一天
    """
    valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]  # 向后多取2天，以便后续如要向后shift有值
    if label_type == 'coda':
        price_df = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date,
                                             pv_type='twp_coda', adj_type='FORWARD')
        ans_df = price_df.shift(-holding_period) / price_df - 1  # 计算收益率
    elif label_type == 'vwap':
        data_df_amt = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date, pv_type='amt',
                                                adj_type='NONE')
        data_df_volume = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date,
                                                   pv_type='volume', adj_type='NONE')
        data_vwap = data_df_amt / data_df_volume  # 计算vwap
        adj_df = Dtk.get_panel_daily_info(stock_list, start_date, end_date, 'adjfactor')
        data_vwap = data_vwap * adj_df  # 计算后复权的vwap
        ans_df = data_vwap.shift(-holding_period) / data_vwap - 1  # 计算收益率
    elif label_type == 'twap':
        price_df = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date, pv_type='twap',
                                             adj_type='FORWARD')
        ans_df = price_df.shift(-holding_period) / price_df - 1  # 计算收益率
    elif label_type in ['twap_excess_300', 'twap_excess_500']:
        if label_type == 'twap_excess_300':
            benchmark = "000300.SH"
        else:
            benchmark = "000905.SH"
        price_df = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date, pv_type='twap',
                                             adj_type='FORWARD')
        benchmark_price_df = Dtk.get_panel_daily_pv_df([benchmark], start_date, valid_end_date, pv_type='twap')
        return_rate_df = price_df.shift(-holding_period) / price_df - 1
        return_rate_benchmark_df = benchmark_price_df.shift(-holding_period) / benchmark_price_df - 1
        ans_df = return_rate_df.sub(return_rate_benchmark_df[benchmark], axis=0)
    elif label_type in ['twap_ir_300', 'twap_ir_500']:
        # information ratio; 因需要计算标准差, 故不建议holding_period太短
        if holding_period <= 2:
            raise Exception('A holding_period of {} is not enough for calculating std'.format(holding_period))
        if label_type == 'twap_ir_300':
            benchmark = "000300.SH"
        else:
            benchmark = "000905.SH"
        price_df = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date, pv_type='twap',
                                             adj_type='FORWARD')
        benchmark_price_df = Dtk.get_panel_daily_pv_df([benchmark], start_date, valid_end_date, pv_type='twap')
        # 计算holding_period的超额收益率
        return_rate_hp_df = price_df.shift(-holding_period) / price_df - 1
        return_rate_benchmark_hp_df = benchmark_price_df.shift(-holding_period) / benchmark_price_df - 1
        excess_return_hp_df = return_rate_hp_df.sub(return_rate_benchmark_hp_df[benchmark], axis=0)
        # 计算1天的超额收益率，用于std计算需要
        return_rate_1d_df = price_df.shift(-1) / price_df - 1
        return_rate_benchmark_1d_df = benchmark_price_df.shift(-1) / benchmark_price_df - 1
        excess_return_1d_df = return_rate_1d_df.sub(return_rate_benchmark_1d_df[benchmark], axis=0)
        excess_return_1d_std = excess_return_1d_df.rolling(min_periods=holding_period, window=holding_period).std()
        # 计算information ratio
        ans_df = excess_return_hp_df / excess_return_1d_std.shift(-holding_period)
    elif label_type == 'max_daily_twap':
        # 最大涨速
        data_df_twap = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date, pv_type='twap',
                                                 adj_type='FORWARD')
        return_rate_df = data_df_twap.shift(-1) / data_df_twap - 1
        for i in range(2, holding_period + 1):
            return_rate_df = np.maximum(return_rate_df, (data_df_twap.shift(-i) / data_df_twap - 1) / i)
        ans_df = return_rate_df
    elif label_type == 'twap_excess_median':
        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        price_df = Dtk.get_panel_daily_pv_df(stock_list, start_date, valid_end_date, pv_type='twap', adj_type='FORWARD')
        return_rate_df = price_df.shift(-holding_period) / price_df - 1
        return_rate_median = return_rate_df.median(axis=1)
        ans_df = return_rate_df.sub(return_rate_median, axis=0)
    elif label_type == 'twap_excess_ind_median':
        def get_ind_mean(series: pd.Series):
            ans = []
            for index, day in enumerate(series.index):
                if str(series.iloc[index]) != 'nan':
                    ans.append(ret_ind_mean_daily[day][series.iloc[index]])
                else:
                    ans.append(np.nan)
            return ans

        def get_ind_std(series: pd.Series):
            ans = []
            for index, day in enumerate(series.index):
                if str(series.iloc[index]) != 'nan':
                    ans.append(ret_ind_std_daily[day][series.iloc[index]])
                else:
                    ans.append(np.nan)
            return ans

        valid_end_date = Dtk.get_n_days_off(end_date, holding_period + 2)[-1]
        complete_stock_list = Dtk.get_complete_stock_list()
        price_df = Dtk.get_panel_daily_pv_df(complete_stock_list, start_date, valid_end_date, pv_type='twap',
                                             adj_type='FORWARD')
        return_rate_df = price_df.shift(-holding_period) / price_df - 1
        ind = Dtk.get_panel_daily_info(complete_stock_list, start_date, valid_end_date, info_type='industry3')
        ind_names = [item for item in np.arange(1, 32, 1)]
        ret_ind_mean_daily = {}
        ret_ind_std_daily = {}
        for day in return_rate_df.index:
            ret_ind_mean = {}
            ret_ind_std = {}
            temp = return_rate_df.loc[day]
            ind_data = ind.loc[day]
            for ind_name in ind_names:
                ret_ind = temp[ind_data.values == ind_name]
                ret_ind_mean.update({ind_name: ret_ind.mean()})
                ret_ind_std.update({ind_name: ret_ind.std()})
            ret_ind_mean_daily.update({day: ret_ind_mean})
            ret_ind_std_daily.update({day: ret_ind_std})
        ret_mean_ind_df = ind.apply(get_ind_mean)
        ret_std_ind_df = ind.apply(get_ind_std)
        ans_df = (return_rate_df - ret_mean_ind_df) / ret_std_ind_df
        ans_df = ans_df.loc[start_date:end_date]
        ans_df = Dtk.convert_df_index_type(ans_df, 'date_int', 'timestamp')
        return ans_df


    else:
        raise TypeError
    if forward_shift:
        ans_df = ans_df.shift(-1)
    ans_df = ans_df.loc[start_date: end_date]
    if output_index_type == 'timestamp':
        # factor的index是timestamp, 而非8位数的日期，这里做转化，以便后续可比
        ans_df = Dtk.convert_df_index_type(ans_df, 'date_int', 'timestamp')
    return ans_df


def calc_group_rank(list_input):
    rank_a = sorted(range(len(list_input)), key=list_input.__getitem__)
    rank_b = rank_a.copy()
    rank_b.sort()
    rank_coef = np.corrcoef(rank_a, rank_b)[0, 1]
    return rank_coef


def df_train_valid_split(df_input, valid_ratio, seed=2019, tail_for_valid=False, train_valid_interval=None,
                         double_index=True):
    if double_index:
        index_l1 = df_input.index.get_level_values(level=0)
        index_l1 = sorted(set(index_l1))  # 排序后的交易日列表
        index_len = index_l1.__len__()
        valid_num = int(index_len * valid_ratio)
        if tail_for_valid:
            # 取尾部valid_ratio作为验证集；seed不起作用
            valid_idx = list(range(index_len - valid_num - 1, index_len))
            full_idx = list(range(index_len))
            train_idx = list(set(full_idx) - set(valid_idx))
            # 若训练集和验证集还要有间隔
            if train_valid_interval is not None:
                valid_idx = valid_idx[train_valid_interval:]
        else:
            # 在训练集上随机均匀地抽取验证集，抽取比例=valid_ratio
            # train_valid_interval不起作用
            np.random.seed(seed)
            valid_idx = np.random.randint(0, index_len, size=(1, valid_num))
            valid_idx = list(valid_idx[0])
            valid_idx.sort()
            full_idx = list(range(index_len))
            train_idx = list(set(full_idx) - set(valid_idx))
        valid_date = [index_l1[x] for x in valid_idx]
        train_date = [index_l1[x] for x in train_idx]
        valid_date.sort()
        df_valid = df_input.loc[valid_date]
        train_date.sort()
        df_train = df_input.loc[train_date]
        output_valid = df_valid.copy()
        output_train = df_train.copy()
        return output_train, output_valid
    else:
        raise TypeError


def shuffle_n_split_df(df_input, fold_num, random_seed=2019, double_index=True):
    if double_index:
        # 将输入的df_input随机分成不互相重叠的fold_num份
        np.random.seed(random_seed)
        index_l1 = df_input.index.get_level_values(level=0)
        index_l1 = sorted(set(index_l1))  # 排序后的交易日列表
        index_len = index_l1.__len__()
        idx_list = list(range(index_len))
        np.random.shuffle(idx_list)  # 将索引list乱序
        while divmod(idx_list.__len__(), fold_num)[1] != 0:
            idx_list.pop(-1)
        idx_list2 = np.array(idx_list)
        idx_list3 = np.split(idx_list2, fold_num)  # 将索引列表分成fold_num份
        df_output_list = []
        for i in range(fold_num):
            days_idx = [index_l1[x] for x in idx_list3[i]]
            days_idx.sort()
            temp_df = df_input.loc[days_idx].copy()
            df_output_list.append(temp_df)
        return df_output_list
    else:
        raise TypeError


def shuffle_n_sample_df(df_input, fold_num, pct, random_seed=2019, double_index=True):
    # 从输入的df_input随机抽取fold_num次样本，每份样本占总数的比例为pct；样本间可以有重叠
    if double_index:
        np.random.seed(random_seed)
        index_l1 = df_input.index.get_level_values(level=0)
        index_l1 = sorted(set(index_l1))  # 排序后的交易日列表
        index_len = index_l1.__len__()
        idx_list = list(range(index_len))
        sample_len = int(index_len * pct)  # 每次取出的样本的长度
        sample_df_output_list = []
        for _ in range(fold_num):
            np.random.shuffle(idx_list)  # 再次乱序
            sample_idx_list = idx_list[:sample_len]
            days_list = [index_l1[x] for x in sample_idx_list]
            temp_df = df_input.loc[days_list].copy()
            sample_df_output_list.append(temp_df)
        return sample_df_output_list
    else:
        raise TypeError


def fillna_with_industry_median(raw_factor_df, ind_df):
    # 用当天的行业中位数填充因子中遇到的nan值
    # 算法原理是：
    #     计算31个行业的因子值的中位数，构造31个矩阵，每个矩阵都先用行业中位数填充所有的nan值，再将非本行业的股票的值
    #     设为0；再将上述31个矩阵直接叠加；最后再 * ind_df / ind_df，使得没有行业的股票的值为nan.
    # univ_df = Dtk.convert_df_index_type(univ_df, 'date_int', 'timestamp')
    ind_df = Dtk.convert_df_index_type(ind_df, 'date_int', 'timestamp')
    factor_df_na_filled = raw_factor_df.copy()
    factor_df_na_filled[:] = 0
    for i in range(1, 32):
        # a matrix full of True/False
        i_industry_df = pd.DataFrame(ind_df.values == i, index=ind_df.index, columns=ind_df.columns)
        # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
        factor_ind_i = raw_factor_df * i_industry_df / i_industry_df
        # 计算本行业的因子值的中位数
        factor_ind_i_median = factor_ind_i.median(axis=1)
        # 将形状为(n, )的series的形状转为(n, 1)
        factor_ind_i_median_reshaped = np.reshape(factor_ind_i_median.values, (factor_ind_i_median.__len__(), 1))
        # 把本行业的中位数的series拓展为矩阵
        factor_ind_i_median_matrix = pd.DataFrame(
            np.tile(factor_ind_i_median_reshaped, [1, raw_factor_df.shape[1]]),
            index=raw_factor_df.index, columns=raw_factor_df.columns)
        # 用行业中位数填充所有的NaN
        factor_ind_i[np.isnan] = factor_ind_i_median_matrix
        # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
        factor_ind_i = factor_ind_i * i_industry_df / i_industry_df
        # 如是本行业的、则值为因子值，如不是本行业的、值为0
        factor_ind_i = factor_ind_i.fillna(0)
        factor_df_na_filled = factor_df_na_filled + factor_ind_i
    # 再以industry_df过滤，若没有行业的股票值为nan
    factor_df_na_filled = factor_df_na_filled * ind_df / ind_df
    # 再以universe_df过滤，若universe不为1的股票值为nan
    # factor_df_na_filled = factor_df_na_filled * univ_df / univ_df
    return factor_df_na_filled


def fillna_with_industry_median2(limit_status, raw_factor_df, ind_df):
    # 用当天的行业中位数填充因子中遇到的nan值
    # 算法原理是：
    #     计算31个行业的因子值的中位数，构造31个矩阵，每个矩阵都先用行业中位数填充所有的nan值，再将非本行业的股票的值
    #     设为0；再将上述31个矩阵直接叠加；最后再 * ind_df / ind_df，使得没有行业的股票的值为nan.
    # univ_df = Dtk.convert_df_index_type(univ_df, 'date_int', 'timestamp')
    clean_factor_df = raw_factor_df * limit_status / limit_status
    ind_df = Dtk.convert_df_index_type(ind_df, 'date_int', 'timestamp')
    factor_df_na_filled = raw_factor_df.copy()
    factor_df_na_filled[:] = 0
    for i in range(1, 32):
        i_industry_df = ind_df == i  # a matrix full of True/False
        # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
        clean_factor_ind_i = clean_factor_df * i_industry_df / i_industry_df
        factor_ind_i = raw_factor_df * i_industry_df / i_industry_df
        # 计算本行业的因子值的中位数
        factor_ind_i_median = clean_factor_ind_i.median(axis=1)
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
        factor_ind_i = factor_ind_i.fillna(0)
        factor_df_na_filled = factor_df_na_filled + factor_ind_i
    # 再以industry_df过滤，若没有行业的股票值为nan
    factor_df_na_filled = factor_df_na_filled * ind_df / ind_df
    # 再以universe_df过滤，若universe不为1的股票值为nan
    # factor_df_na_filled = factor_df_na_filled * univ_df / univ_df
    return factor_df_na_filled


def signal_combine(start_date, end_date, signal_name, model_address):
    trading_day = Dtk.get_trading_day(start_date, end_date)
    result = {}
    for date in trading_day:
        with open(model_address + '/SignalFile' + '/signal_' + str(date) + '.pickle', 'rb') as f:
            temp = pickle.load(f)
        result.update({date: temp})
    with open(model_address + '/' + signal_name + '.pickle', 'wb') as f:
        pickle.dump(result, f)
    print(signal_name + ' making successfully')


def intraday_equally_wt_fast_nav(stock_dict_input, trading_date_list, buy_price_df, sell_price_df, close_price_df,
                                 intraday_buyable_df, intraday_sellable_df, stock_cost_rate):
    """
    按照一个亿金额等权重组合；
    买入卖出的时候考虑最大可买入量和最大可卖出量；
    注意：在计算收益的时候分母使用一个亿资金， 与实际情况有所偏差
    stock_dict_input的key是调仓日，value是股票代码的list
    考虑了停牌的股票不参与top池分配  涨停的股票无法买入  跌停的股票无法卖出
    """
    buy_price_df = buy_price_df.fillna(method='ffill')
    sell_price_df = sell_price_df.fillna(method='ffill')
    close_price_df = close_price_df.fillna(method='ffill')
    close_price_df = close_price_df.reindex(columns=buy_price_df.columns)
    intraday_sellable_df = intraday_sellable_df.reindex(index=buy_price_df.index, columns=buy_price_df.columns)
    intraday_buyable_df = intraday_buyable_df.reindex(index=buy_price_df.index, columns=buy_price_df.columns)
    sellable_array = intraday_sellable_df.values
    buyable_array = intraday_buyable_df.values

    stock_column_dict = {}
    for index, stock_code in enumerate(buy_price_df.columns):
        stock_column_dict.update({stock_code: index})

    buy_array = np.zeros((buy_price_df.shape[0], buy_price_df.shape[1]))  # 买入股票数量的array
    sell_array = np.zeros((buy_price_df.shape[0], buy_price_df.shape[1]))  # 卖出股票数量的array
    hold_array = np.zeros((buy_price_df.shape[0], buy_price_df.shape[1]))  # 不调仓股票数量的array
    net_sell_array = np.zeros((buy_price_df.shape[0], buy_price_df.shape[1]))  # 净卖股票数量的array
    net_buy_array = np.zeros((buy_price_df.shape[0], buy_price_df.shape[1]))  # 净买股票数量的array
    eod_holding_array = np.zeros((buy_price_df.shape[0], buy_price_df.shape[1]))  # 日末持仓股票数量的array

    last_buy_day_row = None
    for i_row, i_date in enumerate(trading_date_list):
        if i_date in stock_dict_input.keys():
            if last_buy_day_row is not None:
                sell_array[i_row] = eod_holding_array[last_buy_day_row]
            stock_list_to_buy_temp = stock_dict_input[i_date]
            weight_scalar = 1 / stock_list_to_buy_temp.__len__()
            for stock_code in stock_list_to_buy_temp:
                # 这里假设不知道要买多少股票，而是按 【1亿元 * weight / twap价格】算出全天的可成交量
                # 今日理论应该持股票以及数量
                buy_array[i_row, stock_column_dict[stock_code]] = weight_scalar * 100000000 / buy_price_df.iat[
                    i_row, stock_column_dict[stock_code]]
            temp_diff_array = sell_array[i_row] - buy_array[i_row]  # 换仓的股票数量 （负为买入，正为卖出）
            temp_diff_array[np.isnan(temp_diff_array)] = 0
            # 今日实际可买入股票及其数量
            temp_buy = np.array([min(i, j) for i, j in zip(buyable_array[i_row], -temp_diff_array)])
            net_buy_array[i_row] = (temp_diff_array < 0) * temp_buy
            # 今日实际可卖出股票及其数量
            temp_sell = np.array([min(i, j) for i, j in zip(sellable_array[i_row], temp_diff_array)])
            net_sell_array[i_row] = (temp_diff_array > 0) * temp_sell
            if last_buy_day_row is not None:
                eod_holding_array[i_row] = eod_holding_array[last_buy_day_row] + net_buy_array[i_row] \
                                           - net_sell_array[i_row]  # 日末持仓的股票数量
                # 不调仓股票及其数量
                hold_array[i_row] = np.array(
                    [min(i, j) for i, j in zip(eod_holding_array[i_row], eod_holding_array[last_buy_day_row])])
            else:
                eod_holding_array[i_row] = net_buy_array[i_row] - net_sell_array[i_row]
            last_buy_day_row = i_row
        else:
            if last_buy_day_row is not None:
                hold_array[i_row] = eod_holding_array[last_buy_day_row]  # 不调仓的股票数量
                eod_holding_array[i_row] = hold_array[i_row]  # 日末持仓的股票数量

    buy_vol_df = pd.DataFrame(net_buy_array, buy_price_df.index, buy_price_df.columns)  # 买入股票数量的df
    hold_vol_df = pd.DataFrame(hold_array, buy_price_df.index, buy_price_df.columns)  # 不调仓股票数量的df
    sell_vol_df = pd.DataFrame(net_sell_array, buy_price_df.index, buy_price_df.columns)  # 卖出股票数量的df
    eod_holding_vol_df = pd.DataFrame(eod_holding_array, buy_price_df.index, buy_price_df.columns)

    hold_income_df = close_price_df - close_price_df.shift(1)
    hold_income_df = hold_income_df.fillna(0)  # 持仓股票的收益金额
    buy_income_df = close_price_df - buy_price_df  # 当天买入的股票的收益金额
    buy_income_df = buy_income_df.fillna(0)
    sell_income_df = sell_price_df - close_price_df.shift(1)
    sell_income_df = sell_income_df.fillna(0)  # 当天卖出股票的收益金额
    sell_amt_df = sell_vol_df * sell_price_df  # 当天净卖出的股票的交易额
    cost_df = sell_amt_df.mul(stock_cost_rate)  # 交易成本的金额 = 净卖出金额 * 交易成本费率
    eod_holding_amt_df = eod_holding_vol_df * close_price_df  # 日末持仓市值

    turnover_series = sell_amt_df.sum(axis=1) / eod_holding_amt_df.sum(axis=1).shift(1)
    avg_turnover_rate = np.nanmean(turnover_series)
    total_income_df = buy_vol_df * buy_income_df + hold_vol_df * hold_income_df + sell_vol_df * sell_income_df
    daily_income = total_income_df.sum(axis=1) - cost_df.sum(axis=1)
    cumsum_income = daily_income.cumsum() + 100000000
    nav = cumsum_income / 100000000
    annulized_return_rate = ((nav.values[-1]) - 1) / (nav.values.__len__() / 244)
    return nav, annulized_return_rate, avg_turnover_rate


def fix_time_signal_combine(start_date, end_date, signal_name, fix_time_mat, model_address):
    trading_day = Dtk.get_trading_day(start_date, end_date)
    result = {}
    for date in trading_day:
        temp = {}
        for fix_time in fix_time_mat:
            if signal_name[-3:] != 'Con':
                temp_address = model_address + '/' + str(fix_time) + '/' + 'Model_File_' + signal_name[7:] + '_' + str(fix_time) + '/SignalFile' + '/signal_' + str(date) + '.pickle'
            else:
                temp_address = model_address + 'Con/' + 'Model_File_' + signal_name[7:] + '/SignalFile/' + str(fix_time) + '/signal_' + str(date) + '.pickle'
            with open(temp_address, 'rb') as f:
                temp2 = pickle.load(f)
            temp.update(temp2)
        result.update({date: temp})
    if not os.path.exists(model_address + '/2400/' + 'Model_File_' + signal_name[7:]):
        os.makedirs(model_address + '/2400/' + 'Model_File_' + signal_name[7:])
    with open(model_address + '/2400/' + 'Model_File_' + signal_name[7:] + '/' + signal_name + '.pickle', 'wb') as f:
        pickle.dump(result, f)
    print(signal_name + ' combining successfully')


def factor_neutralizer_new(factor_df, industry_df, mkt_cap_ard_df):
    """
    注释 - neutral_regressor_backward_shift: 中性化因子（行业、市值）是否要取前一天的
    """
    # 确保industry和mkt_cap_ard与factor_df的index一致，这样才能正确回归
    stock_list = list(factor_df.columns)
    factor_date_list = list(factor_df.index)
    industry_df = industry_df.reindex(factor_df.index)
    mkt_cap_ard_df = mkt_cap_ard_df.reindex(factor_df.index)

    t1 = dt.datetime.now()
    factor_start_line = list(mkt_cap_ard_df.index).index(factor_df.index[0])
    factor_end_line = list(mkt_cap_ard_df.index).index(factor_df.index[-1])
    # 要生成一个从factor_start_line 到 factor_end_line的自然数数列，前后双闭；range是前闭后开，因此区间后半部分要+1
    repeat_lines_list = list(range(factor_start_line, factor_end_line + 1))
    factor_array = factor_df.values
    industry_df2 = industry_df.fillna(0)  # 将行业的缺失值替换为0，以方便后续用np创造one_hot矩阵
    industry_array = industry_df2.values
    mkt_cap_ard_array = mkt_cap_ard_df.values
    stock_col_num = stock_list.__len__()
    residual_list = []
    residual_date_list = []
    if repeat_lines_list.__len__() > 10000:
        division_multiplier = 1000
    elif repeat_lines_list.__len__() > 5000:
        division_multiplier = 500
    else:
        division_multiplier = 100
    for j, i_line in enumerate(repeat_lines_list):
        # if j % division_multiplier == 0:
            # print("factor neutralizing, {} / {} lines".format(j, list(factor_df.index).__len__()))
        y0 = factor_array[j]
        x1_0 = industry_array[i_line].astype(np.int)
        x1_0 = make_one_hot(x1_0)  # 构造one_hot矩阵
        x1_0 = x1_0[:, 1:]  # 去掉第0列，也就是去掉原来无行业的值
        x2_0 = mkt_cap_ard_array[i_line]
        x2_0 = x2_0.reshape([stock_col_num, 1])
        x0 = np.hstack([x1_0, x2_0])
        y0_isnan = np.isnan(y0)
        x0_isnan = np.isnan(np.max(x0, axis=1))
        y0_isvalid = 1 - y0_isnan
        x0_isvalid = 1 - x0_isnan
        valid_rows = x0_isvalid * y0_isvalid
        valid_stock_list = [stock_list[i] for i in range(stock_list.__len__()) if valid_rows[i] == 1]
        x0_valid = x0[valid_rows == 1]
        y0_valid = y0[valid_rows == 1]
        ind_check = np.sum(x0_valid, axis=0)
        empty_industry = []
        for i_col in range(x1_0.shape[1]):
            if ind_check[i_col] < 1:
                empty_industry.append(i_col)
        if empty_industry.__len__() > 0:
            x0_valid = np.delete(x0_valid, empty_industry, 1)
        if x0_valid.__len__() > 0:
            b = np.linalg.inv(x0_valid.T.dot(x0_valid)).dot(x0_valid.T).dot(y0_valid)
            residual = y0_valid - x0_valid.dot(b)  # 求残差
            residual_dict = dict(zip(valid_stock_list, residual))  # 将残差与股票代码关联起来
            residual_list.append(residual_dict)
            residual_date_list.append(factor_date_list[j])
        # 将残差list一次性转变为DataFrame
    neutralized_factor_df = pd.DataFrame(residual_list, index=residual_date_list)
    t2 = dt.datetime.now()
    print("neutralizing costs", t2 - t1)
    return neutralized_factor_df


def fillna_with_industry_median_new(raw_factor_df, ind_df):
    # 用当天的行业中位数填充因子中遇到的nan值
    # 算法原理是：
    #     计算31个行业的因子值的中位数，构造31个矩阵，每个矩阵都先用行业中位数填充所有的nan值，再将非本行业的股票的值
    #     设为0；再将上述31个矩阵直接叠加；最后再 * ind_df / ind_df，使得没有行业的股票的值为nan.
    ind_df = ind_df.reindex(raw_factor_df.index)
    raw_factor_np = raw_factor_df.values
    factor_df_na_filled = np.zeros(raw_factor_np.shape)
    ind_np = ind_df.values
    for i in range(1, 32):
        i_industry = ind_np == i  # a matrix full of True/False
        # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
        factor_ind_i = raw_factor_np * i_industry / i_industry
        # 计算本行业的因子值的中位数
        factor_ind_i_median = np.nanmedian(factor_ind_i, axis=1).T
        # 把本行业的中位数的series拓展为矩阵
        factor_ind_i_median_matrix = np.tile(factor_ind_i_median, [ind_np.shape[1],1]).T
        # 用行业中位数填充所有的NaN
        factor_ind_i[np.isnan(factor_ind_i)] = factor_ind_i_median_matrix[np.isnan(factor_ind_i)]
        # 如是本行业的、则值为因子值，如不是本行业的、值为NaN
        factor_ind_i = factor_ind_i * i_industry / i_industry
        # 如是本行业的、则值为因子值，如不是本行业的、值为0
        factor_ind_i[np.isnan(factor_ind_i)] = 0
        factor_df_na_filled = factor_df_na_filled + factor_ind_i
    # 再以industry_df过滤，若没有行业的股票值为nan
    factor_df_na_filled = factor_df_na_filled * ind_np / ind_np
    ans_df = pd.DataFrame(factor_df_na_filled, index=raw_factor_df.index, columns=raw_factor_df.columns)
    # 再以universe_df过滤，若universe不为1的股票值为nan
    # factor_df_na_filled = factor_df_na_filled * univ_df / univ_df
    return ans_df


def fix_time_signal_combine_wcx(start_date, end_date, signal_name, fix_time_mat, model_address):
    trading_day = Dtk.get_trading_day(start_date, end_date)

    result = {}
    for date in trading_day:
        temp = {}
        for fix_time in fix_time_mat:
            with open(model_address + '/' + str(fix_time) + '/' + 'Model_File_' + signal_name[7:] + '_' + str(fix_time) +'/signal_' + signal_name[7:] + '_'+str(fix_time) + '.pickle', 'rb') as f:
                data = pickle.load(f)
                temp2 =data[date]
            temp.update(temp2)
        result.update({date: temp})
    for ii in range(0,len(fix_time_mat)):
       if ii==0:
            file_name=str(fix_time_mat[ii])
       else:
            file_name=file_name+'_'+str(fix_time_mat[ii])

    if len(fix_time_mat) ==1:
        file_name=str(fix_time_mat[0])+'_'+str(fix_time_mat[-1])

    if not os.path.exists(model_address + '/2400/' + 'Model_File_' + signal_name[7:]+ "_" + file_name):
        os.makedirs(model_address + '/2400/' + 'Model_File_' + signal_name[7:]+ "_" + file_name)
    with open(model_address + '/2400/' + 'Model_File_' + signal_name[7:] +"_" + file_name+'/' + signal_name + '.pickle', 'wb') as f:
        pickle.dump(result, f)
    print(signal_name + ' combining successfully')


def outlier_filter_for_label(value_df,scale = 5):
    """
    本函数以MAD的方式去除极端值
    """
    # 在20160104和20160107这两天，全市场熔断，那么先删除全市场都是nan的数据
    value_df_raw = value_df.copy()
    diversion_series = value_df.apply(lambda x:len(np.unique(x.dropna())),axis=1)/value_df.count(axis=1)

    factor_max = value_df.max(axis=1)
    # factor_max = factor_max.dropna()
    value_df = value_df.reindex(factor_max.index)
    factor_median = value_df.median(axis=1)
    factor_deviation_from_median = value_df.sub(factor_median, axis=0)
    factor_deviation_from_median[pd.DataFrame(factor_deviation_from_median.values==0,index = factor_deviation_from_median.index,columns = factor_deviation_from_median.columns)] = np.nan
    factor_mad = factor_deviation_from_median.abs().median(axis=1)

    lower_limit = factor_median - scale* factor_mad
    upper_limit = factor_median + scale * factor_mad
    lower_limit = lower_limit.fillna(method='ffill')
    upper_limit = upper_limit.fillna(method='ffill')

    lower_limit_plus1 = factor_median - (scale+1)* factor_mad
    upper_limit_plus1 = factor_median + (scale+1) * factor_mad
    lower_limit_plus1 = lower_limit_plus1.fillna(method='ffill')
    upper_limit_plus1 = upper_limit_plus1.fillna(method='ffill')

    lower_limit_plus2 = factor_median - (scale+2)* factor_mad
    upper_limit_plus2 = factor_median + (scale+2) * factor_mad
    lower_limit_plus2 = lower_limit_plus2.fillna(method='ffill')
    upper_limit_plus2 = upper_limit_plus2.fillna(method='ffill')

    extreme_count = (value_df.sub(upper_limit,axis=0)>0)|(value_df.sub(lower_limit,axis=0)<0)
    extreme_count = extreme_count.sum(axis=1)
    nan_count = value_df.count(axis=1)
    extreme_rate = extreme_count/nan_count

    value_df[((diversion_series>0.1)&(diversion_series<=1))==False] = value_df_raw[((diversion_series>0.1)&(diversion_series<=1))==False]
    value_df[(((diversion_series>0.1)&(diversion_series<=1))==True)&(extreme_rate<=0.1)] =  value_df.clip_lower(lower_limit, axis='index').clip_upper(upper_limit, axis='index')[(((diversion_series>0.1)&(diversion_series<=1))==True)&(extreme_rate<=0.1)]
    value_df[(((diversion_series>0.1)&(diversion_series<=1))==True)&(extreme_rate>0.1)&(extreme_rate<=0.2)] =  value_df.clip_lower(lower_limit_plus1, axis='index').clip_upper(upper_limit_plus1, axis='index')[(((diversion_series>0.1)&(diversion_series<=1))==True)&(extreme_rate>0.1)&(extreme_rate<=0.2)]
    value_df[(((diversion_series>0.1)&(diversion_series<=1))==True)&(extreme_rate>0.2)] =  value_df.clip_lower(lower_limit_plus2, axis='index').clip_upper(upper_limit_plus2, axis='index')[(((diversion_series>0.1)&(diversion_series<=1))==True)&(extreme_rate>0.2)]
    return value_df


def fillna_with_industry_mean_forlabel(raw_factor_df, ind_df):
    # 用当天的行业中位数填充因子中遇到的nan值
    # 算法原理是：
    #     计算31个行业的因子值的中位数，构造31个矩阵，每个矩阵都先用行业中位数填充所有的nan值，再将非本行业的股票的值
    #     设为0；再将上述31个矩阵直接叠加；最后再 * ind_df / ind_df，使得没有行业的股票的值为nan.
    factor_df_na_filled = raw_factor_df.copy()
    factor_df_na_filled[:] = 0
    for i in np.unique(ind_df.stack().dropna().values).tolist():
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
        factor_ind_i[pd.DataFrame(i_industry_df.values==False,index = i_industry_df.index,columns = i_industry_df.columns)]=0
        factor_df_na_filled = factor_df_na_filled + factor_ind_i
    # 再以industry_df过滤，若没有行业的股票值为nan
    # factor_df_na_filled = factor_df_na_filled * ind_df / ind_df
    factor_df_na_filled[pd.DataFrame(np.isnan(ind_df.values),index=  ind_df.index,columns=ind_df.columns)] = np.nan
    # 再以universe_df过滤，若universe不为1的股票值为nan
    # factor_df_na_filled = factor_df_na_filled * univ_df / univ_df
    return factor_df_na_filled


def neutralizer_for_label(factor_df,mkt_cap_ard_df,industry_df):
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
