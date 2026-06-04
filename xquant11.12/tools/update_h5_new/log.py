import time
import logging 
import logging.handlers
import os.path
import time
import datetime as dt

rq = (dt.datetime.now()).strftime('%Y%m%d')
setting = {
           'logpath':'/app/tools/update_h5_new/log/',
           # 'logpath':'/log',
           'filename': rq
           }
           
if not os.path.exists("log"):
    os.mkdir("log")

class Log(object):
    ''' '''
    def __init__(self, name,toConsole=True):
        self.path = setting['logpath']
        self.filename = setting['filename']
        self.name = name
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
       # set file handler
        self.fh_info = logging.handlers.TimedRotatingFileHandler(filename=self.path + self.filename + '_' + self.name + '_info.log', when="D", interval=7, backupCount=7)
        self.fh_error = logging.FileHandler(self.path + self.filename  + '_' + self.name + '_error.log')
        self.fh_warning = logging.FileHandler(self.path + self.filename  + '_' + self.name + '_warning.log')
       #set logging Level
        self.fh_info.setLevel(logging.INFO)
        self.fh_error.setLevel(logging.ERROR)
        self.fh_warning.setLevel(logging.WARNING)
        #set data format
        self.formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s\r\n')
        self.fh_info.setFormatter(self.formatter)
        self.fh_error.setFormatter(self.formatter)
        self.fh_warning.setFormatter(self.formatter)
        self.logger.addHandler(self.fh_info)         
        self.logger.addHandler(self.fh_error)         
        self.logger.addHandler(self.fh_warning)

        if toConsole:  
            ch = logging.StreamHandler()  
            ch.setLevel(logging.DEBUG)  
            ch.setFormatter(self.formatter)  
            self.logger.addHandler(ch)  

    def info(self, msg):
        self.logger.info(msg)

    def warning(self, msg):
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.error(msg)

    def debug(self, msg):
        self.logger.debug(msg)

    def close(self):
        self.logger.removeHandler(self.fh)
