import logging
try:
    from .logger import setup_logging
    alpha_logger = setup_logging("quant_debug")
except:
    #unkown error fund
    alpha_logger = logging.getLogger('mylogger')
    alpha_logger.setLevel(logging.WARNING)
