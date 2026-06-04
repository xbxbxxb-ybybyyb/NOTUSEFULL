from sjyy.common.EventFactory import EventFactory
from sjyy.SjyyAnalytics import SjyyAnalytics
from sjyy.entities.UserInfo import UserInfo
from sjyy.entities.SysProject import SysProject
import time
from FactorProvider.conf.DubboConf import get_userid
from xquant.setXquantEnv import xquantEnvFlag


class XQSjyy:
    sa = None

    def __init__(self):
        self.sa = SjyyAnalytics(xquantEnvFlag, bulk_size=1)  # 初始化埋点类

    def add_events(self, function_id, function_title, index_value):
        # eve = __make_event()
        try:
            userInfoexe = UserInfo()
            userInfoexe.setDistinct_id(get_userid())
            userInfoexe.setIs_login_id(1)
            # userInfoexe.setDevice_id("di11")
            # userInfoexe.setKhh("test1")
            # userInfoexe.setRecvtime(int(time.time() * 1000))
            # userInfoexe.setTimezone("UTC+8")

            spexe = SysProject()
            spexe.setProduct_name("XQuant")
            spexe.setProduct_id("000465")
            xquantEnv = xquantEnvFlag if xquantEnvFlag == 'prd' else xquantEnvFlag+'_test'
            spexe.setChannel_env(xquantEnv)

            exe = EventFactory.creatEvents("function")
            exe.setUserInfo(userInfoexe)
            exe.setSysProject(spexe)
            exe.setEvent("function")
            exe.setTime(int(time.time() * 1000))

            param = index_value
            exe.setParam(str(param))

            exe.setFunction_id(function_id)
            exe.setFunction_title(function_title)  # 一般此处用来装饰触发事件函数
            self.sa.addEvents(exe)
        except:
            pass
