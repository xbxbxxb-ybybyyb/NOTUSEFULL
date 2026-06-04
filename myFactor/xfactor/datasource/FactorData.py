import os
import pandas as pd


# 从因子库中获取因子
def get_data(factor_lib, stock_list, start_date, end_date, factor_name):
    file = os.path.join(factor_lib, "{}.pkl".format(factor_name))
    df = pd.read_pickle(file)
    df = df.loc[start_date: end_date]
    return df