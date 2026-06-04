# -*- coding: utf-8 -*-

"""Base Factor"""
import pandas as pd
from tquant import StockData, PsFactorData
from tquant.SmartFactor.util.data_context import get_trade_days, get_stocks_pool, get_before_trade_day, \
    get_before_report_day
from tquant.SmartFactor.util.util import check_date, check_lag_date, check_security_type, check_factor_type, check_factor_name
from tquant.logger import setup_logging


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
    quarter_lag = None  # 需要回溯的季度时间窗口长度，单位为季度，低频财务类因子专用
    day_lag = None  # 需要回溯的日频时间窗口，单位为天，低频因子专用
    security_pool = None  # 股票池 string or list
    depend_factor = []  # 低高频通用 因子依赖的公共因子或其他的个人因子 String : “因子库名.因子名”
    custom_params = {}  # 用户在动态生成因子类的时候可以自由传入参数


    def __init__(self, logger_path='/tmp/factor_data/logs'):
        if self.__initialized:
            return
        self.__initialized = True
        self.log = setup_logging(logger_name='quant_info', dirPath=logger_path)  # log_file

    # 核心方法 用户开发时需要重写该方法
    def calc(self, factor_data):
        """
        计算因子
        factor_data： dict key: 因子名 value: DataFrame  (高低频的DataFrame的格式不同)
        调用需要保证返回一个 pandas.Series, 低频因子: index :标的名, value : 因子值
                                        高频因子：index :MDTime  value : 因子值
        """
        return pd.DataFrame()

    def get_factor_data(self, quarterlag_dt_list, start_date, end_date, securities_list):
        """
        获取依赖的因子数据
        低频必须传入depend_factor,高频可传可不传
        quarterlag_dt_list: 财务因子需要回溯的时间窗口列表 例如：['20180630','20180930','20190331']
        start_date ： 日频因子开始时间 形如“20201123”
        end_date   ： 截止时间 形如“20201123”
        securities_list : 标的列表

        return : dict key: 因子名 value: DataFrame  (高低频的DataFrame的格式不同)
        """
        res_dict = {}
        sd = StockData()
        tps = PsFactorData()

        if len(self.depend_factor):
            date_list = get_trade_days(start_date, end_date)
            for depend_factor_describe in self.depend_factor:
                if len(depend_factor_describe.split('.')) != 2:
                    raise Exception("请按照 因子类型（因子库名）.因子名 的方式书写依赖因子！")
                depend_factor_type, depend_factor_name = depend_factor_describe.split('.')
                # 低频因子 key: 因子名 value: multiindex DataFrame
                # 依赖因子是财务分析或者财务报表的指标
                if depend_factor_type == "BasicFinancialFactor":
                    if not quarterlag_dt_list: raise Exception("依赖因子中包含财务类因子，quarter_lag不能为None")
                    res_dict[depend_factor_describe] = sd.get_tfactor_value(trading_codes=securities_list,
                                                                            date_list=quarterlag_dt_list,
                                                                            factor_list=[depend_factor_name])[
                        depend_factor_name].unstack()

                # 依赖因子是日频因子（market,valuation,risk_analysis,news,alpha,barra）
                elif depend_factor_type == "BasicDayFactor":
                    res_dict[depend_factor_describe] = sd.get_tfactor_value(trading_codes=securities_list,
                                                                            date_list=date_list,
                                                                            factor_list=[depend_factor_name])[
                        depend_factor_name].unstack()
                # 依赖因子是个人库中的因子
                else:
                    res_dict[depend_factor_describe] = tps.get_factor_value(library_name=depend_factor_type,
                                                                            mddate_list=date_list,
                                                                            security_list=securities_list,
                                                                            factor_list=[depend_factor_name],
                                                                            sort=False,
                                                                            in_dataframe=False)[depend_factor_name]

            return res_dict

        # 高频因子的开发可能没有传入depend_factor 返回空的字典
        else:
            return dict()

    # 增加临时跑批调试的方法 可以临时跑当前因子一段时间 在一段标的上的值 返回DataFrame
    def run_day_factor_value(self, start_date, end_date):
        # 校验factor_name
        check_factor_name(self.factor_name)
        #校验因子名和因子类名的一致性
        if self.__class__.__name__ != self.factor_name:
            raise Exception("因子类名{0}与因子名{1}不一致".format(self.__class__.__name__,self.factor_name))
        # 校验factor_type
        check_factor_type(self.factor_type)
        # 校验security_type
        check_security_type(self.security_type)
        # 日期校验
        check_date(start_date, end_date)
        # 校验depend_factor
        if len(self.depend_factor) == 0 and self.factor_type == "DAY":
            raise Exception("低频因子的开发必须传入所依赖的因子")
        # 校验数据播放窗口
        check_lag_date(self.day_lag, self.quarter_lag)
        tradingdays = get_trade_days(start_date, end_date)
        if not tradingdays:
            raise Exception("在日期{0}~{1}之间没有交易日".format(start_date, end_date))
        res_df_list = list()
        for tradingday in tradingdays:
            dt_from = get_before_trade_day(tradingday, self.day_lag) if self.day_lag else tradingday
            securities_list = get_stocks_pool(day=tradingday, security_type=self.security_type, securities=self.security_pool)
            quarterlag_dt_list = get_before_report_day(tradingday, self.quarter_lag) if self.quarter_lag else []
            # factor_data: dict key:因子名 values: DataFrame
            factor_data = self.get_factor_data(quarterlag_dt_list=quarterlag_dt_list,
                                               start_date=dt_from,
                                               end_date=tradingday,
                                               securities_list=securities_list)

            df_series = self.calc(factor_data=factor_data)

            # 　判断低频因子calc（）方法返回的数据格式是否正确
            if (not isinstance(df_series, pd.Series)) or (len(df_series.index) != len(securities_list)):
                raise Exception("低频因子的calc方法需要返回一个index为标的名，value为因子值的pd.Series")
            df = pd.DataFrame()
            df[tradingday] = df_series
            df = df.T
            res_df_list.append(df)
        res_df = pd.concat(res_df_list)
        return res_df

    # 清理内存
    def clead_shared_memory(self):
        pass
