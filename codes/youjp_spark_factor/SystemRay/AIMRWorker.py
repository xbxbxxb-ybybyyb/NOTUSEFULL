import ray
import datetime as dt
from STOCK_LIST import STOCK_LIST
from NONFACTOR_CONFIG import NONFACTOR_CONFIG
from FACTOR_CONFIG import FACTOR_CONFIG
from TAG_CONFIG import TAG_CONFIG
from System.ConfigAnalyzer import ConfigAnalyzer
from SystemRay.TaskSplitter import TaskSplitter
from SystemRay.RayLauncher import RayLauncher
from xquant.compute.aimr import AIMR


def work():
    mdLibrary, factorLibrary, sDate, eDate, dayUnit, stockGroupNum = AIMR.getParam().split("-")

    sDate = int(sDate)
    eDate = int(eDate)
    dayUnit = int(dayUnit)
    stockGroupNum = int(stockGroupNum)

    factorConfig = FACTOR_CONFIG + NONFACTOR_CONFIG + TAG_CONFIG

    dt1 = dt.datetime.now()
    configAnalyzer = ConfigAnalyzer(mdLibrary, factorConfig)
    configAnalyzer.analyzeConfig(sDate, eDate)
    dt2 = dt.datetime.now()
    print("INFO: Time cost for config analysis: {} min".format(round((dt2 - dt1).total_seconds() / 60, 2)))

    stockSetToBeCalculated = set(STOCK_LIST)

    taskSplitter = TaskSplitter(stockSetToBeCalculated, sDate, eDate, dayUnit, stockGroupNum, configAnalyzer)
    taskSplitter.splitTask()
    taskList = taskSplitter.getTaskList()
    dt3 = dt.datetime.now()
    print("INFO: Time cost for splitting tasks: {} min".format(round((dt3 - dt2).total_seconds() / 60, 2)))

    startDatetime = dt.datetime.now()

    rayLauncher = RayLauncher(mdLibrary, factorLibrary, factorConfig)
    rayLauncher.setTaskList(taskList)
    rayLauncher.launch(sDate, eDate, stockSetToBeCalculated)

    endDatetime = dt.datetime.now()
    print("INFO: Time cost for factor calculation: {} min"
          .format(round((endDatetime - startDatetime).total_seconds() / 60, 2)))


work()
