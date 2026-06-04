# -*- coding: UTF-8 -*-

import os
from setuptools import setup, find_packages

#packages = ['FactorProvider', 'FactorProvider.factordata', 'FactorProvider.futuredata',
#            'FactorProvider.conf', 'FactorProvider.storage', 
#            'FactorProvider.utils',
#            'tquant']

setup(
    name="tquant",
    version="3.2.0",
    description="Characterized by massive financial data, factor research framework, distributed computing framework, model development framework and startegy backtesting framework, TQuant is committed to building a brilliant big data quantitative research tool chain, to support research works of the company.",
    author="HTSCQuantGroup",
    author_email='XquantIDE@htsc.com',
    url='http://168.63.118.52:8080/HTAI/v2/help/doc/quant/platform/',
    #packages=packages,
    packages=find_packages(exclude=['tests', 'data-tquant', 'data-tquant*', 'test_tquant*', 'tools*']),  # 项目根目录下需要打包的目录
    py_modules=[],
    package_data={
        '': ['*.properties', '*.proto', '*.ini', '*.so', '*.sh', '*.json'],
        'pytest_tquant': ['*.pkl', '*.coveragerc', '*.ini','*.py','*.txt'],
        'web_entry':['*']
    },
    install_requires=[  # 依赖的包
        'pyarrow',
        'pandas',
        'DBUtils==1.3',
        'pymysql',
        'mysql-connector-python',
        'psutil'
    ]
)
