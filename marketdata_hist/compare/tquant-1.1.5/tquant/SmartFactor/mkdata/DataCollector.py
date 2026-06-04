# -*- coding:utf-8 -*-
from MDCDataProvider.stockdata import StockDataDP
from MDCDataProvider.funddata import FundDataDP
from tquant.SmartFactor.constant import DataCollectMode, transform_datamode
from .helper import *

data_instance = {}


def collect_market_data(security_code, security_type, start_date, end_date, collect_mode = [DataCollectMode.TICK_RAW], tick_sample_interval = None):
    """
    :param security_code: 标的名称
    :param security_type: 标的类型
    :param start_datetime: 取数开始时间
    :param end_datetime: 取数结束时间
    :param collect_mode: list，订阅的数据类型，目前支持TICK_RAW、TICK_SAMPLE（采样Tick数据）、TRANSACTION_RAW、ORDER_RAW、KLINE1M_RAW
    :param tick_interval_seconds: int，采样的时间间隔，单位为秒，当且仅当DataCollectMode为TICK_SAMPLE时必传
    :return:
    """
    start_datetime = start_date + " 092500000"
    end_datetime = end_date + " 150000250"

    assert type(collect_mode) == list, "collect_mode参数类型必须为列表！"
    df_dict = {}
    for mode in collect_mode:
        mode = transform_datamode(mode)
        if mode == DataCollectMode.TICK_RAW:
            if security_type.upper()=="STOCK":
                bar_size = "STOCK"
            else:
                bar_size = "TICK"
            if df_dict.get("tick"):
                raise Exception("DataCollectMode中存在重复的行情数据类型{}，请重新传入！".format(mode))
            df_dict["tick"] = get_market_data(security_code, security_type, start_datetime, end_datetime, bar_size = bar_size)
        elif mode == DataCollectMode.TICK_SAMPLE:
            if security_type.upper()=="STOCK":
                bar_size = "STOCK"
            else:
                bar_size = "TICK"
            if df_dict.get("tick"):
                raise Exception("DataCollectMode中存在重复的行情数据类型{}，请重新传入！".format(mode))
            assert type(tick_sample_interval) == int, "DataCollectMode.TICK_SAMPLE模式下，需要指定TICK的采样时间间隔参数tick_sample_interval, 单位为秒!"
            df_tick = get_market_data(security_code, security_type, start_datetime, end_datetime, bar_size = bar_size)
            df_dict["tick"] = df_tick
            df_dict["tick_sample_args"] = {"security_type":security_type, "tick_interval_seconds": tick_sample_interval}
        elif mode == DataCollectMode.TRANSACTION_RAW:
            if df_dict.get("transaction"):
                raise Exception("DataCollectMode中存在重复的行情数据类型{}，请重新传入！".format(mode))
            df_dict["transaction"] = get_market_data(security_code, security_type, start_datetime, end_datetime, bar_size = "TRANSACTION")
        elif mode == DataCollectMode.TRANSACTION_SAMPLE:
            if df_dict.get("transaction"):
                raise Exception("DataCollectMode中存在重复的行情数据类型{}，请重新传入！".format(mode))
            df_dict["transaction"] = get_market_data(security_code, security_type, start_datetime, end_datetime, bar_size = "TRANSACTION")
            df_dict["transaction_sample_args"] = {"tick_interval_seconds": tick_sample_interval}
        elif mode == DataCollectMode.ORDER_RAW:
            if df_dict.get("order"):
                raise Exception("DataCollectMode中存在重复的行情数据类型{}，请重新传入！".format(mode))
            df_dict["order"] = get_market_data(security_code, security_type, start_datetime, end_datetime, bar_size = "ORDER")
        else:
            raise Exception("DataCollectMode不支持此枚举类型: {}！".format(mode))
    return df_dict


def get_market_data(security_code, security_type, start_datetime, end_datetime, bar_size):
    """
    获取 tick级行情数据
    :param security_code: string
    :param fac_names: list
    :param date： string
    :return:  multiindex DataFrame
                    Factor1 Factor2 Factor3 ...
    MDDate MDTime
    """
    #TODO Stock多一种KLine1M4ZT的的bar_size
    if security_type.upper() == "STOCK":
        if not data_instance.get("stock"):
            #TODO： 是否增加global关键词
            data_instance["stock"] = StockDataDP()
        mdp = data_instance["stock"]
        data = mdp.get_stock_data(symbol=security_code, start_time=start_datetime,
                                 end_time=end_datetime, bar_size = bar_size)

    elif security_type.upper() == 'FUND':
        if not data_instance.get("fund"):
            #TODO： 是否增加global关键词
            data_instance["fund"] = FundDataDP()
        mdp = data_instance["fund"]
        data = mdp.get_fund_data(symbol=security_code, start_time=start_datetime, end_time=end_datetime,
                                 bar_size = bar_size)
    # 之后会支持扩展其他证券类型的因子 bond fund future
    else:
        raise Exception("目前仅支持证券类型为stock,fund的因子开发！")
    if data.empty:
        raise Exception("标的：{0}，在时间范围{1}--{2}内暂无行情数据，请联系Tquant团队解决".format(security_code,start_datetime,end_datetime))

    return data


