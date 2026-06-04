# -*- coding: UTF-8 -*-

import os
from setuptools import setup, find_packages

#packages = ['FactorProvider', 'FactorProvider.factordata', 'FactorProvider.futuredata',
#            'FactorProvider.conf', 'FactorProvider.storage', 
#            'FactorProvider.utils',
#            'tquant']

setup(
    name="tquant",
    version="1.1.5",
    description="tquant's module",
    author="tquant",
    #packages=packages,
    packages=find_packages(exclude=['tests']),  # 项目根目录下需要打包的目录
    py_modules=[],
    package_data={
        '': ['*.properties', '*.proto', '*.ini', '*.so', '*.sh', '*.json'],
        'pytest_tquant': ['*.pkl', '*.coveragerc', '*.ini']
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
