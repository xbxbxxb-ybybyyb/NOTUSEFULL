import sys
import pandas as pd
import os
sys.path.append(os.path.abspath(os.path.abspath(__file__) + "/../.."))
from xquant.factordata import FactorData

class InferSignalConfig:
    def __init__(self):
        self.fa = FactorData()
        self.test_start_date = "20210901"
        self.test_end_date = "20210917"
        self.next_trading_day = self.test_end_date

        self.model_name = "20200313"
        self.model_path = "/data/user/015629/chensf/ray_everest_20210201_20210515/"
        self.signal_library = "Everest20210201_20210515"   
        self.signal_path = "EasySignal/" + self.model_name + "/"
        self.log_path = "/data/user/015629/EasyInferSignal"

        self.code_list = self.get_missing_code_list()

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

    def get_missing_code_list(self):
        date_list = self.fa.tradingday(self.test_start_date, self.test_end_date)
        code_list = []
        for date in date_list:
            missing_stock_list = self.get_missing_signal_stock(date)
            print(" Check Date: {}, {} ".format(date, len(missing_stock_list)))
            if len(missing_stock_list) > 0:
                for stock in missing_stock_list:
                    code_list.append((stock, date))
        print(" Total Missing Stock/Date: {} ".format(len(code_list)))
        return code_list

    def get_missing_signal_stock(self, date):
        stock_list = self.fa.hset('MARKET', str(date), 'ALLA')['stock'].tolist()
        trade_status = self.fa.get_factor_value("Basic_factor", stock_list, [str(date)], ["trade_status"]).droplevel(0)
        traded_stock_list = trade_status[trade_status["trade_status"].isin(["交易", "N"])].index.tolist()
        valid_stock_list = self.fa.search_by_date(self.signal_library, str(date), traded_stock_list)
        missing_stock_list = list(set(traded_stock_list).difference(valid_stock_list))
        return missing_stock_list


if __name__=="__main__":
    config = InferSignalConfig()
    print(config.factor_name_list)





