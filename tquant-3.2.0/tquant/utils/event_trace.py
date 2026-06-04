from sjyy.common.EventFactory import EventFactory
from sjyy.SjyyAnalytics import SjyyAnalytics
from sjyy.entities.UserInfo import UserInfo
from sjyy.entities.SysProject import SysProject
import time, os, sys
import inspect


class EventTrace:
    """类装饰器，发送埋点"""
    env = os.environ.get("DSWMAP_envTag", 'uat').lower()  # prd|sit|release
    data_dict = {'BasicData': (1001, '基础数据读取'),
                 'StockData': (1002, '股票数据读取'),
                 'IndexData': (1003, '指数数据读取'),
                 'FundData': (1004, '基金数据读取'),
                 'FutureData': (1005, '期货数据读取'),
                 'BondData': (1006, '债券数据读取'),
                 'RayCluster': (1007, 'Ray集群启动'),
                 'PsFactorData': (1008, '个人因子存取'),
                 'XBrain': (1010, '策略回测'),
                 }

    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        # __func_name = self.__func.__name__
        obj = self.__func(*args, **kwargs)
        # eve = self.event_function(__func_name)
        # sa = SjyyAnalytics(self.env, bulk_size=1)
        # sa.addEvents(eve)
        return obj

    @staticmethod
    def event_function(func_name):
        userInfoexe = UserInfo()
        userInfoexe.setDistinct_id(os.environ.get('DSWMAP_username', 'unknow'))
        userInfoexe.setIs_login_id(1)
        khh = os.environ.get('DSWMAP_accountid', 'unknow')
        if khh=="unknow":
            khh = os.environ.get('HADOOP_USER_NAME', 'unknow1')
        if not os.path.exists('/.dockerenv'):
            #非docker环境
            khh = "admin"
        userInfoexe.setKhh(khh)
        # userInfoexe.setDevice_id("di11")
        # userInfoexe.setKhh("test1")
        # userInfoexe.setRecvtime(int(time.time() * 1000))
        # userInfoexe.setTimezone("UTC+8")

        spexe = SysProject()
        spexe.setProduct_name("TQuant")
        spexe.setProduct_id("000465T")
        spexe.setChannel_env(EventTrace.env)

        exe = EventFactory.creatEvents("function")
        exe.setUserInfo(userInfoexe)
        exe.setSysProject(spexe)
        exe.setEvent("function")
        exe.setTime(int(time.time() * 1000))

        # f_id, f_name = EventTrace.data_dict[func_name] if func_name in EventTrace.data_dict else (0, 0)
        # exe.setFunction_id(f_id)
        # exe.setFunction_title(f_name)
        return exe


def trunc_str(strings):
    try:
        strings = str(strings)
    except:
        return 'unstandard str'
    if len(strings) > 20:
        return strings[:20] + '...'
    else:
        return strings


def send_factor_trace(function_title, factor_name, factor_list, start_date,
                      end_date, factor_type):
    time1 = time.time()
    eve = EventTrace.event_function(function_title)
    eve.setFunction_id(EventTrace.data_dict.get(function_title, (1009, '个人因子模块'))[0])
    eve.setFunction_title(function_title)
    if type(factor_list) == list:
        factor_list = ', '.join(factor_list)
    params = {'factor_name': factor_name, 'factor_list': factor_list,
              'start_date': start_date, 'end_date': end_date,
              'factor_type': factor_type}
    eve.setParam(str(params))
    eve.setExecute_time(time.time() - time1)

    try:
        sa = SjyyAnalytics(EventTrace.env, bulk_size=1)
        sa.addEvents(eve)
    except:
        raise Exception('个人因子埋点失败')


def event_trace(func):
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        time1 = time.time()
        try:
            cls_name = (args[0].__str__().split()[0].split('.')[-1])
        except:
            cls_name = 'unknow'
        eve = EventTrace.event_function(func.__name__)
        rst = None
        if func.__name__ not in ["run_realtime_calculation_by_securities"]:
            rst = func(*args, **kwargs)
        eve.setExecute_time(time.time() - time1)
        eve.setFunction_id(EventTrace.data_dict.get(cls_name, (1009, "个人因子模块"))[0])
        eve.setFunction_title(func.__name__)

        sig = inspect.signature(func)
        params_new = {}
        try:
            params = dict(sig.bind(*args, **kwargs).arguments)
        except:
            params = dict(sig.bind_partial(*args, **kwargs).arguments)
        for p in params:
            if p == 'self' or type(params[p]) not in [int, str, float, list]:
                continue
            if type(params[p]) == list:
                params_new[p] = [trunc_str(i) for i in params[p]]
                if p in ['factor_list', 'factor_name']:
                    factors = []
                    for fac in params[p]:
                        if type(fac) == str:
                            factors.append(fac)
                        else:
                            try:
                                #为实例化类
                                factors.append(fac.__name__)
                            except:
                                pass
                    params_new[p] = ','.join(factors)
                else:
                    try:
                        if params[p]:
                            params_new[p] = trunc_str(','.join(params[p]))
                    except:
                        pass
            elif type(params[p]) == str and p != 'factor_list':
                if p not in ['factor_list', 'factor_name']:
                    params_new[p] = trunc_str(params[p])
                else:
                    params_new[p] = params[p]
            else:
                params_new[p] = params[p]
        try:
            #记录源表名
            if "table_name" in params_new:
                params_new["factor_list"] = params_new["table_name"] + ',' + params_new["factor_list"]
            params_new['size'] = '{}'.format(rst.shape)
        except:
            pass
        eve.setParam(str(params_new))

        try:
            sa = SjyyAnalytics(EventTrace.env, bulk_size=1)
            sa.addEvents(eve)
        except:
            pass
        if func.__name__ in ["run_realtime_calculation_by_securities"]:
            rst = func(*args, **kwargs)
        return rst

    return wrapper
