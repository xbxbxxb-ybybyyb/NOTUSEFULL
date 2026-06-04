from xquant.setXquantEnv import xquantEnv,testEnv

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


