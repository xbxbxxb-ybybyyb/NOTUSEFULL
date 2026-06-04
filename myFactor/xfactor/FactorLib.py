import os
import pandas as pd
import numpy as np

class FactorLib(object):

    # 因子库地址
    def __init__(self, path):
        if not os.path.isdir(path):
            raise Exception("因子库路径错误：reason='invalid directory'")
        self.root_path = path

    def get_factor_name_list(self, factor_type=None):
        factor_name_list = set()
        for file in os.listdir(self.root_path):
            if file.endswith(".pkl"):
                factor_name = file.split(".")[0]
                if factor_type == "DAY":
                    if factor_name.startswith("Fix"):
                        continue
                    else:
                        factor_name_list.add(factor_name)
                elif factor_type == "FIX":
                    if factor_name.startswith("Fix"):
                        factor_name_list.add(factor_name)
                    else:
                        continue
                else:
                    factor_name_list.add(factor_name)
        return factor_name_list

    def get_factor_cls_name_list(self, factor_type=None):
        factor_list = self.get_factor_name_list(factor_type)
        if factor_type == "DAY":
            return factor_list
        elif factor_type == "FIX":
            return list(set([x[8:] for x in factor_list]))
        else:
            return list(set([x[8:] if x.startswith("Fix") else x for x in factor_list]))

    # 获取因子文件
    def get_factor_file(self, factor_name):
        return os.path.join(self.root_path, "{}.pkl".format(factor_name))

    # 判断因子是否存在
    # factor_name 可以是一个列表
    def is_factor_exists(self, factor_name):
        factor_file = self.get_factor_file(factor_name)
        return os.path.exists(factor_file)

    # 获取因子值
    def get_factor_value(self, factor_name, start_date=None, end_date=None):
        if not self.is_factor_exists(factor_name):
            raise Exception("因子不存在: factor_name={}".format(factor_name))
        file = self.get_factor_file(factor_name)
        df = pd.read_pickle(file)
        if start_date is not None and end_date is not None:
            df = df.loc[start_date:end_date]
        elif start_date is not None and end_date is None:
            df = df.loc[start_date:]
        elif start_date is None and end_date is not None:
            df = df.loc[:end_date]
        return df

    # 更新因子值
    def update_factor_value(self, factor_name, factor_value):
        if self.is_factor_exists(factor_name):
            df = self.get_factor_value(factor_name)
            df.drop(index=factor_value.index, inplace=True, errors="ignore")
            result = pd.concat([df, factor_value], sort=True)
        else:
            result = factor_value
        result.index.name = 'mddate'
        result.columns.name = 'stock'
        result.replace(np.inf, np.nan, inplace=True)
        result.replace(-np.inf, np.nan, inplace=True)
        result.sort_index(inplace=True)
        result.to_pickle(self.get_factor_file(factor_name))
