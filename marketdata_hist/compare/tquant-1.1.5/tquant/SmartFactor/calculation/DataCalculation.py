# -*- coding:utf-8 -*-
import ray
import pandas as pd
from tquant.SmartFactor.util.util import get_fac_class, factor_time_info, check_date, check_return_and_lib, \
    check_factor_list, check_factor_name, check_factor_type, check_lag_date, check_security_type, \
    check_factor_sample_consist, check_security_list
from tquant.SmartFactor.util.data_context import get_trade_days, get_stocks_pool, get_before_trade_day, \
    get_before_trade_days, get_before_report_day
from tquant import PsFactorData
from tquant.SmartFactor.mkdata.DataCollector import collect_market_data
# from xquant.xqutils.perf_profile import profile
from tquant.SmartFactor.calculation.helper import set_ray_options
from tquant.SmartFactor.mkdata.helper import sample_data_aux, precross_data_from_tquant, sample_transaction_data
from tquant.SmartFactor import fac_logger

def run_factors_days(factor_list, start_date, end_date, num_cpus=None, object_store_memory=None, library_name=None,
                     return_mode='show', file_path='./', check_olddata=True, allow_merge_olddata=True, options=None):
    """
    多因子多日 ray并行计算
    :param file_path:
    :param return_mode:
    :param library_name:
    :param factor_list:
    :param num_cpus:
    :param object_store_memory:
    :param start_date: 开始时间 格式 ’YYYYMMDD‘
    :param end_date:   结束时间 格式 ’YYYYMMDD‘
    :param allow_merge_olddata:
    :param check_olddata:
    :param options: dict {'webui_host':127.0.0.1}

    :return:
    """
    # 校验日期
    check_date(start_date, end_date)
    # 校验factor_list
    check_factor_list(factor_list, factor_type="DAY")
    # 校验library_name
    check_return_and_lib(return_mode, library_name)
    # 初始化ray
    set_ray_options(num_cpus=num_cpus, object_store_memory=object_store_memory, options=options)
    r = [run_factor_days.remote(factor_name, start_date, end_date, library_name, return_mode=return_mode,
                                file_path=file_path, check_olddata=check_olddata,
                                allow_merge_olddata=allow_merge_olddata) for factor_name in factor_list]
    facs_days_res = ray.get(r)
    ray.shutdown()
    if return_mode == 'show':
        facs_days_dict = {}
        for fac_days_df in facs_days_res:
            facs_days_dict[fac_days_df.iloc[0]['Factor']] = fac_days_df
        return facs_days_dict


def run_securities_days(factor_list, start_date, end_date, security_list, num_cpus=None, object_store_memory=None,
                        library_name=None, data_input_mode=["TICK_RAW"], security_type=None,
                        return_mode='show', file_path='./', check_olddata=True, options=None):
    """
    :param factor_list: list，需要计算的因子列表，每个元素代表一个因子，可以是srt或者因子类
    :param start_date: str， 计算开始时间，如20190701.
    :param end_date: str，计算结束时间，如20190701.
    :param num_cpus: int，通过Ray并行计算的进程数， 如1。
    :param object_store_memory: int，通过Ray并行计算的共享内存大小，如1e9,单位B
    :param library_name: 因子库名，指定因子存储的因子库的名称。当return_mode=’save’时，因子库为必传。
    :param data_input_mode: list，订阅的数据类型，目前支持TICK_RAW、TICK_SAMPLE（采样Tick数据）、TRANSACTION_RAW、ORDER_RAW、KLINE1M_RAW, SAMPLE模式下因子的custome_param必须有tick_sample_interval属性，用于定义采样时间间隔。
    :param security_type: str，订阅的标的类型，支持STOCK（股票）、FUND（基金）。
    :param security_list: list，需要计算的标的列表，如["159958.SZ", "159915.SZ"]。如果对跨票因子进行跑批计算，需要传入[['159958.SZ','159901.SZ'],['159915.SZ', '159901.SZ']] 或者[('159958.SZ','159901.SZ'),('159915.SZ', '159901.SZ')]
    :param return_mode: 默认为show， save: 存储计算结果到因子库，无返回值;show:字典形式返回计算结果
    :param file_path: 默认值为’./’，file_path表示因子类文件的存储路径（绝对路径与相对路径均可），用于递归搜索并加载因子类。若factor_list中传的因子名为str，会从file_path下搜索。
    :param check_olddata: 默认为True。为True时，会校验factor_values与原因子数据（若之前已经存储过）是否同一天同一个因子有相同的HTSCSecurityID个数；若相同,会用factor_values存储新数据，若不相同参见allow_merge_olddata参数选项。
    :param options: dict， 启动Ray多进程计算的其他初始化参数，如{"local_mode":True},表示以本地调试模式运行。
    :return:
    """
    """
    多标的多日 ray并行计算
    :param file_path:
    :param return_mode:
    :param library_name:
    :param factor_list:
    :param num_cpus: ray.init(num_cpus=X)
    :param security_pool:
    :param object_store_memory: ray.init(object_store_memory=X)
    :param start_date: 开始时间 格式 ’YYYYMMDD‘
    :param end_date:   结束时间 格式 ’YYYYMMDD‘
    :param check_olddata:
    :param options: dict 例如：{'webui_host':127.0.0.1}
    :param tick_sample_interval: 当且仅当data_input_mode中有DataCollectMode.TICK_SAMPLE时有效，为采样时间间隔
    :return:
    """

    # 校验日期
    check_date(start_date, end_date)
    # 如果 是save模式 则校验library_name
    check_return_and_lib(return_mode, library_name)
    # 初始化ray
    set_ray_options(num_cpus=num_cpus, object_store_memory=object_store_memory, options=options)
    # 校验factor_list
    check_factor_list(factor_list, factor_type="TICK")
    # 校验security_list,list 每个元素为（str,list,tuple）中的一个，且必须保持一致
    check_security_list(security_list)
    # 按月对交易日列表进行划分 列表中的每一个元素都是一个时间列表
    date_list = get_trade_days(start_date, end_date)
    # 日期列表返回可能为空，为空时影响接下来的计算
    if not date_list:
        raise Exception("在日期{0}~{1}之间没有交易日".format(start_date, end_date))  # 映射因子与标的的关系
    # 将交易日列表
    date_list_per_month = []
    date_tmp_list = []
    date_list = sorted(date_list)
    day_nums = len(date_list)
    for i, date in enumerate(date_list):
        if len(date_tmp_list) == 0:
            year, month = date[:4], str(int(date[4:6]) + 2).zfill(2)  # 一次算两个月
        if date[:4] == year and date[4:6] <= month:
            date_tmp_list.append(date)
        else:
            date_list_per_month.append(date_tmp_list)
            year, month = date[:4], str(int(date[4:6]) + 2).zfill(2)
            date_tmp_list = [date]
        if date_tmp_list and i == day_nums - 1:
            date_list_per_month.append(date_tmp_list)

    # 映射因子与标的的关系
    fac_to_sec_dict = {}
    for fac_cls in factor_list:
        if type(fac_cls) == str:
            fac_cls = get_fac_class(fac_cls, file_path)
        assert fac_cls.__name__ == fac_cls.factor_name, "因子名称冲突：因子类名{}与因子名{}不一致！".format(
            fac_cls.__name__, fac_cls.factor_name)
        # 校验factor_name
        check_factor_name(fac_cls.factor_name)
        # 校验factor_type
        check_factor_type(fac_cls.factor_type)

        cur_security_pool = None
        fac_to_sec_dict[fac_cls] = cur_security_pool
    tick_sample_interval = 0
    if "TICK_SAMPLE" in [i.upper() for i in data_input_mode] or "TRANSACTION_SAMPLE" in [i.upper() for i in
                                                                                         data_input_mode]:
        check_factor_sample_consist(fac_to_sec_dict.keys())
        tick_sample_interval = fac_cls.custom_params["tick_interval_seconds"]

    # # 映射标的与因子的关系
    # sec_to_fac_dict = {}
    # for key, value in fac_to_sec_dict.items():
    #     for code in value:
    #         sec_to_fac_dict[code] = sec_to_fasc_dict.get(code, [])
    #         sec_to_fac_dict[code].append(key)
    # security_list = list(sec_to_fac_dict.keys())

    # # 提示用户最终需要跑批的标的池
    # fac_logger.debug("According to statistics, this parallel calculation will be in securties list: ", end="")
    # fac_logger.debug(security_list)
    fac_logger.debug("start calculation...")
    r = [run_security_days.remote(factor_list=list(fac_to_sec_dict.keys()), date_list_per_month=date_list_per_month,
                                  security_id=security_id, library_name=library_name,
                                  data_input_mode=data_input_mode, security_type=security_type,
                                  tick_sample_interval=tick_sample_interval,
                                  return_mode=return_mode, check_olddata=check_olddata) for security_id in
         security_list]
    facs_days_list = ray.get(r)
    ray.shutdown()
    if return_mode == 'show':
        facs_days_dict = {}
        for facs_days_df in facs_days_list:
            facs_days_dict[facs_days_df.iloc[0]['HTSCSecurityID']] = facs_days_df
        return facs_days_dict


@ray.remote
def run_factor_days(factor_name, start_date, end_date, library_name=None, return_mode=None, file_path=None,
                    check_olddata=True, allow_merge_olddata=True):
    # 校验factor_name
    check_factor_name(factor_name)

    # 因子实例化, 校验因子名是否一致（传入框架的和对应的类属性中的）
    cls_fac = get_fac_class(factor_name, file_path)
    fac = cls_fac()

    # 校验factor_type
    check_factor_type(fac.factor_type)

    # 校验security_type
    check_security_type(fac.security_type)

    # 校验数据播放窗口
    check_lag_date(fac.day_lag, fac.quarter_lag)

    if factor_name != fac.factor_name:
        raise Exception("The factor name is not same : Calc Framework: {0}  Class Attribute:{1}".format(factor_name,
                                                                                                        fac.factor_name))
    #   获取交易日,股票池
    tradingdays_first = get_trade_days(start_date, end_date)
    if not tradingdays_first:
        raise Exception("在日期{0}~{1}之间没有交易日".format(start_date, end_date))
    securities_list = get_stocks_pool(day=start_date, security_type=fac.security_type, securities=fac.security_pool)

    # 根据日频和季度的lag 获取 数据播放的最大窗口
    start_date = get_before_trade_day(start_date, fac.day_lag) if fac.day_lag else start_date
    quarter_dt_list = get_before_report_day(start_date, fac.quarter_lag) if fac.quarter_lag else []
    # 获取依赖数据
    # 开发低频因子， 必须有依赖的因子
    if len(fac.depend_factor) == 0:
        raise Exception("Depend_factor can not be empty!")

    # 获取计算该因子在dt_from到dt_to需要的所有依赖数据,并放入共享内存中
    factor_data_dict = fac.get_factor_data(quarterlag_dt_list=quarter_dt_list, start_date=start_date,
                                           end_date=end_date, securities_list=securities_list)
    factor_data_dict_id = ray.put(factor_data_dict)

    # run_factor_day.remote()
    results = [run_factor_day.remote(fac, date, factor_data_dict_id, library_name, securities_list=securities_list,
                                     return_mode=return_mode, check_olddata=check_olddata,
                                     allow_merge_olddata=allow_merge_olddata)
               for date in tradingdays_first]
    res = ray.get(results)
    if return_mode == 'show':
        fac_days_df = pd.concat(res)
        return fac_days_df


@ray.remote
def run_security_days(factor_list, date_list_per_month, security_id=None, library_name=None, return_mode=None,
                      data_input_mode=None, security_type=None, tick_sample_interval=None,
                      check_olddata=True):
    # 1  获取行情数据放在共享内存当中
    df_days_list = [pd.DataFrame()]

    # 2 security_id可能存在三种格式，
    #   第一种是str的格式,与原来的因子跑批格式一致，每个因子都在单一标的上进行计算。
    #   第二种是list格式，表示该次跑批都是跨票因子，第一个是主标的，其余为副标的，副标的仅包括Tick数据
    #   第三种是tuple格式， 表示该次跑批都是跨票因子，第一个是主标的，其余为副标的，副标的与主标的有一致的data_input_mode
    # 根据入参security_id 的格式来判断是否是跨票因子
    security_id_extra_list = None
    if isinstance(security_id, (list, tuple)):
        security_id_list = security_id
        security_id = security_id_list[0]
        security_id_extra_list = security_id_list[1:]

    # 按月分配日期 并行计算
    for date_list in date_list_per_month:
        # TODO： price_data改造为字典优化！

        # 获取主标的的行情数据
        price_data_dict_ori = collect_market_data(security_code=security_id, security_type=security_type,
                                                  start_date=date_list[0], end_date=date_list[-1],
                                                  collect_mode=data_input_mode,
                                                  tick_sample_interval=tick_sample_interval)

        # 如果副标的列表/元组不为空，即认为该进程下的因子需要多只标的的行情数据。
        # 因子计算完成存储的时候会存储在主标的下
        if security_id_extra_list:
            # list格式，表示该次跑批都是跨票因子，第一个是主标的，其余为副标的，副标的仅包括Tick数据
            # tuple格式， 表示该次跑批都是跨票因子，第一个是主标的，其余为副标的，副标的与主标的有一致的data_input_mode
            if isinstance(security_id_extra_list, list):
                data_input_mode_extra = list(set(data_input_mode) - {"TRANSACTION_RAW", "ORDER_RAW", "KLINE1M_RAW"})
            elif isinstance(security_id_extra_list, tuple):
                data_input_mode_extra = data_input_mode
            extra_price_data_dict_ori = {}
            # 逐个取副标的行情数据，格式与主标的保持一致，按月取然后放进共享内存中
            # 存在多个副标的的情况下，将行情数据存储为字典 key: securoty_id    value: ray.object_id
            for security_id_extra in security_id_extra_list:
                extra_price_data_dict_ori[security_id_extra] = collect_market_data(security_code=security_id_extra,
                                                                                   security_type=security_type,
                                                                                   start_date=date_list[0],
                                                                                   end_date=date_list[-1],
                                                                                   collect_mode=data_input_mode_extra,
                                                                                   tick_sample_interval=tick_sample_interval)
        r = []
        for date in date_list:
            # 从行情数据中逐天抽取数据，传到相应的task中
            price_data_dict = {}  # 主标的字典 形如：{‘tick’:pd.DataFrame,'transaction':pd.DataFrame}
            extra_price_data_dict = {}  # 副标的的字典 形如{'159901.SZ':{‘tick’:pd.DataFrame,'transaction':pd.DataFrame}}
            # 获取主标的的行情数据
            for key in price_data_dict_ori:
                if "args" in key:
                    price_data_dict[key] = price_data_dict_ori[key]
                    continue
                price_data_dict[key] = price_data_dict_ori[key][price_data_dict_ori[key]['MDDate'] == date]
            # 获取副标的的行情数据
            for extra_security_id in extra_price_data_dict_ori:
                extra_price_data_dict.update({extra_security_id: {}})
                for key in extra_price_data_dict_ori[extra_security_id]:
                    if "args" in key:
                        extra_price_data_dict[extra_security_id][key] = extra_price_data_dict_ori[extra_security_id][
                            key]
                        continue
                    extra_price_data_dict[extra_security_id][key] = extra_price_data_dict_ori[extra_security_id][key][
                        extra_price_data_dict_ori[extra_security_id][key]['MDDate'] == date]

            r.append(run_security_day.remote(factor_list, date, security_id=security_id, security_type=security_type,
                                             library_name=library_name,
                                             extra_price_data_dict=extra_price_data_dict,
                                             price_data_dict=price_data_dict,
                                             return_mode=return_mode, check_olddata=check_olddata))
        df_per_day = ray.get(r)
        if return_mode == 'show':
            df_days_list += df_per_day
    if return_mode == 'show':
        days_df = pd.concat(df_days_list)
        return days_df


@ray.remote
def run_security_day(factor_list, date, price_data_dict, security_id, security_type, library_name, return_mode=None,
                     extra_price_data_dict={}, check_olddata=True):
    # 实例化每一个因子 取出所需的依赖数据 调用计算逻辑
    # 将每个因子的计算结果按照列的方向进行拼接 得到全因子单票单日的DataFrame
    res_df_list = []

    # price_data: 高频行情数据 格式 DataFrame
    if "tick_sample_args" in price_data_dict.keys():
        price_data_dict["tick"] = precross_data_from_tquant(price_data_dict["tick"], security_type)
        price_data_dict["tick"] = sample_data_aux(price_data_dict["tick"], **price_data_dict["tick_sample_args"])
    if "transaction_sample_args" in price_data_dict.keys():
        price_data_dict["transaction"] = sample_transaction_data(price_data_dict["transaction"],
                                                                 **price_data_dict[
                                                                     "transaction_sample_args"])

    # 入参中如果额外标的行情数据不为空，则会读取共享内存中的额外行情数据，采样后按天存进字典中。采样频率与方法和主标的的数据保持一致
    # extra_price_data_dict存储的形式形如 {'159901.SZ':{'tick':pd.DataFrame,'transaction':pd.DataFrame}}
    # 相比主标的的行情字典price_data_dict 在外多套了一层标的 作为外层字典的key
    if extra_price_data_dict:
        for security_id_extra in extra_price_data_dict.keys():
            if "tick_sample_args" in extra_price_data_dict[security_id_extra].keys():
                extra_price_data_dict[security_id_extra]['tick'] = precross_data_from_tquant(
                    extra_price_data_dict[security_id_extra]['tick'][
                        extra_price_data_dict[security_id_extra]['tick']['MDDate'] == date], security_type)

                extra_price_data_dict[security_id_extra]['tick'] = sample_data_aux(
                    extra_price_data_dict[security_id_extra]['tick'],
                    **extra_price_data_dict[security_id_extra]
                    ["tick_sample_args"])
            if "transaction_sample_args" in extra_price_data_dict[security_id_extra].keys():
                extra_price_data_dict[security_id_extra]['transaction'] = sample_transaction_data(
                    extra_price_data_dict[security_id_extra]['transaction'][
                        extra_price_data_dict[security_id_extra]['transaction']['MDDate'] == date],
                    **extra_price_data_dict[security_id_extra]["transaction_sample_args"])

    # 将extra_price_data 放进price_data中， 格式为{'159901.SZ':{'tick':pd.DataFrame,'transaction':pd.DataFrame}}
    price_data_dict.update(extra_price_data_dict)

    for fac_cls in factor_list:
        fac = fac_cls()
        if len(fac.depend_factor):
            factor_data = fac.get_factor_data(start_date=date, end_date=date, securities_list=[security_id])
        else:
            factor_data = {}

        # 调用计算逻辑
        tmp_series = fac.calc(price_data=price_data_dict, factor_data=factor_data, custom_params=fac.custom_params)
        if (not isinstance(tmp_series, pd.Series)) or (len(str(tmp_series.index[0])) not in [8, 9]):
            raise Exception(
                "{} The function calc must return pd.Series[index:MDTime, value:factor value]".format(fac_cls))
        # 数据格式转换
        df = tmp_series.to_frame()
        df.columns = [fac.factor_name]
        if not df.empty:
            res_df_list.append(df)
    if res_df_list:
        res = pd.concat(res_df_list, axis=1)
    else:
        res = pd.DataFrame()
    res.index.name = 'MDTime'
    res = res.reset_index()
    res['MDDate'] = date
    # 判断是存储还是展示，默认是存储

    if return_mode == 'save':
        # 调用存储接口
        tps = PsFactorData()
        tps.update_factor_value_by_security(library_name, res, security=security_id, check_olddata=check_olddata)
        fac_logger.debug("Result has been stored successfully! HTSCSecurityID:{0}, MDDate:{1}".format(security_id, date))
        return
    elif return_mode == 'show':
        res['HTSCSecurityID'] = security_id
        res = res[['MDDate', 'MDTime', 'HTSCSecurityID'] + list(
            set(res.columns.tolist()) - {'MDDate', 'MDTime', 'HTSCSecurityID'})]
        fac_logger.debug("Calculation completed! HTSCSecurityID:{0}, MDDate:{1}".format(security_id, date))
        return res
    else:
        raise Exception("Please choose model from save or show")


@ray.remote
#@factor_time_info
def run_factor_day(fac, dt_to, factor_data_dict_id, library_name, securities_list, return_mode, check_olddata=True,
                   allow_merge_olddata=True):
    """
    :param fac:
    :param allow_merge_olddata:
    :param check_olddata:
    :param return_mode:
    :param library_name:
    :param dt_to:
    :param factor_data_ori:
    :param base_data_ori:
    :return:
    """
    # 获取计算当日因子需要的数据播放窗口
    trade_date_list = get_before_trade_days(dt_to, fac.day_lag) if fac.day_lag else [dt_to]
    report_date_list = get_before_report_day(dt_to, fac.quarter_lag) if fac.quarter_lag else []

    # 从共享内存中获取计算单日需要的依赖因子数据
    factor_data = {}
    for factor_describe in factor_data_dict_id.keys():
        factor_type = factor_describe.split(".")[0]
        if factor_type == "BasicFinancialFactor":
            factor_data[factor_describe] = factor_data_dict_id[factor_describe][
                factor_data_dict_id[factor_describe].index.get_level_values(0).isin(report_date_list)]
        else:
            factor_data[factor_describe] = factor_data_dict_id[factor_describe][
                factor_data_dict_id[factor_describe].index.get_level_values(0).isin(trade_date_list)]

    # 调用calc方法进行计算
    df_series = fac.calc(factor_data=factor_data)
    if (not isinstance(df_series, pd.Series)) or (len(df_series.index) != len(securities_list)):
        raise Exception("The function calc must return pd.Series[index:HTSCSecurityID, value:factor value]")

    # 　判断低频因子calc（）方法返回的数据格式是否正确
    # 校验条件过强 暂时不用
    # if (len(df_series.index) != len(securities_list)) or (
    #         set(df_series.index.to_list()) != set(securities_list)):
    #     raise Exception("The calc method needs to return a pd.Series. Index:securities ")

    # 数据格式转换 需要calc返回统一的格式
    df = pd.DataFrame()
    df[dt_to] = df_series
    df = df.T

    # 判断是存储还是展示，默认是存储

    if return_mode == 'save':
        df = df.stack().to_frame()
        df.index.names = ['MDDate', 'HTSCSecurityID']
        df.columns = ['Value']
        # 调用存储接口
        tps = PsFactorData()
        tps.update_factor_value_by_factor(library_name, df, factor=fac.factor_name, check_olddata=check_olddata,
                                          allow_merge_olddata=allow_merge_olddata)
        fac_logger.debug("Result has been stored successfully! Factor:{0}, MDDate:{1}".format(fac.factor_name, dt_to))
        return
    elif return_mode == 'show':
        df['Factor'] = fac.factor_name
        return df
    else:
        raise Exception("Please choose model from save or show")


if __name__ == '__main__':
    # "pxchange","roll_measure_autocorr", "weighted_buysell_px_spread_delta"
    factor_list = [
        "pxchange"]  # ["pxchange", "roll_measure_autocorr", "TotalBuySellOrderQtyMinus", "order_dispersion", "cor_px_vol",
    # "px_vol_corr_slope", "px_to_high_premium_discount",
    # "sell_buy_qty_spread", "rsi", "roc"]
    res = run_securities_days(factor_list, '20180119', '20180120',
                              num_cpus=1, data_input_mode=["TICK_SAMPLE", "TRANSACTION_SAMPLE"],
                              security_list=["159915.SZ"],
                              security_type="fund",
                              library_name='xx_high11', return_mode='show',
                              file_path='../factors/', options={"local_mode": True})
    # import pickle
    # # pickle.dump(res, open("res.pkl", "wb"))
    # from tquant.SmartFactor.factors.pxchange import pxchange
    # ray.init(num_cpus=1,local_mode=True)
    # price_data_dict = pickle.load(open("price_data_dict.pkl","rb"))
    # df = run_security_day([pxchange], '20180119', price_data_dict, "159915.SZ", "fund", "fund", return_mode="show",
    #                      check_olddata=True)
    # fac_logger.debug(ray.get(df))
    # fac_logger.debug(df)
