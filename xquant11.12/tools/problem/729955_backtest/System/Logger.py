import os
import logging


class Logger:
    def __init__(self, logPath, toScreen=False, level="info"):
        levelDict = {
            "debug": logging.DEBUG,
            "info": logging.INFO,
            "warning": logging.WARNING,
            "error": logging.ERROR,
            "critical": logging.CRITICAL
        }
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

        logDir = logPath[:logPath.rindex("/")]
        if not os.path.exists(logDir):
            os.makedirs(logDir)

        self.__logger = logging.getLogger(logPath)
        self.__logger.setLevel(levelDict[level])
        self.__logger.handlers = []
        self.__logger.propagate = False

        fileHandler = logging.FileHandler(logPath, encoding="utf-8")
        fileHandler.setFormatter(formatter)
        self.__logger.addHandler(fileHandler)

        if toScreen:
            streamHandler = logging.StreamHandler()
            streamHandler.setFormatter(formatter)
            self.__logger.addHandler(streamHandler)

    def log(self, message, level="info"):
        if level == "debug":
            self.__logger.debug(message)
        elif level == "info":
            self.__logger.info(message)
        elif level == "warning":
            self.__logger.warning(message)
        elif level == "error":
            self.__logger.error(message)
        elif level == "critical":
            self.__logger.critical(message)
