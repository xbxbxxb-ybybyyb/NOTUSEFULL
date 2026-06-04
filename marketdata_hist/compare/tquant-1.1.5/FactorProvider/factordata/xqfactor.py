# _*_ coding:utf-8 _*_
import threading
from FactorProvider.utils.utils import utils_set_timeout, is_valid_date
from FactorProvider.storage.db import DML_mysql
from .source_table_config import *
import pandas as pd
import numpy as np
import time
import sys
import datetime as dt
from FactorProvider.setEnv import xquantEnv, sysFlag
from FactorProvider.utils.check import Permission

# 实例化连接池与数据访问层类
if sysFlag == "xquant" or sysFlag == "big_data":
    dml = DML_mysql('xquant_data')
    dml2 = DML_mysql('xquant_wind')
    dml3 = DML_mysql('xquant_gogoal')
elif sysFlag == "tquant" or sysFlag == 'outside':
    if xquantEnv == 0:
        dml = DML_mysql('xquant_cusdata')
        dml2 = dml
        dml3 = dml
    else:
        dml = DML_mysql('htsc_dwa_quant')
        dml2 = dml
        dml3 = dml
else:
    raise Exception("未知运行系统异常！")

ps = Permission()
__f_table_df = None

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
            dates = eval('"' + "'" + date_list + "'" + '"')
            date_list = [date_list]
            params_dict['date_list'] = [date_list, dates, date_style]
        elif isinstance(date_list, str):
            date_style = '='
            dates = eval('"' + "'" + date_list + "'" + '"')
            date_list = [date_list]
            params_dict['date_list'] = [date_list, dates, date_style]
        elif isinstance(date_list, list):
            date_list = [str(date) if isinstance(date, int) else date for date in date_list]
            date_list = list(set(date_list))
            if len(date_list) == 1:
                dates = eval('"' + "'" + date_list[0] + "'" + '"')
                date_style = '='
            else:
                date_style = 'in'
                dates = tuple(date_list)
            params_dict['date_list'] = [date_list, dates, date_style]
        elif isinstance(date_list, tuple):
            pass
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


def __filter_time(date_list):
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    elif isinstance(date_list, list):
        date_list.sort()
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    new_datelist = tradingDay(int(date_list[0]), int(date_list[-1]))
    time_list = []
    tmp_list = []
    for i in new_datelist:
        if i in date_list:
            tmp_list.append(i)
        else:
            if tmp_list:
                time_list.append([tmp_list[0] + " 092500000", tmp_list[-1] + " 163000000"])
            tmp_list = []
    if tmp_list:
        time_list.append([tmp_list[0] + " 092500000", tmp_list[-1] + " 163000000"])
    return time_list


def __get_cname():
    thread = threading.currentThread()
    thread_id = str(thread.ident)
    # 毫秒级时间戳
    time_stamp = str(int(round(time.time() * 1000)))
    c_name = "conn_" + time_stamp + "_" + thread_id  # 链接名
    return c_name


def __get_f_table_1():
    # 获取因子与所存储表的对应关系
    c_name = __get_cname()
    if sysFlag in ["xquant", "big_data"]:
        sql_use = "select factorename,converttable from xquant_data.factor_map"
    else:
        sql_use = "select fac_name,tb_name from fac_info"
    df = dml.getAllByPandas(c_name, sql_use)
    if sysFlag in ["xquant", "big_data"]:
        df.rename(columns={'factorename': 'fac_name', 'converttable': 'tb_name'}, inplace=True)
    dml.close(c_name)
    df.set_index('fac_name', inplace=True)
    return df


def __get_f_table(factor_list):
    global __f_table_df
    if not isinstance(__f_table_df, pd.DataFrame):
        __f_table_df = __get_f_table_1()
    factor_dict = __f_table_df.to_dict()["tb_name"]
    f_table = {}
    for f in factor_list:
        if f in factor_dict:
            if f_table.get(factor_dict[f]):
                f_table[factor_dict[f]].append(f)
            else:
                f_table[factor_dict[f]] = [f]
        else:
            raise Exception("{0} - 无此因子，请检查后输入！".format(f))
    return f_table


def filter_240_kmin(df, factorname):
    item = factorname
    dt_date_list = sorted(list(set(df.index.date)))  # datetime类型的日期列表
    str_date_list = [dt.datetime.strftime(x, '%Y%m%d') for x in dt_date_list]  # str类型的日期列表

    if item == 'open_minute':  # 如是open, 可能第1分钟无成交, 那么把第2分钟的值向前填充之
        for i_day in str_date_list:
            df.loc[i_day].iloc[0:2] = df.loc[i_day].iloc[0:2].fillna(method='bfill')
    days_num = int(df.__len__() / 242)
    # 925和930标记
    sel_num1 = np.union1d(np.arange(days_num) * 242, np.arange(days_num) * 242 + 1)
    min_data1 = df.iloc[list(sel_num1), :]
    # 1459和1500标记
    sel_num2 = np.union1d(np.arange(days_num) * 242 + 240, np.arange(days_num) * 242 + 241)
    min_data2 = df.iloc[list(sel_num2), :]
    if item in ['volume_minute', 'amt_minute']:
        # 处理开盘集合竞价数据，把925的volume和amt和930相加，并归到930
        min_data_va1 = min_data1.rolling(2).sum().iloc[np.arange(days_num) * 2 + 1, :]
        df.loc[min_data_va1.index] = min_data_va1
        # 处理收盘集合竞价数据，把1459的volume和amt和1500相加，并归到1459
        min_data_va2 = min_data2.rolling(2).sum().shift(-1).iloc[np.arange(days_num) * 2, :]
        df.loc[min_data_va2.index] = min_data_va2
    elif item in ['open_minute', 'limit_status']:
        # 处理开盘集合竞价数据，把925的open归到930
        min_data_o = min_data1.shift(1).iloc[np.arange(days_num) * 2 + 1, :]
        df.loc[min_data_o.index] = min_data_o
    elif item == 'close_minute':
        # 处理收盘集合竞价数据，把1500的close归到1459
        min_data_c = min_data2.shift(-1).iloc[np.arange(days_num) * 2, :]
        df.loc[min_data_c.index] = min_data_c
    elif item == 'limit_status':
        # 处理开盘集合竞价数据，把925和930两者的high归到930
        min_data_h1 = min_data1.rolling(2).max().iloc[np.arange(days_num) * 2 + 1, :]
        df.loc[min_data_h1.index] = min_data_h1
        # 处理收盘集合竞价数据，把1459和1500两者的high归到1459
        min_data_h2 = min_data2.rolling(2).max().shift(-1).iloc[np.arange(days_num) * 2, :]
        df.loc[min_data_h2.index] = min_data_h2
    elif item == 'low_minute':
        # 处理开盘集合竞价数据，把925和930两者的low归到930
        min_data_l1 = min_data1.rolling(2).min().iloc[np.arange(days_num) * 2 + 1, :]
        df.loc[min_data_l1.index] = min_data_l1
        # 处理收盘集合竞价数据，把1459和1500两者的low归到1459
        min_data_l2 = min_data2.rolling(2).min().shift(-1).iloc[np.arange(days_num) * 2, :]
        df.loc[min_data_l2.index] = min_data_l2
    df_exc_925 = df.index.time != dt.time(9, 25)
    df_exc_1500 = df.index.time != dt.time(15, 00)
    df = df.loc[np.logical_and(df_exc_925, df_exc_1500)].copy()
    return df


def get_market_price(trading_codes, date_list, factor_list, fill_na=True, daily_bar_num=242, sort_option=True):
    """
    获取行情数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:索引为[日期,股票] 的MultiIndex DataFrame
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】取行情指标数据时，元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    if not trading_codes:
        raise Exception("股票不能为空或None！")
    if not factor_list:
        raise Exception("因子不能为空或None！")
    ps.check_factor_date_permission(date_list[0], date_list[-1])
    hset_base_factor = ["index_weight_hs300", "index_weight_sh50", "index_weight_zz500"]
    index_col = ['MDDate', 'MDTime', 'HTSCSecurityID']
    item_new = ["high_minute", 'open_minute', 'close_minute', 'low_minute', 'volume_minute', 'amt_minute',
                'numtrade_minute']
    item_dict = {'MDDate': 'tdate', 'HTSCSecurityID': 'tradingcode', 'HighPx': 'high_minute', 'OpenPx': 'open_minute',
                 'ClosePx': 'close_minute', 'LowPx': 'low_minute',
                 'TotalVolumeTrade': 'volume_minute',
                 'TotalValueTrade': 'amt_minute', 'NumTrades': 'numtrade_minute'}
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    hset_factor = []
    new_factor_list = []
    market_factor_list = []
    for f in factor_list:
        if f in hset_base_factor:
            hset_factor.append(f)
        elif f in item_new:
            market_factor_list.append(f)
        else:
            new_factor_list.append(f)
    df_list = []
    if market_factor_list:
        market_df_list = []
        from MDCDataProvider import DataProvider as MarketData
        mdp = MarketData()
        time_list = __filter_time(date_list)
        col_dict = {}
        for new_col in factor_list:
            for col in item_dict:
                if item_dict[col] == new_col:
                    col_dict[col] = new_col
        for dt_list in time_list:
            for stock in trading_codes:
                df = mdp.get_data_by_time_frame("Kline1M4ZT", stock, dt_list[0], dt_list[1], ["1", "2", "3"])
                if df.empty:
                    continue
                df = df[index_col + list(col_dict.keys())]
                df.rename(columns=item_dict, inplace=True)
                df = df[df["tradingcode"].isin(trading_codes)]
                market_df_list.append(df)
        if market_df_list:
            df = pd.concat(market_df_list, axis=0)
            df["time_stamp"] = df.apply(lambda x: pd.Timestamp(x.iloc[0] + " " + x.iloc[1][:6]), axis=1)
            df.drop(columns=["tdate", "MDTime"], inplace=True)
            df.set_index(["time_stamp", "tradingcode"], inplace=True)
            if daily_bar_num == 240:
                df = df.iloc[:, 0]
                df = df.unstack()
                # df为datafram，行为timestamp，列为traingcode
                df = filter_240_kmin(df, factor_list[0])
                return df
        else:
            df = pd.DataFrame(columns=["time_stamp", "tradingcode"] + factor_list).set_index(
                ["time_stamp", "tradingcode"])

        return df
    if new_factor_list:
        c_name = __get_cname()
        f_table = __get_f_table(new_factor_list)
        if len(f_table) == 0:
            raise Exception("请输入正确的因子！")
        elif len(f_table) == 1:
            table_name = list(f_table.keys())[0]
            if table_name not in ["factor_d_marketindex", "factor_day_marketindex"]:
                raise Exception("只支持查询日行情因子数据！")
            if sysFlag in ['xquant', 'big_data']:
                table_name1 = 'xquant_data.' + table_name
            else:
                table_name1 = table_name
            sql_use = get_sql_use(table_name1, trading_codes, f_table[table_name], date_list)
            df = dml.getAllByPandas(c_name, sql_use)
            dml.close(c_name)
            df.set_index(["tdate", "tradingcode"], inplace=True)
            df_list.append(df)
        else:
            raise Exception("只支持查询日行情因子数据！")
    if hset_factor:
        hset_df_list = []
        for factor in hset_factor:
            new_factor = factor.split("_")[-1].upper()
            df = hset('INDEX', date_list, new_factor)
            df = df[["tradingday", "STOCK_CODE", "weight"]]
            df.rename(columns={"tradingday": "tdate", "STOCK_CODE": "tradingcode", "weight": factor}, inplace=True)
            df["tdate"] = df["tdate"].apply(lambda x: x.strftime('%Y%m%d'))
            df = df[df["tradingcode"].isin(trading_codes)]
            df.set_index(["tdate", "tradingcode"], inplace=True)
            if not df.empty:
                hset_df_list.append(df)
        if hset_df_list:
            df = pd.concat(hset_df_list, axis=0)
            df_list.append(df)
    if not df_list:
        df = pd.DataFrame(columns=["tdate", "tradingcode"] + factor_list)
    elif len(df_list) > 1:
        df = pd.merge(df_list[0], df_list[1], left_index=True, right_index=True, how='outer')
        df.reset_index(inplace=True)
    else:
        df = df_list[0]
        df.reset_index(inplace=True)
    df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)
    df_result.index.names = ['mddate', 'stock']
    df_result[df_result.isnull()] = np.NAN
    return df_result


def get_factor_idct(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取估值因子风险因子的因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return: 索引为[日期,股票] 的MultiIndex DataFrame
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    if not trading_codes:
        raise Exception("股票不能为空或None！")
    if not factor_list:
        raise Exception("因子不能为空或None！")
    ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_d_valuationmetricsindex", "factor_day_valuationmetricsindex",
                          "factor_d_riskanalysisindex", "factor_day_riskanalysisindex"]:
                raise Exception("只支持查询估值指标与风险指标的因子数据！")
            df1 = _get_factor_idct(c_name, tb, trading_codes, date_list, f_table[tb], fill_na, sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_factor_idct(c_name, table_name, trading_codes, date_list, factor_list, fill_na, sort_option):
    if sysFlag in ['xquant', 'big_data']:
        table_name1 = 'xquant_data.' + table_name
    else:
        table_name1 = table_name
    sql_use = get_sql_use(table_name1, trading_codes, factor_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)


def _fill_df(df, trading_codes, date_list, rpt_date=False, fill_na=True, sort_option=True, func_name=None):
    if isinstance(date_list, tuple):
        if func_name == "_get_finance_idct":
            date_list1 = get_all_qtr(int(date_list[0]), int(date_list[-1]))
            date_list1 = [str(i) for i in date_list1]
            date_list2 = tradingDay(date_list[0], date_list[-1])
            date_list = list(set(date_list1 + date_list2))
            date_list.sort()
        elif func_name in ["_get_finance_report", "get_divid"]:
            date_list = get_all_qtr(int(date_list[0]), int(date_list[-1]))
            date_list = [str(i) for i in date_list]
        else:
            date_list = tradingDay(date_list[0], date_list[-1])
    elif isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(trading_codes, str):
        trading_codes = [trading_codes]
    if trading_codes:
        trading_codes = list(set(trading_codes))
    date_list = list(set(date_list))
    field_date = 'tdate'
    if rpt_date:
        df['rpt_date'] = df['rpt_date'].apply(int)
        df.set_index([field_date, 'tradingcode', 'rpt_date'], inplace=True)
    else:
        df.set_index([field_date, 'tradingcode'], inplace=True)
    if sort_option:
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
    if sort_option:
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


def get_finance_idct(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取财务分析因子数据
    :param trading_codes: 股票代码或股票代码列表
    :param date_list: 日期(string 或 int)或多个日期的列表
    :param factor_list: 因子或因子列表
    :return: 索引为[日期,股票] 的MultiIndex DataFrame
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    if not trading_codes:
        raise Exception("股票不能为空或None！")
    if not factor_list:
        raise Exception("因子不能为空或None！")
    ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_d_financialanalysisindex", "factor_day_financialanalysisindex_part1",
                          "factor_day_financialanalysisindex_part2", "factor_day_financialanalysisindex_part3",
                          "factor_day_financialanalysisindex_part4", "factor_day_financialanalysisindex_part5",
                          "factor_d_financialanalysisindex_ext"]:
                raise Exception("只支持查询财务分析因子数据！")
            df1 = _get_finance_idct(c_name, tb, trading_codes, date_list, f_table[tb], fill_na, sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_finance_idct(c_name, table_name, trading_codes, date_list, field_list, fill_na, sort_option):
    if sysFlag in ['xquant', 'big_data']:
        table_name1 = 'xquant_data.' + table_name
    else:
        table_name1 = table_name
    sql_use = get_sql_use(table_name1, trading_codes, field_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    func_name = sys._getframe().f_code.co_name
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option, func_name=func_name)


def get_stock_info(trading_codes, factor_list, fill_na=True):
    """
    获取股票最新信息
    :param trading_codes: 股票或股票列表
    :param factor_list: 股票信息字段或列表
    :return: DataFrame
    """
    c_name = __get_cname()
    if not trading_codes:
        raise Exception("股票不能为空或None！")
    if not factor_list:
        raise Exception("因子不能为空或None！")
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    elif len(f_table) == 1:
        table_name = list(f_table.keys())[0]
        if table_name not in ["factor_d_newmsgindex", "factor_day_newmsgindex"]:
            raise Exception("只支持查询股票最新消息的因子数据！")
        if sysFlag in ['xquant', 'big_data']:
            table_name1 = 'xquant_data.' + table_name
        else:
            table_name1 = table_name
        sql_use = get_sql_use(table_name1, trading_codes, f_table[table_name])
        df = dml.getAllByPandas(c_name, sql_use)
    else:
        raise Exception("只支持查询股票最新消息的因子数据！")
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


def get_finance_report(trading_codes, date_list, factor_list, statement_type="408001000", fill_na=True,
                       sort_option=True):
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
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    if not trading_codes:
        raise Exception("股票不能为空或None！")
    if not factor_list:
        raise Exception("因子不能为空或None！")
    ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_d_financialreportindex", "factor_day_financialreportindex",
                          "factor_d_issuingdateindex", "factor_day_issuingdateindex"]:
                raise Exception("只支持查询财务报告的因子数据！")
            df1 = _get_finance_report(c_name, tb, trading_codes, date_list, f_table[tb], statement_type, fill_na,
                                      sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_finance_report(c_name, table_name, trading_codes, date_list, field_list, statement_type, fill_na, sort_option):
    if table_name in ["factor_d_issuingdateindex", "factor_day_issuingdateindex"]:
        statement_type = None
    if sysFlag in ['xquant', 'big_data']:
        table_name1 = 'xquant_data.' + table_name
    else:
        table_name1 = table_name
    sql_use = get_sql_use(table_name1, trading_codes, field_list, date_list, statement_type)
    df = dml.getAllByPandas(c_name, sql_use)
    func_name = sys._getframe().f_code.co_name
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option, func_name=func_name)


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


def tradingDay(startTime, endTime, frequency='DAY', dayType=None, dateType='TRADINGDAYS', location='CN'):
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
    :param location: 股票市场，'CN':国内A股，'HK':港股，'US':美股，默认为'CN'
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
    exchangecode_dict = {'CN': 105, 'HK': 161, 'US': 301}
    exchangecode = exchangecode_dict.get(location)

    if not exchangecode:
        raise Exception("【location】参数支持'CN':国内A股，'HK':港股，'US':美股，请重新输入！")
    c_name = __get_cname()
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
    if sysFlag in ['xquant', 'big_data']:
        table1 = 'xquant_wind.pub_tradingday'
        table2 = 'xquant_wind.pub_allnatuday'
    else:
        table1 = 'pub_tradingday'
        table2 = 'pub_allnatuday'
    if frequency == "DAY":
        if _is_valid_date(endTime):
            if istradingday:
                sql_use = "select tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select natuday as tradingday from {2} where (natuday>={0} and natuday <= {1}) order by natuday".format(
                    startTime, endTime, table2)
        elif endTime > 0:
            if endTime > 10000:
                endTime = 10000
            if istradingday:
                sql_use = "select tradingday from {4} where tradingday>='{1}' and exchangecode = {3} {0} order by tradingday limit {2}".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select natuday as tradingday from {2} where natuday>={0} order by natuday limit {1}".format(
                    startTime, endTime, table2)
        elif endTime < 0:
            if endTime < -10000:
                endTime = -10000
            if istradingday:
                sql_use = "select tradingday from {4} where tradingday<='{1}' and exchangecode = {3} {0} order by tradingday desc limit {2}".format(
                    istradingday, startTime, abs(endTime), exchangecode, table1)
            else:
                sql_use = "select natuday as tradingday from {2} where natuday<={0} order by natuday desc limit {1}".format(
                    startTime, abs(endTime), table2)
        else:
            raise ValueError("日期格式为yyyymmdd，frequency为DAY时endTime可取值不为0的整数，请重新输入！")
    elif frequency == "WEEK":
        if not _is_valid_date(endTime):
            raise ValueError("日期格式yyyymmdd，int(20180102) 或string('20180102')！")
        if dayType in ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'):
            if istradingday:
                sql_use = "select tradingday from {5} where (tradingday>='{1}' and tradingday <= '{2}') and dayname(tradingday)='{3}' and exchangecode = {4} {0} order by tradingday".format(
                    istradingday, startTime, endTime, dayType, exchangecode, table1)
            else:
                sql_use = "select natuday as tradingday from {3} where (natuday>={0} and natuday <= {1}) and dayname(natuday)='{2}' order by natuday".format(
                    startTime, endTime, dayType, table2)
        elif dayType == "FIRSTDAY":
            if istradingday:
                sql_use = "select min(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday),week(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select min(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday),week(natuday) order by natuday".format(
                    startTime, endTime, table2)
        elif dayType == "LASTDAY":
            if istradingday:
                sql_use = "select max(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday),week(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select max(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday),week(natuday) order by natuday".format(
                    startTime, endTime, table2)
        else:
            raise ValueError("dayType取值请参考帮助文档，请重新输入！")
    elif frequency == "MONTH":
        if dayType == "FIRSTDAY":
            if istradingday:
                sql_use = "select min(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday),month(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select min(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday),month(natuday) order by natuday".format(
                    startTime, endTime, table2)
        else:
            if istradingday:
                sql_use = "select max(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday),month(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select max(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday),month(natuday) order by natuday".format(
                    startTime, endTime, table2)
    elif frequency == "QUARTER":
        if dayType == "FIRSTDAY":
            if istradingday:
                sql_use = "select min(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday),QUARTER(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select min(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday),QUARTER(natuday) order by natuday".format(
                    startTime, endTime, table2)
        else:
            if istradingday:
                sql_use = "select max(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday),QUARTER(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select max(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday),QUARTER(natuday) order by natuday".format(
                    startTime, endTime, table2)
    elif frequency == "HALFYEAR":
        if dayType == "FIRSTDAY":
            if istradingday:
                sql_use = "select min(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} and month(tradingday) in (6,12) group by year(tradingday),month(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select min(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) and month(natuday) in (6,12) group by year(natuday),month(natuday) order by natuday".format(
                    startTime, endTime, table2)
        else:
            if istradingday:
                sql_use = "select max(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} and month(tradingday) in (6,12) group by year(tradingday),month(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select max(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) and month(natuday) in (6,12) group by year(natuday),month(natuday) order by natuday".format(
                    startTime, endTime, table2)

    elif frequency == "YEAR":
        if dayType == "FIRSTDAY":
            if istradingday:
                sql_use = "select min(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select min(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday) order by natuday".format(
                    startTime, endTime, table2)
        else:
            if istradingday:
                sql_use = "select max(tradingday) as tradingday from {4} where (tradingday>='{1}' and tradingday <= '{2}') and exchangecode = {3} {0} group by year(tradingday) order by tradingday".format(
                    istradingday, startTime, endTime, exchangecode, table1)
            else:
                sql_use = "select max(natuday) as tradingday from {2} where (natuday>={0} and natuday <= {1}) group by year(natuday) order by natuday".format(
                    startTime, endTime, table2)
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
        if len(date) == 8:
            return True
        else:
            return False
    except ValueError:
        return False


def __get_stock_name(dml, c_name, dateTime, use_prev_name=True):
    if sysFlag in ['xquant', 'big_data']:
        table1 = 'xquant_wind.asharepreviousname'
        table2 = 'xquant_wind.asharedescription'
    else:
        table1 = 'asharepreviousname'
        table2 = 'asharedescription'
    if use_prev_name == True:
        sql_name = """select s_info_windcode as STOCK_CODE,s_info_name as STOCK_NAME,begindate,enddate
                 from {0} where BEGINDATE<='{1}' and ('{2}'<=ENDDATE or ENDDATE is null)""".format(table1, dateTime, dateTime)
        # sql_name.format(table1, dateTime, dateTime)
        data_name = dml.getAll(c_name, sql_name)
        df_name = pd.DataFrame(data_name[1:], columns=data_name[0])
        df_name.set_index('STOCK_CODE', inplace=True)
    else:
        sql_des = "select s_info_windcode as STOCK_CODE,s_info_name as STOCK_NAME from {0}".format(table2)
        data_des = dml.getAll(c_name, sql_des)
        df_name = pd.DataFrame(data_des[1:], columns=data_des[0])
        df_name.set_index('STOCK_CODE', inplace=True)
    return df_name


def hset(plateType, dateTime, plateID, weightType=0, use_prev_name=True):
    """
    通过输入的板块类型、时间和板块ID，输出该板块的成分股，如果是指数板块的时候，还会返回成分股的权重
    :param plateType:参数类型，目前只支持行业板块(INDUSTRY)、指数板块(INDEX)、市场板块(MARKET)三个类型
    :param dateTime:查询日期，格式yyyymmdd,例如:20100801。内部也支持dateTime传列表，以获取更快的更新速度，会提前返回结果。
    :param plateID:当plateType为指数板块时，plateID输入为指数代码,如：'HS300'，详见参数说明；
                    当plateType 为行业板块时，plateID为行业代码，如： 'CITICS.b106040700'、'SW.6110'，详见参数说明
                    支持的行业请参见行业代码表；
                    当plateType 为市场板块时，plateID可取'ALLA'(全部A股)，'SHA'(上海A股)，'SZA'(深圳A股)等，详见参数说明
                    当plateType 为概念板块时，plateID可取“职业教育“，”超导“等等，详见参数说明
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
    - MarketType 市场分类代码
        ========    ==============
        类型名称    类型说明
        ALLA        全部A股
        SHA         上海A股
        SZA         深圳A股
        ALLA_HIS    全部A股历史上的股票
        SME         中小板
        GEM         创业板
        STI         科创板
        ========  ==============
    """
    c_name = __get_cname()
    if isinstance(dateTime, int):
        dateTime = str(dateTime)
    elif not isinstance(dateTime, str) and not isinstance(dateTime, list):
        raise Exception("查询日期，格式为yyyymmdd(str or int),例如:20100801")
    if isinstance(dateTime, str):
        if not is_valid_date(dateTime, date_type='year_month_day'):
            raise Exception("【dateTime】的日期为YYYYMMDD格式，如 '20200330'")
    else:
        for i in dateTime:
            if not is_valid_date(i, date_type='year_month_day'):
                raise Exception("【dateTime】的日期为YYYYMMDD格式，如 '20200330'")
    if sysFlag in ['xquant', 'big_data']:
        table_index1 = 'xquant_wind.inx_componentweight'
        table_index2 = 'xquant_wind.inx_component'
        table_index3 = 'xquant_wind.news_csinextdayweight'
        table_ind_csrc = 'xquant_wind.ASHARESECNINDUSTRIESCLASS'
        table_ind_citics = 'xquant_wind.ASHAREINDUSTRIESCLASSCITICS'
        table_ind_sw = 'xquant_wind.ASHARESWINDUSTRIESCLASS'
        table_market1 = 'xquant_wind.ashareeodprices'
        table_market2 = 'xquant_wind.asharepreviousname'
        table_market3 = 'xquant_wind.asharedescription'
    else:
        table_index1 = 'inx_componentweight'
        table_index2 = 'inx_component'
        table_index3 = 'news_csinextdayweight'
        table_ind_csrc = 'ASHARESECNINDUSTRIESCLASS'
        table_ind_citics = 'ASHAREINDUSTRIESCLASSCITICS'
        table_ind_sw = 'ASHARESWINDUSTRIESCLASS'
        table_market1 = 'ashareeodprices'
        table_market2 = 'asharepreviousname'
        table_market3 = 'asharedescription'

    icode_dict = {'SZ50': '000016', 'HS300': '000300', 'ZZ500': '000905'}
    if plateType == "INDEX":
        if plateID[:6] in ['000002', '399001', ]:  # '000905', '000016', '000300',
            sql = """
  SELECT 
       b.secucode,
       {tdate} as tradingday,
       (case b.exchangecode when 101 then concat(b.tradingcode,'.SH') when 105 then concat(b.tradingcode,'.SZ') end) as stock,
       INDATE,
       OUTDATE
  FROM INX_COMPONENT B
 WHERE B.NEWSTATUS = 1
    and INDATE <= {tdate}
    and b.ICODE = {plate_id}
    and (OUTDATE >= {tdate} or OUTDATE is null)
            """.format(tdate=dateTime, plate_id=plateID[:6])
            df_mer23 = dml2.getAllByPandas(c_name, sql)
            df4 = __get_stock_name(dml2, c_name, dateTime, use_prev_name)
            df4.rename(columns={'STOCK_CODE': 'stock', 'STOCK_NAME': 'stock_name'}, inplace=True)
            df = df4.reindex(df_mer23['stock'])
            df.sort_index(inplace=True)
            df.reset_index(inplace=True)
            df[df.isnull()] = np.NAN
            dml2.close(c_name)
            return df[['stock','stock_name']]
        if plateID == "SH50":
            plateID = "SZ50"
        # 获取板块代码
        if plateID[:6] in ['000905', '000016', '000300', ]:
            icode = plateID[:6]
        elif plateID in icode_dict.keys():
            icode = icode_dict[plateID]
        else:
            raise Exception('请传入正确的palteID')
        if type(dateTime) == str:
            dateStr = dateTime
        elif type(dateTime) == list:
            dateStr = ",".join(dateTime)
        else:
            raise Exception("dateTime传入类型错误：目前只支持str和list类型！")
        # inx_component 字段 股票代码
        if weightType != 0 and weightType != 1:
            raise Exception("【weight_Type参数】int型，当plateType为指数板块(INDEX)时，0表示当日权重，1表示次日权重，请重新输入！")
        if weightType == 0:
            # inx_componentweight字段 当日股票权重
            sql3 = """select a.tradingday,a.secucode, 
                        (case exchangecode when '101' then concat(b.tradingcode,'.SH') when '105' then concat(b.tradingcode,'.SZ') end) as 'STOCK_CODE',
                        round(a.weight,4) as weight
                        from {2} a left join {3} b
                        on a.indexcode = b.indexcode and a.secucode = b.secucode
                        where a.tradingday in ({0})
                        and indate <= a.tradingday
                        and (outdate>=a.tradingday or isnull(outdate)) and icode='{1}'
            """.format(dateStr, icode, table_index1, table_index2)
            df_mer23 = dml2.getAllByPandas(c_name, sql3)
        else:
            sql3 = """
                select a.effectivedate, b.secucode,
                (case b.exchangecode when '101' then concat(b.tradingcode,'.SH') when '105' then concat(b.tradingcode,'.SZ') end) as 'STOCK_CODE',
                round(a.weight,4) as weight
                from {2} a left join {3} b on 
                a.constituentcode = b.tradingcode and a.exchangecode = b.exchangecode
                where a.effectivedate in ({0}) and a.indexcode = '{1}' and a.isvalid = 1
                and indate <= a.effectivedate
                and (outdate>=a.effectivedate or isnull(outdate)) and icode='{1}'
                """.format(dateStr, icode, table_index3, table_index2)
            df_mer23 = dml2.getAllByPandas(c_name, sql3)
        if type(dateTime) == list:
            dml2.close(c_name)
            return df_mer23
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
            sql_csrc = "select s_info_windcode as STOCK_CODE,sec_ind_code from {3} " \
                       "where substr(sec_ind_code,1,{0}) = '{1}' and entry_dt <= {2} and (remove_dt>={2} or remove_dt is null)".format(
                len(industrycode), industrycode, dateTime, table_ind_csrc)
            df_csrc = dml2.getAllByPandas(c_name, sql_csrc)
            df_csrc.set_index('STOCK_CODE', inplace=True)
            df = pd.merge(df_csrc, df_des, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df.drop('sec_ind_code', axis=1, inplace=True)
            df.reset_index(inplace=True)
        elif industry == "CITICS":
            sql_citics = "select s_info_windcode as STOCK_CODE,citics_ind_code from {3} " \
                         "where substr(citics_ind_code,1,{0}) = '{1}' and entry_dt <= {2} and (remove_dt>={2} or remove_dt is null)".format(
                len(industrycode), industrycode, dateTime, table_ind_citics)
            df_citics = dml2.getAllByPandas(c_name, sql_citics)
            df_citics.set_index('STOCK_CODE', inplace=True)
            df = pd.merge(df_citics, df_des, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
            df.drop('citics_ind_code', axis=1, inplace=True)
            df.reset_index(inplace=True)
        elif industry == "SW":
            sql_sw = "select s_info_windcode as STOCK_CODE,sw_ind_code from {3} " \
                     "where substr(sw_ind_code,1,{0}) = '{1}' and entry_dt <= {2} and (remove_dt>={2} or remove_dt is null)".format(
                len(industrycode), industrycode, dateTime, table_ind_sw)
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
                        from {2} a 
                        left join {3} b 
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
            sql_mkt = "a.s_info_windcode like '002%.SZ' or  a.s_info_windcode like '003%.SZ'"
        elif plateID == "STI":
            sql_mkt = "a.s_info_windcode like '688%.SH' "
        elif plateID == "MBA":
            sql_mkt = "(a.s_info_windcode like '60%.SH' OR a.s_info_windcode like '00%.SZ') and a.s_info_windcode not like '002%.SZ' and a.s_info_windcode not like '003%.SZ'"
        elif plateID == "ALLA_HIS":
            sql_use = """
            select a.S_INFO_WINDCODE as stock,a.S_INFO_NAME as stock_name from {1} a 
            where s_info_windcode not like 'A%' and s_info_windcode not like 'T%' 
            and a.S_INFO_LISTBOARDNAME in ('主板', '创业板', '中小企业板', '科创板')
            and  '{0}'>=a.S_INFO_LISTDATE and a.S_INFO_LISTDATE is not null""".format(dateTime, table_market3)
            df = dml2.getAllByPandas(c_name, sql_use)
            dml2.close(c_name)
            return df
        else:
            raise Exception("MARKET市场板块暂只支持 'ALLA'(全部A股)，'SHA'(上海A股)，"
                            "'SZA'(深圳A股)，'SME'(中小板)，'GEM'(创业板)，'STI'(科创板)，'ALLA_HIS'(全部A股历史历史上的股票)，请重新输入！")
        sql_use = basic_sql.format(dateTime, sql_mkt, table_market1, table_market2)
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
    elif plateType == "CONCEPT":
        sql = """
SELECT  {tdate}  as tradingday, 
       c.secucode,
       (case c.exchangecode when 101 then concat(c.tradingcode,'.SH') when 105 then concat(c.tradingcode,'.SZ') end) as stock,
       ENTRYDATE,  
       REMOVEDATE
  FROM PUB_CONCEPTIONELEM A
  JOIN PUB_CONCEPTIONTYPE B
    ON A.CONCEPTTYPECODE = B.CONCEPTTYPECODE
  JOIN PUB_SECURITIESMAIN C
    ON A.TRADINGCODE = C.TRADINGCODE
   AND C.EXCHANGECODE IN (101, 105, 111)
   AND C.SECUCATEGORYCODEII IN (1001, 1002)
 WHERE A.ISVALID = 1
   AND B.ISVALID = 1
   AND SUBSTR(B.CONCEPTTYPECODE, 1, 4) IN ('0003', '0006') -- 沪深AB和三板
   and b.CONCEPTTYPECODE = {plate_id}
   and ENTRYDATE <= {tdate}
   and (REMOVEDATE >= {tdate} OR REMOVEDATE IS NULL)
        """.format(tdate=dateTime, plate_id=plateID)
        df = dml2.getAllByPandas(c_name, sql)
        df_name = __get_stock_name(dml2, c_name, dateTime, use_prev_name)
        df_name.rename(columns={'STOCK_CODE': 'stock', 'STOCK_NAME': 'stock_name'}, inplace=True)
        df = df_name.reindex(df['stock'])
        df.sort_index(inplace=True)
        df.reset_index(inplace=True)
    else:
        raise Exception("[plateType参数]暂时仅支持行业板块(INDUSTRY)、指数板块(INDEX)、市场板块(MARKET)、概念板块（CONCEPT），请重新输入！")
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
    """
    c_name = __get_cname()
    if not isinstance(level, int) or level < 0 or level > 3:
        raise Exception("[level]行业级别，取值[0,3]之间的整数，默认0，请重新输入！")
    if sysFlag in ['xquant', 'big_data']:
        table = 'xquant_wind.Ashareindustriescode'
        table_csrc = 'xquant_wind.AshareSECNIndustriesClass'
        table_citics = 'xquant_wind.Ashareindustriesclasscitics'
        table_sw = 'xquant_wind.Ashareswindustriesclass'
    else:
        table = 'Ashareindustriescode'
        table_csrc = 'AshareSECNIndustriesClass'
        table_citics = 'Ashareindustriesclasscitics'
        table_sw = 'Ashareswindustriesclass'
    if industryType == "CSRC":
        if level > 2:
            raise Exception("证监会行业只有两级行业分类取值[0,2]之间的整数，请重新输入！")
        sql_use = "select distinct b.Industriescode, b.Industriesname " \
                  "from {1} a, {2} b " \
                  "where Substr(a.Sec_Ind_Code, 1, (2*({0}+1))) = Substr(b.Industriescode, 1, (2*({0}+1))) " \
                  "and b.INDUSTRIESCODE like '12%' and b.Levelnum = ({0}+1) and a.Cur_Sign = 1 and b.Used = 1 " \
                  "order by b.Industriescode".format(level, table_csrc, table)
    elif industryType == "CITICS":
        sql_use = "select distinct b.Industriescode, b.Industriesname " \
                  "from {1} a, {2} b " \
                  "where Substr(a.CITICS_Ind_Code, 1, (2*({0}+1))) = Substr(b.Industriescode, 1, (2*({0}+1))) " \
                  "and b.INDUSTRIESCODE like 'b1%' and b.Levelnum = ({0}+1) and a.Cur_Sign = 1 and b.Used = 1 " \
                  "order by b.Industriescode".format(level, table_citics, table)
    elif industryType == "SW":
        sql_use = "select distinct b.Industriescode, b.Industriesname " \
                  "from {1} a, {2} b " \
                  "where Substr(a.Sw_Ind_Code, 1, (2*({0}+1))) = Substr(b.Industriescode, 1, (2*({0}+1))) " \
                  "and b.INDUSTRIESCODE like '61%' and b.Levelnum = ({0}+1) and a.Cur_Sign = 1 and b.Used = 1 " \
                  "order by b.Industriescode".format(level, table_sw, table)
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
    """
    if switchFlag not in ['OFF', 'ON']:
        raise Exception("switchFlag 空值过滤标志,'OFF'不过滤空值，'ON'过滤空值，请重新输入！")
    c_name = __get_cname()
    params_dict = _handle_params(tradingcodes)
    # 股票代码
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    if isinstance(date, int):
        date = str(date)
    elif not isinstance(date, str) and not isinstance(date, list):
        raise Exception("日期为yyyymmdd格式(string 或 int) ，默认为查询当天的日期，请重新输入！")
    if not isinstance(industryLevel, int) or industryLevel < 1 or industryLevel > 3:
        raise Exception("[industryLevel]行业级别，取值[1,3]之间的整数，默认为三级行业，请重新输入！")
    if industryType == "CSRC" and industryLevel == 3:
        raise Exception("证监会只有两级分类，取[1,2]的整数！")
    if not industryType and industryLevel == 3:
        print("【WARNING】：证监会（CSRC）只有两级分类，取[1,2]的整数！")
    df_list = []

    if isinstance(date, str):
        if not is_valid_date(date, date_type='year_month_day'):
            raise Exception("【date】的日期为YYYYMMDD格式，如 '20200330'")
        dateStr = "'" + date + "'"
    if isinstance(date, list):
        for i in date:
            if not is_valid_date(i, date_type='year_month_day'):
                raise Exception("【date】的日期为YYYYMMDD格式，如 '20200330'")
        dateStr = "'" + "','".join(date) + "'"

    if sysFlag in ['xquant', 'big_data']:
        table_industry = 'xquant_wind.Ashareindustriescode'
        table_tradingday = 'xquant_wind.pub_allnatuday'
        table_csrc = 'xquant_wind.AshareSECNIndustriesClass'
        table_citics = 'xquant_wind.Ashareindustriesclasscitics'
        table_sw = 'xquant_wind.Ashareswindustriesclass'
    else:
        table_industry = 'Ashareindustriescode'
        table_tradingday = 'pub_allnatuday'
        table_csrc = 'AshareSECNIndustriesClass'
        table_citics = 'Ashareindustriesclasscitics'
        table_sw = 'Ashareswindustriesclass'

    if industryType == "CSRC" or not industryType:
        # sql1 = "select s_info_windcode as trading_code,Substr(sec_ind_code,1,2*({0}+1)) as industry_code from ASHARESECNINDUSTRIESCLASS a, where " \
        #        "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
        #     industryLevel, code_style, stock_codes, date)
        sql1 = """
        select s_info_windcode as trading_code, Substr(sec_ind_code,1,2*({0}+1)) as industry_code, b.natuday as tradingday
        from {4} a , {5} b
        where a.entry_dt <= natuday and (remove_dt>=natuday or remove_dt is null)
        and  a.s_info_windcode {1} {2} and b.natuday in ({3})
        """.format(industryLevel, code_style, stock_codes, dateStr, table_csrc, table_tradingday)
        df1 = dml2.getAllByPandas(c_name, sql1)
        df1.set_index('industry_code', inplace=True)
        if df1.empty:
            dml2.close(c_name)
            return pd.DataFrame()
        industry = list(df1.index.values)
        industry_params = _handle_params(industry)
        industry_codes = industry_params['trading_codes'][1]
        industry_style = industry_params['trading_codes'][2]
        sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from {3} " \
               "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
            industryLevel, industry_style, industry_codes, table_industry)
        df2 = dml2.getAllByPandas(c_name, sql2)
        df2.set_index('industry_code', inplace=True)
        df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
        df["industry_type"] = "证监会行业分类(2012版)"
        df_list.append(df)
    if industryType == "CITICS" or not industryType:
        # sql1 = "select s_info_windcode as trading_code,Substr(citics_ind_code,1,2*({0}+1)) as industry_code from ASHAREINDUSTRIESCLASSCITICS where " \
        #        "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
        #     industryLevel, code_style, stock_codes, date)
        sql1 = """
        select s_info_windcode as trading_code, Substr(citics_ind_code,1,2*({0}+1)) as industry_code, b.natuday as tradingday
        from {4} a , {5} b
        where a.entry_dt <= natuday and (remove_dt>=natuday or remove_dt is null)
        and  a.s_info_windcode {1} {2} and b.natuday in ({3})
        """.format(industryLevel, code_style, stock_codes, dateStr, table_citics, table_tradingday)
        df1 = dml2.getAllByPandas(c_name, sql1)
        df1.set_index('industry_code', inplace=True)
        if df1.empty:
            dml2.close(c_name)
            return pd.DataFrame()
        industry = list(df1.index.values)
        industry_params = _handle_params(industry)
        industry_codes = industry_params['trading_codes'][1]
        industry_style = industry_params['trading_codes'][2]
        sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from {3} " \
               "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
            industryLevel, industry_style, industry_codes, table_industry)
        df2 = dml2.getAllByPandas(c_name, sql2)
        df2.set_index('industry_code', inplace=True)
        df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
        df["industry_type"] = "中信行业分类"
        df_list.append(df)
    if industryType == "SW" or not industryType:
        # sql1 = "select s_info_windcode as trading_code,Substr(sw_ind_code,1,2*({0}+1)) as industry_code from ASHARESWINDUSTRIESCLASS where " \
        #        "s_info_windcode {1} {2} and entry_dt <= {3} and (remove_dt>={3} or remove_dt is null)".format(
        #     industryLevel, code_style, stock_codes, date)
        sql1 = """
        select s_info_windcode as trading_code, Substr(sw_ind_code,1,2*({0}+1)) as industry_code, b.natuday as tradingday
        from {4} a , {5} b
        where a.entry_dt <= natuday and (remove_dt>=natuday or remove_dt is null)
        and  a.s_info_windcode {1} {2} and b.natuday in ({3})
        """.format(industryLevel, code_style, stock_codes, dateStr, table_sw, table_tradingday)
        df1 = dml2.getAllByPandas(c_name, sql1)
        df1.set_index('industry_code', inplace=True)
        if df1.empty:
            dml2.close(c_name)
            return pd.DataFrame()
        industry = list(df1.index.values)
        industry_params = _handle_params(industry)
        industry_codes = industry_params['trading_codes'][1]
        industry_style = industry_params['trading_codes'][2]
        sql2 = "select industriesname as industry_name,Substr(industriescode,1,2*({0}+1)) as industry_code from {3} " \
               "where used=1 and Substr(industriescode,1,2*({0}+1)) {1} {2} and levelnum={0}+1".format(
            industryLevel, industry_style, industry_codes, table_industry)
        df2 = dml2.getAllByPandas(c_name, sql2)
        df2.set_index('industry_code', inplace=True)
        df = pd.merge(df1, df2, how='left', left_index=True, right_index=True, suffixes=('_x', '_y'))
        df["industry_type"] = "申万行业分类"
        df_list.append(df)
    if industryType != "SW" and industryType != "CSRC" and industryType != "CITICS" and industryType != None:
        dml2.close(c_name)
        raise Exception("[industryType]行业类型：'CSRC' 为证监会行业分类，'CITICS' 为中信行业分类，'SW' 为申万行业分类，默认全行业，请重新输入！")
    dml2.close(c_name)
    df = pd.concat(df_list, axis=0)  # 合并hsi查询结果
    if isinstance(date, list):
        df.loc[:, "tradingday"] = df.loc[:, "tradingday"].astype(int).astype(str)
        return df.reset_index().reindex(columns=["tradingday", "trading_code", "industry_code"])
    if df.empty:
        return df
    else:
        df.reset_index(inplace=True)
        df = df[['trading_code', 'industry_type', 'industry_code', 'industry_name']]

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

    """
    if not is_valid_date(filterDate, date_type='year_month_day'):
        raise Exception("【filterDate】的日期为YYYYMMDD格式，如20200330")
    c_name = __get_cname()
    if not stockPool:
        raise Exception('[stockFilter函数]参数stockPool为空，请重新输入！')
    if not isinstance(stockPool, list):
        raise Exception("[stockFilter函数]参数stockPool应为list类型，请重新输入！")

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
    if sysFlag in ['xquant', 'big_data']:
        table1 = 'xquant_wind.ASHAREEODPRICES'
        table2 = 'xquant_wind.asharepreviousname'
    else:
        table1 = 'ASHAREEODPRICES'
        table2 = 'asharepreviousname'
    if use_prev_name == True:
        sql_basic = """select a.S_INFO_WINDCODE as stock, b.S_INFO_NAME as stock_name
                       from {0} a 
                       left join {1} b 
                       on b.S_INFO_WINDCODE=a.S_INFO_WINDCODE
                       where  a.TRADE_DT  = '{2}' and a.S_INFO_WINDCODE in {3}
                       and b.BEGINDATE<='{4}' and ('{5}'<=ENDDATE or ENDDATE is null)
                       and {6}"""
        sql_use = sql_basic.format(table1, table2, date, tuple(stockPool), date, date, filter_cond)
    else:
        sql_use = None
    data = dml2.getAll(c_name, sql_use)
    dml2.close(c_name)
    df = pd.DataFrame(data[1:], columns=data[0])
    return df


def get_divid(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
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
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    elif isinstance(date_list, list):
        date_list.sort()
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如20200330")
    ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    factor_all = ['id', 'tradingcode', 'chiname', 'exchangecode', 'exchangename', 'tdate', 'per_div_trans',
                  'per_cashpaidbeforetax', 'per_cashpaidaftertax', 'div_aualaccmdivpershare', 'div_aualaccmdiv',
                  'div_cashpaidaftertax', 'div_cashpaidbeforetax', 'ex_dt', 'dvd_payout_dt', 'listing_dt_of_dvd_shr',
                  's_div_smtgdate', 'dvd_ann_dt', 's_div_progress', 'per_cashpaidbeforetax_declared',
                  'per_cashpaidaftertax_declared', 'eqy_record_dt', 's_div_prelandate', 's_div_baseshare', 'ann_dt',
                  's_div_object', 'entrytime', 'updatetime']
    factor_unique = ['tradingcode', 'tdate', 'eqy_record_dt', 's_div_prelandate', 'ann_dt', 's_div_baseshare',
                     's_div_object']
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
    if sysFlag in ['xquant', 'big_data']:
        table_name = "xquant_data.factor_d_dividendindex"
    else:
        table_name = "factor_day_dividendindex"
    df = pd.DataFrame()
    if factor_use:
        params_factor1 = _handle_params(factor_list=factor_use)
        # 因子
        fields = params_factor1['factor_list'][1]
        sql_use = "select tradingcode,tdate,eqy_record_dt,s_div_prelandate,ann_dt,s_div_baseshare,s_div_object,{0} " \
                  "from {5} where tradingcode {1} {2} and " \
                  "tdate {3} {4}".format(fields, code_style, stock_codes, date_style, dates, table_name)
        df = dml.getAllByPandas(c_name, sql_use)
        for i in df.columns:
            if i in factor_column:
                df[i] = df[i].astype(float)
    dml.close(c_name)
    df[df.isnull()] = np.NAN
    func_name = sys._getframe().f_code.co_name
    df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option, func_name=func_name)
    df_result.index.names = ['mddate', 'stock']
    return df_result


@utils_set_timeout(120, "sql查询超时！请缩短查询区间！")
def get_conforecast(trading_codes, date_list, factor_list, stock_type, block_type, fill_na=True, sort_option=True):
    """
    一致预期源表查询
    :param trading_codes: 股票代码
    :param date_list: 日期列表
    :param factor_list: 因子列表
    :param stock_type: 证券代码对应的代码类型，1 为A股代码；2 为指数代码；
    :param block_type:组合类型，默认4：行业，详见参数说明
    :return:
    """
    if stock_type not in [0, 1, 2]:
        raise Exception("stock_type 取值1 为A股代码；2 为指数代码 请重新输入！")
    if block_type not in [2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]:
        raise Exception("block_type 组合类型，默认4：行业，其他类型请参考帮助文档！")
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    elif isinstance(date_list, list):
        date_list.sort()
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如20200330")
    ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = str(int(time.time())) + str(threading.get_ident())
    if sysFlag == "xquant":
        dml_schema = DML_mysql(conforecast_config["schema"])
    else:
        dml_schema = dml
    trading_codes = [i.split(".")[0] for i in trading_codes]
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
        raise Exception("【ERROR】:" + str(no_factor_list) + "因子不存在！请重新查询！")
    st = []
    sst = []
    srt = []
    ssrt = []
    bbt = []
    bbrt = []

    for factor in factor_list:
        if table_index[factor_info[factor][1]] == "stock_code as tradingcode,tdate,":
            st.append(factor)
        elif table_index[factor_info[factor][1]] == "stock_code as tradingcode,tdate,rpt_date,":
            srt.append(factor)
        elif table_index[factor_info[factor][1]] == "stock_code as tradingcode,stock_type,tdate,rpt_date,":
            ssrt.append(factor)
        elif table_index[factor_info[factor][1]] == "block_code as tradingcode,block_type,tdate,rpt_date,":
            bbrt.append(factor)
        elif table_index[factor_info[factor][1]] == "block_code as tradingcode,block_type,tdate,":
            bbt.append(factor)
        elif table_index[factor_info[factor][1]] == "stock_code as tradingcode,stock_type,tdate,":
            sst.append(factor)
        else:
            raise Exception("%s因子配置设置错误！" % factor)
    total_list = [i for i in [st, srt, ssrt, sst, bbrt, bbt] if i]
    if len(total_list) > 1:
        raise Exception("不同特殊参数的因子不支持合并查询！")

    rpt_list = []
    no_rpt_list = []
    for tbl in table_factor_dict:
        select_sql = table_index[tbl]
        if select_sql.find("rpt_date") >= 0:
            rpt_list.append(",".join([i.split()[-1] for i in table_factor_dict[tbl]]))
        else:
            no_rpt_list.append(",".join([i.split()[-1] for i in table_factor_dict[tbl]]))
    if rpt_list and no_rpt_list:
        raise Exception("【ERROR】:部分返回数据带RPT_DATE字段，无法和其他因子数据合并！以下因子请再调用一次接口查询：%s ！" % (str(rpt_list)))
    df_list = []
    for tbl in table_factor_dict:
        if sysFlag in ['xquant', 'big_data']:
            table_name = 'xquant_gogoal.' + tbl
        else:
            table_name = tbl
        select_sql = table_index[tbl]
        if select_sql in [SQLTYPE.ST.value, SQLTYPE.SRT.value]:
            sql = "select " + select_sql + ",".join(
                table_factor_dict[tbl]) + " from " + table_name + " where stock_code in (" \
                  + ("'%s'," * len(trading_codes))[:-1] % (tuple(trading_codes)) + ") and tdate in (" + ",".join(
                date_list) + ")"
        elif select_sql in [SQLTYPE.SST.value, SQLTYPE.SSRT.value]:
            sql = "select " + select_sql + ",".join(
                table_factor_dict[tbl]) + " from " + table_name + " where stock_code in (" \
                  + ("'%s'," * len(trading_codes))[:-1] % (tuple(trading_codes)) + ") and tdate in (" + ",".join(
                date_list)
            if stock_type != 0:
                sql = sql + ") and stock_type = " + str(stock_type)
            else:
                sql = sql + ") and stock_type >= 4"
        elif select_sql in [SQLTYPE.BBT.value, SQLTYPE.BBRT.value]:
            sql = "select " + select_sql + ",".join(
                table_factor_dict[tbl]) + " from " + table_name + " where block_code in (" \
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
        df['tdate'] = df['tdate'].astype(float).astype(int).astype(str)
        if no_rpt_list:
            df.set_index(['tdate', 'tradingcode'], inplace=True)
        else:
            df.set_index(['tdate', 'tradingcode', 'rpt_date'], inplace=True)
        df_list.append(df)
    df = pd.concat(df_list, axis=1)
    df.reset_index(inplace=True)
    if no_rpt_list:
        df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)
    else:
        df_result = _fill_df(df, trading_codes, date_list, rpt_date=True, fill_na=fill_na, sort_option=sort_option)
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
    try:
        start_year = dt.datetime.strptime(str(start_date), "%Y%m%d").year
        end_year = dt.datetime.strptime(str(end_date), "%Y%m%d").year
    except Exception as e:
        raise Exception("日期格式不正确：{0}".format(e))
    year_list = [str(i) for i in range(start_year, end_year + 1)]
    month_date = ['0331', '0630', '0930', '1231']
    date_list_complete = [i + j for i in year_list for j in month_date]
    qtr_list = [int(i) for i in date_list_complete if (int(i) <= end_date and int(i) >= start_date)]
    return qtr_list


def get_factor_vip_data(stock, mddate, factor_names, statement_type, wind_type="wind_vip", fill_na=True,
                        sort_option=True):
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
    if not isinstance(mddate, list):
        raise Exception("【mddate】为YYYYMMDD格式的日期列表")
    for i in mddate:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如20200330")
    mddate.sort()
    ps.check_factor_date_permission(mddate[0], mddate[-1])
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
        separate_queries_list = ["factor_vip_financialanalysis_part3", "factor_vip_financialanalysis_part4"]
        for sq in separate_queries_list:
            if len(table_factor_dict) > 1 and table_factor_dict.get(sq):
                raise Exception("请分开查询以下因子：%s" % (str(table_factor_dict[sq])))
        df_list = []
        for tf in table_factor_dict:
            if tf == "factor_vip_financialanalysis_part3":
                if xquantEnv == 0:
                    tf1 = 'xquant_uct.' + tf
                else:
                    tf1 = 'xquant_data.' + tf
                sql = "select tradingcode,tdate," + ",".join(
                    table_factor_dict[
                        "factor_vip_financialanalysis_part3"]) + ",update_time from {} where tradingcode in (".format(tf1) \
                      + ("'%s'," * len(stock))[:-1] % (tuple(stock)) + ") and tdate in (" + ",".join(mddate) + \
                      ") and statement_type = %d" % statement_type
                df = dml_factor_vip.getAllByPandas(c_name, sql)
                df[df.isnull()] = np.NAN
                df.set_index(['tdate', 'tradingcode'], inplace=True)
                df_list.append(df)
            else:
                df = _select_factor_vip(table_factor_dict[tf], tf, stock, mddate, c_name)
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
    df_result = _fill_df(df, stock, mddate, fill_na=fill_na, sort_option=sort_option)
    df_result.index.names = ['mddate', 'stock']
    dml_factor_vip.close(c_name)
    return df_result


def get_mysql_column_attrs(table_name, table_schema):
    """
    :param table_name: 表名
    :param table_schema: 数据库名
    :return: dict
    """
    c_name = __get_cname()
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
    if xquantEnv == 0:
        table = 'xquant_uct.' + table
    else:
        table = 'xquant_data.' + table
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
    c_name = __get_cname()
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


def judge_table_in_mysql(table_name):
    c_name = __get_cname()
    sql_use = "select * from source_table_switch where table_name='%s' and switch=1" % table_name
    data = dml.getAll(c_name, sql_use)
    dml.close(c_name)
    if len(data) > 1:
        return True
    return False


def get_industry_data(stock, mddate, factor_names):
    """
    获取行业数据
    :param stock:
    :param mddate:
    :param factor_names:
    :return:
    """
    if not isinstance(mddate, list):
        raise Exception("【mddate】为YYYYMMDD格式的日期列表")
    for i in mddate:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如20200330")
    mddate.sort()
    ps.check_factor_date_permission(mddate[0], mddate[-1])
    df_list = []
    for factor in factor_names:
        factor_s = factor.split("_")
        new_factor = factor_s[0].upper()
        industry_level = int(factor_s[1][-1])
        df = hsi(stock, mddate, new_factor, industry_level)
        df.rename(columns={"tradingday": "tdate", "trading_code": "stock", "industry_code": factor}, inplace=True)
        df.set_index(["tdate", "stock"], inplace=True)
        df.sort_index(inplace=True)
        df_list.append(df)
    if not df_list:
        return pd.DataFrame()
    df = pd.concat(df_list, axis=1)
    return df


def get_bond_market_data(stock, mddate, factor_names, fill_na=True):
    # 获取债券行情数据
    if not isinstance(mddate, list):
        raise Exception("【mddate】为YYYYMMDD格式的日期列表")
    for i in mddate:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如20200330")
    c_name = __get_cname()
    if len(stock) == 1:
        stocks = "(" + "'" + stock[0] + "'" + ")"
    else:
        stocks = tuple(stock)
    factor_names = [i[5:] for i in factor_names]
    if len(factor_names) == 1:
        factors = factor_names[0]
    else:
        factors = ",".join(factor_names)
    if len(mddate) == 1:
        dates = "(" + "'" + mddate[0] + "'" + ")"
    else:
        dates = tuple(mddate)
    if sysFlag in ['xquant', 'big_data']:
        table_name = 'xquant_data.bond_d_marketindex'
    else:
        table_name = 'bond_d_marketindex'
    sql_use = "select tdate,tradingcode,{0} from {3} where tdate in {1} and tradingcode in {2}".format(
        factors, dates, stocks, table_name)
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    df_result = _fill_df(df, stock, mddate, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    return df_result


def get_bond_value_data(stock, mddate, factor_names, fill_na=True):
    # 获取债券估值数据
    if not isinstance(mddate, list):
        raise Exception("【mddate】为YYYYMMDD格式的日期列表")
    for i in mddate:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【mddate】的日期为YYYYMMDD格式，如20200330")
    c_name = __get_cname()
    if len(stock) == 1:
        stocks = "(" + "'" + stock[0] + "'" + ")"
    else:
        stocks = tuple(stock)
    factor_names = [i[5:] for i in factor_names]
    if len(factor_names) == 1:
        factors = factor_names[0]
    else:
        factors = ",".join(factor_names)
    if len(mddate) == 1:
        dates = "(" + "'" + mddate[0] + "'" + ")"
    else:
        dates = tuple(mddate)
    if sysFlag in ['xquant', 'big_data']:
        table_name = 'xquant_data.bond_d_valuation'
    else:
        table_name = 'bond_d_valuation'
    sql_use = "select tdate,windcode as tradingcode,{0} from {3} where tdate in {1} and windcode in {2}".format(
        factors, dates, stocks, table_name)
    df = dml.getAllByPandas(c_name, sql_use)
    dml.close(c_name)
    df_result = _fill_df(df, stock, mddate, fill_na=fill_na)
    df_result.index.names = ['mddate', 'stock']
    return df_result


def get_sql_use(table_name, trading_codes, factor_list, date_list=None, statement_type=None):
    # 处理参数
    params_dict = _handle_params(trading_codes=trading_codes, date_list=date_list, factor_list=factor_list)
    # 股票代码
    trading_codes = params_dict['trading_codes'][0]
    stock_codes = params_dict['trading_codes'][1]
    code_style = params_dict['trading_codes'][2]
    # 日期
    if date_list:
        if isinstance(date_list, tuple):
            sdate = date_list[0]
            edate = date_list[-1]
        else:
            date_list = params_dict['date_list'][0]
            dates = params_dict['date_list'][1]
            date_style = params_dict['date_list'][2]
    # 因子
    new_factor_list = params_dict['factor_list'][0]
    fields = params_dict['factor_list'][1]
    if date_list is None:
        sql_use = "select tradingcode,{0} from {1} where tradingcode {2} {3}".format(fields, table_name, code_style,
                                                                                     stock_codes)
    elif isinstance(date_list, tuple):
        sql_use = "select tdate,tradingcode,{0} from {1} where tdate >= {2} and tdate <={3} and tradingcode {4} {5}".format(
            fields, table_name, sdate, edate, code_style, stock_codes)
    else:
        sql_use = "select tdate,tradingcode,{0} from {1} where tdate {2} {3} and tradingcode {4} {5}".format(fields,
                                                                                                             table_name,
                                                                                                             date_style,
                                                                                                             dates,
                                                                                                             code_style,
                                                                                                             stock_codes)
    if statement_type:
        sql_use = sql_use + " and statement_type = {0}".format(int(statement_type))
    return sql_use


def get_factor_alph191(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取alpha因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    if not trading_codes:
        raise Exception("股票不能为空或None！")
    if not factor_list:
        raise Exception("因子不能为空或None！")
    # ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_day_alpha191_part1", "factor_day_alpha191_part2"]:
                raise Exception("只支持查询Alpha因子！")
            df1 = _get_factor_alph191(c_name, tb, trading_codes, date_list, f_table[tb], fill_na, sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_factor_alph191(c_name, table_name, trading_codes, date_list, factor_list, fill_na, sort_option):
    sql_use = get_sql_use(table_name, trading_codes, factor_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)


def get_factor_barra(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取barra因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    # ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    df_list = []
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    elif len(f_table) == 1:
        table_name = list(f_table.keys())[0]
        if table_name != "factor_day_barra":
            raise Exception("只支持查询Barra因子！")
        sql_use = get_sql_use(table_name, trading_codes, f_table[table_name], date_list)
        df = dml.getAllByPandas(c_name, sql_use)
        dml.close(c_name)
        df.set_index(["tdate", "tradingcode"], inplace=True)
        df_list.append(df)
    else:
        raise Exception("只支持查询Barra因子！")
    if not df_list:
        df = pd.DataFrame(columns=["tdate", "tradingcode"] + factor_list)
    else:
        df = df_list[0]
        df.reset_index(inplace=True)
    df_result = _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)
    df_result.index.names = ['mddate', 'stock']
    df_result[df_result.isnull()] = np.NAN
    return df_result


def get_factor_technical_analysis(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取技术面因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    # ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_day_technicalanalysis"]:
                raise Exception("只支持查询技术面因子！")
            df1 = _get_factor_technical_analysis(c_name, tb, trading_codes, date_list, f_table[tb], fill_na,
                                                 sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_factor_technical_analysis(c_name, table_name, trading_codes, date_list, factor_list, fill_na, sort_option):
    sql_use = get_sql_use(table_name, trading_codes, factor_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)


def get_index_weight_next_day_csi(dateTime, plateID):
    """
    次日权重原始数据
    :param dateTime: 查询日期
    :param plateID: 指数代码，如HS300，详见参数说明
    :return:

    - plateID 指数代码
        ============  ===========  =============
        类型名称      类型说明     数据开始日期
        HS300         沪深300指数   20050411
        ZZ500         中证500指数   20100104
        SZ50          上证50指数    20100104
        ============  ===========  =============
    """
    c_name = __get_cname()
    if isinstance(dateTime, int):
        dateTime = str(dateTime)
    elif not isinstance(dateTime, str) and not isinstance(dateTime, list):
        raise Exception("查询日期，格式为yyyymmdd(str or int),例如:20100801")
    if isinstance(dateTime, str):
        if not is_valid_date(dateTime, date_type='year_month_day'):
            raise Exception("【dateTime】的日期为YYYYMMDD格式，如 '20200330'")
    else:
        for i in dateTime:
            if not is_valid_date(i, date_type='year_month_day'):
                raise Exception("【dateTime】的日期为YYYYMMDD格式，如 '20200330'")
    icode_dict = {'SZ50': '000016', 'HS300': '000300', 'ZZ500': '000905'}
    try:
        icode = icode_dict[plateID]
    except Exception as e:
        raise Exception("【plateID】只支持SZ50、HS300、ZZ500，请重新输入！")

    if type(dateTime) == str:
        dateStr = dateTime
    elif type(dateTime) == list:
        dateTime = [str(i) for i in dateTime]
        dateStr = ",".join(dateTime)
    else:
        raise Exception("dateTime传入类型错误：目前只支持str和list类型！")
    if sysFlag in ['xquant', 'big_data']:
        table_name = 'xquant_wind.news_csinextdayweight'
    else:
        table_name = 'news_csinextdayweight'

    sql_use = """
            select * from {2} a
            where a.effectivedate in ({0}) and a.indexcode = '{1}' and a.isvalid = 1
            """.format(dateStr, icode, table_name)
    df = dml2.getAllByPandas(c_name, sql_use)
    dml2.close(c_name)
    return df


def get_factor_evaluation(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取评价因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    # ps.check_factor_date_permission(date_list[0], date_list[-1])
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    if 'listing_date' in factor_list:
        factor_list[factor_list.index('listing_date')] = 'listing_date_ps'
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_evaluation"]:
                raise Exception("只支持查询评价因子！")
            df1 = _get_factor_evaluation(c_name, tb, trading_codes, date_list, f_table[tb], fill_na,
                                                 sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
    dml.close(c_name)
    df.index.names = ['mddate', 'stock']
    df[df.isnull()] = np.NAN
    return df


def _get_factor_evaluation(c_name, table_name, trading_codes, date_list, factor_list, fill_na, sort_option):
    if 'listing_date_ps' in factor_list:
        factor_list[factor_list.index('listing_date_ps')] = 'listing_date'
    sql_use = get_sql_use(table_name, trading_codes, factor_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)

def get_factor_emotion(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取情绪类因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    if 'listing_date' in factor_list:
        factor_list[factor_list.index('listing_date')] = 'listing_date_ps'
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_day_emotion"]:
                raise Exception("只支持查询情绪类因子！")
            df1 = _get_factor_emotion(c_name, tb, trading_codes, date_list, f_table[tb], fill_na, sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
        dml.close(c_name)
        df.index.names = ['mddate', 'stock']
        df[df.isnull()] = np.NAN
        return df
def _get_factor_emotion(c_name, table_name, trading_codes, date_list, factor_list, fill_na, sort_option):
    if 'listing_date_ps' in factor_list:
        factor_list[factor_list.index('listing_date_ps')] = 'listing_date'
    sql_use = get_sql_use(table_name, trading_codes, factor_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)
def get_factor_momentum(trading_codes, date_list, factor_list, fill_na=True, sort_option=True):
    """
    获取动量类因子数据
    :param trading_codes: 单支股票代码或多支股票的列表
    :param date_list: 日期(string 或 int)或日期列表
    :param factor_list: 单个因子或因子列表
    :return:
    """
    if isinstance(date_list, str) or isinstance(date_list, int):
        date_list = [date_list]
    if isinstance(date_list, list):
        date_list = [str(date) if isinstance(date, int) else date for date in date_list]
        date_list.sort()
    elif isinstance(date_list, tuple):
        assert len(date_list) == 2
        if int(date_list[0]) > int(date_list[-1]):
            raise Exception("【date_list】元组中的开始日期大于结束日期，请重新输入！")
    else:
        raise Exception("【date_list】参数为str或list类型，请重新输入！")
    for i in date_list:
        if not is_valid_date(i, date_type='year_month_day'):
            raise Exception("【date_list】的日期为YYYYMMDD格式，如 '20200330'")
    c_name = __get_cname()
    if isinstance(factor_list, str):
        factor_list = [factor_list]
    if 'listing_date' in factor_list:
        factor_list[factor_list.index('listing_date')] = 'listing_date_ps'
    f_table = __get_f_table(factor_list)
    if len(f_table) == 0:
        raise Exception("请输入正确的因子！")
    else:
        df = pd.DataFrame()
        for tb in f_table:
            if tb not in ["factor_day_momentum"]:
                raise Exception("只支持查询动量类因子！")
            df1 = _get_factor_momentum(c_name, tb, trading_codes, date_list, f_table[tb], fill_na, sort_option)
            if df.empty:
                df = df1
            else:
                df = pd.concat([df, df1], axis=1)
        dml.close(c_name)
        df.index.names = ['mddate', 'stock']
        df[df.isnull()] = np.NAN
        return df
def _get_factor_momentum(c_name, table_name, trading_codes, date_list, factor_list, fill_na, sort_option):
    if 'listing_date_ps' in factor_list:
        factor_list[factor_list.index('listing_date_ps')] = 'listing_date'
    sql_use = get_sql_use(table_name, trading_codes, factor_list, date_list)
    df = dml.getAllByPandas(c_name, sql_use)
    return _fill_df(df, trading_codes, date_list, fill_na=fill_na, sort_option=sort_option)
