import datetime as dt
from SparkUtils.DataIndusSynthetizeUtils.SparkLauncher import SparkLauncher
from SparkUtils.DataIndusSynthetizeUtils.TaskMeta import TaskMeta
import Utils.HelpFunc as Util
from FactorDataTool.Config import CITICS, CITICS_I_CODE, CITICS_II_CODE, SW, SW_I_CODE, SW_II_CODE


def main(marketDataLibrary, indusList, startDate, endDate, daily, minute, tick, overwrite,  hbase,
         saveFile, savePath, maxExecutorNum):

    taskList = []

    if daily or minute:
        for indus in indusList:
            taskList.append(
                TaskMeta(marketDataLibrary,
                         indus,
                         startDate, endDate,
                         daily, minute, False,
                         overwrite,
                         hbase,
                         saveFile, savePath
                         )
            )

    if tick:

        tradingDayList = Util.get_trading_day(startDate, endDate)
        dateGroups = Util.split_calc_date_into_group(tradingDayList, 3)

        for indus in indusList:
            for dateGroup in dateGroups:
                subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                taskList.append(
                    TaskMeta( marketDataLibrary,
                              indus,
                              subStartDate, subEndDate,
                              False, False, tick,
                              overwrite,
                              hbase,
                              saveFile, savePath
                              )
                    )

    sparkLauncher = SparkLauncher()
    sparkLauncher.setTaskList(taskList)
    sparkLauncher.launch(maxExecutorNum)


if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "XHFDataLib"
    startDate = "20200611"
    endDate = "20200612"
    daily = False
    minute = False
    tick = True
    overwrite = True
    hbase = False
    saveFile = "HDFS"
    savePath = None
    maxExecutorNum = 600

    citicsList = CITICS_I_CODE + CITICS_II_CODE
    citicsList = [CITICS + "." + indus for indus in citicsList]
    swList = SW_I_CODE + SW_II_CODE
    swList = [SW + "." + indus for indus in swList]
    indusList = citicsList + swList

    main(marketDataLibrary, indusList, startDate, endDate, daily, minute, tick, overwrite, hbase,
             saveFile, savePath, maxExecutorNum)

