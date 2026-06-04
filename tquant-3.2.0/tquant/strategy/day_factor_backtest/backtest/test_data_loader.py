# coding:utf-8
import os
import pickle
import datetime as dt
import pandas as pd
from tquant.strategy.day_factor_backtest.backtest.is_valid_raw import is_valid_raw
from tquant.strategy.day_factor_backtest.backtest.is_universe import update_is_universe
from tquant import StockData
from tquant import BasicData

sd = StockData()
bd = BasicData()

# bie
industry_code_all_dict = {}

depend_data_dict = {}
#SJL root_path = "/data/group/800080/factor_test/"
root_path = '/'.join(os.path.abspath(__file__).split('/')[:-3]) + "/backtest_data/factor_test/"
daily_store_path = os.path.join(root_path, "daily")
excess_return_root = os.path.join(root_path, "excess_return")

# bie
def get_industry_code_all(start_date, end_date):
    date_list = bd.get_trading_day(start_date, end_date)
    trading_codes = sd.get_plate_info('MARKET', end_date, 'ALLA_HIS').loc[:, 'stock'].tolist()
    df = sd.get_stock_industry(trading_codes, date_list, 'SW', industry_level=1)
    df.set_index(['tradingday', 'trading_code'], inplace=True)
    df_ind = df['industry_code']
    df_ind.index.names = [None,None]
    df_res = df_ind.unstack(level=1)
    return df_res

# bie
def get_mkt_cap_ard(start_date, end_date):
    # 交易日期列表
    date_list = bd.get_trading_day(start_date, end_date)
    # 截止end_date的全历史股票
    trading_codes = sd.get_plate_info('MARKET', end_date, 'ALLA_HIS').loc[:, 'stock'].tolist()
    data = sd.get_factor_valuation_metrics(trading_codes, date_list, ['mkt_cap_ard'])
    data.reset_index(inplace=True)
    data.set_index(['mddate', 'stock'],inplace=True)
    df_mkt_cap_ard = data['mkt_cap_ard']
    data.index.names = [None, None]
    df = df_mkt_cap_ard.unstack(level=1)
    return df

# bie
def get_price_data(price_type, start_date, end_date):
    # 交易日期列表
    date_list = bd.get_trading_day(start_date, end_date)
    # 截止end_date的全历史股票
    trading_codes = sd.get_plate_info('MARKET', end_date, 'ALLA_HIS').loc[:, 'stock'].tolist()
    df_adj = sd.get_factor_price_daily(trading_codes, date_list, [price_type, 'adjfactor'])
    df_adj[price_type + '_adj'] = df_adj[price_type] * df_adj['adjfactor']
    df_adj.reset_index(inplace=True)
    df_adj.set_index(['mddate', 'stock'], inplace=True)
    df_price_type = df_adj[price_type + '_adj']
    df_price_type.index.names = [None, None]
    df_price_type = df_price_type.unstack(level=1)
    return df_price_type

# bie
def get_is_valid_raw(update_date):
    data = depend_data_dict.get("is_valid_raw")
    if data is not None:
        return data
    data = is_valid_raw(update_date)
    depend_data_dict["is_valid_raw"] = data
    return data
#
# bie
def get_is_universe(start_date, end_date):
    df = update_is_universe(start_date, end_date)
    return df

