# _*_ coding:utf-8 _*_
from xquant.setXquantEnv import xquantEnv,testEnv
test_port = 3307
# test_port = 3309

def get_sql_config(user):
    if xquantEnv == 0:
        sql_config = {  'xquant':{
                                'host': '168.63.1.130',
                                'user': 'xquant',
                                'passwd': 'QQ_jfdf_2289',
                                'db': 'xquant',
                                'port': 3309,
                                'charset': 'utf8'
                                },
                        'xquant_data': {
                            'host': '168.63.1.131',
                            'user': 'xquant_data',
                            'passwd': 'XU_viah_8826',
                            'db': 'xquant_data',
                            'port': test_port,
                            'charset': 'utf8'
                        },
                        'xquant_cusdata': {
                            'host': '168.63.1.131',
                            'user': 'xquant_cusdata',
                            'passwd': 'XU_viah_8826',
                            'db': 'xquant_cusdata',
                            'port': test_port,
                            'charset': 'utf8'
                        },
                        'xquant_wind': {
                            'host': '168.63.1.131',
                            'user': 'xquant_wind',
                            'passwd': 'XU_viah_8826',
                            'db': 'xquant_wind',
                            'port': test_port,
                            'charset': 'utf8'
                        },
                        'xquant_gogoal': {
                            'host': '168.63.1.131',
                            'user': 'xquant_gogoal',
                            'passwd': 'XU_viah_8826',
                            'db': 'xquant_gogoal',
                            'port': test_port,
                            'charset': 'utf8'
                        },
                        'user2':{
                                'host': '168.61.2.14',
                                'user': 'xquant_uct',
                                'passwd': 'xquant',
                                'db': 'xquant_uct',
                                'port': 3312,
                                'charset': 'utf8'
                                }}
    else:
        sql_config = {'xquant': {
            'host': '168.9.65.8',
            'user': 'xquant',
            'passwd': 'X7_mJw12m8UW',
            'db': 'xquant',
            'port': 3326,
            'charset': 'utf8'
        },
            'xquant_data': {
                'host': '168.9.65.8',
                'user': 'xquant_data',
                'passwd': 'X7_mJw12m8UW',
                'db': 'xquant_data',
                'port': 3326,
                'charset': 'utf8'
            },
            'xquant_cusdata': {
                'host': '168.9.65.8',
                'user': 'xquant_cusdata',
                'passwd': 'X7_mJw12m8UW',
                'db': 'xquant_cusdata',
                'port': 3326,
                'charset': 'utf8'
            },
            'xquant_wind': {
                'host': '168.9.65.8',
                'user': 'xquant_wind',
                'passwd': 'X7_mJw12m8UW',
                'db': 'xquant_wind',
                'port': 3326,
                'charset': 'utf8'
            },
            'xquant_gogoal': {
                'host': '168.9.65.8',
                'user': 'xquant_gogoal',
                'passwd': 'X7_mJw12m8UW',
                'db': 'xquant_gogoal',
                'port': 3326,
                'charset': 'utf8'
            }

        }
    return sql_config[user]

pool_config = {'mincached':0,
               'maxcached':1,
               'maxconnections':2,
               'maxshared':1}

StorageConfig = {
    "T+0":{"catalog_type":2,"remark":"T+0高频因子","parent_id":0,"status":1},
    "Alpha":{"catalog_type":1,"remark":"Alpha非高频因子","parent_id":0,"status":1}
}





