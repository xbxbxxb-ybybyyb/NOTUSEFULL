import logging
from logging import handlers
import os
import sys


class Logger(object):
    level_relations = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'crit':logging.CRITICAL
    }

    def __init__(self, root_path, log_file_name, level='info', when='D', backCount=20, fmt='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s'):

        os.makedirs(root_path, exist_ok=True)
        filename = os.path.join(root_path, log_file_name)

        self.logger = logging.getLogger(filename)

        if not self.logger.handlers:

            format_str = logging.Formatter(fmt) # 设置日志格式

            self.logger.setLevel(self.level_relations.get(level)) # 设置日志级别

            sh = logging.StreamHandler(sys.stdout) # 往屏幕上输出

            sh.setFormatter(format_str) # 设置屏幕上显示的格式

            th = handlers.TimedRotatingFileHandler(filename=filename, when=when, backupCount=backCount, encoding='utf-8') # 往文件里写入#指定间隔时间自动生成文件的处理器
            th.setFormatter(format_str) # 设置文件里写入的格式

            # 只有高级别的日志信息才输出到屏幕，否则屏幕信息太多
            if level in ['info', 'warning', 'error', 'crit']:
                self.logger.addHandler(sh) # 把对象加到logger里s

            self.logger.addHandler(th)
        