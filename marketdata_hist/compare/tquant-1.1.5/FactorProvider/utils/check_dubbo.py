# _*_ coding:utf-8 _*_
import threading
import time
from FactorProvider.conf.DubboConf import get_userid
from FactorProvider.storage.db import DML_mysql
from FactorProvider.setEnv import xquantEnv


XTRADER_DICT = {}


def check_xtrader():
    # 测试环境不验证
    if xquantEnv == 0:
        return True

    global XTRADER_DICT
    if not XTRADER_DICT:
        dml_xquant = DML_mysql('xquant_data')
        conn_name = str(int(round(time.time() * 1000))) + str(threading.get_ident())
        sql = "select user_id from xtrader_whitelist"
        user_data = dml_xquant.getAll(conn_name, sql)[1:]
        white_list = [x[0] for x in user_data]
        user_id = get_userid()
        if user_id in white_list:
            XTRADER_DICT['in_white_list'] = True
        else:
            XTRADER_DICT['in_white_list'] = False
        dml_xquant.close(conn_name)

    return XTRADER_DICT['in_white_list']

