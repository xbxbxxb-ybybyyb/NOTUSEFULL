# _*_ coding:utf-8 _*_
import threading
from xquant.utils import utils_set_timeout
from .db import DML_mysql
from .factorenum import *
from .source_table_config import *
import pandas as pd
import numpy as np
import time
import datetime as dt
import sys
from xquant.setXquantEnv import xquantEnv, testEnv

# 实例化连接池与数据访问层类
dml = DML_mysql('xquant_data')

dml2 = DML_mysql('xquant_wind')

dml3 = DML_mysql('xquant_gogoal')

# factor_vip
if xquantEnv == 0:
    dml_factor_vip = DML_mysql('user2')
elif xquantEnv == 1:
    dml_factor_vip = dml
else:
    raise Exception("dml_factor_vip error!")


def _handle_params(trading_codes=None, date_list=None, factor_list=None):
    """
    处理股票代码、日期、因子参数的格式
    :param trading_codes: 股票代码(string)或股票列表(list)
    :param date_list: 日期(string、int)或日期列表(list)
    :param factor_list: 因子(string)或因子列表(list)
    :return: 参数字典(dict)
    """
    params_dict = {}
    # 股票代码
    if trading_codes:
        if isinstance(trading_codes, str):
            code_style = '='
            stock_codes = "'" + trading_codes + "'"
            trading_codes = [trading_codes]
            params_dict['trading_codes'] = [trading_codes, stock_codes, code_style]
        elif isinstance(trading_codes, list):
            trading_codes = list(set(trading_codes))
            if len(trading_codes) == 1:
                code_style = '='
                stock_codes = "'" + trading_codes[0] + "'"
            else:
                code_style = 'in'
                stock_codes = tuple(trading_codes)
            params_dict['trading_codes'] = [trading_codes, stock_codes, code_style]
        else:
            raise Exception("trading_codes 为股票代码(string)，或股票代码列表(list) ! ")
    # 日期
    if date_list:
        if isinstance(date_list, int):
            date_list = str(date_list)
            date_style = '='
            dates = "'" + date_list + "'"
            date_list = [date_list]
            params_dict['date_list'] = [date_list, dates, date_style]
        elif isinstance(date_list, str):
            date_style = '='
            dates = "'" + date_list + "'"
            date_list = [date_list]
            params_dict['date_list'] = [date_list, dates, date_style]
        elif isinstance(date_list, list):
            date_list = [str(date) if isinstance(date, int) else date for date in date_list]
            date_list = list(set(date_list))
            if len(date_list) == 1:
                dates = date_list[0]
                date_style = '='
            else:
                date_style = 'in'
                dates = tuple(date_list)
            params_dict['date_list'] = [date_list, dates, date_style]
        else:
            raise Exception("date_list 为单个日期(string or int)，或日期列表(list) ! ")
    # 因子
    if factor_list:
        if isinstance(factor_list, str):
            factor_list = [factor_list]
        elif isinstance(factor_list, list):
            factor_list = factor_list
            # factor_list = list(set(factor_list))
        else:
            raise Exception("factor_list 为单个因子(string)，或多个因子的列表(list) ! ")
        fields = ""
        for factor in factor_list:
            fields += factor + ','
        fields = fields[:-1]
        params_dict['factor_list'] = [factor_list, fields]

    return params_dict


def get_market_price(trading_codes, date_list, factor_list, fill_na=True):
    """
    获取行情数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:索引为[日期,股票] 的MultiIndex DataFrame
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]
    fields = params_dict['factor_list'][1]
    sql_use = "select tdate,tradingcode,{0} from factor_d_marketindex " \
              "where tdate {1} {2} and tradingcode {3} {4}".format(fields, date_style, dates, code_style, stock_codes)
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    df_result[df_result.isnull()] = np.NAN
    return df_result


def get_factor_idct(trading_codes, date_list, factor_list, fill_na=True):
    """
    获取估值因子风险因子的因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return: 索引为[日期,股票] 的MultiIndex DataFrame
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]

    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_valuationmetricsindex", "factor_d_riskanalysisindex"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_factor_idct(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                   f_table[tb], tb, fill_na)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_factor_idct(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates, field_list, tb,
                     fill_na):
    fields = ""
    for factor in field_list:
        fields += factor + ','
    fields = fields[:-1]
    sql_use = "select tdate,tradingcode,{0} from {5} " \
              "where tdate {1} {2} and tradingcode {3} {4}".format(fields, date_style, dates, code_style, stock_codes,
                                                                   tb)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na)


def _fill_df(df, trading_codes, date_list, rpt_date=False, fill_na=True):
    field_date = 'tdate'
    if rpt_date:
        df['rpt_date'] = df['rpt_date'].apply(int)
        df.set_index([field_date, 'tradingcode', 'rpt_date'], inplace=True)
    else:
        df.set_index([field_date, 'tradingcode'], inplace=True)
    df.sort_index(inplace=True)
    if not fill_na:
        if rpt_date:
            df.reset_index('rpt_date', inplace=True)
        return df
    if rpt_date:
        stock_codes = trading_codes * 4
    else:
        stock_codes = trading_codes
    df_nan = pd.DataFrame(_get_arr_nan(date_list, stock_codes, ['drop_column']), columns=['drop_column'],
                          index=pd.MultiIndex.from_product([date_list, stock_codes]))
    df_nan.sort_index(inplace=True)
    df_nan.index.names = [field_date, 'tradingcode']
    if rpt_date:
        df_nan["rpt_date"] = np.NAN
        for date_d in df_nan.index.levels[0]:
            if isinstance(date_d, int):
                date_d = str(date_d)
            if int(date_d[4:]) >= 501 and int(date_d[4:]) <= 1231:
                benchmark_year = int(date_d[:4])
            else:
                benchmark_year = int(date_d[:4]) - 1
            rpt_date_list = [benchmark_year - 1, benchmark_year, benchmark_year + 1, benchmark_year + 2]
            df_2 = df_nan.loc[date_d, :]
            stock_num = len(set(df_2.index))
            rpt_date_list = rpt_date_list * stock_num
            df_nan.loc[date_d, 'rpt_date'] = rpt_date_list
    if rpt_date:
        df_nan.reset_index(inplace=True)
        df_nan['rpt_date'] = df_nan['rpt_date'].apply(int)
        df_nan.set_index([field_date, 'tradingcode', 'rpt_date'], inplace=True)
    df_result = pd.merge(df_nan, df, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
    if rpt_date:
        df_result.drop(["drop_column"], axis=1, inplace=True)
        df_result.reset_index('rpt_date', inplace=True)
        df_result['rpt_date'] = df_result['rpt_date'].apply(int)
    else:
        df_result.drop("drop_column", axis=1, inplace=True)
    return df_result


def get_finance_idct(trading_codes, date_list, factor_list, fill_na=True):
    """
    获取财务分析因子数据
    :param trading_codes: 股票代码或股票代码列表
    :param date_list: 日期(string 或 int)或多个日期的列表
    :param factor_list: 因子或因子列表
    :return: 索引为[日期,股票] 的MultiIndex DataFrame
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]
    fields = params_dict['factor_list'][1]
    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_financialanalysisindex", "factor_d_financialanalysisindex_ext"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_finance_idct(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                    f_table[tb], tb, fill_na)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    return df


def _get_finance_idct(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates, field_list, tb,
                      fill_na):
    fields = ','.join(field_list)
    if tb == 'factor_d_financialanalysisindex':
        sql_use = "select tdate,tradingcode,{0} from factor_d_financialanalysisindex " \
                  "where tdate {1} {2} and tradingcode {3} {4}".format(fields, date_style, dates, code_style,
                                                                       stock_codes)
    else:
        sql_use = "select tdate,tradingcode,{0} from factor_d_financialanalysisindex_ext " \
                  "where tdate {1} {2} and tradingcode {3} {4}".format(fields, date_style, dates, code_style,
                                                                       stock_codes)
    df = dml.getAllByPandas(c_name, sql_use)
    df[df.isnull()] = np.NAN
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na)


def get_stock_info(trading_codes, factor_list, fill_na=True):
    """
    获取股票最新信息
    :param trading_codes: 股票或股票列表
    :param factor_list: 股票信息字段或列表
    :return: DataFrame
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes=trading_codes, factor_list=factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]
    fields = params_dict['factor_list'][1]

    sql_use = "select tradingcode,{0} from factor_d_newmsgindex " \
              "where tradingcode {1} {2}".format(fields, code_style, stock_codes)
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    if not fill_na:
        df.set_index('tradingcode', inplace=True)
        df.sort_index(inplace=True)
        df.index.name = 'stock'
        df[df.isnull()] = np.NAN
        return df
    usable_stock = list(set(df.loc[:, 'tradingcode'].values))
    usable_col = df.columns.values.tolist()
    stock_nan = []
    if df.empty:
        stock_nan = trading_codes
    else:
        for stock in trading_codes:
            if stock not in usable_stock:
                stock_nan.append(stock)
    df.set_index('tradingcode', inplace=True)
    arr = np.zeros((len(stock_nan), len(usable_col[1:])))
    arr[arr == 0.0] = np.NAN
    df_nan_stock = pd.DataFrame(arr, columns=usable_col[1:], index=stock_nan)
    df_nan_stock.index.name = 'tradingcode'
    df = pd.concat([df, df_nan_stock], axis=0)
    df.sort_index(inplace=True)
    df.index.name = 'stock'
    df[df.isnull()] = np.NAN
    return df


def get_finance_report(trading_codes, date_list, factor_list, statement_type="408001000", fill_na=True):
    """
    获取财务报告数据
    :param trading_codes: 股票或股票列表
    :param date_list: 日期(string 或 int) 或日期列表
    :param factor_list: 单个因子或因子列表
    :param statement_type: str，报告类型，详见参数说明
    :return: 索引为[日期,股票]的MultiIndex DataFrame

    statement_type 参数说明：
    ==============      =====        ======================
        类型名称         数值         类型说明
        COMBINED        408001000      合并报表
        COMBINED_SS     408002000      合并报表(单季度)
        COMBINED_SSA    408003000      合并报表(单季度调整)
        COMBINED_A      408004000      合并报表(调整)
        COMBINED_NM     408005000      合并报表(更正前)
        PARENT          408006000      母公司报表
        PARENT_SS       408007000      母公司报表(单季度)
        PARENT_SSA      408008000      母公司报表(单季度调整)
        PARENT_A        408009000      母公司报表(调整)
        PARENT_NM       408010000      母公司报表(更正前)
    ==================  =====        ======================
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]
    fields = params_dict['factor_list'][1]

    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_issuingdateindex", "factor_d_financialreportindex"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)

    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_finance_report(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                      f_table[tb], tb, fill_na, statement_type)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_finance_report(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates, field_list, tb,
                        fill_na, statement_type):
    fields = ""
    for factor in field_list:
        fields += factor + ','
    fields = fields[:-1]
    if tb == "factor_d_financialreportindex":
        sql_use = "select tdate,tradingcode,{0} from factor_d_financialreportindex " \
                  "where tdate {1} {2} and tradingcode {3} {4} and statement_type = {5}".format(
            fields, date_style, dates, code_style, stock_codes, int(statement_type))
    else:
        sql_use = "select tdate,tradingcode,{0} from factor_d_issuingdateindex " \
                  "where tdate {1} {2} and tradingcode {3} {4}".format(
            fields, date_style, dates, code_style, stock_codes)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na)


def get_conforecast_stock_rpt(trading_codes, date_list, factor_list, stock_type=1, fill_na=True):
    """
    获取股票代码相关的一致预期数据（包括预测报告年度）
    :param trading_codes: 股票或股票代码列表
    :param date_list: 日期(string 或 int ) 或日期列表
    :param factor_list: 单个因子或因子列表
    :param stock_type: 证券代码对应的代码类型，1 为A股代码；2 为指数代码；
    :return: 索引为[日期,股票]的MultiIndex DataFrame
    """
    if stock_type not in [1, 2]:
        raise Exception("stock_type 取值1 为A股代码；2 为指数代码 请重新输入！")
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]

    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_conforecastindex_stock_srt", "factor_d_conforecastindex_stock_ssrt"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_con_forecast(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                    f_table[tb], tb, stock_type, fill_na)
            if df.empty:
                df = df1
            else:
                for field in f_table[tb]:
                    df[field] = df1[field]
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def get_conforecast_stock(trading_codes, date_list, factor_list, stock_type=1, fill_na=True):
    """
    获取股票代码相关的一致预期数据
    :param trading_codes: 股票或股票代码列表
    :param date_list: 日期(string 或 int ) 或日期列表
    :param factor_list: 单个因子或因子列表
    :param stock_type: 证券代码对应的代码类型，1 为A股代码；2 为指数代码；
    :return: 索引为[日期,股票]的MultiIndex DataFrame
    """
    if stock_type not in [1, 2]:
        raise Exception("stock_type 取值1 为A股代码；2 为指数代码 请重新输入！")
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]

    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_conforecastindex_stock_st", "factor_d_conforecastindex_stock_sst"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_con_forecast(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                    f_table[tb], tb, stock_type, fill_na=fill_na)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def get_conforecast_block_rpt(trading_codes, date_list, factor_list, block_type=4, fill_na=True):
    """
    获取行业代码相关的一致预期数据（包括预测报告年度）
    :param trading_codes: 行业代码或列表
    :param date_list: 日期(string 或 int) 或日期列表
    :param factor_list: 单个因子或因子列表
    :param block_type: 组合类型，默认4：行业，详见参数说明
    :return: 索引为[日期,股票]的MultiIndex DataFrame

    参数说明：
    - block_type 组合类型 值>=5为指数分行业，默认值为4：行业
        ==========   =========
        数值         类型说明
        2            指数
        4            行业
        5            沪深300行业
        6            上证180行业
        7            红利指数行业
        8            上证50行业
        9            中证100行业
        10           深证100行业
        11           中小板指行业
        12           巨潮40行业
        13           巨潮300行业
        14           巨潮100行业
        15           中标300行业
        16           中标50行业
        17           新富A50行业
        18           道中88行业
        19           上证A股行业
        20           超大盘行业
        21           中证500行业
        22           中证700行业
        23           中小板指行业
        24           创业板指数行业
        25           上证新兴行业
        26           中证800行业
        ==========   =========
    """
    if block_type not in [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]:
        raise Exception("block_type 组合类型，默认4：行业，其他类型请参考帮助文档！")
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]

    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_conforecastindex_block_bbrt"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_con_forecast(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                    f_table[tb], tb, block_type, fill_na=fill_na)
            if df.empty:
                df = df1
            else:
                for field in f_table[tb]:
                    df[field] = df1[field]
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def get_conforecast_block(trading_codes, date_list, factor_list, block_type=4, fill_na=True):
    """
    获取行业代码相关的一致预期数据
    :param trading_codes: 行业代码或列表
    :param date_list: 日期(string 或 int) 或日期列表
    :param factor_list: 单个因子或因子列表
    :param block_type: 组合类型，默认4：行业，详见参数说明
    :return: 索引为[日期,股票]的MultiIndex DataFrame

    参数说明：
    - block_type 组合类型 值>=5为指数分行业，默认值为4：行业
        ==========   =========
        数值         类型说明
        2            指数
        4            行业
        5            沪深300行业
        6            上证180行业
        7            红利指数行业
        8            上证50行业
        9            中证100行业
        10           深证100行业
        11           中小板指行业
        12           巨潮40行业
        13           巨潮300行业
        14           巨潮100行业
        15           中标300行业
        16           中标50行业
        17           新富A50行业
        18           道中88行业
        19           上证A股行业
        20           超大盘行业
        21           中证500行业
        22           中证700行业
        23           中小板指行业
        24           创业板指数行业
        25           上证新兴行业
        26           中证800行业
        ==========   =========
    """
    if block_type not in [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]:
        raise Exception("block_type 组合类型，默认4：行业，其他类型请参考帮助文档！")
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    date_list = params_dict['date_list'][0]
    dates = params_dict['date_list'][1]
    date_style = params_dict['date_list'][2]
    # 因子
    factor_list = params_dict['factor_list'][0]

    f_table = {}
    for factor in factor_list:
        try:
            table = _get_factor_table(dml, c_name, factor)
        except Exception as e:
            raise Exception("因子库无此因子，请检查是否拼写正确！")
        if table not in ["factor_d_conforecastindex_block_bbt"]:
            raise Exception("The query data failed : 1054 (42S22): Unknown column '%s' in 'field list'" % factor)
        if table not in f_table.keys():
            f_table[table] = [factor]
        else:
            f_table[table].append(factor)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            df1 = _get_con_forecast(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates,
                                    f_table[tb], tb, block_type, fill_na=fill_na)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_con_forecast(c_name, code_style, trading_codes, stock_codes, date_style, date_list, dates, field_list, tb,
                      stock_type, fill_na):
    fields = ""
    for factor in field_list:
        fields += factor + ','
    fields = fields[:-1]
    if tb == "factor_d_conforecastindex_stock_st":
        sql_use = "select tdate,tradingcode,{0} from factor_d_conforecastindex_stock_st " \
                  "where tdate {1} {2} and tradingcode {3} {4}".format(fields, date_style, dates, code_style,
                                                                       stock_codes)
    elif tb == "factor_d_conforecastindex_stock_sst":
        sql_use = "select tdate,tradingcode,{0} from factor_d_conforecastindex_stock_sst " \
                  "where tdate {1} {2} and tradingcode {3} {4} and stock_type = {5}".format(fields, date_style, dates,
                                                                                            code_style, stock_codes,
                                                                                            stock_type)
    elif tb == "factor_d_conforecastindex_stock_srt":
        sql_use = "select tdate,tradingcode,rpt_date,{0} from factor_d_conforecastindex_stock_srt " \
                  "where tdate {1} {2} and tradingcode {3} {4}".format(fields, date_style, dates, code_style,
                                                                       stock_codes)
    elif tb == "factor_d_conforecastindex_stock_ssrt":
        sql_use = "select tdate,tradingcode,rpt_date,{0} from factor_d_conforecastindex_stock_ssrt " \
                  "where tdate {1} {2} and tradingcode {3} {4} and stock_type = {5}".format(fields, date_style, dates,
                                                                                            code_style, stock_codes,
                                                                                            stock_type)
    elif tb == "factor_d_conforecastindex_block_bbt":
        sql_use = "select tdate,tradingcode,{0} from factor_d_conforecastindex_block_bbt " \
                  "where tdate {1} {2} and tradingcode {3} {4} and block_type = {5}".format(fields, date_style, dates,
                                                                                            code_style, stock_codes,
                                                                                            stock_type)
    elif tb == "factor_d_conforecastindex_block_bbrt":
        sql_use = "select tdate,tradingcode,rpt_date,{0} from factor_d_conforecastindex_block_bbrt " \
                  "where tdate {1} {2} and tradingcode {3} {4} and block_type = {5}".format(fields, date_style, dates,
                                                                                            code_style, stock_codes,
                                                                                            stock_type)
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    if df.empty:
        return df
    if tb in ["factor_d_conforecastindex_stock_srt", "factor_d_conforecastindex_stock_ssrt",
              "factor_d_conforecastindex_block_bbrt"]:
        rpt_date = True
    else:
        rpt_date = False
    return _fill_df(df, trading_codes, date_list, rpt_date=rpt_date, fill_na=fill_na)


def _get_arr_nan(x, y, z):
    """
    生成全NAN的numpy数组
    :param x: 日期列表
    :param y: 股票列表
    :param z: 因子列表
    :return:
    """
    arr = np.zeros((len(x) * len(y), len(z)))
    arr[arr == 0.0] = np.NAN
    return arr


def _get_factor_table(dml, c_name, factor):
    # 根据因子获取该因子所在的数据库表
    sql_use = "select CONVERTTABLE from factor_map where factorename = '%s'" % factor
    data = dml.getAll(c_name, sql_use)
    table = data[-1][0]
    return table


def tradingDay(startTime, endTime, frequency='DAY', dayType=None, dateType='TRADINGDAYS'):
    """
    通过输入的起止时间、日期类型、星期属性等参数，返回在这些条件下的交易日期列表
    :param startTime: 开始时间，格式yyyymmdd，int(20180102) 或string('20180102')
    :param endTime:结束时间，格式yyyymmdd，int(20180105) 或string('20180105')，frequency为DAY时可为非零整数：
            以startTime为起点，前后n日的时间序列查询(abs(n) <= 10000，n>10000则最多输出10000条数据)，例如，查询以20180102前10个交易日的序列，
            可以输入：tradingDay(20180102, -10)，后面20日：tradingDay(20180102, 20)
    :param frequency: 数据频率，默认DAY，取值详见参数说明
    :param dayType:日期类型，当frequency 参数为WEEK 时，默认值为FRIDAY；
                    当frequency 参数为其它值，默认值为LASTDAY，frequency为DAY时dayType取值无影响,
                    frequency取值MONTH或YEAR时，dayType仅支持FIRSTDAY、LASTDAY，取值详见参数说明
    :param dateType:日历类型，默认值TRADINGDAYS，取值详见参数说明
    :return: 交易日列表(list)

    参数说明：
        - frequency 数据频率
        ==========   =========
        类型名称     类型说明
        DAY          日
        WEEK         周
        MONTH        月
        QUARTER      季
        HALFYEAR     半年
        YEAR         年
        ==========   =========

    - dayType 日期类型

        ==========   ============
        类型名称     类型说明
        MONDAY       周一
        TUESDAY      周二
        WEDNESDAY    周三
        THURSDAY     周四
        FRIDAY       周五
        SATURDAY     周六
        SUNDAY       周日
        FIRSTDAY     第一天
        LASTDAY      最后一天
        ==========   ============

    - dateType 日历类型

        ============   ========
        类型名称       类型说明
        ALLDAYS        日历日
        TRADINGDAYS    交易日
        ============   ========

    范例：
    # 开始日期 结束日期  其他为默认值
    result1 = tradingDay(20180101, 20181204)
    print(result1)
    
    # frequency为DAY时 DayType选择不改变结果
    result2 = tradingDay(20180101, 20181204,dayType='MONDAY')
    print(result2)
    
    # frequency为DAY时 DayType选择不改变结果 dateType=ALLDAYS
    result3 = tradingDay(20180101, 20181204,dayType='MONDAY',dateType='ALLDAYS')
    print(result3)
    
    # frequency = 'WEEK' dayType默认Friday
    result4 = tradingDay(20180101, 20181204,'WEEK')
    print(result4)
    
    # frequency = 'WEEK' dayType 为SATURDAY SUNDAY时无数据（dateType默认TRADINGDAYS）
    result5 = tradingDay(20180101, 20181204,'WEEK','SUNDAY')
    print(result5)
    
    # frequency = 'WEEK' dayType 为SATURDAY SUNDAY时 dateType默认ALLDAYS
    result6 = tradingDay(20180101, 20181204,'WEEK','SUNDAY',dateType='ALLDAYS')
    print(result6)
    
    # frequency 为 'MONTH' QUARTER HALFYEAR YEAR  dayType只能取FIRSTDAY LASTDAY 默认LASTDAY
    result7 = tradingDay(20180101, 20181204,'MONTH','LASTDAY','ALLDAYS')
    print(result7)
    
    result8 = tradingDay(20180101, 20181204,'MONTH','FIRSTDAY','TRADINGDAYS')
    print(result8)
    
    result9 = tradingDay(20180101, 20181204,'YEAR','FIRSTDAY','TRADINGDAYS')
    print(result9)
    
    # frequency 为DAY 时endtime 可穿int数值获取向前或向后的n天数据
    result10 = tradingDay(20180501,10)
    print(result10)
    
    result11 = tradingDay(20180501,-10)
    print(result11)
    
    result12 = tradingDay(20180101,20181001,frequency='YEAR',dayType='LASTDAY')
    print(result12)
    
    result13 = tradingDay(20180101,20181231,frequency='HALFYEAR',dayType='FIRSTDAY')
    print(result13)
    
    result14 = tradingDay(20180101,20181231,frequency='QUARTER',dayType='LASTDAY')
    print(result14)
    
    result15 = tradingDay(20180101,20181231,frequency='MONTH',dayType='LASTDAY')
    print(result15)
    
    result16 = tradingDay(20180101,20181231,frequency='WEEK',dayType='SUNDAY',dateType="ALLDAYS")
    print(result16)
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    if not dayType:
        if frequency == "WEEK":
            dayType = "FRIDAY"
        else:
            dayType = "LASTDAY"
    if frequency in ["MONTH", "QUARTER", "HALFYEAR", "YEAR"]:
        if dayType not in ["FIRSTDAY", "LASTDAY"]:
            raise ValueError("frequency取值MONTH,QUARTER,HALFYEAR,YEAR时，dayType仅支持FIRSTDAY、LASTDAY，默认取值LASTDAY")
    if dateType == 'TRADINGDAYS':
        istradingday = "and istradingday = 1"
    elif dateType == "ALLDAYS":
        istradingday = ""
    else:
        raise ValueError("dateType 取值TRADINGDAYS 交易日、ALLDAYS 日历日，默认TRADINGDAYS，请重新输入！")
    if isinstance(startTime, int):
        startTime = str(startTime)
    if not _is_valid_date(startTime):
        raise ValueError("日期格式yyyymmdd，int(20180102) 或string('20180102')！")
    if frequency == "DAY":
        if _is_valid_date(endTime):
            sql_use = "select tradingday from qd_tradingdays where (tradingday>={1} and tradingday <= {2}) {0} order by tradingday".format(
                istradingday, startTime, endTime)
        elif endTime > 0:
            if endTime > 10000:
                endTime = 10000
            sql_use = "select tradingday from qd_tradingdays where tradingday>={1} {0} order by tradingday limit {2}".format(
                istradingday, startTime, endTime)
        elif endTime < 0:
            if endTime < -10000:
                endTime = -10000
            sql_use = "select tradingday from qd_tradingdays where tradingday<={1} {0} order by tradingday desc limit {2}".format(
                istradingday, startTime, abs(endTime))
        else:
            raise ValueError("日期格式为yyyymmdd，frequency为DAY时endTime可取值不为0的整数，请重新输入！")
    elif frequency == "WEEK":
        if not _is_valid_date(endTime):
            raise ValueError("日期格式yyyymmdd，int(20180102) 或string('20180102')！")
        if dayType in ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'):
            sql_use = "select tradingday from qd_tradingdays where (tradingday>={1} " \
                      "and tradingday <= {2}) and dayname(tradingday)='{3}' {0} " \
                      "order by tradingday".format(istradingday, startTime, endTime, dayType)
        elif dayType == "FIRSTDAY":
            sql_use = "select min(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday),week(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
        elif dayType == "LASTDAY":
            sql_use = "select max(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday),week(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
        else:
            raise ValueError("dayType取值请参考帮助文档，请重新输入！")
    elif frequency == "MONTH":
        if dayType == "FIRSTDAY":
            sql_use = "select min(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday),month(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
        else:
            sql_use = "select max(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday),month(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
    elif frequency == "QUARTER":
        if dayType == "FIRSTDAY":
            sql_use = "select min(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday),QUARTER(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
        else:
            sql_use = "select max(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday),QUARTER(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
    elif frequency == "HALFYEAR":
        if dayType == "FIRSTDAY":
            sql_use = "select min(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} and month(tradingday) in (6,12) " \
                      "group by year(tradingday),month(tradingday) order by tradingday".format(istradingday, startTime,
                                                                                               endTime)
        else:
            sql_use = "select max(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} and month(tradingday) in (6,12) " \
                      "group by year(tradingday),month(tradingday) order by tradingday".format(istradingday, startTime,
                                                                                               endTime)

    elif frequency == "YEAR":
        if dayType == "FIRSTDAY":
            sql_use = "select min(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
        else:
            sql_use = "select max(tradingday) as tradingday from qd_tradingdays where " \
                      "(tradingday>={1} and tradingday <= {2}) {0} group by year(tradingday) " \
                      "order by tradingday".format(istradingday, startTime, endTime)
    else:
        raise ValueError("frequency取值请参考帮助文档，请重新输入！")

    data = dml2.getAll(c_name, sql_use)
    dml2.close(c_name)
    if not data:
        return []
    df = pd.DataFrame(data[1:], columns=data[0])
    df.sort_values(by='tradingday', inplace=True)
    df = df.loc[:, 'tradingday'].astype(str)
    tradingdays = list(np.array(df))
    return tradingdays


def _is_valid_date(date):
    if isinstance(date, int):
        date = str(date)
    try:
        dt.datetime.strptime(date, '%Y%m%d')
        return True
    except ValueError:
        return False


def __get_stock_name(dml, c_name, dateTime, use_prev_name=True):
    if use_prev_name == True:
        sql_name = """select s_info_windcode as STOCK_CODE,s_info_name as STOCK_NAME,begindate,enddate
                 from asharepreviousname where BEGINDATE<='{}' and ('{}'<=ENDDATE or ENDDATE is null)"""
        sql_name.format(dateTime, dateTime)
        data_name = dml.getAll(c_name, sql_name)
        df_name = pd.DataFrame(data_name[1:], columns=data_name[0])
        df_name.set_index('STOCK_CODE', inplace=True)
    else:
        sql_des = "select s_info_windcode as STOCK_CODE,s_info_name as STOCK_NAME from asharedescription"
        data_des = dml.getAll(c_name, sql_des)
        df_name = pd.DataFrame(data_des[1:], columns=data_des[0])
        df_name.set_index('STOCK_CODE', inplace=True)
    return df_name


def hset(plateType, dateTime, plateID, weightType=0, use_prev_name=True):
    """
    通过输入的板块类型、时间和板块ID，输出该板块的成分股，如果是指数板块的时候，还会返回成分股的权重
    :param plateType:参数类型，目前只支持行业板块(INDUSTRY)、指数板块(INDEX)、市场板块(MARKET)三个类型
    :param dateTime:查询日期，格式yyyymmdd,例如:20100801
    :param plateID:当plateType为指数板块时，plateID输入为指数代码,如：'HS300'，详见参数说明；
                    当plateType 为行业板块时，plateID为行业代码，如： 'CITICS.b106040700'、'SW.6110'，详见参数说明
                    支持的行业请参见行业代码表；
                    当plateType 为市场板块时，plateID可取'ALLA'(全部A股)，'SHA'(上海A股)，'SZA'(深圳A股)
    :param weightType: int型，当plateType为指数板块(INDEX)时，0表示当日权重，1表示次日权重
    :return:
    参数说明：
    - IndexType 指数代码

        ============  ===========  =============
        类型名称      类型说明     数据开始日期
        HS300         沪深300指数   20050411
        ZZ500         中证500指数   20100104
        SH50          上证50指数    20100104
        ============  ===========  =============

    - IndustryType 行业分类代码

        ========  ==============
        类型名称  类型说明
        CSRC      证监会行业分类
        CITICS    中信行业分类
        SW        申万行业分类
        ========  ==============
    范例：
    # 中信行业全部
    result1 = hset('INDUSTRY','20030101','CITICS.b1')
    print(result1)
    # 中信一级行业
    result2 = hset('INDUSTRY','20030101','CITICS.b101')
    print(result2)
    # 中信二级行业
    result3 = hset('INDUSTRY','20030101','CITICS.b10102')
    print(result3)
    # 中信三级行业
    result4 = hset('INDUSTRY','20030101','CITICS.b1010201')
    print(result4)
    
    # 申万行业全部
    result5 = hset('INDUSTRY','20070702','SW.61')
    print(result5)
    
    # 申万一级行业
    result6 = hset('INDUSTRY','20070702','SW.6102')
    print(result6)
    
    # 申万二级行业
    result7 = hset('INDUSTRY','20070702','SW.610102')
    print(result7)
    
    # 申万三级行业
    result8 = hset('INDUSTRY','20070702','SW.61010201')
    print(result8)
    
    # 证监会行业全部
    result9 = hset('INDUSTRY','20121231','CSRC.12')
    print(result9)
    
    # 证监会一级行业
    result10 = hset('INDUSTRY','20121231','CSRC.1202')
    print(result10)
    
    # 证监会二级行业
    result11 = hset('INDUSTRY','20121231','CSRC.120102')
    print(result11)
    
    # 指数 沪深300
    result12 = hset('INDEX','20110309','HS300')
    print(result12)
    
    # 指数 中证500 weightType默认0 查询当天权重
    result13 = hset('INDEX','20110309','ZZ500')
    print(result13)

    # 指数 上证50 weightType=1时查询次日权重
    result14 = hset('INDEX','20110308','SZ50',1)
    print(result14)

    # 市场板块 全部A股
    result7_15 = hset('MARKET',20110309,'ALLA')
    print(result7_15)

    # 市场板块 上海A股
    result7_16 = hset('MARKET',20110309,'SHA')
    print(result7_16)

    # 市场板块 深圳A股
    result7_17 = hset('MARKET',20110309,'SZA')
    print(result7_17)
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    if isinstance(dateTime, int):
        dateTime = str(dateTime)
    elif not isinstance(dateTime, str):
        raise Exception("查询日期，格式为yyyymmdd(str or int),例如:20100801")
    if plateType == "INDEX":
        if plateID == "SH50":
            plateID = "SZ50"
        # 获取板块代码
        sql1 = "select icode from con_index where sspell = '{0}'".format(plateID)
        data1 = dml3.getAll(c_name, sql1)
        icode = data1[-1][0]
        dml3.close(c_name)
        # inx_component 字段 股票代码
        sql2 = "select indexcode,secucode," \
               "(case exchangecode when '101' then concat(tradingcode,'.SH') when '105' then concat(tradingcode,'.SZ') end) as 'STOCK_CODE' " \
               "from inx_component where indate<=date_format('{0}','%Y-%m-%d') " \
               "and (outdate>=date_format('{0}','%Y-%m-%d') or isnull(outdate)) and icode='{1}'".format(dateTime, icode)
        df2 = dml2.getAllByPandas(c_name, sql2)
        if weightType == 0:
            df2.set_index(['indexcode', 'secucode'], inplace=True)
        elif weightType == 1:
            df2.drop('indexcode', axis=1, inplace=True)
            df2.set_index('secucode', inplace=True)
        else:
            raise Exception("【weight_Type参数】int型，当plateType为指数板块(INDEX)时，0表示当日权重，1表示次日权重，请重新输入！")
        if weightType == 0:
            # inx_componentweight字段 当日股票权重
            sql3 = "select indexcode,secucode,round(weight,2) as weight from inx_componentweight " \
                   "where TRADINGDAY = {0}".format(dateTime)
            df3 = dml2.getAllByPandas(c_name, sql3)
            df3.set_index(['indexcode', 'secucode'], inplace=True)
            df_mer23 = pd.merge(df2, df3, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df_mer23.reset_index('indexcode', drop=True, inplace=True)
        else:
            # inx_ixcsiwgtnd 次日股票权重
            sql3 = "select secucode,round(weight,2) as weight from inx_ixcsiwgtnd " \
                   "where tradingday = {0} and indexcode = '{1}' and isvalid = 1".format(dateTime, icode)
            df3 = dml2.getAllByPandas(c_name, sql3)
            df3.set_index('secucode', inplace=True)
            df_mer23 = pd.merge(df2, df3, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
        # stk_abbrchange 字段 股票名称
        df4 = __get_stock_name(dml2, c_name, dateTime, use_prev_name)
        df_mer23.reset_index(drop=True, inplace=True)
        df_mer23.set_index('STOCK_CODE', inplace=True)
        df = pd.merge(df_mer23, df4, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
        df.reset_index(inplace=True)
        columns = ['STOCK_CODE', 'STOCK_NAME', 'weight']
        df = df.loc[:, columns]
        df.reset_index(drop=True, inplace=True)
    elif plateType == "INDUSTRY":
        try:
            industry = plateID.split('.')[0]
            industrycode = plateID.split('.')[1]
        except Exception as e:
            raise Exception("plateID可取值如：'CSRC.12'、'CITICS.b1'、'SW.61'等，详情请参考帮助文档！")
        t = len(industrycode)
        if t == 0 or t % 2 != 0:
            raise Exception("plateID可取值如：'CSRC.12'、'CITICS.b1'、'SW.61'等，详情请参考帮助文档！")

        df_des = __get_stock_name(dml2, c_name, dateTime, use_prev_name)
        if industry == "CSRC":
            sql_csrc = "select s_info_windcode as STOCK_CODE,sec_ind_code from ASHARESECNINDUSTRIESCLASS " \
                       "where substr(sec_ind_code,1,{0}) = '{1}' and entry_dt <= {2} and (remove_dt>={2} or remove_dt is null)".format(
                len(industrycode), industrycode, dateTime)
            df_csrc = dml2.getAllByPandas(c_name, sql_csrc)
            df_csrc.set_index('STOCK_CODE', inplace=True)
            df = pd.merge(df_csrc, df_des, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df.drop('sec_ind_code', axis=1, inplace=True)
            df.reset_index(inplace=True)
        elif industry == "CITICS":
            sql_citics = "select s_info_windcode as STOCK_CODE,citics_ind_code from ASHAREINDUSTRIESCLASSCITICS " \
                         "where substr(citics_ind_code,1,{0}) = '{1}' and entry_dt <= {2} and (remove_dt>={2} or remove_dt is null)".format(
                len(industrycode), industrycode, dateTime)
            df_citics = dml2.getAllByPandas(c_name, sql_citics)
            df_citics.set_index('STOCK_CODE', inplace=True)
            df = pd.merge(df_citics, df_des, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df.drop('citics_ind_code', axis=1, inplace=True)
            df.reset_index(inplace=True)
        elif industry == "SW":
            sql_sw = "select s_info_windcode as STOCK_CODE,sw_ind_code from ASHARESWINDUSTRIESCLASS " \
                     "where substr(sw_ind_code,1,{0}) = '{1}' and entry_dt <= {2} and (remove_dt>={2} or remove_dt is null)".format(
                len(industrycode), industrycode, dateTime)
            df_sw = dml2.getAllByPandas(c_name, sql_sw)
            df_sw.set_index('STOCK_CODE', inplace=True)
            df = pd.merge(df_sw, df_des, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df.drop('sw_ind_code', axis=1, inplace=True)
            df.reset_index(inplace=True)
        else:
            raise ValueError("plateID可取值如：'CSRC.12'、'CITICS.b1'、'SW.61'等，详情请参考帮助文档！")
    elif plateType == "MARKET":
        if isinstance(dateTime, str):
            dateTime = int(dateTime)
        basic_sql = """select a.s_info_windcode as STOCK_CODE, b.s_info_name as STOCK_NAME
                        from ashareeodprices a 
                        left join asharepreviousname b 
                        on b.S_INFO_WINDCODE=a.S_INFO_WINDCODE
                        where a.trade_dt = '{0}' and {1} 
                        and BEGINDATE<='{0}' and ('{0}'<=ENDDATE or ENDDATE is null)
                        order by a.s_info_windcode"""
        if plateID == "ALLA":
            sql_mkt = "(a.s_info_windcode like '0%.SZ' or " \
                      "(a.s_info_windcode like '3%.SZ' and a.s_info_windcode not like '399%.SZ') or " \
                      "a.s_info_windcode like '6%.SH')"
        elif plateID == "SHA":
            sql_mkt = "a.s_info_windcode like '6%.SH'"
        elif plateID == "SZA":
            sql_mkt = "(a.s_info_windcode like '0%.SZ' or (a.s_info_windcode like '3%.SZ' and a.s_info_windcode not like '399%.SZ')) "
        elif plateID == "GEM":
            sql_mkt = "a.s_info_windcode like '3%.SZ' and a.s_info_windcode not like '399%.SZ'"
        elif plateID == "SME":
            sql_mkt = "a.s_info_windcode like '002%.SZ' "
        else:
            raise Exception("MARKET市场板块暂只支持 'ALLA'(全部A股)，'SHA'(上海A股)，"
                            "'SZA'(深圳A股)，'SME'(中小板)，'GEM'(创业板)，请重新输入！")
        sql_use = basic_sql.format(dateTime, sql_mkt)
        data_mkt = dml2.getAll(c_name, sql_use)
        df_mkt = pd.DataFrame(data_mkt[1:], columns=data_mkt[0])
        if use_prev_name:
            dml2.close(c_name)
            return df_mkt.rename(columns={'STOCK_CODE': 'stock', "STOCK_NAME": 'stock_name'})
        else:
            df_mkt = df_mkt.reindex(columns=["STOCK_CODE"])
            df_mkt.rename(columns={'STOCK_CODE': 'stock'}, inplace=True)
        df = df_mkt.copy()

        df_name = __get_stock_name(dml2, c_name, dateTime, use_prev_name)
        df_name.rename(columns={'STOCK_CODE': 'stock', 'STOCK_NAME': 'stock_name'}, inplace=True)

        df.set_index('stock', inplace=True)
        df = pd.merge(df, df_name, how='left', left_index=True, right_index=True, suffixes=['_x', '_y'])
        df.sort_index(inplace=True)
        df.reset_index(inplace=True)
    else:
        raise Exception("[plateType参数]暂时仅支持行业板块(INDUSTRY)、指数板块(INDEX)、市场板块(MARKET)，请重新输入！")
    dml2.close(c_name)
    df.rename(columns={'STOCK_CODE': 'stock', 'STOCK_NAME': 'stock_name'}, inplace=True)
    df[df.isnull()] = np.NAN
    return df


def hind(industryType, level=0):
    """
    根据输入的行业类别、级别查询该类别行业代码信息
    :param industryType:行业类型，'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类
    :param level: 级别，取值[0,3]之间整数，默认0，证监会行业只有两级分类取值[0,2]之间的整数
    :return:
    范例：
    # 证监会行业
    result1 = hind('CSRC',0)
    print(result1)
    
    # 证监会一级行业代码
    result2 = hind('CSRC',1)
    print(result2)
    
    # 证监会二级行业代码
    result3 = hind('CSRC',2)
    print(result3)
    
    # 中信行业
    result4 = hind('CITICS',0)
    print(result4)
    
    # 中信一级行业
    result5 = hind('CITICS',1)
    print(result5)
    
    # 中信二级行业
    result6 = hind('CITICS',2)
    print(result6)
    
    # 中信三级行业
    result7 = hind('CITICS',3)
    print(result7)
    
    # 申万行业
    result8 = hind('SW',0)
    print(result8)
    
    # 申万一级行业
    result9 = hind('SW',1)
    print(result9)
    
    # 申万二级行业
    result10 = hind('SW',2)
    print(result10)
    
    # 申万三级行业
    result11 = hind('SW',3)
    print(result11)
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    if not isinstance(level, int) or level < 0 or level > 3:
        raise Exception("[level]行业级别，取值[0,3]之间的整数，默认0，请重新输入！")

    if industryType == "CSRC":
        if level > 2:
            raise Exception("证监会行业只有两级行业分类取值[0,2]之间的整数，请重新输入！")
        sql_use = "select distinct b.Industriescode, b.Industriesname " \
                  "from AshareSECNIndustriesClass a, Ashareindustriescode b " \
                  "where Substr(a.Sec_Ind_Code, 1, (2*({0}+1))) = Substr(b.Industriescode, 1, (2*({0}+1))) " \
                  "and b.Levelnum = ({0}+1) and a.Cur_Sign = 1 and b.Used = 1 " \
                  "order by b.Industriescode".format(level)
    elif industryType == "CITICS":
        sql_use = "select distinct b.Industriescode, b.Industriesname " \
                  "from Ashareindustriesclasscitics a, Ashareindustriescode b " \
                  "where Substr(a.CITICS_Ind_Code, 1, (2*({0}+1))) = Substr(b.Industriescode, 1, (2*({0}+1))) " \
                  "and b.Levelnum = ({0}+1) and a.Cur_Sign = 1 and b.Used = 1 " \
                  "order by b.Industriescode".format(level)
    elif industryType == "SW":
        sql_use = "select distinct b.Industriescode, b.Industriesname " \
                  "from Ashareswindustriesclass a, Ashareindustriescode b " \
                  "where Substr(a.Sw_Ind_Code, 1, (2*({0}+1))) = Substr(b.Industriescode, 1, (2*({0}+1))) " \
                  "and b.Levelnum = ({0}+1) and a.Cur_Sign = 1 and b.Used = 1 " \
                  "order by b.Industriescode".format(level)
    else:
        raise Exception("[industryType]行业类型：'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，请重新输入！")
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    df.rename(columns={'Industriescode': 'industry_code', 'Industriesname': 'industry_name'}, inplace=True)
    df['industry_code'] = df['industry_code'].apply(lambda x: x[:(level + 1) * 2])
    df[df.isnull()] = np.NAN
    return df


def hsi(tradingcodes, date=dt.date.today().strftime("%Y%m%d"), industryType=None, industryLevel=3, switchFlag='OFF'):
    """
    查询股票指定日期所属的指定级别行业信息，目前支持的行业类别有证监会新行业分类、中信行业分类、申万行业分类三种
    :param tradingcodes: 股票代码 或 股票列表
    :param date: 日期(string 或 int) ，默认为查询当天的日期
    :param industryType: 行业类型，'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，默认全部行业
    :param industryLevel: 行业级别，取值[1,3]之间的整数，默认为三级行业，证监会行业只有两级分类取[1,2]的整数
    :return: 索引为trading_code的DataFrame
    
    范例：
    # CSRC 证监会一级行业 switchFlag默认不过滤NAN值
    result1 = hsi(['000100.SZ','000807.SZ','1111.SZ'], 20121231, 'CSRC',1)
    print(result1)
    
    # CSRC 证监会二级行业（证监会只有两级分类） switchFlag默认不过滤NAN值
    result2 = hsi(['000100.SZ','000807.SZ','1111.SZ'], '20121231','CSRC',2)
    print(result2)
    
    # CSRC 证监会二级行业 switchFlag取'ON'，过滤NAN值
    result3 = hsi(['000100.SZ','000807.SZ','1111.SZ'], '20121231','CSRC',2,switchFlag='ON')
    print(result3)
    
    # CITICS 中信行业一级 switchFlag默认不过滤NAN值
    result4 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='CITICS',industryLevel=1)
    print(result4)
    
    # CITICS 中信行业一级 switchFlag取'ON'，过滤NAN值
    result5 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='CITICS',industryLevel=1,switchFlag='ON')
    print(result5)
    
    # CITICS 中信行业二级 switchFlag默认不过滤NAN值
    result6 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='CITICS',industryLevel=2)
    print(result6)
    
    # CITICS 中信行业三级 switchFlag默认不过滤NAN值
    result7 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='CITICS',industryLevel=3)
    print(result7)
    
    # SW 申万行业一级 switchFlag默认不过滤NAN值
    result8 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='SW',industryLevel=1)
    print(result8)
    
    # SW 申万行业一级 switchFlag取'ON'，过滤NAN值
    result9 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='SW',industryLevel=1,switchFlag='ON')
    print(result9)
    
    # SW 申万行业二级 switchFlag默认不过滤NAN值
    result10 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='SW',industryLevel=2)
    print(result10)
    
    # SW 申万行业三级 switchFlag默认不过滤NAN值
    result11 = hsi(['000001.SZ','000002.SZ','000009.SZ','111111.SZ'],'20121231',industryType='SW',industryLevel=3)
    print(result11)
    
    
    # industryType 默认全部行业 ，industryLevel默认3级分类
    result12 = hsi(['000001.SZ','000002.SZ','000009.SZ'],'20121231',industryLevel=2)
    print(result12)
    
    # industryType 默认全部行业 ，industryLevel默认3级分类 switchFlag过滤空值
    result13 = hsi(['000001.SZ','000002.SZ','000009.SZ'],'20121231',industryLevel=2,switchFlag='ON')
    print(result13)
    
    # 单支股票测试 industryType 默认全部行业 ，industryLevel默认3级分类 switchFlag过滤空值
    result14 = hsi('000001.SZ','20121231',industryLevel=2,switchFlag='ON')
    print(result14)
    """
    if switchFlag not in ['OFF', 'ON']:
        raise Exception("switchFlag 空值过滤标志,'OFF'不过滤空值，'ON'过滤空值，请重新输入！")
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    params_dict = _handle_params(tradingcodes)
    # 股票代码
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    if isinstance(date, int):
        date = str(date)
    elif not isinstance(date, str):
        raise Exception("日期为yyyymmdd格式(string 或 int) ，默认为查询当天的日期，请重新输入！")
    if not isinstance(industryLevel, int) or industryLevel < 1 or industryLevel > 3:
        raise Exception("[industryLevel]行业级别，取值[1,3]之间的整数，默认为三级行业，请重新输入！")
    if industryType == "CSRC" and industryLevel == 3:
        print("证监会只有两级分类，取[1,2]的整数！")
        return
    if not industryType:
        if industryLevel == 3:
            industryLevel_CSRC = 2
        else:
            industryLevel_CSRC = industryLevel
        # 证监会行业
        sql1 = "select s_info_windcode as trading_code,Substr(sec_ind_code,1,2*({0}+1)) as industry_code from ASHARESECNINDUSTRIESCLASS where " \
               "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
            industryLevel_CSRC, code_style, stock_codes, date)
        df1_1 = dml2.getAllByPandas(c_name, sql1)
        df1_1.set_index('industry_code', inplace=True)
        if df1_1.empty:
            df1 = pd.DataFrame()
        else:
            industry1 = list(df1_1.index.values)
            industry_params1 = _handle_params(industry1)
            industry_codes1 = industry_params1['trading_codes'][1]
            industry_style1 = industry_params1['trading_codes'][2]
            sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from Ashareindustriescode " \
                   "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
                industryLevel_CSRC, industry_style1, industry_codes1)
            df1_2 = dml2.getAllByPandas(c_name, sql2)
            df1_2.set_index('industry_code', inplace=True)
            df1 = pd.merge(df1_1, df1_2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df1["industry_type"] = "证监会行业分类(2012版)"

        # 中信行业
        sql3 = "select s_info_windcode as trading_code,Substr(citics_ind_code,1,2*({0}+1)) as industry_code from ASHAREINDUSTRIESCLASSCITICS where " \
               "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
            industryLevel, code_style, stock_codes, date)
        df2_1 = dml2.getAllByPandas(c_name, sql3)
        df2_1.set_index('industry_code', inplace=True)
        if df2_1.empty:
            df2 = pd.DataFrame()
        else:
            industry2 = list(df2_1.index.values)
            industry_params2 = _handle_params(industry2)
            industry_codes2 = industry_params2['trading_codes'][1]
            industry_style2 = industry_params2['trading_codes'][2]
            sql4 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from Ashareindustriescode " \
                   "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
                industryLevel, industry_style2, industry_codes2)
            df2_2 = dml2.getAllByPandas(c_name, sql4)
            df2_2.set_index('industry_code', inplace=True)
            df2 = pd.merge(df2_1, df2_2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df2["industry_type"] = "中信行业分类"

        # 申万行业
        sql5 = "select s_info_windcode as trading_code,Substr(sw_ind_code,1,2*({0}+1)) as industry_code from ASHARESWINDUSTRIESCLASS where " \
               "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
            industryLevel, code_style, stock_codes, date)
        df3_1 = dml2.getAllByPandas(c_name, sql5)
        df3_1.set_index('industry_code', inplace=True)
        if df3_1.empty:
            df3 = pd.DataFrame()
        else:
            industry3 = list(df3_1.index.values)
            industry_params3 = _handle_params(industry3)
            industry_codes3 = industry_params3['trading_codes'][1]
            industry_style3 = industry_params3['trading_codes'][2]
            sql6 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from Ashareindustriescode " \
                   "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
                industryLevel, industry_style3, industry_codes3)
            df3_2 = dml2.getAllByPandas(c_name, sql6)
            df3_2.set_index('industry_code', inplace=True)
            df3 = pd.merge(df3_1, df3_2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df3["industry_type"] = "申万行业分类"

        df = pd.concat([df1, df2, df3], axis=0)
    else:
        if industryType == "CSRC":
            sql1 = "select s_info_windcode as trading_code,Substr(sec_ind_code,1,2*({0}+1)) as industry_code from ASHARESECNINDUSTRIESCLASS where " \
                   "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
                industryLevel, code_style, stock_codes, date)
            df1 = dml2.getAllByPandas(c_name, sql1)
            df1.set_index('industry_code', inplace=True)
            if df1.empty:
                return pd.DataFrame()
            industry = list(df1.index.values)
            industry_params = _handle_params(industry)
            industry_codes = industry_params['trading_codes'][1]
            industry_style = industry_params['trading_codes'][2]
            sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from Ashareindustriescode " \
                   "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
                industryLevel, industry_style, industry_codes)
            df2 = dml2.getAllByPandas(c_name, sql2)
            df2.set_index('industry_code', inplace=True)
            df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df["industry_type"] = "证监会行业分类(2012版)"
        elif industryType == "CITICS":
            sql1 = "select s_info_windcode as trading_code,Substr(citics_ind_code,1,2*({0}+1)) as industry_code from ASHAREINDUSTRIESCLASSCITICS where " \
                   "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
                industryLevel, code_style, stock_codes, date)
            df1 = dml2.getAllByPandas(c_name, sql1)
            df1.set_index('industry_code', inplace=True)
            if df1.empty:
                return pd.DataFrame()
            industry = list(df1.index.values)
            industry_params = _handle_params(industry)
            industry_codes = industry_params['trading_codes'][1]
            industry_style = industry_params['trading_codes'][2]
            sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from Ashareindustriescode " \
                   "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
                industryLevel, industry_style, industry_codes)
            df2 = dml2.getAllByPandas(c_name, sql2)
            df2.set_index('industry_code', inplace=True)
            df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df["industry_type"] = "中信行业分类"
        elif industryType == "SW":
            sql1 = "select s_info_windcode as trading_code,Substr(sw_ind_code,1,2*({0}+1)) as industry_code from ASHARESWINDUSTRIESCLASS where " \
                   "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
                industryLevel, code_style, stock_codes, date)
            df1 = dml2.getAllByPandas(c_name, sql1)
            df1.set_index('industry_code', inplace=True)
            if df1.empty:
                return pd.DataFrame()
            industry = list(df1.index.values)
            industry_params = _handle_params(industry)
            industry_codes = industry_params['trading_codes'][1]
            industry_style = industry_params['trading_codes'][2]
            sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from Ashareindustriescode " \
                   "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
                industryLevel, industry_style, industry_codes)
            df2 = dml2.getAllByPandas(c_name, sql2)
            df2.set_index('industry_code', inplace=True)
            df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df["industry_type"] = "申万行业分类"
        else:
            raise Exception("[industryType]行业类型：'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，默认全行业，请重新输入！")
    if df.empty:
        return df
    else:
        df.reset_index(inplace=True)
        df = df[['trading_code', 'industry_type', 'industry_code', 'industry_name']]
    dml2.close(c_name)
    if switchFlag == 'OFF':
        stock_nan = []
        if isinstance(tradingcodes, str):
            tradingcodes = [tradingcodes]
        for stock in tradingcodes:
            if stock not in df.loc[:, 'trading_code'].tolist():
                stock_nan.append(stock)
        if stock_nan:
            data_nan = []
            for i in stock_nan:
                data_nan.append([i, np.NAN, np.NAN, np.NAN])
            df1 = pd.DataFrame(data_nan, columns=['trading_code', 'industry_type', 'industry_code', 'industry_name'])
            df = pd.concat([df, df1], axis=0, ignore_index=True)
    else:
        df.dropna(inplace=True)
    df.set_index('trading_code', inplace=True)
    df.sort_index(inplace=True)
    df.index.name = 'stock'
    df[df.isnull()] = np.NAN
    df = df.reset_index()
    return df


def stockFilter(stockPool, filterDate=dt.date.today().strftime("%Y%m%d"), filterType='SSO', use_prev_name=True):
    """
    过滤股票池中不符合条件的股票。过滤掉STPT，停牌，开盘涨停等股票
    :param stockPool: 股票池，列表类型
    :param filterDate:查询日期,数值型，例如：20151231，默认查询当天日期
    :param filterType: 过滤类型，默认为过滤掉STPT，停牌，开盘涨停的股票，引用格式：StockFilterType.SSO
    :return: DataFrame
    
    范例：
    stockPool = hset('INDEX','20110309','ZZ500')['STOCK_CODE'].tolist()
    # STPT
    result1 = stockFilter(stockPool,20180104,'STPT')
    print(result1)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result1))
    
    # SUSPEND
    result2 = stockFilter(stockPool,20180104,'SUSPEND')
    print(result2)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result2))
    
    # OPENUPLIMIT
    result3 = stockFilter(stockPool,20180104,'OPENUPLIMIT')
    print(result3)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result3))
    
    # OPENDOWNLIMIT
    result4 = stockFilter(stockPool,20180104,'OPENDOWNLIMIT')
    print(result4)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result4))
    
    # SSO
    result5 = stockFilter(stockPool,20180104,'SSO')
    print(result5)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result5))
    
    # STSPEND
    result6 = stockFilter(stockPool,20180104,'STSPEND')
    print(result6)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result6))
    
    # STUP
    result7 = stockFilter(stockPool,20180104,'STUP')
    print(result7)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result7))
    
    # STDOWN
    result8 = stockFilter(stockPool,20180104,'STDOWN')
    print(result8)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result8))
    
    # UPSPEND
    result9 = stockFilter(stockPool,20180104,'UPSPEND')
    print(result9)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result9))
    
    # DNSPWND
    result10 = stockFilter(stockPool,20180104,'DNSPWND')
    print(result10)
    print("股票池中股票数量：\n",len(stockPool))
    print("过滤后股票的数量：",len(result10))
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    if not stockPool:
        print('[stockFilter函数]参数stockPool为空，请重新输入！')
        return
    if not isinstance(stockPool, list):
        print("[stockFilter函数]参数stockPool应为list类型，请重新输入！")
        return

    if isinstance(filterDate, int):
        date = filterDate
    elif isinstance(filterDate, str):
        date = int(filterDate)
    else:
        raise Exception("filterDate yyyymmdd类型的日期，支持int 与 str类型 如20180104")
    df_stock = pd.DataFrame(np.zeros((len(stockPool), 1)), columns=['col_delete'], index=stockPool)
    df_stock.index.name = 'STOCK_CODE'
    df_final = __stock_filter(c_name, date, stockPool, filterType, use_prev_name)
    # 根据filterType进行第一层过滤
    return df_final


def __stock_filter(c_name, date, stockPool, filter_type, use_prev_name):
    if len(stockPool) == 1:
        stockPool.append("None")
    # date int型
    if filter_type == "STPT":
        # ("特别处理特殊处理", 1),
        filter_cond = "instr(b.S_INFO_NAME, 'ST') = 0"
        # 暂按照df['STPT'] == 1 时为保留的股票
    elif filter_type == "SUSPEND":

        filter_cond = "s_dq_amount > 0"
    elif filter_type == "OPENUPLIMIT":

        filter_cond = "round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)<110"
        # SUSPEND 停牌
        # df['SUSPEND'] = df['SUSPEND'].astype(float)
    elif filter_type == "OPENDOWNLIMIT":
        # OPENDOWNLIMIT 开盘跌停
        filter_cond = "round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)>90"
        #  OPENUPLIMIT 开盘涨停
    elif filter_type == "SSO":
        #  SSO STPT + 停牌 + 开盘涨停
        filter_cond = "instr(b.S_INFO_NAME, 'ST') = 0 and s_dq_amount > 0 and  round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)<110"
    elif filter_type == "STSPEND":
        # STSPEND STPT+停牌
        filter_cond = "instr(b.S_INFO_NAME, 'ST') = 0 and s_dq_amount > 0"
    elif filter_type == "STUP":
        # STUP STPT + 开盘涨停
        filter_cond = "instr(b.S_INFO_NAME, 'ST') = 0 and round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)<110"
    elif filter_type == "STDOWN":
        # ("特别处理特殊处理 + 开盘跌停", 13),\
        filter_cond = "instr(b.S_INFO_NAME, 'ST') = 0 and round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)>90"
    elif filter_type == "UPSPEND":
        # UPSPEND 停牌 + 开盘涨停
        filter_cond = "s_dq_amount > 0 and round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)<110"
    elif filter_type == "DWSPEND" or filter_type == "DNSPWND":
        # DNSPWND 停牌 + 开盘跌停
        filter_cond = "s_dq_amount > 0 and round(100*a.S_DQ_OPEN/a.S_DQ_PRECLOSE)>90"
    else:
        raise Exception("[stockFilter函数]参数filterType类型错误: {}，请重新输入！".format(filter_type))
    if use_prev_name == True:
        sql_basic = """select a.S_INFO_WINDCODE as stock, b.S_INFO_NAME as stock_name
                       from ASHAREEODPRICES a 
                       left join asharepreviousname b 
                       on b.S_INFO_WINDCODE=a.S_INFO_WINDCODE
                       where  a.TRADE_DT  = '{}' and a.S_INFO_WINDCODE in {}
                       and b.BEGINDATE<='{}' and ('{}'<=ENDDATE or ENDDATE is null)
                       and {}"""
        sql_use = sql_basic.format(date, tuple(stockPool), date, date, filter_cond)
    else:
        sql_use = None
    data = dml2.getAll(c_name, sql_use)
    dml2.close(c_name)
    df = pd.DataFrame(data[1:], columns=data[0])
    return df


def get_divid(trading_codes, date_list, factor_list, fill_na=True):
    """
    获取分红因子数据数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:索引为[日期,股票] 的MultiIndex DataFrame

    范例：
    # 多支股票  日期  因子
    result14_1 = get_divid(['300465.SZ','300527.SZ','002016.SZ'],['20180630','20180930'],['per_div_trans','per_cashpaidbeforetax','ex_dt','dvd_payout_dt'])
    print(result14_1)
    # 单支股票 日期 因子
    result14_2 = get_divid('300465.SZ',20180630,'per_div_trans')
    print(result14_2.columns)
    """
    # 主键：EQY_RECORD_DT(eqy_record_dt股权登记日),S_DIV_PRELANDATE（s_div_prelandate预案公告日）,
    # S_DIV_BASESHARE(基准股本(万股))，ANN_DT(最新公告日期)
    # REPORT_PERIOD(分红年度)
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    factors_1 = ['ex_dt', 'dvd_payout_dt', 'listing_dt_of_dvd_shr', 's_div_smtgdate', 'dvd_ann_dt', 's_div_progress']

    factors_calc = ['per_div_trans', 'per_cashpaidbeforetax', 'per_cashpaidaftertax', 'per_cashpaidbeforetax_Declared',
                    'per_cashpaidaftertax_Declared', 'div_aualaccmdivpershare',
                    'div_aualaccmdiv', 'div_cashpaidaftertax', 'div_cashpaidbeforetax']

    factor_calc_dict = {'per_div_trans': 'stk_dvd_per_sh as per_div_trans',
                        'per_cashpaidbeforetax': 'cash_dvd_per_sh_pre_tax as per_cashpaidbeforetax',
                        'per_cashpaidaftertax': 'cash_dvd_per_sh_after_tax as per_cashpaidaftertax',
                        'per_cashpaidbeforetax_declared': 'cash_dvd_per_sh_pre_tax as per_cashpaidbeforetax_declared',
                        'per_cashpaidaftertax_declared': 'cash_dvd_per_sh_after_tax as per_cashpaidaftertax_declared',
                        'div_aualaccmdivpershare': 'cast(cash_dvd_per_sh_pre_tax as decimal(10,4)) as div_aualaccmdivpershare',
                        'div_aualaccmdiv': 'cast(cash_dvd_per_sh_pre_tax*s_div_baseshare*10000 as decimal(20,4)) as div_aualaccmdiv',
                        'div_cashpaidaftertax': 'round(cash_dvd_per_sh_after_tax,4) as div_cashpaidaftertax',
                        'div_cashpaidbeforetax': 'round(cash_dvd_per_sh_pre_tax,4) as div_cashpaidbeforetax'}
    factor_column = {'per_div_trans': 'stk_dvd_per_sh', 'per_cashpaidbeforetax': 'cash_dvd_per_sh_pre_tax',
                     'per_cashpaidaftertax': 'cash_dvd_per_sh_after_tax', 's_div_baseshare': 's_div_baseshare',
                     }
    factors_3 = ['div_if_']
    factor_use1 = []
    factor_use2 = []
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    for factor in factor_list:
        if factor in factors_1:
            factor_use1.append(factor)
        elif factor in factors_calc:
            factor_use1.append(factor_calc_dict[factor])
        elif factor in factors_3:
            factor_use2.append(factor)
        else:
            raise Exception("[factor_list]因子 %s 不属于分红指标，请重新输入！" % factor)
    params_dict1 = _handle_params(trading_codes, date_list)
    # 股票代码
    trading_codes = params_dict1['trading_codes'][0]
    stock_codes = params_dict1['trading_codes'][1]
    code_style = params_dict1['trading_codes'][2]
    # 日期
    date_list = params_dict1['date_list'][0]
    dates = params_dict1['date_list'][1]
    date_style = params_dict1['date_list'][2]
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    if factor_use1:
        params_factor1 = _handle_params(factor_list=factor_use1)
        # 因子
        fields1 = params_factor1['factor_list'][1]
        sql_use1 = "select S_INFO_WINDCODE as tradingcode,REPORT_PERIOD as tdate,eqy_record_dt,s_div_prelandate,ANN_DT,S_DIV_BASESHARE,{0} " \
                   "from asharedividend where S_INFO_WINDCODE {1} {2} and " \
                   "REPORT_PERIOD {3} {4}".format(fields1, code_style, stock_codes, date_style, dates)
        # print(sql_use1)
        df1 = dml2.getAllByPandas(c_name, sql_use1)
        for i in df1.columns:
            if i in factor_column.keys():
                df1[i] = df1[i].astype(float)
    if factor_use2:
        df2 = pd.DataFrame()
        # params_factor2 = _handle_params(factor_list=factor_use2)
        # # 因子
        # fields2 = params_factor2['factor_list'][1]
        # # sql_use2 =
        # data2 = dml2.getAll(c_name, sql_use2)
        # if not data2:
        #     return
        # df2 = pd.DataFrame(data2[1:], columns=data2[0])
    dml2.close(c_name)
    columns1 = list(df1.columns)
    columns2 = list(df2.columns)
    if not columns1 and not columns2:
        return
    elif columns1 and not columns2:
        df = df1
    elif not columns1 and columns2:
        df = df2
    else:
        df2.drop(['eqy_record_dt', 's_div_prelandate'], axis=1, inplace=True)
        df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=['_x', '_y'])
    df[df.isnull()] = np.NAN
    df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    return df_result


def get_divid_1(trading_codes, date_list, factor_list, fill_na=True):
    """
    获取分红因子数据数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:索引为[日期,股票] 的MultiIndex DataFrame

    范例：
    # 多支股票  日期  因子
    result14_1 = get_divid(['300465.SZ','300527.SZ','002016.SZ'],['20180630','20180930'],['per_div_trans','per_cashpaidbeforetax','ex_dt','dvd_payout_dt'])
    print(result14_1)
    # 单支股票 日期 因子
    result14_2 = get_divid('300465.SZ',20180630,'per_div_trans')
    print(result14_2.columns)
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    factor_all = ['id', 'tradingcode', 'chiname', 'exchangecode', 'exchangename', 'tdate', 'per_div_trans',
                  'per_cashpaidbeforetax', 'per_cashpaidaftertax', 'div_aualaccmdivpershare', 'div_aualaccmdiv',
                  'div_cashpaidaftertax', 'div_cashpaidbeforetax', 'ex_dt', 'dvd_payout_dt', 'listing_dt_of_dvd_shr',
                  's_div_smtgdate', 'dvd_ann_dt', 's_div_progress', 'per_cashpaidbeforetax_declared',
                  'per_cashpaidaftertax_declared', 'eqy_record_dt', 's_div_prelandate', 's_div_baseshare', 'ann_dt',
                  's_div_object', 'entrytime', 'updatetime']
    factor_unique = ['tradingcode', 'tdate', 'eqy_record_dt', 's_div_prelandate', 'ann_dt', 's_div_baseshare']
    factor_column = ['per_div_trans', 'per_cashpaidbeforetax', 'per_cashpaidaftertax', 's_div_baseshare']
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    factor_use = []
    for factor in factor_list:
        if factor not in factor_all:
            raise Exception("[factor_list]因子 %s 不属于分红指标，请重新输入！" % factor)
        if factor in factor_unique:
            continue
        else:
            factor_use.append(factor)
    params_dict1 = _handle_params(trading_codes, date_list)
    # 股票代码
    trading_codes = params_dict1['trading_codes'][0]
    stock_codes = params_dict1['trading_codes'][1]
    code_style = params_dict1['trading_codes'][2]
    # 日期
    date_list = params_dict1['date_list'][0]
    dates = params_dict1['date_list'][1]
    date_style = params_dict1['date_list'][2]
    df = pd.DataFrame()
    if factor_use:
        params_factor1 = _handle_params(factor_list=factor_use)
        # 因子
        fields = params_factor1['factor_list'][1]
        sql_use = "select tradingcode,tdate,eqy_record_dt,s_div_prelandate,ann_dt,s_div_baseshare,{0} " \
                  "from factor_d_dividendindex where tradingcode {1} {2} and " \
                  "tdate {3} {4}".format(fields, code_style, stock_codes, date_style, dates)
        df = dml.getAllByPandas(c_name, sql_use)
        for i in df.columns:
            if i in factor_column:
                df[i] = df[i].astype(float)
    dml.close(c_name)
    df[df.isnull()] = np.NAN
    df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    return df_result


@utils_set_timeout(120, "sql查询超时！请缩短查询区间！")
def get_conforecast(trading_codes, date_list, factor_list, stock_type, block_type, fill_na=True):
    """
    一致预期源表查询
    :param trading_codes: 股票代码
    :param date_list: 日期列表
    :param factor_list: 因子列表
    :param stock_type: 证券代码对应的代码类型，1 为A股代码；2 为指数代码；
    :param block_type:组合类型，默认4：行业，详见参数说明
    :return:
    参数说明：
    - block_type 组合类型 值>=5为指数分行业，默认值为4：行业
        ==========   =========
        数值         类型说明
        2            指数
        4            行业
        5            沪深300行业
        6            上证180行业
        7            红利指数行业
        8            上证50行业
        9            中证100行业
        10           深证100行业
        11           中小板指行业
        12           巨潮40行业
        13           巨潮300行业
        14           巨潮100行业
        15           中标300行业
        16           中标50行业
        17           新富A50行业
        18           道中88行业
        19           上证A股行业
        20           超大盘行业
        21           中证500行业
        22           中证700行业
        23           中小板指行业
        24           创业板指数行业
        25           上证新兴行业
        26           中证800行业
        ==========   =========
    """
    if stock_type not in [1, 2]:
        raise Exception("stock_type 取值1 为A股代码；2 为指数代码 请重新输入！")
    if block_type not in [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]:
        raise Exception("block_type 组合类型，默认4：行业，其他类型请参考帮助文档！")
    c_name = str(int(time.time())) + str(threading.get_ident())
    dml_schema = DML_mysql(conforecast_config["schema"])

    # 处理参数
    params_dict = _handle_params(trading_codes, date_list, factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    # 日期
    date_list = params_dict['date_list'][0]
    # 因子
    factor_list = params_dict['factor_list'][0]

    factor_info = conforecast_config["factor_info"]
    table_index = conforecast_config["table_index"]
    table_factor_dict = {}
    no_factor_list = []
    for factor in factor_list:
        if factor not in factor_info:
            no_factor_list.append(factor)
        else:
            if factor_info[factor][1] not in table_factor_dict:
                table_factor_dict[factor_info[factor][1]] = [factor_info[factor][0] + " as " + factor]
            else:
                table_factor_dict[factor_info[factor][1]].append(factor_info[factor][0] + " as " + factor)
    if no_factor_list:
        raise Exception(str(no_factor_list) + "因子不存在！")

    rpt_list = []
    no_rpt_list = []
    for tbl in table_factor_dict:
        select_sql = table_index[tbl]
        if select_sql.find("rpt_date") >= 0:
            rpt_list.append(",".join([i.split()[-1] for i in table_factor_dict[tbl]]))
        else:
            no_rpt_list.append(",".join([i.split()[-1] for i in table_factor_dict[tbl]]))
    if rpt_list and no_rpt_list:
        raise Exception("数据无法合并错误！以下因子请再调用一次接口查询：%s" % (str(rpt_list)))
    df_list = []
    for tbl in table_factor_dict:
        select_sql = table_index[tbl]
        if select_sql in [SQLTYPE.ST.value, SQLTYPE.SRT.value]:
            sql = "select " + select_sql + ",".join(table_factor_dict[tbl]) + " from " + tbl + " where stock_code in (" \
                  + ("'%s'," * len(trading_codes))[:-1] % (tuple(trading_codes)) + ") and tdate in (" + ",".join(
                date_list) + ")"
        elif select_sql in [SQLTYPE.SST.value, SQLTYPE.SSRT.value]:
            sql = "select " + select_sql + ",".join(table_factor_dict[tbl]) + " from " + tbl + " where stock_code in (" \
                  + ("'%s'," * len(trading_codes))[:-1] % (tuple(trading_codes)) + ") and tdate in (" + ",".join(
                date_list) + ") and stock_type = " + str(stock_type)
        elif select_sql in [SQLTYPE.BBT.value, SQLTYPE.BBRT.value]:
            sql = "select " + select_sql + ",".join(
                table_factor_dict[tbl]) + " from " + tbl + " where block_code in (" \
                  + ("'%s'," * len(trading_codes))[:-1] % (tuple(trading_codes)) + ") and tdate in (" + ",".join(
                date_list) + ") and block_type = " + str(block_type)
        else:
            raise Exception("SQLTYPE ERROR!")
        df = dml_schema.getAllByPandas(c_name, sql)
        if df.empty:
            if "stock_type" in df.columns:
                df.drop("stock_type", axis=1, inplace=True)
            if "block_type" in df.columns:
                df.drop("block_type", axis=1, inplace=True)
        df[df.isnull()] = np.NAN
        df['tdate'] = df['tdate'].apply(str)
        if no_rpt_list:
            df.set_index(['tdate', 'tradingcode'], inplace=True)
        else:
            df.set_index(['tdate', 'tradingcode', 'rpt_date'], inplace=True)
        df_list.append(df)
    df = pd.concat(df_list, axis=1)
    df.reset_index(inplace=True)
    if no_rpt_list:
        df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na)
    else:
        df_result = _fill_df(df, trading_codes, date_list, rpt_date=True, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    dml_schema.close(c_name)
    return df_result


def get_all_qtr(start_date, end_date):
    """
    获取季末日期列表
    :param start_date: 开始日期，int型，例：20180105
    :param end_date: 结束日期，int型，例：20181231
    :return:
    """
    if start_date > end_date:
        raise Exception("satrt_date > end_date !")
    start_year = dt.datetime.strptime(str(start_date), "%Y%m%d").year
    end_year = dt.datetime.strptime(str(end_date), "%Y%m%d").year
    year_list = [str(i) for i in range(start_year, end_year + 1)]
    month_date = ['0331', '0630', '0930', '1231']
    date_list_complete = [i + j for i in year_list for j in month_date]
    qtr_list = [int(i) for i in date_list_complete if (int(i) <= end_date and int(i) >= start_date)]
    return qtr_list


def get_factor_vip_data(stock, mddate, factor_names, statement_type,wind_type="wind_vip", fill_na=True):
    """
    获取factor_vip数据
    :param stock: 股票
    :param mddate: 日期列表
    :param factor_names: 因子列表
    :param statement_type: 1表示合并报表，2表示母公司报表，3表示合并报表(调整)，4表示母公司报表(调整)
    statement_type 参数说明：
    ==============      =====        ======================
        类型名称         数值         类型说明
        COMBINED        408001000      合并报表
        PARENT          408006000      母公司报表
        COMBINED_A      408004000      合并报表(调整)
        PARENT_A        408009000      母公司报表(调整)
    ==================  =====        ======================
    :return:
    """
    statement_type_dict = {
        408001000: 1,
        408006000: 2,
        408004000: 3,
        408009000: 4
    }
    if statement_type not in statement_type_dict:
        raise Exception("statement_type 取值只能在[408001000,408006000,408004000,408009000]!")
    statement_type = statement_type_dict[statement_type]
    no_factor_list = []
    if wind_type == "wind_vip":
        table_factor_dict = {}
        table_map = table_map_factors
    elif wind_type == "wind_vip_us":
        table_factor_dict = {}
        table_map = table_map_factors_us
    elif wind_type == "wind_vip_commodity":
        table_factor_dict = {}
        table_map = table_map_factors_commodity
    for factor_name in factor_names:
        if factor_name not in table_map:
            no_factor_list.append(factor_name)
        else:
            if not table_factor_dict.get(table_map[factor_name][0]):
                table_factor_dict[table_map[factor_name][0]] = [factor_name]
            else:
                table_factor_dict[table_map[factor_name][0]].append(factor_name)
    if no_factor_list:
        raise Exception("该库中不存在以下因子：" + str(no_factor_list))
    c_name = str(int(time.time())) + str(threading.get_ident())
    if wind_type == "wind_vip":
        separate_queries_list = ["factor_vip_financialanalysis_part3","factor_vip_financialanalysis_part4"]
        for sq in separate_queries_list:
            if len(table_factor_dict)>1 and table_factor_dict.get(sq):
                raise Exception("请分开查询以下因子：%s" % (str(table_factor_dict[sq])))
        df_list = []
        for tf in table_factor_dict:
            if tf == "factor_vip_financialanalysis_part3":
                sql = "select tradingcode,tdate," + ",".join(
                    table_factor_dict[
                        "factor_vip_financialanalysis_part3"]) + ",update_time from factor_vip_financialanalysis_part3 where tradingcode in (" \
                      + ("'%s'," * len(stock))[:-1] % (tuple(stock)) + ") and tdate in (" + ",".join(mddate) + \
                      ") and statement_type = %d" % statement_type
                df = dml_factor_vip.getAllByPandas(c_name, sql)
                df[df.isnull()] = np.NAN
                df.set_index(['tdate', 'tradingcode'], inplace=True)
                df_list.append(df)
            else:
                df = _select_factor_vip(table_factor_dict[tf],tf, stock, mddate, c_name)
                df_list.append(df)
        df = pd.concat(df_list, axis=1)
    elif wind_type == "wind_vip_us":
        for tf in table_factor_dict:
            df = _select_factor_vip(table_factor_dict[tf],
                                    tf, stock, mddate, c_name)
    elif wind_type == "wind_vip_commodity":
        for tf in table_factor_dict:
            df = _select_factor_vip(table_factor_dict[tf],
                                    tf, stock, mddate, c_name)
    df.reset_index(inplace=True)
    df_result = _fill_df(df, stock, mddate, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    dml_factor_vip.close(c_name)
    return df_result

def get_mysql_column_attrs(table_name, table_schema):
    """
    :param table_name: 表名
    :param table_schema: 数据库名
    :return: dict
    """
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    sql_use = "select COLUMN_NAME,DATA_TYPE from information_schema.COLUMNS where " \
              "table_name = '{0}' and table_schema = '{1}'".format(table_name, table_schema)
    if table_schema == "xquant_data":
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
    elif table_schema == "xquant_wind":
        df = dml2.getAllByPandas(c_name, sql_use)
        dml2.close(c_name)
    # xquant_gogoal
    elif table_schema == "xquant_gogoal":
        df = dml3.getAllByPandas(c_name, sql_use)
        dml3.close(c_name)
    else:
        raise Exception("【table_schema参数】该接口无 %s ！" % table_schema)
    df.set_index('COLUMN_NAME', inplace=True)
    attrs_dict = df.to_dict()
    return attrs_dict['DATA_TYPE']


def _select_factor_vip(table_factor_list, table, stock, mddate, c_name):
    sql = "select tradingcode,tdate," + ",".join(
        table_factor_list) + ",update_time from " + table + " where tradingcode in (" \
          + ("'%s'," * len(stock))[:-1] % (tuple(stock)) + ") and tdate in (" + ",".join(mddate) + ")"
    df = dml_factor_vip.getAllByPandas(c_name, sql)
    df[df.isnull()] = np.NAN
    df.set_index(['tdate', 'tradingcode'], inplace=True)
    return df


def transformat_column_attr(df, table_name, table_schema):
    attrs_dict = get_mysql_column_attrs(table_name, table_schema)
    attrs_dict_new = {}
    for key in attrs_dict.keys():
        attrs_dict_new[key.lower()] = attrs_dict[key]
    for factor in df.columns:
        if factor in attrs_dict_new.keys() and attrs_dict_new[factor] == 'decimal':
            df[factor] = df[factor].astype(float)
    return df


def transformat_str_to_date(value, column_attr):
    # value string类型
    import re
    try:
        operator = re.match(r'[><=!]+', value).group()
    except:
        operator = None
    if column_attr.lower() in ['date', 'datetime']:
        if operator:
            str_date = value[len(operator):].strip()
            if len(str_date) == 8:
                date = "str_to_date" + "(" + str_date + "," + "'%Y%m%d'" + ")"
            elif len(str_date) == 14:
                date = "str_to_date" + "(" + str_date + "," + "'%Y%m%d%H%i%s'" + ")"
            else:
                raise Exception("日期格式支持年月日(如'20190826')、年月日时分秒(如'20190826103000')，请重新输入！")
        else:
            if isinstance(value, int):
                value = str(value)
            try:
                if len(value) == 8:
                    date = "str_to_date" + "(" + value + "," + "'%Y%m%d'" + ")"
                elif len(value) == 14:
                    date = "str_to_date" + "(" + value + "," + "'%Y%m%d%H%i%s'" + ")"
                else:
                    raise Exception("日期格式支持年月日(如'20190826')、年月日时分秒(如'20190826103000')，请重新输入！")
            except:
                date = value
        if operator:
            value = operator + " " + date
        else:
            value = date
    else:
        pass
    return value, operator


def _handle_params2(key, value, column_attr, or_param=None):
    operator_list = [">", "<", ">=", "<=", "!=", "<>"]
    if isinstance(value, str):
        try:
            value, operator = transformat_str_to_date(value, column_attr)
        except:
            operator = None
        if operator in operator_list:
            where_str = key + " " + value
        elif value.lower().strip() == "is not null" or value.lower().strip() == "is null":
            where_str = key + " " + value
        elif value.strip()[:4] == "like":
            where_str = key + " " + value
        else:
            if 'str_to_date' in value:
                value = "(" + value + ")"
            else:
                value = "(" + "'" + value + "'" + ")"
            where_str = key + " " + "in" + " " + value
    elif isinstance(value, int) or isinstance(value, float):
        if column_attr.lower() in ['date', 'datetime']:
            value, operator = transformat_str_to_date(str(value), column_attr)
        try:
            if 'str_to_date' in value:
                value = "(" + value + ")"
            else:
                value = "(" + "'" + value + "'" + ")"
        except:
            value = "(" + str(value) + ")"
        where_str = key + " " + "in" + " " + value
    elif isinstance(value, list):
        if len(value) == 0:
            where_str = ""
        elif len(value) == 1:
            p_value = value[0]
            if isinstance(p_value, str):
                p_value, operator = transformat_str_to_date(p_value, column_attr)
                if operator in operator_list:
                    where_str = key + " " + p_value
                elif p_value.lower().strip() == "is not null" or p_value.lower().strip() == "is null":
                    where_str = key + " " + p_value
                elif p_value.strip()[:4] == "like":
                    where_str = key + " " + p_value
                else:
                    if 'str_to_date' in p_value:
                        p_value = "(" + p_value + ")"
                    else:
                        p_value = "(" + "'" + p_value + "'" + ")"
                    where_str = key + " " + "in" + " " + p_value
            elif isinstance(p_value, int) or isinstance(p_value, float):
                p_value = "(" + str(p_value) + ")"
                where_str = key + " " + "in" + " " + p_value
        else:
            compare_oprator = 0
            for i in value:
                if isinstance(i, str):
                    i = i.strip()
                if isinstance(i, str) and (i[0] in operator_list or i[:2] in operator_list):
                    compare_oprator += 1
            if compare_oprator == 0:
                if column_attr.lower() == "date":
                    value_str = "("
                    for i in value:
                        i = "str_to_date" + "(" + str(i) + "," + "'%Y%m%d'" + ")"
                        if len(value_str) > 1:
                            value_str += "," + i
                        else:
                            value_str += i
                    value_str += ")"
                elif column_attr.lower() == "datetime":
                    value_str = "("
                    for i in value:
                        i = "str_to_date" + "(" + str(i) + "," + "'%Y%m%d%H%i%s'" + ")"
                        if len(value_str) > 1:
                            value_str += "," + i
                        else:
                            value_str += i
                    value_str += ")"
                else:
                    value_str = str(tuple(value))
                where_str = key + " " + "in" + " " + value_str
            else:
                where_str = ""
                value_num = len(value)
                for i in range(value_num):
                    try:
                        v, operator = transformat_str_to_date(value[i].strip(), column_attr)
                        if not where_str:
                            if value_num > 1 and or_param and key.lower() == or_param.lower():
                                where_str += "(" + key + " " + v
                            else:
                                where_str += key + " " + v
                        else:
                            if or_param and key.lower() == or_param.lower():
                                if i == value_num - 1:
                                    where_str += " " + "or" + " " + key + " " + v + ")"
                                else:
                                    where_str += " " + "or" + " " + key + " " + v
                            else:
                                where_str += " " + "and" + " " + key + " " + v
                    except Exception as e:
                        raise Exception("{0}--{1}--{2}".format(key, value, e))
    else:
        raise Exception("条件参数的值，仅支持单个值 或多个值的列表，请重新输入！")
    return where_str


@utils_set_timeout(60, "sql查询超时！请缩短查询区间！")
def get_mysql_source(library_name, **kwargs):
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    if library_name[:4] == "WIND":
        table_name = library_name[5:]
        table_schema = "xquant_wind"
    elif library_name[:6] == "GOGOAL":
        table_name = library_name[7:]
        table_schema = "xquant_gogoal"
    else:
        raise Exception("PYTHON查询MYSQL源表暂时只支持万得(WIND)与朝阳永续(GOGOAL)，请重新输入！")
    if not kwargs:
        sql_use = "select * from {0}".format(table_name)
    else:
        columns_attrs = get_mysql_column_attrs(table_name, table_schema)
        factor_fields = ""
        where_str = ""
        or_param = kwargs.get("OR", None)
        for key in kwargs:
            if key == "factors":
                factor_cols = kwargs["factors"]
                if isinstance(factor_cols, str):
                    factor_cols = [factor_cols]
                elif isinstance(factor_cols, list):
                    factor_cols = factor_cols
                else:
                    raise Exception("factors为单个列名或多个列名的列表！")
                # factor_cols = [i.upper() for i in factor_cols]
                factor_fields = ",".join(factor_cols)
            elif key == "OR":
                continue
            else:
                try:
                    column_attr = columns_attrs[key.lower()]
                except:
                    column_attr = columns_attrs[key.upper()]
                if not where_str:
                    where_str += " " + _handle_params2(key, kwargs[key], column_attr, or_param)
                else:
                    where_str += " " + "and" + " " + _handle_params2(key, kwargs[key], column_attr, or_param)
        if not factor_fields:
            columns = "*"
        else:
            columns = factor_fields
        if where_str:
            where_str = "where" + " " + where_str
        sql_use = "select {0} from {1} {2}".format(columns, table_name, where_str)
    if table_schema == "xquant_wind":
        df = dml2.getAllByPandas(c_name, sql_use)
        dml2.close(c_name)
    else:
        df = dml3.getAllByPandas(c_name, sql_use)
        dml3.close(c_name)
    df[df.isnull()] = np.NAN

    attrs_dict = get_mysql_column_attrs(table_name, table_schema)
    for col in df.columns:
        try:
            col_attr = attrs_dict[col.lower()]
        except:
            col_attr = attrs_dict[col.upper()]
        if col_attr in ['date', 'datetime']:
            df[col] = df[col].astype(str)

    return df


# def judge_table_in_mysql(table_name, table_schema):
#     # 判断table_name是否在table_schema数据库下
#     thread = threading.currentThread()
#     thread_id = str(thread.ident)
#     # 毫秒级时间戳
#     time_stamp = str(int(round(time.time() * 1000)))
#     c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
#     sql_use = "select table_name from information_schema.tables where table_schema='%s'" % table_schema
#     if table_schema == "xquant_wind":
#         data = dml2.getAll(c_name, sql_use)
#         dml2.close(c_name)
#         df = pd.DataFrame(data[1:], columns=data[0])
#         df['table_name'] = df['table_name'].apply(lambda x: x.lower())
#         table_list = df['table_name'].tolist()
#         if table_name.lower() in table_list:
#             return True
#         else:
#             return False
#     elif table_schema == "xquant_gogoal":
#         data = dml3.getAll(c_name, sql_use)
#         dml3.close(c_name)
#         df = pd.DataFrame(data[1:], columns=data[0])
#         df['table_name'] = df['table_name'].apply(lambda x: x.lower())
#         table_list = df['table_name'].tolist()
#         if table_name.lower() in table_list:
#             return True
#         else:
#             return False
#     else:
#         raise Exception("PYTHON查询MYSQL源表暂时只支持万得(WIND)与朝阳永续(GOGOAL)，请重新输入！")

def judge_table_in_mysql(table_name):
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    sql_use = "select * from source_table_switch where table_name='%s' and switch=1"%table_name
    data = dml.getAll(c_name, sql_use)
    dml.close(c_name)
    if len(data) > 1:
        return True
    return False



