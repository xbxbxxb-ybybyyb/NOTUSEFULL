import os

def get_env():
    # 判断运行程序的系统
    if os.environ.get("ENV_VERSION"):
        sysFlag = "xquant"
    elif os.environ.get("DSWMAP_envTag"):
        sysFlag = "tquant"
    elif os.environ.get('BIG_DATA_PREPATH', False) and not os.environ.get('ENV_VERSION', False):
        sysFlag = "big_data"
    else:
        sysFlag = "outside"
        os.environ['outside_env'] = 'uat'

    # 判断系统的运行环境是生产还是测试
    if sysFlag == "xquant":
        envFlag = os.environ.get("ENV_VERSION")
    elif sysFlag == "tquant":
        envFlag = os.environ.get("DSWMAP_envTag")
    elif sysFlag == "outside":
        envFlag = os.environ.get("outside_env")

    if envFlag.lower() == "prd":
        env = "prd"
    elif envFlag.lower() == "uat":
        env = "uat"
    else:
        raise Exception('当前只有prd/uat环境有数据')

    return env
