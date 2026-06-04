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
    "version":1,
    "disable_existing_loggers":False,
    "formatters":{
        "simple":{
            "format":"%(name)s-%(process)d-%(asctime)s %(filename)s %(funcName)s : %(levelname)s  %(message)s"
        }
    },
    "handlers":{
        "console":{
            "class":"logging.StreamHandler",
            "level":"DEBUG",
            "formatter":"simple",
            "stream":"ext://sys.stdout"
        },
                
        "debug_file_handler":{
            "class":"logging.handlers.RotatingFileHandler",
            "level":"DEBUG",
            "formatter":"simple",
            "filename":"$DIRPATH/debug_$PID.log",
            "maxBytes":104857600,
            "backupCount":20,
            "encoding":"utf8"
        },
                
        "info_file_handler":{
            "class":"logging.handlers.RotatingFileHandler",
            "level":"INFO",
            "formatter":"simple",
            "filename":"$DIRPATH/info_$PID.log",
            "maxBytes":104857600,
            "backupCount":20,
            "encoding":"utf8"
        },
                
        "error_file_handler":{
            "class":"logging.handlers.RotatingFileHandler",
            "level":"ERROR",
            "formatter":"simple",
            "filename":"$DIRPATH/errors_$PID.log",
            "maxBytes":10485760,
            "backupCount":20,
            "encoding":"utf8"
        }
    },
    "loggers":{ 
        "quant_debug":{
            "level":"DEBUG",
            "handlers":[ "console", "debug_file_handler", "error_file_handler"],
            #Note If you attach a handler to a logger and one or more of its ancestors, it may emit the same record multiple times. In general, you should not need to attach a handler to more than one logger -
            "propagate": False
        },
         "quant_info":{
            "level":"INFO",
            "handlers":[ "console", "info_file_handler"],
            "propagate": False
        },
            "quant_handle":{
            "level":"INFO",
            "handlers":["console"],
            "propagate": False
        }
    },
    #默认的root logger，不需要修改
    #"root":{
    #    "level":"CRITICAL"
    #}
}

 
def setup_logging(logger_name = '', dirPath = "/tmp"):
    """
    dirPath: 生成日志文件的路径
    """
    assert type(logger_name) == str, "logger_name类型为str，请设置为的用户自定义logger名称."
    thread_id = datetime.date.today().strftime("%Y%m%d")+"_"+str(threading.get_ident())[-8:]
    dirPath = os.path.join(dirPath, thread_id)

    if not os.path.exists(dirPath):
        os.makedirs(dirPath)
    if dirPath[-1] == "/":
        dirPath = dirPath[:-1]

    if logger_name:
        if logger_name not in ["quant_handle", "quant_info", "quant_debug"]:
            log_config["loggers"][logger_name] = log_config["loggers"]["quant_handle"]
    else:
        logger_name = "quant_info"
    json_str = json.dumps(log_config)
    json_str = json_str.replace('$DIRPATH', dirPath)
    #保证多进程写不同的文件
    json_str = json_str.replace('$PID', str(os.getpid()))
    logging.config.dictConfig(json.loads(json_str))
    return logging.getLogger(logger_name)


 
if __name__ == "__main__":
    
    #仅在需要打印日志时初始化化，若不初始化，添加默认handler，日志级别是WARNING
    setup_logging()
            
    logger_debug = setup_logging("quant_debug")
    
    logger_debug.info("start func")
    logger_debug.info("exec func")
    logger_debug.debug("end func")
    
    logger_info = setup_logging("quant_info")
    
    logger_info.info("start func")
    logger_info.info("exec func")
    logger_info.debug("end func")