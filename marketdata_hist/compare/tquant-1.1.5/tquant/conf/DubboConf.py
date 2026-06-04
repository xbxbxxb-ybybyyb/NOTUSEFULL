from FactorProvider.setEnv import xquantEnv, testEnv, sysFlag
import os
import sys
import json
import traceback
import psutil
try:
    from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig
except:
    pass

sysFlag = 'tquant'

if xquantEnv == 0:
    DUBBO_CONFIG = {
        "DUBBO_REGISTY_UTILS": 'xquant-sdgp-openapi-test',
        "DUBBO_REGISTY_FACTOR": "xquant-sdgp-openapi-test2"}
    if testEnv == 40:
        # DUBBO_CONFIG = '168.61.11.118:2181'
        DUBBO_CONFIG["DUBBO_CONFIG_IP"] = '168.61.2.23:2181,168.61.2.24:2181,168.61.2.25:2181'
    elif testEnv == 63:
        DUBBO_CONFIG["DUBBO_CONFIG_IP"] = '168.63.65.196:2182,168.63.65.197:2182,168.63.65.198:2182'

elif xquantEnv == 1:
    DUBBO_CONFIG = {
        "DUBBO_CONFIG_IP": '168.6.5.22:2181,168.8.189.50:2181,168.8.189.51:2181',
        "DUBBO_REGISTY_UTILS": 'xquant-jurisdictionData',
        "DUBBO_REGISTY_FACTOR": "xquant-factor"}


DUBBO_APPLICATIONCONFIG_UTILS = DUBBO_CONFIG["DUBBO_REGISTY_UTILS"]
DUBBO_APPLICATIONCONFIG_FACTOR = DUBBO_CONFIG["DUBBO_REGISTY_FACTOR"]
DUBBO_CONFIG_IP = DUBBO_CONFIG["DUBBO_CONFIG_IP"]

# dubbo缓存对象配置
jurisdictionData_user_provider_dict = {}
user_provider_db_pool_dict = {}
factordata_registry_dict = {}

def get_jdd_cache():
    if os.path.exists("/tmp/__jurisdictionData_config.py"):
        try:
            p = psutil.Process()
            if 'raylet' in ",".join(p.cmdline()):
                return json.loads(
                    open("/tmp/__jurisdictionData_config.py").readlines()[0].split("=")[1].strip())
        except:
            print("【Waring】__jurisdictionData_config.py error!")


def get_jurisdictionData():
    c_name = "jurisdictionData"
    global jurisdictionData_user_provider_dict

    if sysFlag == "tquant":
        json_str = get_jdd_cache()
        if json_str:
            return json_str
        userAccount ='73f0ba2a2876492094bbdcb8bfb43ce0'
        if not userAccount:
            raise Exception("未获取到userId!")
        try:
            if not jurisdictionData_user_provider_dict.get(c_name):
                # jurisdictionData dubbo配置
                jurisdictionData_service_interface = 'com.htsc.quant.factor.manager.dubbo.python.GenerateJurisdictionFileService'
                jurisdictionData_config = ApplicationConfig(DUBBO_APPLICATIONCONFIG_UTILS)
                config_registry = ZookeeperRegistry(DUBBO_CONFIG_IP, jurisdictionData_config)
                jurisdictionData_user_provider_dict[c_name] = DubboClient(jurisdictionData_service_interface,
                                                                          config_registry,
                                                                          version="2.0.0")
            json_dict = {"request": {"userAccount": str(userAccount)}}
            json_str = json.dumps(json_dict)
            get_result = jurisdictionData_user_provider_dict[c_name].GenerateJurisdictionFile(json_str)
            return json.loads(get_result.split("=")[1].strip())
        except Exception as e:
            print(traceback.print_exc())
            raise Exception(str(e))
    else:
        print("【warning】当前系统不存在jurisdictionData！")
        return


def __set_factordata_registry():
    global factordata_registry_dict
    c_name = "factordata_registry"
    if not factordata_registry_dict:
        if sysFlag == "tquant":
            factordata_ApplicationConfig = ApplicationConfig(DUBBO_APPLICATIONCONFIG_FACTOR)
            factordata_registry_dict[c_name] = ZookeeperRegistry(DUBBO_CONFIG_IP, factordata_ApplicationConfig)
        else:
            factordata_registry_dict[c_name] = None
    return factordata_registry_dict.get(c_name)


def set_user_provider_db_pool():
    global user_provider_db_pool_dict
    c_name = "user_provider_db_pool"
    if not user_provider_db_pool_dict:
        if sysFlag == "xquant" or os.environ.get('tmp_tmp', False) or sysFlag == "tquant":
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_db_pool = 'com.htsc.quant.factor.manager.dubbo.python.MySqlProcessConfigService'
                user_provider_db_pool_dict[c_name] = DubboClient(service_interface_db_pool, factordata_registry,
                                                                 version="2.0.0")
            except:
                raise Exception("set_user_provider_db_pool Dubbo接口调用失败！")

    return user_provider_db_pool_dict.get(c_name)


if __name__=="__main__":
    ss = get_jurisdictionData()
    print(type(ss))
    print(ss)
