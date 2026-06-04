# _*_ coding:utf-8 _*_

import os

test_py_list = ['test_factordata', 'test_factordata_wind_db', 'test_future', 'test_marketdata',
                'test_textdata_newsdata', 'test_strategy', 'test_aimr', 'test_sparkmr',
                'test_xqutils_hdfsfile', 'test_xqutils_ftpfile', 'test_xqutils_xqdraw',
                'test_xqutils_xqlog', 'test_xqutils_pyfilelib', 'test_thirdpartydata_marketdata',
                'test_thirdpartydata_multifactor_io', 'test_thirdpartydata_quantapi',
                'test_thirdpartydata_factor', 'test_thirdpartydata_pyfilelib', 'test_pandas', 'test_keras',
                'test_multiprocess', 'test_statisticlog']

for test_py in test_py_list:
    print("======= {0}开始执行！========".format(test_py))
    command_str = "python3 -m unittest {0}".format(test_py)
    os.system(command_str)
    print("======= {0}执行完毕！========".format(test_py))
