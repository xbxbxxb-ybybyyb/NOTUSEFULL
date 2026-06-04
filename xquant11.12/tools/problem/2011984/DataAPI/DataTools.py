import pandas as pd
import numpy as np
from DataAPI.TradingDay import trading_day
from Utils.UtilsCode import code_classify, get_code_status
from xquant.factordata import FactorData


fa = FactorData()


def get_stock_daily_result(code_list, date_list, factor_name_list):
    """获取股票日频数据，factor_name_list为：[high, open, close, low, volume（手）, amt（千元）, pre_close]"""
    date_list = list(map(str, date_list))
    code_type = list(set([code_classify(code) for code in code_list]))
    if code_type == ['stock']:
        data = fa.get_factor_value('Basic_factor', code_list, mddate=date_list, factor_names=factor_name_list)
    elif code_type == ['cb']:
        data = fa.get_factor_value('Basic_factor', code_list, mddate=date_list, factor_names=factor_name_list, category='bond')
    else:
        raise ValueError
    return data


def get_pre_close(code, date):
    pre_close = get_stock_daily_result([code], [date], ['pre_close'])['pre_close'].values[0]
    return pre_close


def get_stock_minute_result(code_list, date_list, factor_name, method=1):
    # factor_name为：high, open, close, low, volume, amt, numtrade
    # method=1为从Basic_factor库中取(推荐取多只股票，转债不行)，method=2为从ZeusDataLib库中取（推荐取单只股票）
    date_list = list(map(str, date_list))
    if method == 1:
        data = fa.get_factor_value("Basic_factor", code_list, mddate=date_list, factor_names=["{}_minute".format(factor_name)],
                                   return_single_factor=True, daily_bar_num=240)
        data['time'] = [str(x).split(' ')[1] for x in data.index]
        data['M_Date'] = [str(x).split(' ')[0].replace('-', '') for x in data.index]
        data = data.set_index(['M_Date', 'time'])
        return data
    else:
        factor_name_map = {'high': 'M_HighPrice', 'open':'M_OpenPrice', 'close':'M_ClosePrice', 'low': 'M_LowPrice',
                           'volume': 'M_Volume', 'amt': 'M_Amount', 'numtrade': 'M_NumTrades'}
        date_list = list(map(str, date_list))
        res_list = []
        for code in code_list:
            # print(code)
            res_market = fa.get_factor_value('ZeusDataLib', code, '20200102', ["M_Date", "M_Time", factor_name_map[factor_name]])
            res1 = res_market.set_index('M_Date').loc[date_list]
            res1['time'] = ['{}:{}:00'.format(x[0:2], x[2:4]) for x in res1['M_Time']]
            res2 = res1.reset_index().set_index(['M_Date', 'time'])[factor_name_map[factor_name]]
            res_list.append(res2)
        res_df = pd.concat(res_list, axis=1)
        res_df.columns = code_list
        return res_df


def single_minute_data(code, date_list, factor_name_list):
    factor_name_map = {'high': 'M_HighPrice', 'open': 'M_OpenPrice', 'close': 'M_ClosePrice', 'low': 'M_LowPrice',
                       'volume': 'M_Volume', 'amt': 'M_Amount', 'numtrade': 'M_NumTrades'}
    factor_name_map_revert = dict(zip(factor_name_map.values(), factor_name_map.keys()))
    date_list = list(map(str, date_list))
    factor_list = [factor_name_map[x] for x in factor_name_list]
    data_df = fa.get_factor_value('ZeusDataLib', code + '_M', '20200102', ["M_Date", "M_Time"] + factor_list)
    data_df = data_df.rename(columns={'M_Date': 'date'})
    data_df = data_df.set_index('date').loc[date_list]
    data_df = data_df.dropna()
    data_df['time'] = ['{}:{}:00'.format(x[0:2], x[2:4]) for x in data_df['M_Time']]
    data_df = data_df[['time'] + factor_list]
    data_df = data_df.rename(columns=factor_name_map_revert)
    return data_df


def transfer_multi_min_data(min_data_df, min_period=1):
    """将1min的股票数据转换成n分钟的股票数据"""
    all_trade_date = list(sorted(set(min_data_df.index)))
    data_out = []
    for trade_date in all_trade_date:
        data_single = min_data_df.loc[trade_date]
        data_transfer = pd.DataFrame(index=data_single.index)
        data_transfer['time'] = data_single['time']
        data_transfer['high'] = data_single['high'].rolling(min_period).max().shift(-min_period + 1)
        data_transfer['open'] = data_single['open']
        data_transfer['low'] = data_single['low'].rolling(min_period).min().shift(-min_period + 1)
        data_transfer['close'] = data_single['close'].shift(-min_period + 1)
        data_transfer['volume'] = data_single['volume'].rolling(min_period).sum().shift(-min_period + 1)
        data_transfer['amt'] = data_single['amt'].rolling(min_period).sum().shift(-min_period + 1)
        data_transfer = data_transfer.dropna()
        data_out.append(data_transfer)
    data_out = pd.concat(data_out)
    return data_out


def get_tag_data(code, trade_date):
    lib_name = 'Model20200501'
    tag_data = fa.get_factor_value(lib_name, code, str(trade_date),
                                   ['timestamp', 'tag1minLong', 'tag1minShort', 'tag2minLong', 'tag2minShort', 'tag5minLong', 'tag5minShort'])
    return tag_data.set_index('timestamp')


def load_lib_data(code, all_trading_days, signal_lib, columns):
    """原始tick行情数据库为：ZeusDataLib"""
    all_data = []
    for trade_date in all_trading_days:
        try:
            data = fa.get_factor_value(signal_lib, code, str(trade_date), columns)
            all_data.append(data)
        except:
            print(f"no signal data in library {signal_lib}: {code} {trade_date}")
            continue
    if len(all_data) > 0:
        return pd.concat(all_data)
    return pd.DataFrame()


def get_index_data(code, st_date, ed_date, factor_name_list):
    # 读取指数数据，中证全指000985.CSI，中证转债000832.CSI
    # factor_name_list可以取close, amt, pre_close
    st_date, ed_date = str(st_date.replace('-', '')), str(ed_date.replace('-', ''))
    date_list = trading_day(st_date, ed_date)
    if code == '000832.SH'or code == '000832.CSI':
        factor_name_map = {'high': 'D_HighPrice', 'open': 'D_OpenPrice', 'close': 'D_ClosePrice', 'low': 'D_LowPrice',
                           'volume': 'D_Volume', 'amt': 'D_Amount', 'pre_close': 'D_PreviousClose'}
        factor_list = [factor_name_map[x] for x in factor_name_list]
        index_data = fa.get_factor_value('ZeusDataLib', '000832.SH', '20200102', ['D_Date'] + factor_list).set_index('D_Date')
        factor_name_map_revert = dict(zip(factor_name_map.values(), factor_name_map.keys()))
        index_data = index_data.rename(columns=factor_name_map_revert).loc[st_date: ed_date]
    else:
        index_data = fa.get_factor_value('Basic_factor', [code], date_list, factor_name_list).droplevel(1)
    return index_data


def get_index_intra_data(trade_date, index_code='000300.SH', frequency='min'):
    """获取指数日内数据，frequency为分钟频（min）或tick频率（tick）"""
    close = fa.get_factor_value('ZeusDataLib', index_code, '20200102', ["D_Date", "D_ClosePrice"]).set_index("D_Date")
    pre_close = close.shift(1).loc[trade_date].values[0]
    if frequency == 'tick':  # tick频
        data = fa.get_factor_value('ZeusDataLib', index_code, str(trade_date), ["T_Time", "T_LastPrice"])
        data['time'] = ['{}:{}:{}'.format(x[0:2], x[2:4], x[4:6]) for x in data['T_Time']]
        data['T_Pct'] = data['T_LastPrice'] / pre_close - 1
        data = data.set_index('time')[["T_LastPrice", "T_Pct"]]
    elif frequency == 'min':  # 分钟频
        data = fa.get_factor_value('ZeusDataLib', index_code, '20200102', ["M_Date", "M_Time", "M_ClosePrice"])
        data = data[data['M_Date'] == str(trade_date)]
        data['time'] = ['{}:{}:{}'.format(x[0:2], x[2:4], x[4:6]) for x in data['M_Time']]
        data['M_Pct'] = data['M_ClosePrice'] / pre_close - 1
        data = data.set_index('time')[["M_ClosePrice", "M_Pct"]]
    else:
        raise ValueError
    data.columns = ['index_close', 'index_pct']
    return data


def check_lib_existing(signal_lib_list):
    # 判断因子库是否存在
    signal_lib_info = fa.get_library_info()
    signal_lib_all = list(signal_lib_info.keys())
    if isinstance(signal_lib_list, str):
        signal_lib_list = [signal_lib_list]
    for signal_lib in signal_lib_list:
        if signal_lib in signal_lib_all:
            print(f'{signal_lib} √')
        else:
            print(f'{signal_lib} ×')


def existing_code_in_lib(signal_lib, trade_date, code_list):
    existing_code_list = fa.search_by_date(signal_lib, trade_date, code_list)
    return existing_code_list


def check_lib_code_existing(signal_lib, trade_date, code_list):
    # 判断一个因子库中，某个日期，股票列表是否都存在
    existing_code_list = fa.search_by_date(signal_lib, trade_date, code_list)
    no_existing_list = list(sorted(set(code_list) - set(existing_code_list)))
    if len(no_existing_list) > 0:
        code_status = get_code_status(no_existing_list, str(trade_date))
        no_existing_list = [x for (x, y) in code_status.items() if y not in ['停牌', 'N']]
    return no_existing_list
