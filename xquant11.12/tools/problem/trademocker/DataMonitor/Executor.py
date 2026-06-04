from DataInterface.Config import USER_ID, DAILY_SUFFIX, MINUTE_SUFFIX, TICK_SUFFIX, TRANSACTION_SUFFIX, ORDER_SUFFIX
from FactorDataTool.Config import CITICS_I_CODE, CITICS_II_CODE, SW_I_CODE, SW_II_CODE
from Utils.HelpFunc import get_code_type, get_industry_type

import os
import pickle
from xquant.xqutils.xqfile import HDFSFile


def Executor(library, code, dataSource, startDate, endDate, daily, minute, tick, tran, order, overwrite, monitor,
         hbase, saveFile, savePath, saveCheck, saveCheckPath, updateMissing):

    # Step 1: Data Check
    from DataMonitor.DataCheck import DataCheck

    dc = DataCheck(library, code, startDate, endDate, daily=daily, minute=minute, tick=tick, tran=tran, order=order,
                   save=saveCheck, save_path=saveCheckPath)
    dc.run()

    ### Step 2：Load Missing Data Info From HDFS, Update Missing
    if updateMissing:
        from DataUpdate.Executor import Executor

        code_type = get_code_type(code)

        root = os.path.join(USER_ID if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ else "", saveCheckPath)
        file_name = os.path.join(root, "{}_{}.pickle".format(code, "invalid_date_list"))

        hf = HDFSFile()

        if hf.exists(file_name):
            f = hf.open(file_name, "rb")
            invalid_dict = pickle.load(f)

            if invalid_dict:
                # 日频缺失数据
                invalid_daily = invalid_dict.get(DAILY_SUFFIX, [])
                if invalid_daily:
                    for invalid_date in invalid_daily:
                        missingStartDate = invalid_date
                        missingEndDate = invalid_date

                        if code_type == "INDUSTRY" and get_industry_type(code) != "SHENWAN":
                            continue
                        else:
                            hfd = Executor(library,
                                           code,
                                           dataSource,
                                           missingStartDate, missingEndDate,
                                           daily=True, minute=False, tick=False, tran=False, order=False,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath
                                           )
                            hfd.run()

                # 分钟频缺失数据
                invalid_minute = invalid_dict.get(MINUTE_SUFFIX, [])
                if invalid_minute:
                    for invalid_date in invalid_minute:
                        missingStartDate = invalid_date
                        missingEndDate = invalid_date

                        if code_type == "INDUSTRY" and get_industry_type(code) != "SHENWAN":
                            continue
                        else:
                            hfd = Executor(library,
                                           code,
                                           dataSource,
                                           missingStartDate, missingEndDate,
                                           daily=False, minute=True, tick=False, tran=False, order=False,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath
                                           )

                            hfd.run()

                # TICK频缺失数据
                invalid_tick = invalid_dict.get(TICK_SUFFIX, [])
                if invalid_tick:
                    for invalid_date in invalid_tick:
                        missingStartDate = invalid_date
                        missingEndDate = invalid_date

                        if code_type == "INDUSTRY" and get_industry_type(code) in ["CITICS", "SW"]:
                            from IndustrySynthetize.IndusSynthetizeDataUpdate import IndusSynthetizeDataUpdate
                            if code in CITICS_I_CODE + CITICS_II_CODE:
                                IndustryName = "CITICS."
                            elif code in SW_I_CODE + SW_II_CODE:
                                IndustryName = "SW."
                            idu = IndusSynthetizeDataUpdate(library,
                                                            IndustryName + code,
                                                            missingStartDate, missingEndDate,
                                                            False, False, tick,
                                                            overwrite,
                                                            hbase,
                                                            saveFile, savePath
                                                            )
                            idu.run()
                        else:
                            hfd = Executor(library,
                                           code,
                                           dataSource,
                                           missingStartDate, missingEndDate,
                                           daily=False, minute=False, tick=True, tran=False, order=False,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath
                                           )

                            hfd.run()

                # Transaction缺失数据
                invalid_transaction = invalid_dict.get(TRANSACTION_SUFFIX, [])
                if invalid_transaction:
                    for invalid_date in invalid_transaction:
                        missingStartDate = invalid_date
                        missingEndDate = invalid_date

                        if code_type not in ["STOCK", "CBOND", "ETF", "LOF"]:
                            continue
                        else:
                            hfd = Executor(library,
                                           code,
                                           dataSource,
                                           missingStartDate, missingEndDate,
                                           daily=False, minute=False, tick=False, tran=True, order=False,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath
                                           )

                            hfd.run()

                # Order缺失数据
                invalid_order = invalid_dict.get(ORDER_SUFFIX, [])
                if invalid_order:
                    for invalid_date in invalid_order:
                        missingStartDate = invalid_date
                        missingEndDate = invalid_date

                        if not (code_type in ["STOCK", "CBOND", "ETF", "LOF"] and code.endswith(".SZ")):
                            continue
                        else:
                            hfd = Executor(library,
                                           code,
                                           dataSource,
                                           missingStartDate, missingEndDate,
                                           daily=False, minute=False, tick=False, tran=False, order=True,
                                           overwrite=overwrite,
                                           monitor=monitor,
                                           hbase=hbase,
                                           save_file=saveFile, save_path=savePath
                                           )

                            hfd.run()





