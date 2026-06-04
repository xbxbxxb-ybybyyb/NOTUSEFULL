# -*- coding: utf-8 -*-

"""Base Factor"""
import ray
import pandas as pd
import os
from tqdm import trange
from SmartFactor.util.data_context import get_trade_days, get_stocks_pool
from SmartFactor.util.util import get_factor_attr, parse_extra_data
from SmartFactor import setup_logging
# from SmartFactor import get_custom_factor_class
from SmartFactor.calculation.helper import set_ray_options, get_docker_memory
from SmartFactor.MetaFactor import MetaBaseFactor

avaliable_shared_memory = get_docker_memory()


class Factor(object):
    """因子基类
    所有因子的定义都应继承自本类，并重写 calc 方法
    类属性
    factor_type:   因子类型 ： 分日频(DAY)和高频  (MIN, TICK) 三种
    factor_name:   因子的名称。
    security_type: 因子适用的证券类型， 股票stock 基金fund 债券bond 期货future
    quarter_lag:   需要回溯的季度时间窗口长度，单位为季度，低频财务类因子专用
    day_lag  :     需要回溯的日频时间窗口，单位为天，低频因子专用
    security_pool: 股票池 string or list
    depend_factor: 低高频通用 因子依赖的公共因子或其他的个人因子 String : “因子库名.因子名”
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(Factor, 'instance_dict'):
            Factor.instance_dict = {}

        if str(cls) not in Factor.instance_dict.keys():
            instance = super().__new__(cls, *args, **kwargs)
            Factor.instance_dict[str(cls)] = instance
            instance.__initialized = False
        return Factor.instance_dict[str(cls)]

    factor_type = "DAY"  # 暂时分日频和高频（分钟） “DAY”（日频） “MIN”（分钟级）"TICK"(Tick级)
    factor_name = ''  # 因子名，因子类名，因子文件名 保持一致，否则报错
    security_type = 'stock'  # 证券类型 stock,future,fund,future,bond
    quarter_lag = 1  # 需要回溯的季度时间窗口长度，单位为季度，低频财务类因子专用
    day_lag = 0  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    reform_window = 1  # 后置计算需要的窗口大小 默认是1 低频因子专用
    security_pool = None  # 股票池 string or list
    depend_factor = []  # 低高频通用 因子依赖的公共因子或其他的个人因子 String : “因子库名.因子名”
    custom_params = {}  # 用户在动态生成因子类的时候可以自由传入参数
    external_data_memory_id_dict = dict()  # 用户依赖的外部数据的共享内存的id，与路径一一对应
    used_shared_memory = 0
    data_source = 'finchina'  # 数据源
    use_cache = False

    def mapping_name_func(self, class_name, custom_params):
        name_suffix = []
        if custom_params:
            para_names = sorted(custom_params.keys())
            name_suffix = [para + str(custom_params[para]) for para in para_names]
        name_suffix.insert(0, class_name)
        return "_".join(name_suffix)

    def __init__(self, logger_path='/tmp/factor_data/logs'):
        if self.__initialized:
            return
        self.__initialized = True
        self.log = setup_logging(logger_name='quant_info', dirPath=logger_path)  # log_file


    # 核心计算方法 计算过程中，并行计算每日数据时会调用，用户开发时可根据需要选择性重写该方法
    def calc(self, factor_data, **custom_params):
        """
        计算因子
        factor_data： dict key: 因子名 value: DataFrame  (高低频的DataFrame的格式不同)
        调用需要保证返回一个 pandas.Series, 低频因子: index :标的名, value : 因子值
                                        高频因子：index :MDTime  value : 因子值
        """
        return pd.DataFrame()




    # 用户调用低频因子的调试方法，
    def run_day_factor_value(self, start_date, end_date):
        pass

    # 清理内存
    def clead_shared_memory(self):
        pass

    # 获取存储在共享内存中的外部数据，返回一个字典，key为调用加载外部数据的接口时 传入的data_name,value为pd.DataFrame
    def get_external_shared_data(self):
        df_dict = dict()
        if self.external_data_memory_id_dict:
            for data_name, shared_id in self.external_data_memory_id_dict.items():
                df_dict[data_name] = ray.get(shared_id)
        else:
            print('未发现因子 {} 的外部数据数据，请检查因子文件是否重写了 onRunDaysStart 方法'.format(self.factor_name))
        return df_dict

   