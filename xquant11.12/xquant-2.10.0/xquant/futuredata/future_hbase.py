# _*_ coding:utf-8 _*_

import happybase
import datetime as dt
import pandas as pd
from .future_enum import *

from xquant.thirdpartydata.marketdata import MarketData

connection = happybase.Connection('168.61.38.14')

def get_change_date(symbol, date, contract_type):
    """
    获取主力合约的信息
    :param symbol:合约品种符号，如rb, cu等，为字符串
    :param date:查询日期，str或int型，如'20190702'或20190702
    :param contract_type: 合约类型，主力合约为'ZL00'，次主力合约为'ZL01'
    :return:包含当日主力合约名称（如rb1809），主力合约换仓日和移仓合约名称
    """
    if contract_type not in ['ZL00', 'ZL01']:
        raise Exception("[contract_type参数]合约类型，主力合约为'ZL00'，次主力合约为'ZL01'，请重新输入！")
    table = connection.table('BT_FUTURES:CONTRACT_ZL_INFO')
    if isinstance(date, int):
        date = str(date)
    # table.scan(row_key_start,row_key_end) 为前闭后开，查询date当天的主力合约，date需加1
    date = dt.datetime.strftime(dt.datetime.strptime(date, '%Y%m%d') + dt.timedelta(1), '%Y%m%d')
    row_key_start = symbol + contract_type + '20170101'
    row_key_end = symbol + contract_type + date
    df = pd.DataFrame()
    for key, value in table.scan(row_key_start, row_key_end):
        df_value = pd.DataFrame(value, pd.Index([key]))
        df = pd.concat([df, df_value])
    df.reset_index(drop=True, inplace=True)
    column_dict = {}
    for column in df.columns:
        column_dict[column] = _decode_column_name(column)
        df[column] = df[column].str.decode('utf-8')
    df.rename(columns=column_dict, inplace=True)
    if df is None or df.empty:
        return
    df['TDATE'] = df['TDATE'].astype(int)
    df['ZL_STARTDATE'] = df['ZL_STARTDATE'].astype(int)
    df['ZL_ENDDATE'] = df['ZL_ENDDATE'].astype(int)
    tdate = max(df['TDATE'].tolist())
    df.set_index('TDATE', inplace=True)
    ZL_MAPPINGCODE = df.loc[tdate, 'ZL_MAPPINGCODE']
    ZL_STARTDATE = df.loc[tdate, 'ZL_STARTDATE']
    ZL_STARTDATE_LIST = list(set(df['ZL_STARTDATE'].tolist()))
    ZL_STARTDATE_LIST.remove(ZL_STARTDATE)
    if len(ZL_STARTDATE_LIST) >= 1:
        PRE_ZL_STARTDATE = max(ZL_STARTDATE_LIST)
        PRE_ZL_MAPPINGCODE = df.loc[PRE_ZL_STARTDATE, 'ZL_MAPPINGCODE']
    else:
        PRE_ZL_MAPPINGCODE = ZL_MAPPINGCODE
    dataList = [ZL_MAPPINGCODE, ZL_STARTDATE, PRE_ZL_MAPPINGCODE]
    return dataList


def _decode_column_name(column):
    column_name = column.decode('utf-8')
    column_name = column_name.split(':')[-1]
    return column_name


def get_instrument_all(symbol, start_date, end_date):
    """
    获取某一个期货品种在时间区间内的所有合约列表
    :param symbol:合约品种符号，如rb, cu等，为字符串
    :param start_date:起始日期 int或str 如20170101或'20170101'
    :param endDate:终止日期 int或str 如20190702或'20190702'
    :return:返回指定时间区间内，所有的合约列表。(按日期从近到远排列）
    """
    if isinstance(start_date, str):
        start_date = int(start_date)
    if isinstance(end_date, str):
        end_date = int(end_date)

    table = connection.table('BT_FUTURES:CONTRACT_ALL_INFO')
    row_key_start = _create_params(symbol, 10, 1)
    row_key_end = _create_params(symbol, 99, 13)
    value_list = []
    index_list = []
    for key, value in table.scan(row_key_start, row_key_end):
        value_list.append(value)
        index_list.append(key)
    df = pd.DataFrame(value_list, pd.Index(index_list))

    df.reset_index(drop=True, inplace=True)
    column_dict = {}
    for column in df.columns:
        column_dict[column] = _decode_column_name(column)
        df[column] = df[column].str.decode('utf-8')
    df.rename(columns=column_dict, inplace=True)
    df['STARTDATE'] = df['STARTDATE'].astype(int)
    df['ENDDATE'] = df['ENDDATE'].astype(int)
    df = df[(df['STARTDATE'] >= start_date) & (df['ENDDATE'] <= end_date)]
    df.sort_values(by='HTSCCODE', ascending=False, inplace=True)
    InstrumentList = df['HTSCCODE'].tolist()
    return InstrumentList


def _get_htsc_contract_suffix(contract):
    CF_CONTRACT_LIST = ['IF', 'IC', 'IH']
    SHF_CONTRACT_LIST = ['CU', 'AL', 'ZN', 'PB', 'NI', 'SN', 'AU', 'AG', 'RB', 'WR', 'HC', 'SC', 'FU', 'BU', 'RU', 'SP']
    ZCE_CONTRACT_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP',
                         'TA', 'FG', 'SF', 'MA', 'ZC', 'SM']
    DCE_CONTRACT_LIST = ['C', 'CS', 'A', 'B', 'M', 'Y', 'P', 'FB', 'BB', 'JD',
                         'L', 'V', 'PP', 'J', 'JM', 'I', 'EG']
    if contract in CF_CONTRACT_LIST:
        return 'CF'
    elif contract in SHF_CONTRACT_LIST:
        return 'SHF'
    elif contract in ZCE_CONTRACT_LIST:
        return 'ZCE'
    elif contract in DCE_CONTRACT_LIST:
        return 'DCE'
    else:
        raise Exception('Unknown contract: {}'.format(contract))


def _create_params(contract, year, month):
    ZCE_CONTRACT_LIST = ['WH', 'SR', 'RS', 'LR', 'CJ', 'PM', 'OI', 'RM', 'CY', 'CF', 'RI', 'JR', 'AP',
                         'TA', 'FG', 'SF', 'MA', 'ZC', 'SM']
    year_str = str(year)
    month_str = str(month) if month > 9 else '0' + str(month)
    suffix = _get_htsc_contract_suffix(contract)
    year_str = year_str if contract not in ZCE_CONTRACT_LIST else year_str[1]
    code = "{}{}{}.{}".format(contract, year_str, month_str, suffix)
    return code

def get_instrument_info(symbol):
    # 获取任一期货合约的具体属性
    table = connection.table('BT_FUTURES:CONTRACT_PROPERTY')
    row_key_strat = symbol
    row_key_end = symbol
    df_value = pd.DataFrame()
    for key, value in table.scan(row_key_strat, row_key_end):
        df_value = pd.DataFrame(value, pd.Index([key]))
    if df_value.empty:
        return
    else:
        df_value.reset_index(drop=True, inplace=True)
        column_dict = {}
        for column in df_value.columns:
            column_dict[column] = _decode_column_name(column)
            df_value[column] = df_value[column].str.decode('utf-8')
        df_value.rename(columns=column_dict, inplace=True)
        # df_value = df_value.T
        # try:
        #     df_value.rename(columns={0:"PROPERTY"},inplace=True)
        # except:
        #     pass
        return df_value


def get_future_data(symbol, startTime, endTime, barSize, method=False, contract_type='ZL00'):
    """
    调取期货行情数据
    :param symbol: 普通合约名称（如RB1808），主力合约输入品种名+ZL（如RBZL）
    :param startTime:起始日期,string类型，如'20190102000000000'
    :param endTime:终止日期，string类型，如'20190102235900000'
    :param barSize:数据周期枚举类，支持1day(KLINE_TYPE.K_DAY), 1min(KLINE_TYPE.K_1MIN), tick(KLINE_TYPE.TICK)
    :param method:是否复权，默认False 不复权
    :return:
    """
    assert len(startTime) == 17
    assert len(endTime) == 17
    if symbol[-2:] == "ZL":
        if barSize == KLINE_TYPE.K_DAY:
            startTime = startTime[:8]
            endTime = endTime[:8]
            table = connection.table('BT_FUTURES:MDKLine_1D')
            row_key_start = symbol[:-2] + contract_type + "{}000000000".format(startTime)
            row_key_end = symbol[:-2] + contract_type + "{}235900000".format(endTime)

        elif barSize == KLINE_TYPE.K_1MIN:
            table = connection.table('BT_FUTURES:MDKLine_1M')
            # scan取数据为左闭右开
            endTime = str(int(endTime) + 100000)
            row_key_start = symbol[:-2] + contract_type + startTime
            row_key_end = symbol[:-2] + contract_type + endTime

        elif barSize == KLINE_TYPE.TICK:
            table = connection.table('BT_FUTURES:MDTick')
            # scan取数据为左闭右开
            endTime = str(int(endTime) + 100)
            row_key_start = symbol[:-2] + contract_type + startTime
            row_key_end = symbol[:-2] + contract_type + endTime
        else:
            raise Exception(
                "[barSize参数]暂时只支持支持1day(KLINE_TYPE.K_DAY), 1min(KLINE_TYPE.K_1MIN), tick(KLINE_TYPE.TICK)，请重新输入！")
        value_list = []
        index_list = []
        for key, value in table.scan(row_key_start, row_key_end):
            value_list.append(value)
            index_list.append(key)
        df = pd.DataFrame(value_list, pd.Index(index_list))
        if df.empty:
            return
        else:
            df.reset_index(drop=True, inplace=True)
            column_dict = {}
            for column in df.columns:
                column_dict[column] = _decode_column_name(column)
                df[column] = df[column].str.decode('utf-8')
            df.rename(columns=column_dict, inplace=True)
        for col in df.columns:
            try:
                if col not in ['MDDate', 'MDTime']:
                    df[col] = df[col].astype(float)
            except:
                pass
        if method:
            df.set_index('MDDate', inplace=True)
            ZL_CODE = list(set(df['ZL_MAPPINGCODE'].tolist()))
            date_list_e = []
            date_list_s = []
            for i in ZL_CODE:
                date_s = min(df[df["ZL_MAPPINGCODE"] == i].index.values)
                date_e = max(df[df["ZL_MAPPINGCODE"] == i].index.values)
                date_list_e.append(date_e)
                date_list_s.append(date_s)
            date_list_e.sort()
            date_list_s.sort()
            assert len(date_list_s) == len(date_list_e)
            row_key_s = symbol[:-2] + contract_type + date_list_e[0]
            row_key_e = symbol[:-2] + contract_type + "20990101"
            df = _get_zl_adj(date_list_s, date_list_e, df, row_key_s, row_key_e)
            df.reset_index(inplace=True)
    else:
        ma = MarketData()
        month = int(symbol[-2:])
        try:
            date_len = 4
            year = int(symbol[-4:-2])
        except:
            date_len = 3
            year = int(symbol[-3:-2])

        code = _create_params(symbol[:-date_len], year, month)
        if barSize == KLINE_TYPE.K_DAY:
            startTime = startTime[:8]
            endTime = endTime[:8]
            start_date = '{}000000000'.format(startTime)
            end_date = '{}235900000'.format(endTime)
            df = ma.getMDSecurityKLineDataFrame(code, start_date, end_date, 10, 25)
        elif barSize == KLINE_TYPE.K_1MIN:
            df = ma.getMDSecurityKLineDataFrame(code, startTime, endTime, 10, 20)
        elif barSize == KLINE_TYPE.TICK:
            df = ma.getMDSecurityTickDataFrame(code, startTime, endTime, 1)
        else:
            raise Exception(
                "[barSize参数]暂时只支持支持1day(KLINE_TYPE.K_DAY), 1min(KLINE_TYPE.K_1MIN), tick(KLINE_TYPE.TICK)，请重新输入！")
    return df


def _get_zl_adj(date_list_s, date_list_e, df, row_key_start, row_key_end):
    table_name = "BT_FUTURES:CONTRACT_ZL_INFO"
    table = connection.table(table_name)
    df_zl = pd.DataFrame()
    for key, value in table.scan(row_key_start, row_key_end):
        df_value = pd.DataFrame(value, pd.Index([key]))
        df_zl = pd.concat([df_zl, df_value])
    if df_zl.empty:
        return
    else:
        df_zl.reset_index(drop=True, inplace=True)
        column_dict = {}
        for column in df_zl.columns:
            column_dict[column] = _decode_column_name(column)
            df_zl[column] = df_zl[column].str.decode('utf-8')
        df_zl.rename(columns=column_dict, inplace=True)
    df_zl.set_index('TDATE', inplace=True)
    df_zl.sort_index(inplace=True)
    df_zl['ZL_ADJ'] = df_zl['ZL_ADJ'].astype(float)
    df_zl['ZL_ADJ'].fillna(0.0, inplace=True)
    df_zl.sort_index(ascending=False, inplace=True)
    df_zl['ADJ_VALUE'] = df_zl['ZL_ADJ'].cumsum()
    # # 前复权列名 "OpenPx","HighPx","LowPx","ClosePx","OpenPxAdj","HighPxAdj","LowPxAdj","ClosePxAdj"
    for i in range(len(date_list_s)):
        df.loc[date_list_s[i]:date_list_e[i], 'OpenPxAdj'] = df.loc[date_list_s[i]:date_list_e[i], 'OpenPx'] + \
                                                             df_zl.loc[date_list_e[i], 'ADJ_VALUE']
        df.loc[date_list_s[i]:date_list_e[i], 'HighPxAdj'] = df.loc[date_list_s[i]:date_list_e[i], 'HighPx'] + \
                                                             df_zl.loc[date_list_e[i], 'ADJ_VALUE']
        df.loc[date_list_s[i]:date_list_e[i], 'LowPxAdj'] = df.loc[date_list_s[i]:date_list_e[i], 'LowPx'] + \
                                                            df_zl.loc[date_list_e[i], 'ADJ_VALUE']
        df.loc[date_list_s[i]:date_list_e[i], 'ClosePxAdj'] = df.loc[date_list_s[i]:date_list_e[i], 'ClosePx'] + \
                                                              df_zl.loc[date_list_e[i], 'ADJ_VALUE']
    return df
