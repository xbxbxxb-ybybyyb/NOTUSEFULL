from sjyy.common.EventFactory import EventFactory
from sjyy.SjyyAnalytics import SjyyAnalytics
from sjyy.entities.UserInfo import UserInfo
from sjyy.entities.SysProject import SysProject
import time, os, sys


class EventTrace:
    """类装饰器，发送埋点"""
    env = os.environ.get("DSWMAP_envTag",'sit').lower()  # prd|sit|release
    data_dict = {'BasicData': (1001, '基础数据读取'),
                 'StockData': (1002, '股票数据读取'),
                 'IndexData': (1003, '指数数据读取'),
                 'FundData': (1004, '基金数据读取'),
                 'FutureData': (1005, '期货数据读取'),
                 'BondData': (1006, '债券数据读取'),
                 'RayCluster': (1007, 'Ray集群启动'),
                 'PsFactorData': (1008, '个人因子存取')
                 }

    def __init__(self, func):
        self.__func = func

    def __call__(self, *args, **kwargs):
        # __func_name = self.__func.__name__
        obj = self.__func(*args, *kwargs)
        # eve = self.event_function(__func_name)
        # sa = SjyyAnalytics(self.env, bulk_size=1)
        # sa.addEvents(eve)
        return obj

    @staticmethod
    def event_function(func_name):
        userInfoexe = UserInfo()
        userInfoexe.setDistinct_id(os.environ.get('DSWMAP_username', '123'))
        userInfoexe.setIs_login_id(1)
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
        param = {'param1': 1, 'param2': 2}
        exe.setParam(str(param))
        return exe


def event_trace(func):
    import functools
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # time1 = time.time()
        cls_name = (args[0].__str__().split()[0].split('.')[-1])
        eve = EventTrace.event_function(func.__name__)
        rst = func(*args, **kwargs)
        # eve.setExecute_time(time.time() - time1)
        eve.setFunction_id(EventTrace.data_dict[cls_name][0])
        eve.setFunction_title(func.__name__)
        # size = sys.getsizeof(rst)
        # param = {'size': size, 'library_name': 2}
        # eve.setParam(str(param))
        try:
            sa = SjyyAnalytics(EventTrace.env, bulk_size=1)
            sa.addEvents(eve)
        except:
            pass
        return rst

    return wrapper
