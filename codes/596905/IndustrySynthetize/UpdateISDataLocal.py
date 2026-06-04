import datetime as dt
from xquant.xqutils.helper import multicore_init
import multiprocessing as mp
import Utils.HelpFunc as Util
from FactorDataTool.Config import CITICS, CITICS_I_CODE, CITICS_II_CODE, SW, SW_I_CODE, SW_II_CODE


def main(marketDataLibrary, indus, startDate, endDate, daily, minute, tick, overwrite,
         hbase, saveFile, savePath, env):

    from IndustrySynthetize.IndusSynthetizeDataUpdate import IndusSynthetizeDataUpdate

    idu = IndusSynthetizeDataUpdate(marketDataLibrary,
                                    indus,
                                    startDate, endDate,
                                    daily, minute, tick,
                                    overwrite,
                                    hbase,
                                    saveFile, savePath,
                                    env)
    idu.run_update()



if __name__ == "__main__":
    today = dt.datetime.today().strftime('%Y%m%d')

    marketDataLibrary = "XHFDataLib"
    startDate = "20200320"
    endDate = "20200327"
    daily = False
    minute = False
    tick = True
    overwrite = False
    hbase = True
    saveFile = "HDFS"
    savePath = "HFDataDump"
    env = "Docker"
    isMultiProcess = False

    citicsList = CITICS_I_CODE + CITICS_II_CODE
    citicsList = [CITICS + "." + indus for indus in citicsList]
    swList = SW_I_CODE + SW_II_CODE
    swList = [SW + "." + indus for indus in swList]
    indusList = citicsList + swList

    if daily or minute:
        if not isMultiProcess:
            for indus in indusList:
                main(marketDataLibrary, indus, startDate, endDate, daily, minute, tick, overwrite,
                     hbase, saveFile, savePath, env)
        else :
            task_list = []
            for indus in indusList:
                task = (marketDataLibrary, indus, startDate, endDate, daily, minute, tick, overwrite,
                                                         hbase, saveFile, savePath, env, )
                task_list.append(task)

            if len(task_list) > 0:
                assert multicore_init() == True
                pool = mp.Pool(processes=min(20, len(task_list)))
                for task in task_list:
                    pool.apply_async(main, task)
                pool.close()
                pool.join()

    if tick:

        tradingDayList = Util.get_trading_day(startDate, endDate)
        dateGroups = Util.split_calc_date_into_group(tradingDayList, 3)

        if not isMultiProcess:
            for indus in indusList:
                for dateGroup in dateGroups:
                    subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                    main(marketDataLibrary, indus, subStartDate, subEndDate, daily, minute, tick, overwrite,
                         hbase, saveFile, savePath, env)

        else:
            task_list = []
            for indus in indusList:
                for dateGroup in dateGroups:
                    subStartDate, subEndDate = dateGroup[0], dateGroup[-1]
                    task = (marketDataLibrary, indus, subStartDate, subEndDate, daily, minute, tick, overwrite,
                                                         hbase, saveFile, savePath, env, )
                    task_list.append(task)

            if len(task_list) > 0:
                assert multicore_init() == True
                pool = mp.Pool(processes=min(20, len(task_list)))
                for task in task_list:
                    pool.apply_async(main, task)
                pool.close()
                pool.join()
