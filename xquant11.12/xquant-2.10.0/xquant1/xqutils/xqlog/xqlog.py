import time
import logging
import logging.handlers
import os
import time
import datetime as dt
import sys
import traceback

from xquant1.pyfile import Pyfile
import threading


rq = (dt.datetime.now()).strftime('%Y%m%d_%H%M%S')
setting = {
    'logpath': 'logs/',
    'filename': rq
}

class XqLog(object):
    def __init__(self, name, toConsole=False):
        '''
        @brief 日志信息以及报错堆栈信息的读写功能

        @param name:模块名，如：'marketdata'
        @arg name: string
        @param toConsole:控制台是否打印日志信息，默认False(不打印)
        @arg toConsole: bool

        @note
        @code
        from xquant.log.log import Log
        logger = Log("ceshi")
        print(logger.path)
        logger.info("error1")
        logger.debug("zxcv")
        logger.error("1234")
        logger.warning("qwer")
        try:
            1/0
        except Exception as e:
            logger.log_except(e)
        @endcode
        '''
        self.pid = str(threading.get_ident())
        self.filename = setting['filename']
        self.name = name
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        if not os.environ.get('IS_JUPYTER',False):
            self.taskid = sys.argv[6]
            # set file handler
            self.py = Pyfile()
            self.py.mkdir(setting['logpath'])
            self.path = setting['logpath'] + self.filename + "_" + self.taskid+"_" + self.pid + ".log"
            self.py.create(self.path)

        # set data format
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s\r\n')

        if toConsole:
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            ch.setFormatter(self.formatter)
            self.logger.addHandler(ch)

    def append(self,message):
        with self.py.open(self.path, 'ab') as f:
            f.write(message)

    def info(self, msg):
        message = self.filename + " - " + self.name + " - INFO - " + msg +"\r\n"
        self.logger.info(msg)
        if not os.environ.get('IS_JUPYTER', False):
            self.append(message)

    def warning(self, msg):
        message = self.filename + " - " + self.name + " - WARNING - " + msg +"\r\n"
        self.logger.warning(msg)
        if not os.environ.get('IS_JUPYTER', False):
            self.append(message)


    def error(self, msg):
        message = self.filename + " - " + self.name + " - ERROR - " + msg + "\r\n"
        self.logger.error(msg)
        if not os.environ.get('IS_JUPYTER', False):
            self.append(message)

    def debug(self, msg):
        message = self.filename + " - " + self.name + " - DEBUG - " + msg + "\r\n"
        self.logger.debug(msg)
        if not os.environ.get('IS_JUPYTER', False):
            self.append(message)

    def log_except(self,msg):
        self.logger.exception(msg)
        self.err = traceback.format_exc()
        if not os.environ.get('IS_JUPYTER', False):
            self.append(self.err)

    def close(self):
        self.logger.removeHandler(self.fh)