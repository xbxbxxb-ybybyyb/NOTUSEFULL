import os
import importlib.util
# from FactorProvider.conf import TDubboConf
import functools
import time, re
import datetime as dt
from tquant.SmartFactor import fac_logger


def factor_time_info(func):
    @functools.wraps(func)
    def wrapper(cls, *args, **kwargs):
        "cls为func的第一个参数"
        # 运行前
        time1 = time.time()
        # 运行中
        log_info = None
        try:
            res = func(cls, *args, **kwargs)
        except Exception as e:
            cls.log.error(
                'factor func {} failed! error msg:\n {}'.format('frame' if cls.factor_name is None else cls.factor_name,
                                                                e))
            raise e
        finally:
            # 运行后
            cls.log.info(
                "{} func: {} success! use time {:.2f} s".format(cls.factor_name, func.__name__, time.time() - time1, ))
        return res

    return wrapper


def check_date(start_date, end_date):
    # start_date 单个日期，若end_date不为None则start_date 应小于end_date
    # date_type为日期类型 year,month,day,hour,minute,second
    if (not isinstance(start_date, str)) or (not isinstance(end_date, str)):
        raise Exception("请输入字符串形式的开始日期与结束日期")
    try:
        assert len(start_date) == 8
        assert len(end_date) == 8
        sdate = dt.datetime.strptime(start_date, '%Y%m%d')
        edate = dt.datetime.strptime(end_date, '%Y%m%d')
        if sdate > edate:
            raise Exception("开始日期{0}大于结束日期{1}，请检查后输入！".format(start_date, end_date))
    except:
        raise Exception("日期-{0}-{1}的格式有误，请传入正确格式如'20200201'".format(start_date, end_date))


def check_lag_date(day_lag, quarter_lag):
    if day_lag is not None:
        if not isinstance(day_lag, int):
            raise Exception("日频数据播放窗口需要传入一个整数。")
        elif day_lag <= 0 or day_lag >= 251:
            raise ValueError("日频数据播放窗口的范围为[1,250]")
    if quarter_lag is not None:
        if not isinstance(quarter_lag, int):
            raise Exception("季频数据播放窗口需要传入一个整数。")
        elif quarter_lag <= 0 or quarter_lag >= 5:
            raise ValueError("季频数据播放窗口的范围为[1,4]")


def check_security_type(security_type):
    support_type_list = ['stock']
    if security_type not in support_type_list:
        raise Exception("目前仅支持{0}的标的类型".format(','.join(i for i in support_type_list)))


def check_factor_sample_consist(fac_list):
    """
    判断是否所有因子的采样时间间隔一致
    :param fac_list:
    :return:
    """
    consist_interval = None
    for fac in fac_list:
        try:
            custom_params = getattr(fac, "custom_params")
        except:
            raise Exception("tick_interval_seconds缺失错误：在data_input_mode包含TICK_SAMPLE或者TRANSACTION_SAMPLE的情况下，因子{}未对类属性custom_params中的tick_interval_seconds（采样时间间隔）赋值！".format(fac.__name__))
        tick_interval_seconds = custom_params.get("tick_interval_seconds", None)
        fac_logger.debug("{}, tick_interval_seconds: {}".format(fac.__name__, tick_interval_seconds))
        if not tick_interval_seconds:
            raise Exception("tick_interval_seconds缺失错误：在data_input_mode包含TICK_SAMPLE或者TRANSACTION_SAMPLE的情况下，因子{}未对类属性custom_params中的tick_interval_seconds（采样时间间隔）赋值！".format(fac.__name__))
        if not consist_interval:
            consist_interval = tick_interval_seconds
        else:
            assert tick_interval_seconds==consist_interval, "tick_interval_seconds不一致错误：因子{}的tick_interval_seconds为{}，和这批因子中其他因子的tick_interval_seconds值{}不一致！".format(fac.__name__, tick_interval_seconds, consist_interval)


def check_factor_type(factor_type):
    if factor_type not in ['DAY', 'TICK']:
        raise Exception("factor_type目前仅支持DAY(低频因子)，TICK(高频因子)两种情况")
    return


def check_factor_name(factor_name):
    if not isinstance(factor_name, str):
        raise Exception("因子名必须是字符串格式")
    if re.search(r"\W", factor_name):
        raise Exception("因子名{0}不符合格式，必须为大小写字母、数字或下划线的组合".format(factor_name))


def check_security_list(security_list):
    # security_list 支持的格式包括，
    # ['601688.SH','000001.SZ']  无跨标的因子
    # [['601688.SH', '000001.SZ'],['000002.SZ', '000003.SZ']] 跨标的因子开发过程中，副标的仅使用tick数据
    # [('601688.SH', '000001.SZ'),('000002.SZ', '000003.SZ')] 跨标的因子开发过程中，副标的与主标的数据类型完全一致
    if not isinstance(security_list, list):
        raise Exception("参数security_list应为list格式")
    if not isinstance(security_list[0], (list, tuple, str)):
        raise Exception("security_list 中每个元素的类型应当在（str, list, tuple）三种类型中")
    for i in range(1, len(security_list)):
        if not isinstance(security_list[i], (list, tuple, str)):
            raise Exception("security_list 中每个元素的类型应当在（str, list, tuple）三种类型中")
        if not isinstance(security_list[i], type(security_list[i - 1])):
            raise Exception("security_list 中每一个元素的类型应当是一致的")
    return


def check_factor_list(factor_list, factor_type):
    if not isinstance(factor_list, list):
        raise Exception("请保证factor_list是列表。")
        # 校验factor_list中的元素是否为str类型
    if (factor_type == 'DAY') and (not all(isinstance(x, str) for x in factor_list)):
        raise Exception("请保持factor_list中元素是因子名（string类型）。")
    if (factor_type == 'TICK') and (not all(isinstance(x, (str, type)) for x in factor_list)):
        raise Exception("factor_list中元素的只能是因子名（string类型）或者因子类（type类型）。")
    return


def get_factor_module(factor_name, file_path):
    # 遍历文件夹下的所有.py文件
    file_path_list = []
    for root, dirs, files in os.walk(file_path):
        for file in files:
            # 获取文件名称
            if not file.endswith('.py'):
                continue
            file_name, file_tail = file.split('.')[:2]
            # 获取文件绝对路径
            file_abs_path = os.path.join(root, file)
            if file_name == factor_name and file_tail == 'py':
                file_path_list.append(file_abs_path)
    if len(file_path_list) == 0:
        raise Exception("无法加载因子类：文件夹'{}'下无与因子{}同名的因子文件，请指定正确的file_path因子文件目录！".format(
            file_path, factor_name))
        return
    elif len(file_path_list) > 1:
        print("匹配到多个因子文件:" + " ".join(
            i for i in file_path_list) + "，请指定正确的file_path因子文件目录！")
        return
    else:
        return file_path_list[0]
    return


def get_fac_class(factor_name, file_path):
    file_abs_path = get_factor_module(factor_name, file_path)
    module_spec = importlib.util.spec_from_file_location(factor_name, file_abs_path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    try:
        cls = getattr(module, factor_name)
    except Exception:
        raise Exception("ERROR: Please keep factor class name same as factor name!")
    return cls


def check_return_and_lib(return_mode, library_name):
    if return_mode == 'show':
        pass
    elif return_mode == 'save':
        if not isinstance(library_name, str):
            raise Exception("因子库名应为str的格式")
        # jurisdictionData_dict = get_jurisdictionData()
        # db_list = list(
        #     jurisdictionData_dict["因子信息"]["jurisdictionData"].keys())
        # if not library_name in db_list:
        #     raise Exception(
        #         "library_name doesn't exist: %s！" % library_name)
    else:
        raise Exception("返回模式只有save和show两种")


import json


def get_factorAttribute(factor_name):
    json_dict = {"request": {"factor_name": factor_name}}
    json_str = json.dumps(json_dict)  # 发送给dubbo接口

    factor_attr = json.load()
    return factor_attr


def fac_name2cls(factor_name, file_path):
    """
    :params: factor_name : str 因子名
    :params: file_path : str 因子文件路径
    :return cls
    """
    # 调用dubbo接口 入参为因子名 返回为因子属性
    factor_attr_dict = get_factorAttribute(factor_name)
    # fac_cls_ori = get_fac_class(factor_name, file_path=file_path)
    return factor_attr_dict
