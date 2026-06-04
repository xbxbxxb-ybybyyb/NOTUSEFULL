# -*- coding: UTF-8 -*-
import os
from setuptools import setup, find_packages

packages = find_packages(exclude=(['tests']))

setup(
    name="artifacts",
    version="1.0.0",
    description="Model parameter files, signal parameter files, evaluation data storage.",
    author="HTSCQuantGroup",
    author_email='XquantIDE@htsc.com',
    url='http://168.00.00.000:8080/sdk-help/',
    # packages=find_packages(include=['test', 'test.test_case', 'test.test_perf']),
    packages=packages,
    py_modules=[],
    package_data={
        '': ['*.properties', '*.proto', '*.ini', '*.json', '*.pkl', ],
    },
    install_requires=[  # 依赖的包
        'pyarrow',
    ]
)
