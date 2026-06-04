# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name:     Factor_DB
   Description :  因子数据库相关操作
   Author :       K0380044
   date:          2019/7/16
-------------------------------------------------
   Change Activity:
                   2019/7/16:
-----------------------------------pip--------------
"""
import pandas as pd, os, sys
from tquant.logger import setup_logging
# 导入工程库
basedir = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
sys.path.append(basedir)
tquant_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), '../../..'))
sys.path.insert(0, tquant_dir)



class Factor():
    # 设置因子名称
    name = None
    # 获取数据的时间窗口长度
    max_window = 3
    # 股票池筛选
    stock_pool = 'ALLA'
    # 设置依赖因子
    person_dependencing = []
    public_dependencing = []

    def __init__(self, logger_path = '/tmp/factor_data/logs'):
        super(Factor, self).__init__()
        self.tb_name = None  # 因子数据表
        self.log = setup_logging(logger_name='quant_info', dirPath = logger_path)  # log_file

    def calc(self, person_data, public_data, trade_day):
        """
        :param person_data:
        :param public_data:
        :param trade_day: 当日计算交易日
        :return:pandas.Series,index是股票代码，value因子值
        """
        # print(person_data, public_data)
        df1 = pd.DataFrame()
        return df1


if __name__ == '__main__':
    fc = Factor()
