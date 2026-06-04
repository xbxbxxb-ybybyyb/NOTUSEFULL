import datetime
import numpy as np
import pandas as pd


from joblib import Parallel, delayed
from xquant.marketdata import MarketData
from AutoMiningFrame.DataCaculation.entry.FactorManager import FactorProvider
from src.utils import *
# from src.utils.utils import *

class TaggerData():
    """
    该类用来组织从 dolphinDB或Xquant中取出的数据， 每个标的一个实例；
    """
    def __init__(self, depend_data, data_config):
        if type(data_config)==dict:
            data_config = Args(**data_config)
        self.data_config = data_config
        self.start_time = self.data_config.start_time
        self.end_time   = self.data_config.end_time
        self.raw_df_list = []
        self.data_oi = FactorProvider(userID="016884")
        self.xquant_data_ori = MarketData()
        self.depend_data = depend_data
        self._load_data()

    def _load_data(self):
        self.split_df_by_day(self.depend_data)

    def get_labels_ready(self, tagger_calculator):
        label_list = Parallel(n_jobs=self.data_config.n_job)(
            delayed(tagger_calculator.calculate)(self.raw_df_list[n]) for n in range(len(self.raw_df_list)))
        self.label_df = pd.concat(label_list, axis=0)
        print([v for v in self.label_df.columns if v.startswith("label")])
        return self.label_df

    def split_df_by_day(self, df):
        df.replace([np.inf, -np.inf], np.NaN, inplace=True)
        df.dropna(axis=1, how='all', inplace=True)
        # df.dropna(axis=0, how='any', inplace=True)

        for index, (name, group) in enumerate(df.groupby('MDDate')):
            tmp_df = filter_valid_data(group)
            tmp_df.sort_values("MDTime", inplace=True)
            self.raw_df_list.append(tmp_df)