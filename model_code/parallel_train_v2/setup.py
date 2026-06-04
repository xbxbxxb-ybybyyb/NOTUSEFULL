# -* -coding: UTF-8 -* -
import setuptools

packages = ['parallel_train',
            'parallel_train.train',
            'parallel_train.train.callbacks', 'parallel_train.train.depends',
            'parallel_train.train.callbacks.results_preprocessors', 'parallel_train.train.depends.ml_utils',
            ]

setuptools.setup(
    name="parallel_train",
    version="2.0.0",
    description="parallel_train is a lightweight library for distributed deep learning,"
                " allowing you to scale up and speed up training for your deep learning models.",
    author="HTSCQuantGroup",
    author_email='XquantIDE@htsc.com',
    url='http://168.63.118.52:8080/HTAI/v2/help/doc/quant/platform/',
    packages=packages,  # 项目根目录下需要打包的目录
    py_modules=[],
    package_data={
        '': ['*.py', '*.so'],
    },
    install_requires=[  # 依赖的包
        'ray==1.5.2',
        'aiohttp==3.7.4',
        'redis<=4.1.4'
    ]
)


