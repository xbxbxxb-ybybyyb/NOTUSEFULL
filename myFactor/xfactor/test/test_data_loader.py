import os
import shutil
import pickle
import pandas as pd
import datetime as dt
from xfactor.FactorLib import FactorLib
from settings import X_FACTOR_LIB, VALID_FACTOR_LIB
from dateutil.relativedelta import relativedelta
import xfactor.test.symbol_team.DataAPI.DataToolkit as Dtk

depend_data_dict = {}
factor_lib1 = FactorLib(X_FACTOR_LIB)
factor_lib2 = FactorLib(VALID_FACTOR_LIB)
root_path = "/data/group/800080/factor_test/"
daily_store_path = os.path.join(root_path, "daily")
excess_return_root = os.path.join(root_path, "excess_return")
top_group_nav_root = os.path.join(root_path, "top_group_nav")
test_data_local_path = "/tmp/"
test_data_server_path = "/data/group/800080/factor_test/test_data/"
fix_inlib_factors_path = os.path.join(root_path, "inlib_info/inlibfixfactors_dict.pkl")
fix_inlib_factors_path_bk = os.path.join(root_path, "inlib_info/inlibfixfactors_dict_bk.pkl")

day_inlib_factors_path = "/data/group/800002/alpha_factor/test/depend_data/day/inlib_dct/inlibdayfactors.pkl"
day_inlib_factors_path_bk = "/data/group/800002/alpha_factor/test/depend_data/day/inlib_dct/inlibdayfactors_bk.pkl"
top_group_nav_path = "/data/group/800002/alpha_factor/test/depend_data/fix/excess_return"

orth_factors_path = '/data/group/800002/alpha_factor/test/depend_data/day/orth_basis_value_daily/'
factors_spe_IC_path = '/data/group/800002/alpha_factor/test/depend_data/day/res_effi/resic.pkl'
label_path_for_NonLinearIC = '/data/group/800002/alpha_factor/test/depend_data/day/label/'


def check_factor_result(factor_result):
    if factor_result is None or len(factor_result) == 0:
        raise Exception("factor data is not valid !")

    day_factor_set = set()
    fix_factor_set = set()
    for factor_name in factor_result.keys():
        if factor_name.startswith("Fix"):
            fix_factor_set.add(factor_name[8:])
        else:
            day_factor_set.add(factor_name)
    if len(day_factor_set) > 1 or len(fix_factor_set) > 1:
        raise Exception("more than one factor exists: day= " + str(day_factor_set) + " fix=" + str(fix_factor_set))
    if len(fix_factor_set) == 1 and len(factor_result) < 7:
        raise Exception("fix factor: " + str(fix_factor_set) + " has no seven time points value")


def merge_test_data(factor_names, local=False):
    tmp_path = test_data_local_path if local else test_data_server_path
    for factor_name in factor_names:
        factor_path = os.path.join(tmp_path, factor_name)
        if not os.path.exists(factor_path):
            raise Exception(factor_path + " not exists, do factor test first")

        file_map = {}
        excess_return_type = "vwap"
        test_data_files = os.listdir(factor_path)

        for test_data_file in test_data_files:
            file_path = os.path.join(factor_path, test_data_file)
            if test_data_file.startswith("excess_return"):
                excess_return_type = test_data_file[:-4].split('-')[-1]
                file_map["excess_return"] = file_path
            elif test_data_file.startswith("top_group_nav"):
                file_map["top_group_nav"] = file_path
            else:
                os.remove(file_path)

        # if factor_name.startswith("Fix"):
        #     if set(["top_group_nav"]).symmetric_difference(file_map.keys()):
        #         raise Exception("test data file for " + factor_name + " is not valid: " + str(test_data_files))
        # else:
        #     if set(["excess_return"]).symmetric_difference(file_map.keys()):
        #         raise Exception("test data file for " + factor_name + " is not valid: " + str(test_data_files))

        if "excess_return" in file_map:
            merge_to_excess_return_dir(factor_name, excess_return_type, file_map["excess_return"])
        if "top_group_nav" in file_map:
            merge_to_top_group_nav_dir(factor_name, file_map["top_group_nav"])
    print("save test data finished: ", str(factor_names))


def merge_to_excess_return_dir(factor_name, excess_return_type, excess_return_file):
    dst = os.path.join(excess_return_root, excess_return_type, factor_name + '.pkl')
    shutil.copy(excess_return_file, dst)


def merge_to_top_group_nav_dir(factor_name, file_path):
    ans_df = pd.read_pickle(file_path)
    ans_df.name = factor_name
    start_dt = 20160401
    end_dt = 20200331
    import numpy as np
    trading_dates = Dtk.get_trading_day(start_dt, end_dt)
    year_month_list = sorted(np.unique([str(item)[:6] for item in trading_dates]))
    for year_month in year_month_list:
        save_path = '{}/{}_minute_ret.pkl'.format(top_group_nav_path, year_month)
        start = year_month + '01'
        end = year_month + '31'
        days = Dtk.get_trading_day(int(start), int(end))
        check_exists = os.path.exists(save_path)
        if check_exists:
            ori_df = pd.read_pickle(save_path)
        task_factors = [factor_name]
        if task_factors.__len__() == 0:
            continue
        if check_exists:
            final_df = pd.concat([ori_df, ans_df.loc[str(min(days)):str(max(days))]], axis=1)
        else:
            final_df = ans_df.loc[str(min(days)):str(max(days))]
        final_df.to_pickle('{}/{}_minute_ret.pkl'.format(top_group_nav_path, year_month))


def get_top_group_nav_data(factor_name, factors_inlib_thetime_inem):
    if factor_name.startswith("Fix"):
        top_group_nav_dir = os.path.join(root_path, "top_group_nav/fix", factor_name[3:7])
    else:
        raise Exception("only support Fix")

    if not os.path.exists(top_group_nav_dir):
        os.makedirs(top_group_nav_dir)
        return None

    nav_files = os.listdir(top_group_nav_dir)
    if len(nav_files) == 0:
        return None

    nav_df_list = []
    for nav_file in nav_files:
        if not nav_file.startswith(factor_name) and nav_file[:-4] in factors_inlib_thetime_inem:
            nav_df_list.append(pd.read_csv(os.path.join(top_group_nav_dir, nav_file), index_col=0))
    data = pd.concat(nav_df_list, axis=1).fillna(0)

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


def save_top_group_data(factor_name, top_group_nav, local):
    tmp_path = test_data_local_path if local else test_data_server_path
    factor_path = os.path.join(tmp_path, factor_name)
    if not os.path.exists(factor_path):
        os.makedirs(factor_path)
    if top_group_nav is not None:
        file_name = os.path.join(factor_path, "top_group_nav.pkl")
        if os.path.exists(file_name):
            os.remove(file_name)
        top_group_nav.to_pickle(file_name)
