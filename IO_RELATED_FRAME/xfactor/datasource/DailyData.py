import pandas as pd
import os
import settings


# 获取日频数据
def get_data(data_type, stock_list, start_date, end_date, factor_name):
    if data_type == "stock":
        df = pd.read_pickle(os.path.join(settings.DAILY_DATA_PATH, "{}.pkl".format(factor_name)))
        df = df.loc[start_date: end_date]
        # df = df.reindex(stock_list, axis=1)
    elif data_type == "index":
        df = pd.read_pickle(os.path.join(settings.DAILY_DATA_PATH, "index", "{}.pkl".format(factor_name)))
        df = df.loc[start_date: end_date]
        df = pd.DataFrame(df[stock_list].stack(), columns=[factor_name]).unstack()
    return df


def filter_data_type(depend_data_type_list):
    return list(filter(lambda x: "Basic_factor." in x and "_minute" not in x, depend_data_type_list))
