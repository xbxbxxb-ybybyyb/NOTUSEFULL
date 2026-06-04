'''
设置xquant运行环境
0代表测试环境
1代表生产环境
'''
import os
import socket

# 判断运行程序的系统
if os.environ.get("ENV_VERSION"):
    sysFlag = "xquant"
elif os.environ.get("DSWMAP_envTag"):
    sysFlag = "tquant"
elif os.environ.get('BIG_DATA_PREPATH', False):
    sysFlag = "big_data"
else:
    sysFlag = "outside"
    os.environ['outside_env'] = 'prd'

# 判断系统的运行环境是生产还是测试
if sysFlag == "big_data":
    xquantEnv = 1  # 表示生产环境
    testEnv = 63  # which 测试环境
    if socket.gethostname().startswith('ip-168-61'):
        xquantEnv = 0
else:
    if sysFlag == "xquant":
        envFlag = os.environ.get("ENV_VERSION")
    elif sysFlag == "tquant":
        envFlag = os.environ.get("DSWMAP_envTag")
    elif sysFlag == 'outside':
        envFlag = os.environ.get("outside_env")

    if envFlag.lower() == "prd":
        xquantEnv = 1
        testEnv = 63
    elif envFlag.lower() == "uat":
        xquantEnv = 0
        testEnv = 63
    elif envFlag.lower() == "sit":
        xquantEnv = 0
        testEnv = 40
    else:
        raise Exception("no XQUANT_ENV!")

