import os
import gc
import datetime as dt
import pandas as pd
from Utils.HelpFunc import get_trading_day, MyPrint
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile
from InferSpark.InferModel import InferModel
USER_ID = "013050"


class CalcSignal(object):
    """"""
    def __init__(self, code, start_date, end_date, model_name, model_path, factor_library_list=None, factor_names_dict=None,
                       window_size_dict=None, save=True, save_library_list=None, concat_1s_signal=True, save_1s_library=None
        ):
        self.code = code
        self.start_date = start_date
        self.end_date = end_date
        self.model_name = model_name
        self.model_path = model_path
        self.factor_library_list = factor_library_list
        self.factor_names_dict = factor_names_dict
        self.save = save
        self.save_library_list = save_library_list
        assert len(self.factor_library_list) == len(self.save_library_list), " Factor Library {} NOT Match Save Library {} ".format(self.factor_library_list, self.save_library_list)
        self.concat_1s_signal = concat_1s_signal
        self.save_1s_library = save_1s_library

        self.fa = FactorData()
        self.hf = HDFSFile()

        self.sliceLags = window_size_dict

        self.open_tick_num = 21

        self.tag_names = None
        self.input_names_dict = dict()
        self.input_list = None
        self.input_indexes = dict()
        self.factor_list = None
        self.second_list = None

        self.collect_factor_info()

    def collect_factor_info(self):
        """"""
        self.tag_names = sorted(list(self.factor_names_dict.keys()))
        self.input_names_dict = self.factor_names_dict
        self.input_list = sorted(set([factor for tag_name, factor_name_list in self.input_names_dict.items() for factor in factor_name_list]))
        self.factor_list = self.input_list
        for tag_name, factor_name_list in self.input_names_dict.items():
            self.input_indexes[tag_name] = [self.input_list.index(factor) for factor in factor_name_list]

    def calculate(self):
        """"""
        MyPrint(" Start to Infer Signal: {}-{}-{}-{}".format(self.code, self.model_name, self.start_date, self.end_date))

        test_date_list = get_trading_day(self.start_date, self.end_date)
        factor_columns = ["timestamp"] + self.factor_list + self.tag_names
        try:
            total_time, load_time, infer_time, dump_time = 0, 0, 0, 0

            concat_1s_signal_list = []

            for factor_library, save_library in zip(self.factor_library_list, self.save_library_list):

                time1 = dt.datetime.now()

                test_timestamp = {"timestamp": dict()}
                test_factor_data = dict()
                test_tag_data = dict()
                for tag_name in self.tag_names:
                    test_tag_data[tag_name] = dict()

                for test_date in test_date_list:
                    try:
                        factor_tag_timestamp_df = self.fa.get_factor_value(
                            factor_library,
                            self.code,
                            test_date,
                            factor_columns
                        )

                        test_factor_data[test_date] = factor_tag_timestamp_df[self.input_list].values
                        test_timestamp["timestamp"][test_date] = factor_tag_timestamp_df["timestamp"].tolist()
                        for tag_name in self.tag_names:
                            test_tag_data[tag_name][test_date] = factor_tag_timestamp_df[tag_name].tolist()
                    except:
                        MyPrint(" {} No Factor Data on {}-{}".format(factor_library, self.code, test_date))
                        continue

                if not test_factor_data or not test_tag_data or not test_timestamp:
                    MyPrint(" {} No Data between {} and {} In {} ".format(self.code, self.start_date, self.end_date, factor_library))

                time2 = dt.datetime.now()

                root_path = USER_ID if "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ else ""
                model_path = os.path.join(root_path, "ModelWeights/{}/".format(self.model_name))
                if not self.hf.exists(model_path):
                    raise Exception(" Model Weights Not Exist: {} ".format(self.model_name))

                paraModel = {
                    "code": self.code,
                    "tagNames": self.tag_names,
                    "sliceLags": self.sliceLags,
                    "test_factor_data": test_factor_data,
                    "test_tag_data": test_tag_data,
                    "test_timestamp": test_timestamp,
                    "open_tick_num": self.open_tick_num,
                    "model_path": model_path,
                    "factor_names_dict": self.input_names_dict,
                    "factor_indexes": self.input_indexes
                }

                model = InferModel(paraModel=paraModel)

                # 训练模型
                daily_prediction = model.infer()

                time3 = dt.datetime.now()

                for date in daily_prediction:
                    if daily_prediction[date]["signals"]:
                        dt_frame = pd.DataFrame(data=daily_prediction[date]["signals"])
                        dt_frame["ticktime"] = dt_frame["timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%H:%M:%S:%f"))
                        if self.save:
                            self.fa.update_factor_value(save_library, dt_frame, self.code, date)

                        if self.concat_1s_signal:
                            concat_1s_signal_list.append(dt_frame)

                time4 = dt.datetime.now()

                total_time += (time4 - time1).total_seconds()
                load_time += (time2 - time1).total_seconds()
                infer_time += (time3 - time2).total_seconds()
                dump_time += (time4 - time3).total_seconds()

            time5 = dt.datetime.now()

            if len(concat_1s_signal_list) == len(self.factor_library_list):
                concat_1s_signal = pd.concat(concat_1s_signal_list, axis=0).sort_values(by="timestamp")
                concat_1s_signal["date"] = concat_1s_signal["timestamp"].apply(lambda x: dt.datetime.fromtimestamp(x).strftime("%Y%m%d"))
                date_list = sorted(set(concat_1s_signal["date"].tolist()))
                for date in date_list:
                    if self.save:
                        daily_1s_signal = concat_1s_signal[concat_1s_signal["date"] == date].reset_index(drop=True)
                        daily_1s_signal.drop("date", axis=1, inplace=True)
                        self.fa.update_factor_value(self.save_1s_library, daily_1s_signal, self.code, date)
            else:
                MyPrint(" Concat 1S Signal Not Match: {}-{}-{} ".format(self.code, len(concat_1s_signal_list), len(self.factor_library_list)))

            time6 = dt.datetime.now()
            dump_time += (time6 - time5).total_seconds()

            MyPrint(" {}-{}-{} Total Calculate Time: {}S, Load Data: {}S, Inference: {}S, Dump Data: {}S ".format(
                self.code, self.start_date, self.end_date, round(total_time, 2), round(load_time, 2), round(infer_time, 2), round(dump_time, 2)))

            gc.collect()
        except Exception as e:
            MyPrint(" {} Inference Signal Failed: {} ".format(self.code, e))

def run_meta_task_numpy(task):
    codeList = task.codeList
    startDate = task.startDate
    endDate = task.endDate
    modelName = task.modelName
    modelPath = task.modelPath
    factorLibraryList = task.factorLibraryList
    factorNamesDict = task.factorNamesDict
    windowSizeDict = task.windowSizeDict
    save = task.save
    saveLibraryList = task.saveLibraryList
    concat1sSignal = task.concat1sSignal
    save1sLibrary = task.save1sLibrary

    for code in codeList:
        cs = CalcSignal(code, startDate, endDate, modelName, modelPath, factorLibraryList, factorNamesDict,
                         windowSizeDict, save, saveLibraryList, concat1sSignal, save1sLibrary)
        cs.calculate()

        gc.collect()
