# -*- coding: UTF-8 -*-

import os
from setuptools import setup, find_packages


setup(
    name="automining",
    version="1.7.4",
    description="high freq factor auto mining",
    author="ABC",
    #packages=packages,
    # data_files=[('/opt/anaconda3/lib/python3.6/site-packages/AutoMiningFrame/DataCaculation/factors', ['DataCaculation/factors/*'])],
    packages=find_packages(where='.', exclude=['server_config', 'data-check', 'data-automining'], include=('*')),
    py_modules=[],
    package_data={
        '': ['*.ini', '*.py', '*.dos','*.json'],
        'FactorBacktest': ['*.json', '*.py', '*.dos'],
        'DataCaculation': ['*.json', '*.py', '*.dos', "factors/*",'nonefactors/*'],
        'FactorAutoMining': ['*.json', '*.py', '*.dos'],
    },
    install_requires=[  # 依赖的包
        'dolphindb',
        'xquant'
    ]
)
