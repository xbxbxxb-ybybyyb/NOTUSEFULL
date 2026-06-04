import pandas as pd
import numpy as np
from copy import deepcopy
import datetime as dt
from tquant import StockData
from tquant import BasicData

sd = StockData()
bd = BasicData()


def wrangle_up_down_limit(price, pre_close, is_valid_raw, limit=0.1):
    is_valid_hf = is_valid_raw.copy()
    is_valid_hf[pre_close * (1 - limit) >= price] = 0
    is_valid_hf[pre_close * (1 + limit) <= price] = 0
    return is_valid_hf


def wrangle_valid(date_list, stock_list, raw_data):
    list_date = raw_data['listing_date']
    delist_date = raw_data['delisting_date']
    trade_status = raw_data['trade_status']
    stpt = raw_data['stpt']
    report_trading_date = raw_data['report_trading_date']
    date_list_timestamp = pd.to_datetime(date_list, format='%Y%m%d')
    isValid = np.ones((len(date_list), len(stock_list)), dtype=int)
    # Proceed new listing stocks
    isValid[:, list_date > date_list[-1]] = 0
    report_trading_date_mx = report_trading_date.reshape(1, -1).T * np.ones(len(stock_list))
    date_list_mx = date_list.reshape(1, -1).T * np.ones(len(stock_list))

    if np.sum(list_date <= date_list[-1]) > 0:
        list_position = np.where(report_trading_date_mx >= list_date)
        list_position = pd.DataFrame(index=['row', 'col'], data=np.array(list_position)).T
        list_position = list_position.groupby(['col'], as_index=False).min().values.T
        stk_less_120 = list_position[1, :] + 120 >= len(report_trading_date)
        list_position_120 = deepcopy(list_position)
        list_position_120[1, stk_less_120] = -1
        list_position_120[1, ~stk_less_120] += 120

        # vectorized implementation
        list_date_120 = report_trading_date_mx[list_position_120[1, :], list_position_120[0, :]]
        isValid_list = isValid[:, list_position_120[0, :]]
        isValid_list[date_list_mx[:, list_position_120[0, :]] <= list_date_120] = 0
        isValid[:, list_position_120[0, :]] = isValid_list

    num_trade_days = (trade_status.astype(str) != 'nan').rolling(window=60, min_periods=1).sum()
    min_num = 60 * np.ones(trade_status.shape)
    min_num[:59] = np.linspace(1, 59, 59).astype(int).reshape(1, -1).T * np.ones(len(trade_status.columns))
    min_num = pd.DataFrame(index=trade_status.index, columns=trade_status.columns, data=min_num)
    isValid[num_trade_days.loc[date_list_timestamp] < min_num.loc[date_list_timestamp]] = 0

    # Proceed delisting stocks
    isValid[date_list_mx >= delist_date] = 0

    # bct_data
    isValid_bct = deepcopy(isValid)

    # Proceed suspension stocks
    isValid_bct[np.logical_or(trade_status.loc[date_list_timestamp] == '停牌',
                              trade_status.astype(str).loc[date_list_timestamp] == 'nan')] = 0
    isValid_bct[stpt > 0] = 0
    isValid_bct_pd = pd.DataFrame(index=date_list_timestamp, columns=stock_list, data=isValid_bct)
    is_valid_raw = deepcopy(isValid_bct_pd)
    return is_valid_raw.replace(0, np.nan)


def wrangle_report_apply_date(date_list, stock_list, stm_issuingdate, quarter_date, report_trading_date):
    report_apply_date = np.zeros((len(date_list), len(stock_list))) * np.nan
    quarter_date_mx = np.repeat(np.array(quarter_date).reshape(len(quarter_date), 1), len(stock_list), axis=1)
    for i, dt in enumerate(date_list):
        report_apply_date[i] = pd.DataFrame(np.where(stm_issuingdate <= int(dt), \
                                                     quarter_date_mx, np.nan)).fillna(method='ffill').iloc[-1].values
    return report_apply_date


def get_raw_data(date_list, stock_list, trade_start_date):
    raw_data = {}
    temp1 = sd.get_factor_newsmsg(stock_list, ['listing_date', 'delisting_date'])
    basic_factors = ['close', 'pre_close', 'open', 'vwap']
    temp2 = sd.get_factor_price_daily(stock_list, date_list, basic_factors)
    raw_data['listing_date'] = temp1['listing_date'].reindex(index=stock_list).values
    raw_data['delisting_date'] = temp1['delisting_date'].reindex(index=stock_list).values
    for f in basic_factors:
        raw_data[f] = temp2[f].unstack().reindex(columns=stock_list).values
    trade_status_date = bd.get_trading_day(trade_start_date, date_list[-1])
    trade_status = sd.get_factor_price_daily(stock_list, trade_status_date, ['trade_status'])[
        'trade_status'].unstack().reindex(columns=stock_list)
    trade_status.index = pd.to_datetime(trade_status.index)
    raw_data['trade_status'] = trade_status
    stpt = np.ones((len(date_list), len(stock_list)))
    for i, item in enumerate(date_list):
        temp = sd.stock_filter(stock_list, int(item), 'STPT').set_index('stock')['stock_name']
        if len(temp) == 0:
            stpt[i] = 0
        else:
            idx = ~temp.reindex(stock_list).isnull().values
            stpt[i, idx] = 0
    raw_data['stpt'] = stpt
    ### calculate quarter date and report trading date
    start_date = int(date_list[0])
    start_year = np.floor(start_date / 10000) - 1
    end_date = int(date_list[-1])
    end_year = np.floor(end_date / 10000)
    all_year = np.arange(start_year, end_year + 1)
    all_quarter = np.array([331, 630, 930, 1231])
    quarter_date = all_year.reshape(len(all_year), 1).dot(np.ones((1, len(all_quarter)))) * 10000 + np.ones(
        (len(all_year), 1)).dot(all_quarter.reshape(1, len(all_quarter)))
    quarter_date = list(quarter_date[quarter_date < end_date].astype('int').astype('str'))
    report_trading_date = bd.get_trading_day(int(start_year * 10000 + 101), int(end_date))
    report_trading_date = np.array(report_trading_date).astype('int')
    stm_issuingdate = sd.get_factor_financial_report(stock_list, quarter_date,
                                                     ['stm_issuingdate']).stm_issuingdate.astype('float').unstack()
    stm_issuingdate = stm_issuingdate.reindex(columns=stock_list).values

    raw_data['quarter_date'] = np.array(quarter_date).astype('int')
    raw_data['report_trading_date'] = report_trading_date
    raw_data['stm_issuingdate'] = stm_issuingdate
    return raw_data


def is_valid_raw(start_date, update_date):
    # bie 测试环境数据不全 暂改为20180102
    # date_list = bd.get_trading_day('20090101', update_date)
    date_list = bd.get_trading_day(start_date, update_date)
    # 截止end_date的全历史股票
    stock_list = sd.get_plate_info('MARKET', update_date, 'ALLA_HIS').loc[:, 'stock'].tolist()
    raw_data = get_raw_data(date_list, stock_list, start_date)
    raw_valid = wrangle_valid(np.array([int(d) for d in date_list]), stock_list, raw_data)
    raw_valid.index.name = 'index'
    raw_valid.reset_index(inplace=True)
    raw_valid['index'] = raw_valid['index'].apply(lambda x: x.strftime('%Y%m%d'))
    raw_valid.set_index('index', inplace=True)
    raw_valid.index.name = None
    return raw_valid
