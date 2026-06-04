'''
设置xquant运行环境
0代表测试环境
1代表生产环境
'''
import os
import socket

if os.environ.get('BIG_DATA_PREPATH', False):
    # xquantEnv = 0
    xquantEnv = 1
    # testEnv = 40
    testEnv = 63
    if socket.gethostname().startswith('ip-168-61'):
        xquantEnv = 0
else:
    if os.environ.get("ENV_VERSION"):
        xquantEnvFlag = os.environ.get("ENV_VERSION")
    if os.environ.get("DSWMAP_envTag"):
        xquantEnvFlag = os.environ.get("DSWMAP_envTag")
    if xquantEnvFlag == "prd":
        xquantEnv = 1
        testEnv = 63
    elif xquantEnvFlag == "uat":
        xquantEnv = 0
        testEnv = 63
    elif xquantEnvFlag == "sit":
        xquantEnv = 0
        testEnv = 40
    else:
        raise Exception("no XQUANT_ENV!")




# # 测试环境分两个，testEnv=40时对应168.61.13.40，testEnv = 63时对应168.63.129.80
# # if xquantEnv == 0:
# # testEnv = 40
# testEnv = 63