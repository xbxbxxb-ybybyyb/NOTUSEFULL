import os
import shutil
import pickle
import pandas as pd
import numpy as np
import datetime as dt
from dateutil.relativedelta import relativedelta
from tquant.psfactor import PsFactorData
from tquant.stock_data import StockData
from tquant.basic_data import BasicData
from tquant.strategy.factor_tester.is_valid_raw import is_valid_raw

sd = StockData()
bd = BasicData()
tps = PsFactorData()


def get_industry_code_all(start_date, end_date):
    # bie
    date_list = bd.get_trading_day(start_date, end_date)
    trade_edate = bd.get_trading_day(end_date, -5)[-1]
    trading_codes = sd.get_plate_info('MARKET', trade_edate, 'ALLA_HIS').loc[:, 'stock'].tolist()
    df = sd.get_stock_industry(trading_codes, date_list, 'SW', industry_level=1)
    df.set_index(['tradingday', 'trading_code'], inplace=True)
    df_ind = df['industry_code']
    df_ind.index.names = [None, None]
    data = df_ind.unstack(level=1)

    return data[start_date:end_date]


def get_mkt_cap_ard(start_date, end_date):
    # bie
    date_list = bd.get_trading_day(start_date, end_date)
    trade_edate = bd.get_trading_day(end_date, -5)[-1]
    trading_codes = sd.get_plate_info('MARKET', trade_edate, 'ALLA_HIS').loc[:, 'stock'].tolist()
    df = sd.get_factor_valuation_metrics(trading_codes, date_list, ['mkt_cap_ard'])
    df.reset_index(inplace=True)
    df.set_index(['mddate', 'stock'], inplace=True)
    df_mkt_cap_ard = df['mkt_cap_ard']
    df_mkt_cap_ard.index.names = [None, None]
    data = df_mkt_cap_ard.unstack(level=1)
    return data[start_date:end_date]


def get_price_data(price_type, start_date, end_date):
    # bie
    trade_edate = bd.get_trading_day(end_date, -5)[-1]
    date_list = bd.get_trading_day(str(start_date), str(end_date))
    stock_list = sd.get_plate_info('MARKET', trade_edate, 'ALLA_HIS')['stock'].tolist()
    md_list = [price_type, 'adjfactor']
    md_dict = {}
    for fac in md_list:
        sub_df = sd.get_factor_price_daily(stock_list, date_list, [fac], fill_na=True).iloc[:, 0].unstack()
        sub_df.replace(0.0, np.nan, inplace=True)
        sub_df.fillna(method='ffill', inplace=True)
        sub_df.index.name = 'dt'
        # sub_df.index = pd.DatetimeIndex(sub_df.index)
        md_dict[fac] = sub_df
    md_dict['%s_adj' % (price_type)] = md_dict[price_type] * md_dict['adjfactor']
    data = md_dict['%s_adj' % (price_type)]
    return data


def get_is_valid_raw(start_date, update_date):
    # bie
    data = is_valid_raw(start_date, update_date)
    return data


def get_is_universe(start_date, end_date):
    # bie
    trade_edate = bd.get_trading_day(end_date, -5)[-1]
    stock_list = sd.get_plate_info('MARKET', trade_edate, 'ALLA_HIS')['stock'].tolist()
    df = sd.get_factor_evaluation(stock_list, (start_date, end_date), ['alpha_universe'])
    data = df['alpha_universe'].unstack()

    data = data.astype(float)
    return data


def get_factor_names(is_day_factor, factor_name):
    factor_list = get_all_factors()
    if is_day_factor:
        return list(filter(lambda x: x[:3] != "Fix", factor_list))
    else:
        pre_fix = factor_name[:9]
        return list(filter(lambda x: x.startswith(pre_fix), factor_list))


def get_all_factors():
    # bie research用project_id，release用space_id
    factor_list = tps.get_library_info()[os.environ.get('space_id') + '_DAY']
    if factor_list is None:
        # bie
        raise Exception("can not access space_id: " + os.environ.get('space_id'))
    return set(factor_list)


# def save_excess_return(factor_name, factor_excess, price_type, local):
#     tmp_path = test_data_local_path if local else test_data_server_path
#     factor_path = os.path.join(tmp_path, factor_name)
#     print(factor_path)
#     if not os.path.exists(factor_path):
#         os.makedirs(factor_path)
#     if factor_excess is not None:
#         factor_excess_name = os.path.join(factor_path, 'excess_return-' + price_type + '.pkl')
#         if os.path.exists(factor_excess_name):
#             os.remove(factor_excess_name)
#         pickle.dump(factor_excess, open(factor_excess_name, 'wb'))


def temp_save_daily_excess_return(factor_name, factor_excess, path):
    if not os.path.exists(path):
        os.makedirs(path)
    if factor_excess is not None:
        factor_excess_name = os.path.join(path, factor_name + '.pkl')
        if os.path.exists(factor_excess_name):
            os.remove(factor_excess_name)
        pickle.dump(factor_excess, open(factor_excess_name, 'wb'))


def check_factor_result(factor_result):
    if factor_result is None or len(factor_result) == 0:
        raise Exception("factor data is not valid !")

    day_factor_set = set()
    fix_factor_set = set()
    # factor_list = get_all_factors()
    for factor_name in factor_result.keys():
        # if factor_name in factor_list:
        #     raise Exception(factor_name + " already in factor lib: " + factor_lib)
        if factor_name.startswith("Fix"):
            fix_factor_set.add(factor_name[8:])
        else:
            day_factor_set.add(factor_name)
    if len(day_factor_set) > 1:  # or len(fix_factor_set) > 1
        raise Exception("more than one factor exists: day= " + str(day_factor_set) + " fix=" + str(fix_factor_set))


def adapt_for_analysis(factor_value, start_date, end_date):
    start_date, end_date = str(start_date), str(end_date)
    start, end = str(factor_value.index[0]), str(factor_value.index[-1])
    if start_date < start:
        start_date = start
    if end_date > end:
        end_date = end
    return factor_value[:end_date], start_date, end_date
