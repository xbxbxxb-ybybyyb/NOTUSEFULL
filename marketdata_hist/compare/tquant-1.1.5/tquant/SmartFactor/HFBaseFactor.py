# -*- coding: utf-8 -*-
"""
Created on Tue Nov 24 22:48:39 2020
@author: 013150
"""
import re
import pandas as pd
from tquant.SmartFactor.util.util import check_date, check_factor_name, check_factor_type
from tquant.logger import setup_logging
from tquant.SmartFactor.util.data_context import get_trade_days, get_stocks_pool
from tquant import StockData, FundData, PsFactorData

# class MetaHFBaseFactor(type):
#     def __new__(cls, name, bases, attrs):
#         """
#         attrs: 用户定义的参数
#         类改名，按用户定义的方式
#         """
#         if name == "HfreBaseFactor":
#             return type.__new__(cls, name, bases, attrs)
#
#         for k, v in attrs.items():
#             # 保存类属性和列的映射关系到mappings字典
#             if k == "custom_params":
#                 for subk, subv in attrs["custom_params"].items():
#                     assert type(subv) == int or type(subv) == str, "参数{}类型错误：custom_params只支持传入str或者int类型的参数！".format(
#                         subk)
#                     if type(subv) == str:
#                         assert re.search(r"\W", subv), "参数{}值错误: custom_params只支持传入值为大小写字母、数字或下划线组合的值！".format(subk)
#
#         mapping_name_func = getattr(bases[0], "mapping_name_func", lambda x, y: x)  # 获取高频因子基类中的类命名函数
#         if "custom_params" in attrs:
#             new_name = mapping_name_func(bases[0], name, attrs["custom_params"])
#         else:
#             new_name = name
#         instance = super(MetaHFBaseFactor, cls).__new__(cls, new_name, bases, attrs)
#         setattr(instance, "factor_name", new_name)
#         for k, v in attrs.items():
#             # 覆盖原始因子类中的参数，比如security_type或securities
#             if k != "custom_params":
#                 print("注意：当前正在修改基础因子类的默认类属性{}：{}!".format(k, v))
#                 setattr(instance, k, v)
#         return instance


class HFBaseFactor(object):
    """因子基类
    所有因子的定义都应继承自本类，并重写 calc 方法
    类属性
    factor_type:   高频  (MIN, TICK)
    factor_name:   因子的名称。
    security_type: 因子适用的证券类型， 股票stock 基金fund 债券bond 期货future
    security_pool: 股票池 string or list
    depend_factor: 因子依赖的公共因子或其他的个人因子 String : “因子库名.因子名”
    custom_params: 用户在动态生成因子类的时候可以自由传入参数
    """

    def __new__(cls, *args, **kwargs):
        if not hasattr(HFBaseFactor, 'instance_dict'):
            HFBaseFactor.instance_dict = {}

        if str(cls) not in HFBaseFactor.instance_dict.keys():
            instance = super().__new__(cls, *args, **kwargs)
            HFBaseFactor.instance_dict[str(cls)] = instance
            instance.__initialized = False
        return HFBaseFactor.instance_dict[str(cls)]

    factor_type = "TICK"  # “MIN”（分钟级）"TICK"(Tick级)
    factor_name = ''  # 因子名，因子类名，因子文件名 保持一致，否则报错
    security_type = 'stock'  # 证券类型 stock,future,fund,future,bond
    security_pool = None  # 股票池 string or list
    depend_factor = []  # 因子依赖的公共因子或其他的个人因子 String : “因子库名.因子名”
    custom_params = {}  # 用户在动态生成因子类的时候可以自由传入参数

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

    # 计算
    def calc(self, price_data, factor_data, **custom_params):
        """计算因子
        price_data : DataFrame
        factor_data：DataFrame
        custom_params : 用户可以灵活传入需要的参数
        需要保证返回一个 pandas.Series, index 为股票代码, value 是因子值
        """
        return pd.DataFrame()

    def get_price_data(self, start_date, end_date, securitiy_code):
        """
        高频因子专用 返回price_data 高频行情数据
        """
        start_datetime = start_date + " 080000000"
        end_datetime = end_date + " 235900000"
        if self.factor_type == "MIN":
            return self.get_kline_data(securitiy_code=securitiy_code, start_datetime=start_datetime,
                                       end_datetime=end_datetime)
        elif self.factor_type == "TICK":
            return self.get_tick_data(securitiy_code=securitiy_code, start_datetime=start_datetime,
                                      end_datetime=end_datetime)
        else:
            raise Exception("仅在开发MIN,TICK两种类型的因子时需要依赖高频行情数据！")

    def get_kline_data(self, securitiy_code, start_datetime, end_datetime):

        """
        读取 K线数据
        :param security_code: string
        :param fac_names: list
        :param date ： string
        :return:  multiindex DataFrame
                        Factor1 Factor2 Factor3 ...
        MDDate MDTime

        """
        if self.security_type == "stock":
            sd = StockData()
            data = sd.get_stock_kline(trading_code=securitiy_code, start_datetime=start_datetime,
                                      end_datetime=end_datetime)
        # 之后会支持扩展其他证券类型的因子 bond fund future
        elif self.security_type == 'fund':
            fd = FundData()
            data = fd.get_fund_kline(symbol=securitiy_code, start_datetime=start_datetime, end_datetime=end_datetime)
        else:
            raise Exception("目前仅支持证券类型为stock,fund的因子开发")
        return data

    def get_tick_data(self, securitiy_code, start_datetime, end_datetime):

        """
        获取 tick级行情数据
        :param security_code: string
        :param fac_names: list
        :param date： string
        :return:  multiindex DataFrame
                        Factor1 Factor2 Factor3 ...
        MDDate MDTime
        """
        if self.security_type == "stock":
            sd = StockData()
            data = sd.get_stock_tick(trading_code=securitiy_code, start_datetime=start_datetime,
                                     end_datetime=end_datetime)
        elif self.security_type == 'fund':
            fd = FundData()
            data = fd.get_fund_tick(symbol=securitiy_code, start_time=start_datetime, end_time=end_datetime)

        # 之后会支持扩展其他证券类型的因子 bond fund future
        else:
            raise Exception("目前仅支持证券类型为stock,fund的因子开发！")
        return data

    def get_factor_data(self, start_date, end_date, security_id):
        """
        获取依赖的因子数据,高频可传可不传
        quarterlag_dt_list: 财务因子需要回溯的时间窗口列表 例如：['20180630','20180930','20190331']
        start_date ： 日频因子开始时间 形如“20201123”
        end_date   ： 截止时间 形如“20201123”
        securities_list : 标的列表

        return : dict key: 因子名 value: DataFrame  (高低频的DataFrame的格式不同)
        """
        res_df = pd.DataFrame()
        res_df_list = []
        tps = PsFactorData()  # SDK中已增加单例
        if len(self.depend_factor):
            date_list = get_trade_days(start_date, end_date)
            for depend_factor_describe in self.depend_factor:
                if len(depend_factor_describe.split('.')) != 2:
                    raise Exception("请按照 因子类型（因子库名）.因子名 的方式书写依赖因子！")
                depend_factor_type, depend_factor_name = depend_factor_describe.split('.')
                # 高频因子 key:因子名 value:  DataFrame
                if depend_factor_type == "BasicMinFactor":
                    # 接口仍在继续开发,暂无公共的分钟级因子
                    tmp_df = self.get_min_factor_values(securities_list=[security_id],
                                                        start_date=start_date,
                                                        end_date=end_date,
                                                        factor_name=depend_factor_name)[
                        depend_factor_name, 'MDTime']

                elif depend_factor_type == "BasicTickFactor":
                    # 接口仍在继续开发，暂无公共的tick级因子
                    tmp_df = self.get_tick_factor_values(securities_list=[security_id],
                                                         start_date=start_date,
                                                         end_date=end_date,
                                                         factor_name=depend_factor_name)[
                        depend_factor_name, 'MDTime']
                # 依赖因子是个人库中的因子
                else:
                    tmp_df = tps.get_factor_value(library_name=depend_factor_type,
                                                  mddate_list=date_list,
                                                  security_list=[security_id],
                                                  factor_list=[depend_factor_name],
                                                  sort=False,
                                                  in_dataframe=False)[security_id][
                        depend_factor_name, 'MDTime', 'MDDate']
                    tmp_df = tmp_df.set_index(['MDDate', 'MDTime'])
                res_df_list.append(tmp_df)
            res_df = pd.concat(res_df_list, axis=1)
            res_df.reset_index()

        return res_df


    def get_min_factor_values(self, securities_list, start_date, end_date, factor_name):

        """
        securities_list : list 标的列表
        start_date : str 开始时间 “20201123”
        end_date : str 结束时间 “20201123”
        factor_name : str 因子名
        return : DataFrame :
        """
        return pd.DataFrame()

    # 获取tick级的高频因子数据，开发中
    def get_tick_factor_values(self, securities_list, start_date, end_date, factor_name):

        """
        securities_list : list 标的列表
        start_date : str 开始时间 “20201123”
        end_date : str 结束时间 “20201123”
        factor_name : str 因子名
        return : DataFrame :
        """
        return pd.DataFrame()

    # 高频因子的跑批
    def run_hfre_factor_value(self, start_date, end_date):
        # 校验factor_name
        check_factor_name(self.factor_name)
        # 校验factor_type
        check_factor_type(self.factor_type)
        # 日期校验
        check_date(start_date, end_date)
        # 加入判断条件（时间是否按照要求进行输入）
        tradingdays = get_trade_days(start_date, end_date)
        if not tradingdays:
            raise Exception("在日期{0}~{1}之间没有交易日".format(start_date, end_date))
        securities_list = get_stocks_pool(day=start_date, security_type=self.security_type,
                                          securities=self.security_pool)
        res_df_dict = {}
        for security_code in securities_list:
            res_df_list = []
            for tradingday in tradingdays:
                # 获取依赖的高频基础因子数据
                # base_data,factor_data: dict key:factor value:dataframe
                if len(self.depend_factor) > 0:
                    factor_data = self.get_factor_data(start_date=tradingday, end_date=tradingday,
                                                       security_id=security_code)
                else:
                    factor_data = dict()
                # 获取依赖的高频的行情数据 DataFrame
                price_data = self.get_price_data(start_date=tradingday, end_date=tradingday,
                                                 securitiy_code=security_code)
                # 计算 返回pd.Series 并校验
                tmp_series = self.calc(price_data=price_data, factor_data=factor_data, custom_params=self.custom_params)

                # 校验calc方法返回的数据格式是否正确
                if (not isinstance(tmp_series, pd.Series)) or (len(str(tmp_series.index[0])) not in [8, 9]):
                    raise Exception("高频因子的calc方法需要返回一个index为MDTime，value为因子值的pd.Series")

                # 调整数据格式，拼接，返回
                # tmp_series.index = price_data["MDTime"]
                tmp_df = tmp_series.to_frame()
                tmp_df.columns = [self.factor_name]
                tmp_df.index.name = 'MDTime'
                tmp_df.reset_index(inplace=True)
                tmp_df['MDDate'], tmp_df['HTSCSecurityID'] = tradingday, security_code
                tmp_df = tmp_df[['MDDate', 'MDTime', 'HTSCSecurityID'] + list(
                    set(tmp_df.columns.tolist()) - {'MDDate', 'MDTime', 'HTSCSecurityID'})]
                if not tmp_df.empty:
                    res_df_list.append(tmp_df)
            if res_df_list:
                res_df_dict[security_code] = pd.concat(res_df_list)
            else:
                res_df_dict[security_code] = pd.DataFrame()

        return res_df_dict


if __name__ == "__main__":
    from . import get_custom_factor_class
    from .FactorCalc import run_securities_days


    class MyFactor(HFBaseFactor):
        factor_name = "MyFactor"
        custom_params = {"min": 5, "lag": 3}
        security_pool = ["000001.SZ", "000002.SZ"]

        def calc(self, price_data, factor_data, **custom_params):
            print("custom_params: ", custom_params)
            df = price_data["ClosePx"]
            df.index = price_data['MDTime']
            return df


    print(MyFactor)
    mf = MyFactor()
    print(mf)
    print(MyFactor())
    print("===============")

    MyFactor_min5_lag3 = get_custom_factor_class(MyFactor, {"custom_params": {"min": 5, "lag": 3}})
    MyFactor_min3_lag3 = get_custom_factor_class(MyFactor, {"custom_params": {"min": 3, "lag": 3}})

    print(MyFactor_min3_lag3)
    mf1 = MyFactor_min3_lag3()
    print(mf1.run_hfre_factor_value("20191201", "20191203"))
    print(mf1)
    print(MyFactor_min3_lag3())

    df = run_securities_days([MyFactor_min3_lag3], "20191201", "20191213", return_mode="show", library_name='b20180808',
                             file_path='.')
    # print(df)
