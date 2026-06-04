from FactorProvider.setEnv import xquantEnv, testEnv
import os
import json
import traceback

try:
    from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig
except:
    pass

sysFlag = 'tquant'

if xquantEnv == 0:
    DUBBO_CONFIG = {
        "DUBBO_CONFIG_UTILS": 'xquant-sdgp-openapi-test',
        "DUBBO_CONFIG": "xquant-sdgp-openapi-test2",
        "DUBBO_CONFIG_NEWSDATA_GETNEWSBODY": "xquant-newsdata-getnewsbody-test"}

    if testEnv == 40:
        # DUBBO_CONFIG = '168.61.11.118:2181'
        DUBBO_CONFIG["DUBBO_CONFIG_IP"] = '168.61.2.23:2181,168.61.2.24:2181,168.61.2.25:2181'
    elif testEnv == 63:
        DUBBO_CONFIG["DUBBO_CONFIG_IP"] = '168.63.65.196:2182,168.63.65.197:2182,168.63.65.198:2182'

elif xquantEnv == 1:
    DUBBO_CONFIG = {
        "DUBBO_CONFIG_IP": '168.6.5.22:2181,168.8.189.50:2181,168.8.189.51:2181',
        "DUBBO_CONFIG": 'xquant-jurisdictionData',
        "DUBBO_CONFIG_UTILS": "xquant-jurisdictionData",
        "DUBBO_CONFIG_NEWSDATA_GETNEWSBODY": "xquant-newsdata-getnewsbody"}

DUBBO_APPLICATIONCONFIG_UTILS = DUBBO_CONFIG["DUBBO_CONFIG_UTILS"]
DUBBO_APPLICATIONCONFIG = DUBBO_CONFIG["DUBBO_CONFIG"]
DUBBO_CONFIG_IP = DUBBO_CONFIG["DUBBO_CONFIG_IP"]

# jurisdictionData dubbo配置
jurisdictionData_user_provider_dict = {}

factordata_registry_dict = {}
user_provider_create_library_dict = {}
user_provider_add_factor_dict = {}
user_provider_remove_factor_dict = {}


def get_userAccount():
    userAccount = os.environ.get("DSWMAP_username")
    return userAccount


def get_jurisdictionData():
    c_name = "jurisdictionData"
    global jurisdictionData_user_provider_dict

    userAccount = get_userAccount()
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


def __set_factordata_registry():
    global factordata_registry_dict
    c_name = "factordata_registry"
    if not factordata_registry_dict:
        if sysFlag == "tquant":
            factordata_ApplicationConfig = ApplicationConfig(DUBBO_APPLICATIONCONFIG)
            factordata_registry_dict[c_name] = ZookeeperRegistry(DUBBO_CONFIG_IP, factordata_ApplicationConfig)
        else:
            factordata_registry_dict[c_name] = None
    return factordata_registry_dict.get(c_name)


def set_user_provider_create_library():
    global user_provider_create_library_dict
    c_name = "service_interface_create_library"
    if not user_provider_create_library_dict:
        if sysFlag == "tquant":
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_create_library = 'com.htsc.quant.factor.manager.dubbo.python.FactorMetaResourcesStoredService'
                user_provider_create_library_dict[c_name] = DubboClient(service_interface_create_library,
                                                                        factordata_registry, version="2.0.0")
            except:
                raise Exception("user_provider_create_library Dubbo接口调用失败！")
    return user_provider_create_library_dict.get(c_name)


def set_user_provider_add_factor():
    global user_provider_add_factor_dict
    c_name = "user_provider_add_factor"
    if not user_provider_add_factor_dict:
        if sysFlag == "tquant":
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_add_factor = 'com.htsc.quant.factor.manager.dubbo.python.FactorMetaResourcesStoredService'
                user_provider_add_factor_dict[c_name] = DubboClient(service_interface_add_factor, factordata_registry,
                                                                    version="2.0.0")
            except:
                raise Exception("user_provider_add_factor Dubbo接口调用失败！")
    return user_provider_add_factor_dict.get(c_name)


def set_user_provider_remove_factor():
    global user_provider_remove_factor_dict
    c_name = "user_provider_remove_factor"
    if not user_provider_remove_factor_dict:
        if sysFlag == "tquant":
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_remove_factor = 'com.htsc.quant.factor.manager.dubbo.python.FactorMetaResourcesStoredService'
                user_provider_remove_factor_dict[c_name] = DubboClient(service_interface_remove_factor,
                                                                       factordata_registry, version="2.0.0")
            except:
                raise Exception("user_provider_remove_factor Dubbo接口调用失败！")
    return user_provider_remove_factor_dict.get(c_name)
