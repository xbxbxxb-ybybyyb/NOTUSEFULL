import os
from setuptools import setup, find_packages

packages = ['xquant', 'test-xquant',
            'xquant.conf',
            'xquant.compute', 'xquant.compute.aimr', 'xquant.compute.sparkmr',
            'xquant.factordata',
            'xquant.futuredata',
            'xquant.futuredata.conf',
            'xquant.marketdata',
            'xquant.pydraw',
            'xquant.quant',
            'xquant.sandbox',
            'xquant.strategy', 'xquant.strategy.backtest', 'xquant.strategy.trademocker',
            'xquant.textdata',
            'xquant.thirdpartydata', 'xquant.thirdpartydata.factor', 'xquant.thirdpartydata.factor.proto',
            'xquant.thirdpartydata.marketdata', 'xquant.thirdpartydata.marketdata.proto',
            'xquant.thirdpartydata.marketdata.proto.config',
            'xquant.thirdpartydata.multifactor', 'xquant.thirdpartydata.multifactor.IO', 'xquant.thirdpartydata.quant',
            'xquant.xqutils', 'xquant.xqutils.pyfilelib', 'xquant.xqutils.xqdraw', 'xquant.xqutils.xqfile',
            'xquant.xqutils.xqlog','xquant.xqutils.helper',
            'test-xquant.test_case',
            'tools.profiler',
            ]

setup(
    name="xquant",
    version="2.10.0",
    description="xquant's module",
    author="hy",
    # packages=find_packages(include=['test', 'test.test_case', 'test.test_perf']),
    packages=packages,
    py_modules=[],
    package_data={
        '': ['*.properties', '*.proto', '*.ini'],
        'test-xquant.test_case': ['*.pkl'],
    },
    install_requires=[  # 依赖的包
        'pyarrow',
        'pandas',
        'grpcio'
    ]
)
