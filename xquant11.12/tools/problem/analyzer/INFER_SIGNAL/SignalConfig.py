import sys
import pandas as pd
import datetime as dt
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from xquant.factordata import FactorData


class InferSignalConfig:
    def __init__(self):
        self.fa = FactorData()
        today = dt.datetime.today().strftime("%Y%m%d")
        pre_trading_day = self.fa.tradingday(today, -2)[0]
        self.test_start_date = pre_trading_day
        self.test_end_date = pre_trading_day
        self.next_trading_day = today

        self.model_name = "20200313"
        self.model_path = "/data/user/015629/chensf/ray_everest_20210201_20210515/"
        self.signal_library = "Everest20210201_20210515"   
        self.signal_path = "EasySignal/" + self.model_name + "/"
        self.log_path = "/data/user/015629/EasyInferSignal"
        self.fa = FactorData()

        stockList = sorted(self.fa.hset('MARKET', self.test_end_date, 'ALLA_HIS')['stock'].tolist())
        self.code_list = stockList

        self.is_multiprocess = True

        self.library_name = "Factor_Zeus_Plus"

        self.tag_names = [["1minLong", "1minShort"], ["2minLong", "2minShort"], ["5minLong", "5minShort"]]
        self.factor_names, self.factorIndex = self.get_factor_names_indexes()
        self.factor_name_list = self.factor_names

        self.tag_dict = {
            "1minLong": "tag1minLong",
            "1minShort": "tag1minShort",
            "2minLong": "tag2minLong",
            "2minShort": "tag2minShort",
            "5minLong": "tag5minLong",
            "5minShort": "tag5minShort"
        }

    def get_factor_names_indexes(self):
        factor_name_dict = {}
        model_factor_set = set()
        for tagNameList in self.tag_names:
            for tag in tagNameList:
                tag_file_name = self.model_path + "{}_corr_label_be_nf.csv".format(tag)
                tag_factor_list = pd.read_csv(tag_file_name, index_col=0).iloc[:, 0].tolist()
                factor_name_dict.update({tag: tag_factor_list})
                model_factor_set = model_factor_set.union(tag_factor_list)

        model_factor_list = sorted(list(model_factor_set))
        print(" Model Total Factor Number: {}".format(len(model_factor_list)))

        libraryInfo = self.fa.get_library_info()
        libraryFactor = libraryInfo[self.library_name]
        factor_names = sorted(list(set(model_factor_list).intersection(libraryFactor)))
        factor_name_list = factor_names

        factorIndex = {}
        for tag, factorList in factor_name_dict.items():
            indexList = []
            for factor in factorList:
                indexList.append(factor_name_list.index(factor))
            factorIndex.update({tag: indexList})

        return factor_names, factorIndex


if __name__=="__main__":
    config = InferSignalConfig()
    for tag, indexes in config.factorIndex.items():
        print(tag, len(indexes))
    print(config.factor_name_list.__len__())