import pandas as pd
import os
import random


def select_factor():
    factor_df = pd.read_pickle("ret_stat.pkl")
    factor_df['voli'] = factor_df['max_ret'] - factor_df['ave_ret']
    res_max = list(factor_df.sort_values(by='max_ret')['factor_name'][:600].values)
    res_ave = list(factor_df.sort_values(by='ave_ret')['factor_name'][:600].values)
    res_voli = list(factor_df.sort_values(by='voli', ascending=False)['factor_name'][:600].values)
    res = list(set(res_max).union(res_ave, res_voli))
    return res


def select_factors(factors_file_path, factors_nums):
    factor_file_list = []
    for root, dirs, files in os.walk(factors_file_path):
        for file in files:
            factor_file_list.append(file[:-4])
    factor_file_list_sample = random.sample(factor_file_list, factors_nums)
    return factor_file_list_sample
