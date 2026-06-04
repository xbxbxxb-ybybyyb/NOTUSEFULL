import logging
 
def init_logging(filename):
    # 创建logger对象
    logger = logging.getLogger('test_logger')
     
    # 设置日志等级
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
     
        # 追加写入文件a ，设置utf-8编码防止中文写入乱码
        test_log = logging.FileHandler(filename,'a',encoding='utf-8')
         
        # 向文件输出的日志级别
        test_log.setLevel(logging.DEBUG)
         
        # 向文件输出的日志信息格式
        formatter = logging.Formatter('%(levelname)s - %(asctime)s - %(message)s')
         
        test_log.setFormatter(formatter)
         
        # 加载文件到logger对象中
        logger.addHandler(test_log)
        logger.propagate=False

    return logger
 
if __name__ == "__main__":
    logger = init_logging('./log.log')
    logger.debug('----调试信息 [debug]------')
    logger.info('[info]')
    logger.warning('警告信息[warning]')
    logger.error('错误信息[error]')
    logger.critical('严重错误信息[crtical]')
