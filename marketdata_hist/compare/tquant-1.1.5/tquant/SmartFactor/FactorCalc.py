import os
import ray
import pandas as pd
from tquant.SmartFactor.util.util import get_fac_class, factor_time_info, check_date, check_return_and_lib, \
    check_factor_list, check_factor_name, check_factor_type, check_lag_date, check_security_type
from tquant.SmartFactor.util.data_context import get_trade_days, get_stocks_pool, get_before_trade_day, get_factor, \
    get_before_trade_days, get_before_report_day
from tquant import PsFactorData


def set_ray_options(num_cpus, object_store_memory, options):
    if ray.is_initialized():
        raise Exception("Ray计算环境启动失败：当前有正在使用的Ray计算环境，请用ps -ef|grep ray查看并停止！")
    if num_cpus is None:
        num_cpus = 4
    if options is None:
        options = {}
    if object_store_memory:
        ray.init(num_cpus=num_cpus, object_store_memory=object_store_memory,
                 **options) if not ray.is_initialized() else None
    else:
        ray.init(num_cpus=num_cpus, **options)


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


def run_securities_days(factor_list, start_date, end_date, num_cpus=None, object_store_memory=None,
                        library_name=None, return_mode='show', file_path='./', check_olddata=True, options=None):
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
    # 按月对交易日列表进行划分 列表中的每一个元素都是一个时间列表
    date_list = get_trade_days(start_date, end_date)
    # 日期列表返回可能为空，为空时影响接下来的计算
    if not date_list:
        raise Exception("在日期{0}~{1}之间没有交易日".format(start_date, end_date))  # 映射因子与标的的关系
    date_list_per_month = []
    date_tmp_list = []
    start_year_month = date_list[0][:6]
    day_nums = len(date_list)
    for i in range(day_nums):
        if date_list[i][:6] == start_year_month:
            date_tmp_list.append(date_list[i])
        else:
            start_year_month = date_list[i][:6]
            date_list_per_month.append(date_tmp_list)
            date_tmp_list = [date_list[i]]
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

        cur_security_pool = get_stocks_pool(day=start_date, security_type=fac_cls.security_type,
                                            securities=fac_cls.security_pool)
        fac_to_sec_dict[fac_cls] = cur_security_pool

    # 映射标的与因子的关系
    sec_to_fac_dict = {}
    for key, value in fac_to_sec_dict.items():
        for code in value:
            sec_to_fac_dict[code] = sec_to_fac_dict.get(code, [])
            sec_to_fac_dict[code].append(key)
    security_list = list(sec_to_fac_dict.keys())

    # # 提示用户最终需要跑批的标的池
    # print("According to statistics, this parallel calculation will be in securties list: ", end="")
    # print(security_list)

    r = [run_security_days.remote(factor_list=sec_to_fac_dict[security_id], date_list_per_month=date_list_per_month,
                                  security_id=security_id, library_name=library_name,
                                  return_mode=return_mode, check_olddata=check_olddata) for security_id in security_list]
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
                      check_olddata=True):
    fac_cls = factor_list[0]
    fac = fac_cls()
    df_days_list = [pd.DataFrame()]
    # 按月分配日期 并行计算
    for date_list in date_list_per_month:
        price_data_ori = fac.get_price_data(start_date=date_list[0], end_date=date_list[-1], securitiy_code=security_id)
        price_data_ori_id = ray.put(price_data_ori)
        r = [run_security_day.remote(factor_list, date, security_id, library_name, price_data_ori_id, return_mode,
                                     check_olddata) for date in date_list]
        df_per_day = ray.get(r)
        if return_mode == 'show':
            df_days_list += df_per_day
    if return_mode == 'show':
        days_df = pd.concat(df_days_list)
        return days_df


@ray.remote
def run_security_day(factor_list, date, security_id, library_name, price_data_ori_id, return_mode=None,
                     check_olddata=True):
    # 实例化每一个因子 取出所需的依赖数据 调用计算逻辑
    # 将每个因子的计算结果按照列的方向进行拼接 得到全因子单票单日的DataFrame
    res_df_list = []
    price_data = price_data_ori_id[price_data_ori_id['MDDate'] == date]
    for fac_cls in factor_list:
        fac = fac_cls()

        #  高频因子暂无依赖因子可选
        if len(fac.depend_factor):
            factor_data = fac.get_factor_data(day_start_date=date, end_date=date, securities_list=[security_id])
        else:
            factor_data = {}

        # 调用计算逻辑
        tmp_series = fac.calc(price_data=price_data, factor_data=factor_data, custom_params=fac.custom_params)
        if (not isinstance(tmp_series, pd.Series)) or (len(str(tmp_series.index[0])) not in [8, 9]):
            raise Exception("The function calc must return pd.Series[index:MDTime, value:factor value]")
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
        print("Result has been stored successfully! HTSCSecurityID:{0}, MDDate:{1}".format(security_id, date))
        return
    elif return_mode == 'show':
        res['HTSCSecurityID'] = security_id
        res = res[['MDDate', 'MDTime', 'HTSCSecurityID'] + list(
            set(res.columns.tolist()) - {'MDDate', 'MDTime', 'HTSCSecurityID'})]
        print("Calculation completed! HTSCSecurityID:{0}, MDDate:{1}".format(security_id, date))
        return res
    else:
        raise Exception("Please choose model from save or show")


@ray.remote
@factor_time_info
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
        print("Result has been stored successfully! Factor:{0}, MDDate:{1}".format(fac.factor_name, dt_to))
        return
    elif return_mode == 'show':
        df['Factor'] = fac.factor_name
        return df
    else:
        raise Exception("Please choose model from save or show")


if __name__ == '__main__':
    # ray.init(num_cpus=3, webui_host='127.0.0.1') if not ray.is_initialized() else None
    # run_factors_days(['turnover_w_ave', 'turnover_w_ave_float', 'vwap_close'], '20191112', '20191112',
    #                  library_name='xx_low_8',
    #                  save_or_show='show', file_path='/tmp/pycharm_project_backtest/data-tquant/factor_data/')
    # res = run_factors_days(['ma5'], '20191112', '20191129',library_name='ma5', save_or_show='show',file_path='/tmp/pycharm_project_584/tquant/tquant/SmartFactor/test/')
    # print(res['ma5'])

    # run_stocks_days(['hfre_fac_nsw', 'hfre_fac_test'], '20191112', '20191112', ['601688.SH', '000001.SZ'],
    #                 library_name='xx_high11', save_or_show='show',file_path='/tmp/pycharm_project_backtest/tquant/SmartFactor/factor_data/')
    res = run_securities_days(['hfre_fac_nsw', 'hfre_fac_test'], '20191112', '20191114', ['601688.SH', '000001.SZ'],
                              options={'ray.num_cpus': 10},
                              library_name='xx_high11', return_mode='show',
                              file_path='/tmp/pycharm_project_backtest/data-tquant/factor_data/', )

    print(res['601688.SH'])
    print(res['000001.SZ'])
