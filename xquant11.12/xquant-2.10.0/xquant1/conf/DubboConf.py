from xquant1.setXquantEnv import xquantEnv,testEnv
import os
import sys
import json
try:
    from ht_dubbo_client import ZookeeperRegistry, DubboClient, DubboClientError, ApplicationConfig
except:
    pass


if xquantEnv == 0:
    DUBBO_CONFIG = {
    "DUBBO_CONFIG_UTILS":'xquant-sdgp-openapi-test',
    "DUBBO_CONFIG":"xquant-sdgp-openapi-test2",
    "DUBBO_CONFIG_NEWSDATA_GETNEWSBODY":"xquant-newsdata-getnewsbody-test"}
    if testEnv == 40:
        # DUBBO_CONFIG = '168.61.11.118:2181'
        DUBBO_CONFIG["DUBBO_CONFIG_IP"] = '168.61.2.23:2181,168.61.2.24:2181,168.61.2.25:2181'
    elif testEnv == 63:
        DUBBO_CONFIG["DUBBO_CONFIG_IP"] = '168.63.65.196:2182,168.63.65.197:2182,168.63.65.198:2182'
elif xquantEnv == 1:
    DUBBO_CONFIG = {
    "DUBBO_CONFIG_IP" :'168.6.5.22:2181,168.8.189.50:2181,168.8.189.51:2181,168.160.36.11:2181',
    "DUBBO_CONFIG":'xquant-jurisdictionData',
    "DUBBO_CONFIG_UTILS" : "xquant-jurisdictionData",
    "DUBBO_CONFIG_NEWSDATA_GETNEWSBODY" : "xquant-newsdata-getnewsbody"}

DUBBO_APPLICATIONCONFIG_UTILS = DUBBO_CONFIG["DUBBO_CONFIG_UTILS"]
DUBBO_APPLICATIONCONFIG = DUBBO_CONFIG["DUBBO_CONFIG"]
DUBBO_CONFIG_IP = DUBBO_CONFIG["DUBBO_CONFIG_IP"]


#jurisdictionData dubbo配置
jurisdictionData_user_provider_dict = {}
#
# # xquantConfig dubbo配置
xquantConfig_user_provider_dict = {}

factordata_registry_dict = {}
user_provider_create_library_dict = {}
user_provider_add_factor_dict = {}
user_provider_remove_factor_dict = {}
query_wind_from_oracle_dict = {}
query_gogoal_from_oracle_dict = {}
ZlGoalDailyTargetDubboService_dict = {}
user_provider_db_pool_dict = {}


def __find_config(path):
    while True:
        path = os.path.split(path)[0]
        dir_list = os.listdir(path)
        for dir in dir_list:
            if dir == "__xquant_config.py":
                return path
        if path == os.path.split(path)[0]:
            break
    raise Exception("未找到__xquant_config文件！")


def get_jurisdictionData():
    c_name = "jurisdictionData"
    global jurisdictionData_user_provider_dict
    if not jurisdictionData_user_provider_dict.get(c_name):
        # jurisdictionData dubbo配置
        jurisdictionData_service_interface = 'com.htsc.xquant.factor.manager.server.python.GenerateJurisdictionFileService'
        jurisdictionData_config = ApplicationConfig(DUBBO_APPLICATIONCONFIG_UTILS)
        jurisdictionData_registry = ZookeeperRegistry(DUBBO_CONFIG_IP, jurisdictionData_config)
        jurisdictionData_user_provider_dict[c_name] = DubboClient(jurisdictionData_service_interface, jurisdictionData_registry,
                                                     version="1.0.0")

    if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION',False):
        abs_path = os.environ['BIG_DATA_PREPATH']
        sys_path = __find_config(abs_path)
        sys.path.append(sys_path)
        import __jurisdictionData_config
        jurisdictionData_dict = __jurisdictionData_config.jurisdictionData_dict
        return jurisdictionData_dict
    else:
        userAccount = get_userid()
        if not userAccount:
            raise Exception("未获取到userId!")
        try:
            # 调用dubbo接口
            json_dict = {"request": {"userAccount": str(userAccount)}}
            json_str = json.dumps(json_dict)
            get_result = jurisdictionData_user_provider_dict[c_name].GenerateJurisdictionFile(json_str)
            return json.loads(get_result.split("=")[1].strip())
        except DubboClientError as e:
            raise "Exception " + str(e)

def get_userid():
    XQUANT_CONF_FILE = os.environ['XQUANT_CONF_FILE']
    # XQUANT_CONF_FILE = "/tmp/python/xquant_conf"
    with open(XQUANT_CONF_FILE, 'r') as f:
        r = f.readlines()
        for line in r:
            if line.startswith("userId"):
                return line.strip().split("=")[-1].strip()

def get_xquantConfig():
    c_name = "xquantConfig"
    global xquantConfig_user_provider_dict
    if not xquantConfig_user_provider_dict.get(c_name):
        # xquantConfig dubbo配置
        xquantConfig_service_interface = 'com.htsc.xquant.factor.manager.server.python.CreateXquantConfigService'
        xquantConfig_config = ApplicationConfig(DUBBO_APPLICATIONCONFIG_UTILS)
        xquantConfig_registry = ZookeeperRegistry(DUBBO_CONFIG_IP, xquantConfig_config)
        xquantConfig_user_provider_dict[c_name] = DubboClient(xquantConfig_service_interface, xquantConfig_registry, version="1.0.0")

    if os.environ.get('BIG_DATA_PREPATH', False) or not os.environ.get('ENV_VERSION',False):
        abs_path = os.environ['BIG_DATA_PREPATH']
        sys_path = __find_config(abs_path)
        sys.path.append(sys_path)
        import __xquant_config
        __xquant_config_dict = __xquant_config.__xquant_config_json
        return __xquant_config_dict
    elif os.environ.get('IS_JUPYTER', False):
        abs_path = "/app/anaconda/lib/python3.6/site-packages/xquant/"
        sys_path = __find_config(abs_path)
        sys.path.append(sys_path)
        import __xquant_config
        __xquant_config_dict = __xquant_config.__xquant_config_json
        return __xquant_config_dict
    else:
        userAccount = get_userid()
        if not userAccount:
            raise Exception("未获取到userId!")
        try:
            # 调用dubbo接口
            json_dict = {"request": {"userAccount": str(userAccount)}}
            json_str = json.dumps(json_dict)
            get_result = xquantConfig_user_provider_dict[c_name].CreateXquantConfig(json_str)
            return json.loads(get_result.split("=")[1])
        except:
            raise Exception("用户配置文件生成失败！")







def __set_factordata_registry():
    global factordata_registry_dict
    c_name = "factordata_registry"
    if not factordata_registry_dict:
        if os.environ.get('ENV_VERSION', False):
            factordata_ApplicationConfig = ApplicationConfig(DUBBO_APPLICATIONCONFIG)
            factordata_registry_dict[c_name] = ZookeeperRegistry(DUBBO_CONFIG_IP, factordata_ApplicationConfig)
        else:
            factordata_registry_dict[c_name] = None
    return factordata_registry_dict[c_name]


def set_user_provider_create_library():
    global user_provider_create_library_dict
    c_name = "service_interface_create_library"
    if not user_provider_create_library_dict:
        if os.environ.get('ENV_VERSION', False):
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_create_library = 'com.htsc.xquant.factor.manager.server.python.FactorMetaResourcesStoredService'
                user_provider_create_library_dict[c_name] = DubboClient(service_interface_create_library, factordata_registry, version="1.0.0")
            except:
                raise Exception("user_provider_create_library Dubbo接口调用失败！")
    return user_provider_create_library_dict.get(c_name)



def set_user_provider_add_factor():
    global user_provider_add_factor_dict
    c_name = "user_provider_add_factor"
    if not user_provider_add_factor_dict:
        if os.environ.get('ENV_VERSION', False):
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_add_factor = 'com.htsc.xquant.factor.manager.server.python.FactorMetaResourcesStoredService'
                user_provider_add_factor_dict[c_name] = DubboClient(service_interface_add_factor, factordata_registry, version="1.0.0")
            except:
                raise Exception("user_provider_add_factor Dubbo接口调用失败！")
    return user_provider_add_factor_dict.get(c_name)


def set_user_provider_remove_factor():
    global user_provider_remove_factor_dict
    c_name = "user_provider_remove_factor"
    if not user_provider_remove_factor_dict:
        if os.environ.get('ENV_VERSION', False):
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_remove_factor = 'com.htsc.xquant.factor.manager.server.python.FactorMetaResourcesStoredService'
                user_provider_remove_factor_dict[c_name] = DubboClient(service_interface_remove_factor, factordata_registry,version="1.0.0")
            except:
                raise Exception("user_provider_remove_factor Dubbo接口调用失败！")
    return user_provider_remove_factor_dict.get(c_name)


def set_query_wind_from_oracle():
    global query_wind_from_oracle_dict
    c_name = "query_wind_from_oracle"
    if not query_wind_from_oracle_dict:
        if os.environ.get('ENV_VERSION', False):
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_query_wind = 'com.htsc.xquant.dataagent.service.dubbo.WindInfoService'
                query_wind_from_oracle_dict[c_name] = DubboClient(service_interface_query_wind, factordata_registry, version="1.0.0")
            except:
                raise Exception("query_wind_from_oracle Dubbo接口调用失败！")
    return query_wind_from_oracle_dict.get(c_name)

def set_query_gogoal_from_oracle():
    global query_gogoal_from_oracle_dict
    c_name = "query_gogoal_from_oracle"
    if not query_gogoal_from_oracle_dict:
        if os.environ.get('ENV_VERSION', False):
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_query_gogoal = 'com.htsc.xquant.dataagent.service.dubbo.GogoalOrGogoalNewInfoService'
                query_gogoal_from_oracle_dict[c_name] = DubboClient(service_interface_query_gogoal, factordata_registry, version="1.0.0")
            except:
                raise Exception("query_gogoal_from_oracle Dubbo接口调用失败！")
    return query_gogoal_from_oracle_dict.get(c_name)



def set_ZlGoalDailyTargetDubboService():
    global ZlGoalDailyTargetDubboService_dict
    c_name = "ZlGoalDailyTargetDubboService"
    if not ZlGoalDailyTargetDubboService_dict:
        if os.environ.get('ENV_VERSION', False):
            try:
                operation_config = ApplicationConfig("ZlGoalDailyTargetDubboService")
                operation_service_interface = "com_htsc_zlcft_api.ZlGoalDailyTargetDubboService"
                operation_registry = ZookeeperRegistry(
                    "168.6.5.21:2181,168.6.5.22:2181,168.8.189.51:2181,168.8.189.50:2181,168.160.36.11:2181",
                    operation_config)
                ZlGoalDailyTargetDubboService_dict[c_name] = DubboClient(operation_service_interface, operation_registry,version="1.0.0")
            except:
                raise Exception("ZlGoalDailyTargetDubboService Dubbo接口调用失败！")
    return ZlGoalDailyTargetDubboService_dict.get(c_name)


def set_user_provider_db_pool():
    global user_provider_db_pool_dict
    c_name = "user_provider_db_pool"
    if not user_provider_db_pool_dict:
        if os.environ.get('ENV_VERSION', False) or os.environ.get('tmp_tmp', False):
            factordata_registry = __set_factordata_registry()
            try:
                service_interface_db_pool = 'com.htsc.xquant.factor.manager.server.python.MySqlProcessConfigService'
                user_provider_db_pool_dict[c_name] = DubboClient(service_interface_db_pool, factordata_registry, version="1.0.0")
            except:
                raise Exception("set_user_provider_db_pool Dubbo接口调用失败！")

    return user_provider_db_pool_dict.get(c_name)


