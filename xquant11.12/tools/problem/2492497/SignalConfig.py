import copy
import pandas as pd
from Utils.HelpFunc import get_trading_day, split_calc_date_into_group
from xquant.factordata import FactorData


class SignalConfig(object):
    def __init__(self, enable=False):
        self.enable = enable
        self.start_date = "20221001"
        self.end_date = "20230228"
        self.code_unit = 1      # Code Num in Each Group
        self.date_unit = 1      # Date Num in Each Group, None for All Dates
        self.fa = FactorData()
#        self.code_list = pd.read_excel("/data/user/015629/StockPool/sz_stock_1s_stock_list.xlsx")["stock"].tolist()
        index_date = "20220601"
        hs300 = self.fa.hset('INDEX', index_date, 'HS300')['stock'].tolist()
        zz500 = self.fa.hset('INDEX', index_date, 'ZZ500')['stock'].tolist()
        zz1000 = self.fa.hset('INDEX', index_date, 'ZZ1000')['stock'].tolist()
        hs300 = [c for c in hs300 if c[-2:] == "SH"]
        zz500 = [c for c in zz500 if c[-2:] == "SH"]
        zz1000 = [c for c in zz1000 if c[-2:] == "SH"]
        self.code_list = hs300 + zz500 + zz1000
        self.model_name = "Albest20221001SHOrder"
        self.model_path = "/data/user/013050/chensf/ray_albest_20221001_20221130_order_sh/"
        self.tag_names = ["tag1minLong", "tag1minShort", "tag2minLong", "tag2minShort", "tag5minLong", "tag5minShort"]
        self.freq_list = ["036", "147", "258"]
        self.factor_library_list = ["Factor_{}_Channel_SH".format(freq) for freq in self.freq_list]
        self.factor_names_dict = self.get_factor_names_dict(self.factor_library_list[0])

        self.window_size_dict = {"tag1minLong": 160, "tag1minShort": 160, "tag2minLong": 200, "tag2minShort": 200, "tag5minLong": 240, "tag5minShort": 240}
        self.save = True
        self.save_library_list = ["Albest20221001SHOrder{}Signals".format(freq) for freq in self.freq_list]
        self.concat_1s_signal = True
        self.save_1s_library = "Albest20221001SHOrder1Signals"

        # Run Params
        self.infer_type = "numpy"     # "tensorflow", "numpy"
        self.mode = "Spark"           # "Local", "Ray", "MultiProcess", "Spark"
        if self.infer_type == "tensorflow":
            assert  self.mode in ["Local", "Ray", "MultiProcess"], " TensorFlow Inference Only Support Local/Ray/MultiProcess Mode "
        if self.infer_type == "numpy":
            assert self.mode in ["Local", "MultiProcess", "Ray", "Spark"], " Numpy Model Inference Only Support Local/Ray/MultiProcess/Spark Mode "
            self.prepare_model_weights()

        self.aimr_num = 0
        self.cpus_num = 20
        self.max_executor_num = 600

        self.data_check = True       # True for Check and Update Missing, False for Newly Update

        if self.data_check:
            self.task_list = self.generate_data_check_task(self.code_list, self.start_date, self.end_date)
        else:
            self.task_list = self.split_codes_dates_task(self.code_list, self.start_date, self.end_date, self.code_unit, self.date_unit)

        if self.enable:
            print(" Total Task Num: {} ".format(len(self.task_list)))

    def get_task_list(self):
        return self.task_list

    def get_factor_names_dict(self, factor_library):
        factor_names_dict = {}
        for tag_name in self.tag_names:
            tag_file_name = self.model_path + "{}_corr_label_be_nf.csv".format(tag_name.split("tag")[1])
            tag_factor_list = pd.read_csv(tag_file_name, index_col=0).iloc[:, 0].tolist()
            factor_names_dict.update({tag_name: tag_factor_list})

        factor_name_list = sorted(set([factor for tag_name, factor_name_list in factor_names_dict.items() for factor in factor_name_list]))
        print(" Model Total Factor Number: {}".format(len(factor_name_list)))

        library_factors = self.fa.get_library_info()[factor_library]
        not_exist_factors = sorted(set(factor_name_list).difference(library_factors))
        assert len(not_exist_factors) == 0, " Factor Library {} Has NOT Factors: {} ".format(factor_library, not_exist_factors)

        return factor_names_dict

    def prepare_model_weights(self):
        from xquant.xqutils.xqfile import HDFSFile
        hf = HDFSFile()
        combine_path = "ModelWeights/{}/".format(self.model_name)
        if not hf.exists(combine_path):
            hf.upload(combine_path, self.model_path)

    @staticmethod
    def split_codes_dates_task(code_list, start_date, end_date, code_unit=1, date_unit=None):
        date_list = get_trading_day(start_date, end_date)
        date_unit = date_unit if date_unit is not None else len(date_list)
        date_groups = split_calc_date_into_group(date_list, date_unit)
        code_groups = split_calc_date_into_group(code_list, code_unit)

        task_list = []
        for sub_code_list in code_groups:
            for date_group in date_groups:
                sub_start_date, sub_end_date = date_group[0], date_group[-1]
                task_list.append( [sub_code_list, sub_start_date, sub_end_date]
                )
        return task_list

    def generate_data_check_task(self, code_list, start_date, end_date):
        date_list = get_trading_day(start_date, end_date)
        task_list = []
        for date in date_list:
            check_library_list = copy.deepcopy(self.save_library_list)
            if self.concat_1s_signal:
                check_library_list += [self.save_1s_library]
            missing_code_list = []
            for check_library in check_library_list:
                missing_codes = self.get_missing_signal_code(check_library, code_list, date)
                missing_code_list = sorted(set(missing_codes).union(missing_code_list))
            if len(missing_code_list) > 0:
                if self.enable:
                    print(" Date {} Missing {} Codes ".format(date, len(missing_code_list)))
                for code in missing_code_list:
                    task_list.append([[code], date, date])
        return task_list

    @staticmethod
    def generate_data_check_task2(save_library):
        missing_dict = pd.read_pickle("/data/user/013050/MISC/SignalCheck/signal_check_{}.pickle".format(save_library))
        task_list = []
        for code, missing_dates in missing_dict.items():
            for date in missing_dates:
                task_list.append([[code], date, date])
        return task_list        

    def get_missing_signal_code(self, save_library, code_list, date):
        trade_status = self.fa.get_factor_value("Basic_factor", code_list, [str(date)], ["trade_status"]).droplevel(0)
        traded_code_list = trade_status[trade_status["trade_status"].isin(["交易", "N"])].index.tolist()
        valid_code_list = self.fa.search_by_date(save_library, str(date), traded_code_list)
        return list(set(traded_code_list).difference(valid_code_list))


if __name__ == "__main__":
    sc = SignalConfig(enable=True)














