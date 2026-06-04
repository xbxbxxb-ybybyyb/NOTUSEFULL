# -*- coding:utf-8 -*-
import ray
import os
import pandas as pd
import traceback
import time
from xquant.factordata import FactorData

from SmartFactor.util.util import get_fac_class, factor_time_info, \
    check_date, check_return_and_lib, check_factor_list, check_factor_type, check_lag_date, check_security_type, \
    check_factor_sample_consist, get_factor_attr, get_fac_to_sec_dict, get_sec_to_fac_dict, check_security_list, \
    check_factor_name, parse_date_list, check_data_input_mode_consist, check_run_end_df
from SmartFactor.util.data_context import get_trade_days, \
    get_stocks_pool, get_before_trade_day, get_before_trade_days, \
    get_before_report_day
from SmartFactor.mkdata.DataCollector import collect_market_data
# from xquant.xqutils.perf_profile import profile
from SmartFactor.mkdata.helper import sample_data_aux, \
    precross_data_from_tquant, sample_transaction_data, sample_orderbook
from SmartFactor.MetaFactor import MetaBaseFactor
from SmartFactor.calculation.helper import set_ray_options



def run_securities_days(factor_list, start_date, end_date, library_name, security_type,
                        data_input_mode=None,
                        security_list=None, return_mode='show',
                        library_env='research', file_path='./',
                        check_olddata=True,
                        num_cpus=None, object_store_memory=None,
                        options=None, verbose=0):
    """
    :param factor_list: list，需要计算的因子列表，每个元素代表一个因子，可以是srt或者因子类
    :param start_date: str， 计算开始时间，如20190701.
    :param end_date: str，计算结束时间，如20190701.
    :param num_cpus: int，通过Ray并行计算的进程数， 如1。
    :param object_store_memory: int，通过Ray并行计算的共享内存大小，如1e9,单位B
    :param library_name: 因子库名，指定因子存储的因子库的名称。当return_mode=’save’时，因子库为必传。
    :param data_input_mode: list，订阅的数据类型，目前支持TICK_RAW、TICK_SAMPLE（采样Tick数据）、TRANSACTION_RAW、TRANSACTION_SAMPLE、ORDER_RAW、ORDER_SAMPLE、KLINE1M_RAW, SAMPLE模式下因子的custome_param必须有tick_sample_interval属性，用于定义采样时间间隔。
    :param security_type: str，订阅的标的类型，支持STOCK（股票）、FUND（基金）。
    :param security_list: list，需要计算的标的列表，如["159958.SZ", "159915.SZ"]。如果对跨票因子进行跑批计算，需要传入[['159958.SZ','159901.SZ'],['159915.SZ', '159901.SZ']] 或者[('159958.SZ','159901.SZ'),('159915.SZ', '159901.SZ')]
    :param return_mode: 默认为show， save: 存储计算结果到因子库，无返回值;show:字典形式返回计算结果
    :param file_path: 默认值为’./’，file_path表示因子类文件的存储路径（绝对路径与相对路径均可），用于递归搜索并加载因子类。若factor_list中传的因子名为str，会从file_path下搜索。
    :param check_olddata: 默认为True。为True时，会校验factor_values与原因子数据（若之前已经存储过）是否同一天同一个因子有相同的HTSCSecurityID个数；若相同,会用factor_values存储新数据，若不相同参见allow_merge_olddata参数选项。
    :param options: dict， 启动Ray多进程计算的其他初始化参数，如{"local_mode":True},表示以本地调试模式运行。
    :param verbose: int 默认为0。大于0时显示详细的错误信息
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
    :param dynamic_load_attr:
    :param factor_type
    :param start_date: 开始时间 格式 ’YYYYMMDD‘
    :param end_date:   结束时间 格式 ’YYYYMMDD‘
    :param check_olddata:
    :param options: dict 例如：{'webui_host':127.0.0.1}
    :param tick_sample_interval: 当且仅当data_input_mode中有DataCollectMode.TICK_SAMPLE时有效，为采样时间间隔

    :return:
    """
    dynamic_load_attr = False
    factor_type = 'factor'
    if security_type not in ['stock', 'fund']:
        raise Exception("security_type 支持stock（股票）, fund（基金）!")

    # 校验日期
    check_date(start_date, end_date)
    # 如果 是save模式 则校验library_name
    check_return_and_lib(return_mode, library_env, library_name)
    # 初始化ray
    set_ray_options(num_cpus=num_cpus, object_store_memory=object_store_memory,
                    options=options)
    # 校验factor_list
    check_factor_list(factor_list)
    # 校验security_list,list 每个元素为（str,list,tuple）中的一个，且必须保持一致
    check_security_list(security_list)
    # 按月对交易日列表进行划分 列表中的每一个元素都是一个时间列表
    date_list = get_trade_days(start_date, end_date)
    # 日期列表返回可能为空，为空时影响接下来的计算
    if not date_list:
        raise Exception(
            "在日期{0}~{1}之间没有交易日".format(start_date, end_date))  # 映射因子与标的的关系
    date_list_per_month = parse_date_list(date_list=date_list)

    # 映射因子与标的的关系
    fac_to_sec_dict = get_fac_to_sec_dict(factor_list, dynamic_load_attr, library_env, end_date, file_path)
    fac_cls_list = list(fac_to_sec_dict.keys())

    sec_to_fac_dict = get_sec_to_fac_dict(fac_to_sec_dict)

    # 若入参中security_list参数为None 则计算任务根据因子属性中的标的池进行计算
    # 若入参中security_list参数不为None 则计算的是该参数下每一个标的的所有factor_list中因子的值
    if not security_list:
        security_list = list(sec_to_fac_dict.keys())

    # 若计算入口不传data_input_mode 则根据所有因子的data_input_mode来计算
    # 若计算入口传了data_input_mode 则根据参数所传的data_input_mode来计算
    if not data_input_mode:
        # 校验所有因子的data_input_mode一致
        check_data_input_mode_consist(fac_cls_list)
        data_input_mode = fac_cls_list[0].data_input_mode
    tick_sample_interval = 0
    if {'TICK_SAMPLE', 'TRANSACTION_SAMPLE', 'ORDER_SAMPLE'}.intersection({i.upper() for i in data_input_mode}):
        # 当data_input_mode 中包含采样的数据类型时， 校验所有因子的sample_period一致
        check_factor_sample_consist(fac_cls_list)
        tick_sample_interval = fac_cls_list[0].custom_params.get("sample_period")

    print("start calculation...")
    r = [run_security_days.remote(factor_list=fac_cls_list,
                                  date_list_per_month=date_list_per_month,
                                  data_input_mode=data_input_mode,
                                  security_type=security_type,
                                  security_id=security_id,
                                  return_mode=return_mode,
                                  library_env=library_env,
                                  file_path=file_path,
                                  tick_sample_interval=tick_sample_interval,
                                  factor_type=factor_type,
                                  check_olddata=check_olddata,
                                  library_name=library_name,
                                  verbose=verbose) for security_id
         in security_list]
    result_list = ray.get(r)
    facs_days_dict = {}
    empty_secs_days_dict = {}
    for result in result_list:
        df_sec_days, empty_days_dict = result
        facs_days_dict[df_sec_days.iloc[0]['HTSCSecurityID']] = df_sec_days
        if empty_days_dict:
            empty_secs_days_dict[df_sec_days.iloc[0]['HTSCSecurityID']] = empty_days_dict

    if empty_secs_days_dict:
        print("=============")
        print("注意：以下标的对应日期内的计算结果为空，请检验因子的计算逻辑准确性，或者依赖行情的数据完整度！")
        print(empty_secs_days_dict)
        print("=============")

    if return_mode == 'show':
        ray.shutdown()
        return facs_days_dict
    ray.shutdown()





@ray.remote
def run_security_days(factor_list, date_list_per_month, data_input_mode,
                      security_type, security_id, return_mode,
                      library_env='research', file_path=None, factor_type='factor',
                      tick_sample_interval=None, check_olddata=True,
                      library_name=None, verbose=0):
    # 获取因子标的类型
    if not security_type:
        try:
            fac = factor_list[0]()
            security_type = fac.security_type
        except:
            security_type = None
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

    df_days_list = []
    empty_days_dict = {}
    # 3. 按照日期并行
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
        # 从行情数据中逐天抽取数据，传到相应的task中
        for date in date_list:
            price_data_dict = {}  # 主标的字典 形如：{‘tick’:pd.DataFrame,'transaction':pd.DataFrame}
            extra_price_data_dict = {}  # 副标的的字典 形如{'159901.SZ':{‘tick’:pd.DataFrame,'transaction':pd.DataFrame}}
            # 获取主标的的行情数据
            for key in price_data_dict_ori:
                if "args" in key:
                    price_data_dict[key] = price_data_dict_ori[key]
                    continue
                price_data_dict[key] = price_data_dict_ori[key][price_data_dict_ori[key]['MDDate'] == date]
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
                                extra_price_data_dict_ori[extra_security_id][key]['MDDate'] == date]
            # 此处security_id为单一的主标的，可用get_security_type获取security_type
            if not security_type:
                # xquant没有取标的类型的接口需手动传入
                raise Exception("security_type 标的类型未设置！")
            r.append(run_security_day.remote(factor_list, date,
                                             security_id=security_id,
                                             security_type=security_type,
                                             return_mode=return_mode,
                                             library_env=library_env,
                                             price_data_dict=price_data_dict,
                                             extra_price_data_dict=extra_price_data_dict,
                                             factor_type=factor_type,
                                             check_olddata=check_olddata,
                                             library_name=library_name,
                                             verbose=verbose))
        days_res = ray.get(r)
        for result in days_res:
            df_per_day, empty_fac_date_dic = result
            if isinstance(df_per_day, pd.DataFrame):
                df_days_list.append(df_per_day)
            if empty_fac_date_dic:
                empty_days_dict.update(empty_fac_date_dic)

    if return_mode == 'show':
        if df_days_list:
            days_df = pd.concat(df_days_list)
            return days_df, empty_days_dict
        else:
            return pd.DataFrame([security_id], columns=['HTSCSecurityID']), empty_days_dict
    else:
        return pd.DataFrame([security_id], columns=['HTSCSecurityID']), empty_days_dict


@ray.remote
def run_security_day(factor_list, date, security_id, security_type, return_mode,
                     library_env, price_data_dict, extra_price_data_dict={}, factor_type='factor',
                     check_olddata=True, library_name=None, verbose=0):
    # 实例化每一个因子 取出所需的依赖数据 调用计算逻辑
    # 将每个因子的计算结果按照列的方向进行拼接 得到全因子单票单日的DataFrame
    res_df_list = []
    # price_data: 高频行情数据 格式 DataFrame
    if "tick_sample_args" in price_data_dict.keys():
        if isinstance(security_type, list):
            s_type = security_type[0]
        else:
            s_type = security_type
        price_data_dict["tick"] = precross_data_from_tquant(price_data_dict["tick"], s_type)
        price_data_dict["tick"] = sample_data_aux(price_data_dict["tick"], **price_data_dict["tick_sample_args"])
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
            if isinstance(security_type, list):
                bd = BasicData()
                security_type_extra = bd.get_security_type(security_id_extra)
            else:
                security_type_extra = security_type
            if "tick_sample_args" in extra_price_data_dict[security_id_extra].keys():
                extra_price_data_dict[security_id_extra]['tick'] = precross_data_from_tquant(
                    extra_price_data_dict[security_id_extra]['tick'][
                        extra_price_data_dict[security_id_extra]['tick']['MDDate'] == date], security_type_extra)

                extra_price_data_dict[security_id_extra]['tick'] = sample_data_aux(
                    extra_price_data_dict[security_id_extra]['tick'],
                    **extra_price_data_dict[security_id_extra]
                    ["tick_sample_args"])
            if "transaction_sample_args" in extra_price_data_dict[security_id_extra].keys():
                extra_price_data_dict[security_id_extra]['transaction'] = sample_transaction_data(
                    extra_price_data_dict[security_id_extra]['transaction'][
                        extra_price_data_dict[security_id_extra]['transaction']['MDDate'] == date],
                    **extra_price_data_dict[security_id_extra]["transaction_sample_args"])
            if "order_sample_args" in extra_price_data_dict[security_id_extra].keys():
                extra_price_data_dict[security_id_extra]['order'] = sample_orderbook(
                    extra_price_data_dict[security_id_extra]['order'][
                        extra_price_data_dict[security_id_extra]['order']['MDDate'] == date],
                    **extra_price_data_dict[security_id_extra]["order_sample_args"])

    # 将extra_price_data 放进price_data中， 格式为{'159901.SZ':{'tick':pd.DataFrame,'transaction':pd.DataFrame}}
    price_data_dict.update(extra_price_data_dict)

    #
    empty_fac_date_list = []
    for fac_cls in factor_list:
        fac = fac_cls()
        if len(fac.depend_factor):
            factor_data = fac.get_factor_data(start_date=date, end_date=date, securities_list=[security_id])
        else:
            factor_data = {}
        try:
            start_time = time.time()
            # 调用计算逻辑
            tmp_series = fac.calc(price_data=price_data_dict, factor_data=factor_data, custom_params=fac.custom_params)
            print("The calc function cost {} s".format(time.time() - start_time))
        except Exception as e:
            print("The calc function has error !!: Factor:{0}, Date:{1},Security:{2}".format(fac.factor_name, date,
                                                                                             security_id))
            if verbose == 0:
                print("Exception:" + repr(e))
            else:
                print("=============Traceback=============")
                traceback.print_exc()
            empty_fac_date_list.append(fac.factor_name)
            res_df_list.append(pd.DataFrame(columns=[fac.factor_name]))
            continue

        # 校验数据格式
        if not isinstance(tmp_series, pd.Series):
            raise Exception("【Calc Func Error】The function calc must return Series! Not {}".format(type(tmp_series)))
        if len(str(tmp_series.index[0])) not in [8, 9]:
            raise Exception("【Calc Func Error】"
                            "The index of the Series returned by the calc method must be timestamp of length 8 or 9!"
                            "Not {}".format(tmp_series.index[0]))
        # 数据格式转换
        df = tmp_series.to_frame()
        df.columns = [fac.factor_name]
        res_df_list.append(df)
        if df.dropna(how='all', axis=1).empty:
            empty_fac_date_list.append(fac.factor_name)

    if res_df_list:
        res = pd.concat(res_df_list, axis=1)
        res.index.name = 'MDTime'
        res = res.reset_index()
        res['MDDate'] = date
    else:
        res = pd.DataFrame()
    # 如果存在某个因子在某日计算结果全是NAN值，则返回{'20191102':['Fac1','Fac2','Fac3']}格式的字典
    empty_fac_date_dic = None
    if empty_fac_date_list:
        empty_fac_date_dic = {date: empty_fac_date_list}

    # 如果res是空的，证明res_df_list为空 当日所有因子计算有问题，返回False 和 有问题的字典。
    if res.empty:
        return False, empty_fac_date_dic
    # 判断是存储还是展示，默认是存储
    if return_mode == 'save':
        # 调用存储接口
        from SmartFactor.psfactor import FactorData as XFactorData
        xps = XFactorData()
        if factor_type == 'factor':
            xps.update_factor_value_by_security(library_name, res,
                                                security=security_id,
                                                check_olddata=check_olddata)
            print(
                "Factor data has been stored successfully! HTSCSecurityID:{0}, MDDate:{1}".format(
                    security_id, date))

        elif factor_type == 'label':
            # TODO: 更新标签，必须传入library_name
            tps.update_label_value(label_values=res,
                                   security=security_id,
                                   check_olddata=check_olddata)
            print(
                "Label data has been stored successfully! HTSCSecurityID:{0}, MDDate:{1}".format(
                    security_id, date))
        return True, empty_fac_date_dic
    elif return_mode == 'show':
        res['HTSCSecurityID'] = security_id
        res = res[['MDDate', 'MDTime', 'HTSCSecurityID'] + list(
            set(res.columns.tolist()) - {'MDDate', 'MDTime',
                                         'HTSCSecurityID'})]
        print("Calculation completed! HTSCSecurityID:{0}, MDDate:{1}".format(
            security_id, date))
        return res, empty_fac_date_dic
    else:
        raise Exception("Please choose model from save or show")


