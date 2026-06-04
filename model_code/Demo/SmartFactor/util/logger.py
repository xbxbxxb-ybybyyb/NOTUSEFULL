# -*- coding: utf-8 -*-
"""
Created on Wed Jul  1 11:18:47 2020
@author: 013150
"""

import logging.config
import logging
import json
import os
import threading
import datetime

log_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(name)s-%(process)d-%(asctime)s %(filename)s %(funcName)s : %(levelname)s  %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "stream": "ext://sys.stdout"
        },

    },
    "loggers": {
        "quant_info": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False
        },

    },
    # 默认的root logger，不需要修改
    # "root":{
    #    "level":"CRITICAL"
    # }
}


def setup_logging(logger_name='', dirPath="/tmp"):
    """
    dirPath: 生成日志文件的路径
    """
    assert type(logger_name) == str, "logger_name类型为str，请设置为的用户自定义logger名称."
    thread_id = datetime.date.today().strftime("%Y%m%d") + "_" + str(threading.get_ident())[-8:]
    dirPath = os.path.join(dirPath, thread_id)

    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    if dirPath[-1] == "/":
        dirPath = dirPath[:-1]


    return logging.getLogger(logger_name)


if __name__ == "__main__":
    # 仅在需要打印日志时初始化化，若不初始化，添加默认handler，日志级别是WARNING
    setup_logging()

    logger_info = setup_logging("quant_info")

    logger_info.info("start func")
    logger_info.info("exec func")
    logger_info.debug("end func")
