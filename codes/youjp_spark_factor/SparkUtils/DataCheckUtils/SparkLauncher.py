import os
import pickle
import uuid
from HFDataLoader.Config import USER_ID, DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, MOCK_TICK_SUFFIX
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE, SHENWAN_I_CODE, SHENWAN_II_CODE
from HFDataMonitor.DataCheck import DataCheck
from HFDataLoader.HFDataUpdate import HFDataUpdate
import Utils.HelpFunc as Util
from xquant.compute.sparkmr import Configuration
from xquant.compute.sparkmr import Job
from xquant.xqutils.xqfile import HDFSFile


class SparkLauncher:
    def __init__(self):
        self.__uuid = uuid.uuid1()

        self.__taskList = None

    def setTaskList(self, taskList):
        self.__taskList = taskList

    def launch(self, maxExecutorNum):
        config = self.__getSparkConf(maxExecutorNum)
        job = Job(config, mode="OverWrite")
        job.add_tasks(self.__taskList)
        job.set_func(self.func)
        job.start()

    @staticmethod
    def func(context, taskMeta):
        marketDataLibrary = taskMeta.getMarketDataLibrary()
        code = taskMeta.getCode()
        startDate = taskMeta.getStartDate()
        endDate = taskMeta.getEndDate()
        daily = taskMeta.getDaily()
        minute = taskMeta.getMinute()
        tick = taskMeta.getTick()
        mockTick = taskMeta.getMockTick()
        mockFreq = taskMeta.getMockFreq()
        overwrite = taskMeta.getOverwrite()
        monitor = taskMeta.getMonitor()
        hbase = taskMeta.getHbase()
        saveFile = taskMeta.getSaveFile()
        savePath = taskMeta.getSavePath()
        saveCheck = taskMeta.getSaveCheck()
        saveCheckPath = taskMeta.getSaveCheckPath()
        updateMissing = taskMeta.getUpdateMissing()
        env = taskMeta.getEnv()

        codeType = Util.get_code_type(code)

        ### Step 1： 检查缺失的数据， 保存到HDFS中
        dc = DataCheck(marketDataLibrary,
                        code,
                        startDate, endDate,
                        daily=daily, minute=minute, tick=tick, mock_tick=mockTick,
                        save=saveCheck, save_path=saveCheckPath,
                        env=env)

        dc.run_check()

        ### Step 2：从HDFS中读取缺失的数据，进行重新更新
        if updateMissing:
            hf = HDFSFile()
            if saveCheckPath is None:
                saveCheckPath = "HFDataCheck"
            root = os.path.join(USER_ID, saveCheckPath)
            file_name = os.path.join(root, "{}_{}.pkl".format(code, "invalid_date_list"))
            if hf.exists(file_name):
                with hf.open(file_name, "rb") as f:
                    data = f.read()
                    invalid_dict = pickle.loads(data)
                if invalid_dict:
                    ### 日频缺失数据
                    invalid_daily = invalid_dict.get(DAILY_SUFFIX, [])
                    if invalid_daily:
                        for invalid_date in invalid_daily:
                            MissingStartDate = invalid_date
                            MissingEndDate = invalid_date

                            if codeType == "INDUSTRY" and Util.get_industry_type(code) != "SHENWAN":
                                pass

                            else:
                                hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=True, minute=False, tick=False,
                                           mock_tick=False, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                                hfd.run_update()

                    ### 分钟频缺失数据
                    invalid_minute = invalid_dict.get(MINUTE_SUFFIX, [])
                    if invalid_minute:
                        for invalid_date in invalid_minute:
                            MissingStartDate = invalid_date
                            MissingEndDate = invalid_date

                            if codeType == "INDUSTRY" and Util.get_industry_type(code) != "SHENWAN":
                                pass

                            else:
                                hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=False, minute=True, tick=False,
                                           mock_tick=False, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                                hfd.run_update()

                    ### TICK频缺失数据
                    invalid_tick = invalid_dict.get(TICK_SUFFIX, [])
                    if invalid_tick:
                        for invalid_date in invalid_tick:
                            MissingStartDate = invalid_date
                            MissingEndDate = invalid_date

                            if codeType == "INDUSTRY" and Util.get_industry_type(code) in ["CITICS", "SW"]:
                                from IndustrySynthetize.IndusSynthetizeDataUpdate import IndusSynthetizeDataUpdate
                                if code in CITICS_I_CODE + CITICS_II_CODE:
                                    IndusName = "CITICS."
                                elif code in SW_I_CODE + SW_II_CODE:
                                    IndusName = "SW."
                                idu = IndusSynthetizeDataUpdate(marketDataLibrary,
                                                                IndusName + code,
                                                                MissingStartDate, MissingEndDate,
                                                                False, False, tick,
                                                                overwrite,
                                                                hbase,
                                                                saveFile, savePath,
                                                                env)
                                idu.run_update()
                            else:
                                hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=False, minute=False, tick=True,
                                           mock_tick=False, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                                hfd.run_update()

                    ### MOCK TICK 缺失数据
                    invalid_mock_tick = invalid_dict.get(MOCK_TICK_SUFFIX, [])
                    if invalid_mock_tick:
                        for invalid_date in invalid_mock_tick:
                            MissingStartDate = invalid_date
                            MissingEndDate = invalid_date

                            if codeType != "STOCK":
                                pass

                            else:
                                hfd = HFDataUpdate(marketDataLibrary,
                                           code,
                                           MissingStartDate, MissingEndDate,
                                           daily=False, minute=False, tick=False,
                                           mock_tick=True, mock_freq=mockFreq,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath,
                                           env=env)

                                hfd.run_update()

    def __getSparkConf(self, maxExecutorNum):
        config = Configuration()
        config.set_app_name(str(self.__uuid))
        config.set_dst_dir("015629/Trash/{}/".format(self.__uuid))
        config.set_env_dir(self.__get_env_dir())
        config.set_executor_instances(str(min(len(self.__taskList), maxExecutorNum)))
        config.set_executor_memory("4G")

        return config

    @staticmethod
    def __get_env_dir():
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
