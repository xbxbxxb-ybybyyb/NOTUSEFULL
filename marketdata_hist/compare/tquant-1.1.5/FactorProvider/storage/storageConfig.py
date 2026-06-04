# _*_ coding:utf-8 _*_
import base64
import json
from os import path
from FactorProvider.setEnv import xquantEnv,sysFlag


def  get_sql_config(user):
    #未来如果有tquant和xquant中共用的数据，则为两个都新增一个sql_config的key项，来共用
    try:
        file_path = path.join(path.dirname(__file__),
                              "encrypted_database.json")
        with open(file_path, 'rb') as f:
            ENCRYPTED_HOSTS = json.load(f)
    except Exception as e:
        raise Exception("无法读取加密文件")

    if sysFlag == "xquant" or sysFlag == "big_data":
        if xquantEnv == 0:
            sql_config = {  'xquant':{
                                    'host': '168.63.1.130',
                                    'user': 'xquant',
                                    'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant']['ciphertext'],
                                    'db': 'xquant',
                                    'port': 3309,
                                    'charset': 'utf8'
                                    },
                            'xquant_data': {
                                'host': '168.63.1.130',
                                'user': 'xquant_data',
                                'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant_data']['ciphertext'],
                                'db': 'xquant_data',
                                'port': 3309,
                                'charset': 'utf8'
                            },
                            'xquant_cusdata': {
                                'host': '168.63.1.130',
                                'user': 'xquant_cusdata',
                                'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant_cusdata']['ciphertext'],
                                'db': 'xquant_cusdata',
                                'port': 3309,
                                'charset': 'utf8'
                            },
                            'xquant_wind': {
                                'host': '168.63.1.130',
                                'user': 'xquant_wind',
                                'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant_wind']['ciphertext'],
                                'db': 'xquant_wind',
                                'port': 3309,
                                'charset': 'utf8'
                            },
                            'xquant_gogoal': {
                                'host': '168.63.1.130',
                                'user': 'xquant_gogoal',
                                'passwd': ENCRYPTED_HOSTS['xquant']['test']['xquant_gogoal']['ciphertext'],
                                'db': 'xquant_gogoal',
                                'port': 3309,
                                'charset': 'utf8'
                            },
                            'user2':{
                                    'host': '168.61.2.14',
                                    'user': 'xquant_uct',
                                    'passwd': ENCRYPTED_HOSTS['xquant']['test']['user2']['ciphertext'],
                                    'db': 'xquant_uct',
                                    'port': 3312,
                                    'charset': 'utf8'
                                    }
            }
        else:
            sql_config = {'xquant': {
                'host': '168.6.68.72',
                'user': 'xquant',
                'passwd':ENCRYPTED_HOSTS['xquant']['prd']['xquant']['ciphertext'],
                'db': 'xquant',
                'port': 3306,
                'charset': 'utf8'
            },
                'xquant_data': {
                    'host': '168.6.68.72',
                    'user': 'xquant_client',
                    'passwd': ENCRYPTED_HOSTS['xquant']['prd']['xquant_client']['ciphertext'],
                    'db': 'xquant_data',
                    'port': 3306,
                    'charset': 'utf8'
                },
                'xquant_cusdata': {
                    'host': '168.11.241.65',
                    'user': 'xquant_cusdata',
                    'passwd': ENCRYPTED_HOSTS['xquant']['prd']['xquant_cusdata']['ciphertext'],
                    'db': 'xquant_cusdata',
                    'port': 3306,
                    'charset': 'utf8'
                },
                'xquant_wind': {
                    'host': '168.6.68.72',
                    'user': 'xquant_client',
                    'passwd': ENCRYPTED_HOSTS['xquant']['prd']['xquant_client']['ciphertext'],
                    'db': 'xquant_wind',
                    'port': 3306,
                    'charset': 'utf8'
                },
                'xquant_gogoal': {
                    'host': '168.6.68.72',
                    'user': 'xquant_client',
                    'passwd': ENCRYPTED_HOSTS['xquant']['prd']['xquant_client']['ciphertext'],
                    'db': 'xquant_gogoal',
                    'port': 3306,
                    'charset': 'utf8'
                }
            }
    elif sysFlag=="tquant" or sysFlag == 'outside':
        if xquantEnv == 0:
            sql_config = {'xquant': {
                'host': '168.63.1.131',
                'user': 'xquant',
                'passwd': ENCRYPTED_HOSTS['tquant']['test']['xquant']['ciphertext'],
                'db': 'xquant',
                'port': 3307,
                'charset': 'utf8'
                },
                'xquant_cusdata': {
                    'host': '168.63.1.131',
                    'user': 'xquant_cusdata',
                    'passwd': ENCRYPTED_HOSTS['tquant']['test']['xquant_cusdata']['ciphertext'],
                    'db': 'xquant_cusdata',
                    'port': 3307,
                    'charset': 'utf8'
                },
                'user2': {
                    'host': '168.61.2.14',
                    'user': 'xquant_uct',
                    'passwd': ENCRYPTED_HOSTS['tquant']['test']['user2']['ciphertext'],
                    'db': 'xquant_uct',
                    'port': 3312,
                    'charset': 'utf8'
                },
                'xquant_data': {
                                'host': '168.63.1.130',
                                'user': 'xquant_data',
                                'passwd': ENCRYPTED_HOSTS['tquant']['test']['xquant_data']['ciphertext'],
                                'db': 'xquant_data',
                                'port': 3309,
                                'charset': 'utf8'
                },
            }
        else:
            sql_config = {'xquant': {
                'host': '168.11.241.39',
                'user': 'htsc_dwa_quant',
                'passwd': ENCRYPTED_HOSTS['tquant']['prd']['xquant']['ciphertext'],
                'db': 'htsc_dwa_quant_mgr',
                'port': 3306,
                'charset': 'utf8'
                },
                'htsc_dwa_quant': {
                'host': '168.11.241.39',
                'user': 'htsc_dwa_quant',
                'passwd': ENCRYPTED_HOSTS['tquant']['prd']['htsc_dwa_quant']['ciphertext'],
                'db': 'htsc_dwa_quant',
                'port': 3306,
                'charset': 'utf8'
                },
                'xquant_data': {
                    'host': '168.6.68.72',
                    'user': 'xquant_data',
                    'passwd': ENCRYPTED_HOSTS['tquant']['prd']['xquant_data']['ciphertext'],
                    'db': 'xquant_data',
                    'port': 3306,
                    'charset': 'utf8'
                },
            }
    else:
        raise Exception("invalid sysFlag!")
    return sql_config[user]

pool_config = {'mincached':0,
               'maxcached':1,
               'maxconnections':2,
               'maxshared':1}







