import logging
try:
    from .logger import setup_logging,MyLogger
    alpha_logger = MyLogger()#logger对象无法pickle，换成自定义的logger
except:
    #unkown error fund
    alpha_logger = logging.getLogger('mylogger')
    alpha_logger.setLevel(logging.WARNING)
