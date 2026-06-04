import os
import ray
import pandas as pd
from SmartFactor.util.data_context import get_trade_days, get_stocks_pool, get_before_trade_day, \
    get_before_report_day, get_before_trade_days
from SmartFactor.util.util import check_date, check_lag_date, check_security_type, check_factor_type, \
    check_factor_name, get_factor_attr, check_security_list, check_data_input_mode_consist, check_factor_sample_consist, \
    get_factor_module, check_run_end_df
from SmartFactor.mkdata.DataCollector import collect_market_data
from SmartFactor.mkdata.helper import sample_data_aux, \
    precross_data_from_tquant, sample_transaction_data, sample_orderbook

code_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-1]), "factors")



def run_hfre_factor_value(fac_cls, start_date, end_date):
    """
    : params : fac_cls : 因子类
    : return : DataFrame
    """
    fac = fac_cls()
    # 校验factor_name
    check_factor_name(fac.factor_name)
    # 校验factor_type
    check_factor_type(fac.factor_type)
    # 校验因子名和因子类名和因子文件名的一致性
    if not fac.__class__.__name__ == fac.factor_name:
        raise Exception("因子类名:{0}与因子名:{1} 不完全一致".format(fac.__class__.__name__, fac.factor_name))

    # get_factor_module(fac.factor_name, "/app/mount/code")
    get_factor_module(fac.factor_name, code_path)
    # 日期校验
    check_date(start_date, end_date)
    # 行情数据类型data_input_mode的校验
    check_data_input_mode_consist([fac_cls])

    # 行情采样参数tick_intereval_seconds的校验
    if {'TICK_SAMPLE', 'TRANSACTION_SAMPLE', 'ORDER_SAMPLE'}.intersection({i.upper() for i in fac.data_input_mode}):
        check_factor_sample_consist([fac_cls])
    # 加入判断条件（时间是否按照要求进行输入）
    tradingdays = get_trade_days(start_date, end_date)
    if not tradingdays:
        raise Exception("在日期{0}~{1}之间没有交易日".format(start_date, end_date))
    securities_list = get_stocks_pool(day=start_date, security_type=fac.security_type,
                                      securities=fac.security_pool)
    # 校验security_list,list 每个元素为（str,list,tuple）中的一个，且必须保持一致
    check_security_list(securities_list)
    res_df_dict = {}
    for security_code in securities_list:
        res_df_list = []
        # 获取依赖的高频基础因子数据
        # base_data,factor_data: dict key:factor value:dataframe
        # if len(fac.depend_factor) > 0:
        #     factor_data = fac.get_factor_data(start_date=tradingday, end_date=tradingday,
        #                                       security_id=security_code)
        # else:
        #     factor_data = dict()
        # 获取依赖的高频的行情数据 DataFrame
        security_id_extra_list = None
        if isinstance(security_code, (list, tuple)):
            security_id_list = security_code
            security_code = security_id_list[0]
            security_id_extra_list = security_id_list[1:]

        sample_period = fac.custom_params.get("sample_period")

        price_data_dict_ori = collect_market_data(security_code=security_code, security_type=fac.security_type,
                                                  start_date=tradingdays[0], end_date=tradingdays[-1],
                                                  collect_mode=fac.data_input_mode,
                                                  tick_sample_interval=sample_period)
        # 如果副标的列表/元组不为空，即认为该进程下的因子需要多只标的的行情数据。
        # 因子计算完成存储的时候会存储在主标的下
        if security_id_extra_list:
            # list格式，表示该次跑批都是跨票因子，第一个是主标的，其余为副标的，副标的仅包括Tick数据
            # tuple格式， 表示该次跑批都是跨票因子，第一个是主标的，其余为副标的，副标的与主标的有一致的data_input_mode
            if isinstance(security_id_extra_list, list):
                data_input_mode_extra = list(set(fac.data_input_mode) - {"TRANSACTION_RAW", "ORDER_RAW", "KLINE1M_RAW"})
            elif isinstance(security_id_extra_list, tuple):
                data_input_mode_extra = fac.data_input_mode
            extra_price_data_dict_ori = {}
            # 逐个取副标的行情数据，格式与主标的保持一致，按月取然后放进共享内存中
            # 存在多个副标的的情况下，将行情数据存储为字典 key: securoty_id    value: ray.object_id
            for security_id_extra in security_id_extra_list:
                extra_price_data_dict_ori[security_id_extra] = collect_market_data(security_code=security_id_extra,
                                                                                   security_type=fac.security_type,
                                                                                   start_date=tradingdays[0],
                                                                                   end_date=tradingdays[-1],
                                                                                   collect_mode=data_input_mode_extra,
                                                                                   tick_sample_interval=sample_period)
        for tradingday in tradingdays:
            price_data_dict = {}  # 主标的字典 形如：{‘tick’:pd.DataFrame,'transaction':pd.DataFrame}
            extra_price_data_dict = {}  # 副标的的字典 形如{'159901.SZ':{‘tick’:pd.DataFrame,'transaction':pd.DataFrame}}
            # 获取主标的的行情数据
            for key in price_data_dict_ori:
                if "args" in key:
                    price_data_dict[key] = price_data_dict_ori[key]
                    continue
                price_data_dict[key] = price_data_dict_ori[key][price_data_dict_ori[key]['MDDate'] == tradingday]
            # 获取副标的的行情数据
            if security_id_extra_list:
                for extra_security_id in extra_price_data_dict_ori:
                    extra_price_data_dict.update({extra_security_id: {}})
                    for key in extra_price_data_dict_ori[extra_security_id]:
                        if "args" in key:
                            extra_price_data_dict[extra_security_id][key] = \
                                extra_price_data_dict_ori[extra_security_id][key]
                            continue
                        extra_price_data_dict[extra_security_id][key] = \
                            extra_price_data_dict_ori[extra_security_id][key][
                                extra_price_data_dict_ori[extra_security_id][key]['MDDate'] == tradingday]

            # price_data: 高频行情数据 格式 DataFrame
            if "tick_sample_args" in price_data_dict.keys():
                price_data_dict["tick"] = precross_data_from_tquant(price_data_dict["tick"], fac.security_type)
                price_data_dict["tick"] = sample_data_aux(price_data_dict["tick"],
                                                          **price_data_dict["tick_sample_args"])
            if "transaction_sample_args" in price_data_dict.keys():
                price_data_dict["transaction"] = sample_transaction_data(price_data_dict["transaction"],
                                                                         **price_data_dict[
                                                                             "transaction_sample_args"])
            if "order_sample_args" in price_data_dict.keys():
                price_data_dict['order'] = sample_orderbook(price_data_dict['order'],
                                                            **price_data_dict['order_sample_args'])
                # 入参中如果额外标的行情数据不为空，则会读取共享内存中的额外行情数据，采样后按天存进字典中。采样频率与方法和主标的的数据保持一致
                # extra_price_data_dict存储的形式形如 {'159901.SZ':{'tick':pd.DataFrame,'transaction':pd.DataFrame}}
                # 相比主标的的行情字典price_data_dict 在外多套了一层标的 作为外层字典的key
            if extra_price_data_dict:
                for security_id_extra in extra_price_data_dict.keys():
                    if "tick_sample_args" in extra_price_data_dict[security_id_extra].keys():
                        extra_price_data_dict[security_id_extra]['tick'] = precross_data_from_tquant(
                            extra_price_data_dict[security_id_extra]['tick'][
                                extra_price_data_dict[security_id_extra]['tick']['MDDate'] == tradingday],
                            fac.security_type)

                        extra_price_data_dict[security_id_extra]['tick'] = sample_data_aux(
                            extra_price_data_dict[security_id_extra]['tick'],
                            **extra_price_data_dict[security_id_extra]
                            ["tick_sample_args"])
                    if "transaction_sample_args" in extra_price_data_dict[security_id_extra].keys():
                        extra_price_data_dict[security_id_extra]['transaction'] = sample_transaction_data(
                            extra_price_data_dict[security_id_extra]['transaction'][
                                extra_price_data_dict[security_id_extra]['transaction']['MDDate'] == tradingday],
                            **extra_price_data_dict[security_id_extra]["transaction_sample_args"])
                    if "order_sample_args" in extra_price_data_dict[security_id_extra].keys():
                        extra_price_data_dict[security_id_extra]['order'] = sample_orderbook(
                            extra_price_data_dict[security_id_extra]['order'][
                                extra_price_data_dict[security_id_extra]['order']['MDDate'] == tradingday],
                            **extra_price_data_dict[security_id_extra]["order_sample_args"])
            # 将extra_price_data 放进price_data中， 格式为{'159901.SZ':{'tick':pd.DataFrame,'transaction':pd.DataFrame}}
            price_data_dict.update(extra_price_data_dict)
            # 为了保持与计算框架中 price_data的格式一致， 形如{ ‘tick’: pd.DataFrame }
            tmp_series = fac.calc(price_data=price_data_dict, factor_data={}, custom_params=fac.custom_params)

            # 校验calc方法返回的数据格式是否正确
            if not isinstance(tmp_series, pd.Series):
                raise Exception("【calc方法返回值错误】高频因子的calc方法必须返回一个pd.Series格式的数据！目前是：{}".format(type(tmp_series)))
            if len(str(tmp_series.index[0])) not in [8, 9]:
                raise Exception(
                    "【calc方法返回值错误】高频因子的calc方法返回值Series的索引应为8位或9位长度的时间戳！目前是：{}".format(str(tmp_series.index[0])))
            # 调整数据格式，拼接，返回
            # tmp_series.index = price_data["MDTime"]
            tmp_df = tmp_series.to_frame()
            tmp_df.columns = [fac.factor_name]
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
    import os

    code_path = os.path.join("/".join(os.path.abspath(__file__).split("/")[:-1]), "factors")
    print(code_path)
