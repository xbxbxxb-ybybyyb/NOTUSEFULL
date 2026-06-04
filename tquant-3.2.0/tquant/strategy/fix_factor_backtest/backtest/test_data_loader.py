import os
import pickle
import pandas as pd
import datetime as dt
from dateutil.relativedelta import relativedelta
import fix_factor_backtest.backtest.DataAPI.DataToolkit as Dtk

depend_data_dict = {}
#SJL
# root_path = "/data/group/800080/factor_test/"
root_path = '/'.join(os.path.abspath(__file__).split('/')[:-4])+'/data/factor_test'

def get_top_group_nav_data(factor_name):
    top_group_nav_dir = os.path.join(root_path, "top_group_nav/day")
    if factor_name.startswith("Fix"):
        top_group_nav_dir = os.path.join(root_path, "top_group_nav/fix", factor_name[3:7])

    if not os.path.exists(top_group_nav_dir):
        os.makedirs(top_group_nav_dir)
        return None

    nav_files = os.listdir(top_group_nav_dir)
    if len(nav_files) == 0:
        return None

    nav_df_list = []
    for nav_file in nav_files:
        if not nav_file.startswith(factor_name):
            nav_df_list.append(pd.read_csv(os.path.join(top_group_nav_dir, nav_file), index_col=0))
    data = pd.concat(nav_df_list, axis=1)

    if len(data.columns) == 0:
        return None
    return data


def adapt_for_algorithm(factor_value, start_date, end_date):
    start_date, end_date = str(start_date), str(end_date)
    start, end = str(factor_value.index[0]), str(factor_value.index[-1])
    if start_date < start:
        start_date = start
    if end_date > end:
        end_date = end
    return factor_value[:end_date], start_date, end_date


def adapt_for_symbol(factor_name, factor_value, check_date_list, is_day_factor=True):
    start_date, end_date = str(check_date_list[0]), str(check_date_list[-1])
    start_date = dt.datetime.strptime(start_date, '%Y%m%d') - relativedelta(years=2) + relativedelta(days=1)
    start_date = start_date.strftime("%Y%m%d")

    data_start = Dtk.get_trading_day(int(start_date), int(end_date))[0]
    if is_day_factor:
        data_start = Dtk.get_n_days_off(data_start, -2)[0]
    factor_value = factor_value[str(data_start):end_date]

    if not is_day_factor:
        fix_time = factor_name[3:7] + "00"
        factor_value.index = list(map(lambda x: x.strftime('%Y%m%d') + fix_time, factor_value.index))

    factor_value.index = factor_value.index.astype(int)
    index_list = list(factor_value.index)
    index_list_datetime = Dtk.convert_date_or_time_int_to_datetime(index_list)
    index_list_timestamp = [i.timestamp() for i in index_list_datetime]
    factor_value.index = index_list_timestamp
    return factor_value, int(start_date), int(end_date)
