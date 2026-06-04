"""转债动态阈值投票选取逻辑—————update @2021.8.11"""

import numpy as np
import pandas as pd
from DataAPI.DataTools import load_lib_data
from DataAPI.DataView import save_json_file, make_dir
from DataAPI.TradingDay import trading_day_gap, trading_day
from Manager.SignalManager import SignalManager
from Manager.UtilsModel.VotingTriggers import *
from Utils.UtilsFile import transfer_file
from Utils.MultiTasks import main_multiprocess, main_spark
from xquant.factordata import FactorData


class SignalCV:
    def __init__(self, st_date, ed_date, code, signal_lib, tag_lib, save_path='lib', is_add_mock=True, dfs=None):
        self.st_date = st_date
        self.ed_date = ed_date
        self.code = code
        self.signal_lib = signal_lib
        self.tag_lib = tag_lib
        # self.tag_list = get_voting_list([1, 2, 5])
        self.tag_list = get_voting_list([0.25, 0.5, 1, 2, 5])
        self.__is_add_sec = self.__add_sec()
        self.n = 10  # 过去N日
        self.is_add_mock = is_add_mock
        self.dfs = dfs
        self.save_path = save_path
        if save_path != 'lib':
            make_dir(self.save_path, dfs=dfs)
        else:
            self.fa = FactorData()

    def start(self):
        signal_data_df, valid_date_list = self.get_signal_data()

        trigger_ratio_by_date = dict()
        for trade_date in valid_date_list:
            trigger_ratio_by_date.update({trade_date: {}})
            signal_data_df_select = signal_data_df.loc[trade_date]
            for tag_name in self.tag_list:
                if signal_data_df_select.empty:
                    long_trigger_ratio, short_trigger_ratio = [99999.0, 0.0], [-99999.0, 0.0]
                else:
                    long_trigger_ratio = self.select_best_triggers(signal_data_df_select, tag_name, dir_='long')
                    short_trigger_ratio = self.select_best_triggers(signal_data_df_select, tag_name, dir_='short')
                trigger_ratio_by_date[trade_date].update({f'{tag_name}min': long_trigger_ratio + short_trigger_ratio})

        all_date_list = trading_day(self.st_date, self.ed_date)
        trigger_ratio_all_date = dict([(x, {}) for x in all_date_list])
        for tag_name in self.tag_list:
            trigger_ratio_by_date_df = pd.DataFrame(dict([(x_, y_[f'{tag_name}min']) for (x_, y_) in trigger_ratio_by_date.items()])).T
            for trade_date in all_date_list:
                select_date_list = []
                if len(valid_date_list) != 0:
                    if trade_date <= valid_date_list[0]:
                        trigger_dict = {'longTriggerRatio': 99999, 'shortTriggerRatio': -99999, 'longCloseRatio': 0, 'shortCloseRatio': 0,
                                        'longRiskRatio': -0.2, 'shortRiskRatio': 0.2}
                        trigger_ratio_all_date[trade_date].update({f'{tag_name}min': trigger_dict})
                        continue
                    ed_idx = np.argwhere(np.array(valid_date_list) < trade_date)[-1][-1] + 1
                    select_date_list = valid_date_list[:ed_idx][-self.n:]
                    if max(select_date_list) >= trade_date:
                        raise ValueError('！！！存在未来数据，请检查')
                if len(select_date_list) < 5:
                    long_trigger_ratio, short_close_ratio, short_trigger_ratio, long_close_ratio = 99999, 0, -99999, 0
                else:
                    trigger_ratio_select_df = trigger_ratio_by_date_df.loc[select_date_list]
                    long_trigger_ratio = trigger_ratio_select_df[0].sort_values().values[1:-1].mean()
                    short_close_ratio = trigger_ratio_select_df[1].sort_values().values[1:-1].mean()
                    short_trigger_ratio = trigger_ratio_select_df[2].sort_values().values[1:-1].mean()
                    long_close_ratio = trigger_ratio_select_df[3].sort_values().values[1:-1].mean()
                trigger_dict = {'longTriggerRatio': long_trigger_ratio, 'shortTriggerRatio': short_trigger_ratio,
                                'longCloseRatio': long_close_ratio, 'shortCloseRatio': short_close_ratio,
                                'longRiskRatio': long_close_ratio - 0.2, 'shortRiskRatio': short_close_ratio + 0.2}
                trigger_ratio_all_date[trade_date].update({f'{tag_name}min': trigger_dict})
        if self.save_path == 'lib':
            for trade_date, triggers in trigger_ratio_all_date.items():
                trigger_fa = pd.DataFrame({self.signal_lib: triggers})
                self.fa.update_factor_value('DynamicTriggers', trigger_fa, self.code, trade_date)
        else:
            save_json_file(trigger_ratio_all_date, f'{self.save_path}/{self.code}.json', dfs=self.dfs)
        print('Finish ', self.code)

    @staticmethod
    def select_best_triggers(signal_data_df_select, tag_name, dir_):
        triggers = signal_data_df_select[f'{tag_name}min{dir_.capitalize()}'].values
        # tag_ave = signal_data_df_select[f'tag{tag_name}min{dir_.capitalize()}'].values
        tag_ave = signal_data_df_select[f'tag8min{dir_.capitalize()}'].values
        if dir_ == 'short':
            tag_ave *= -1
        sort_idx = triggers.argsort()[::-1] if dir_ == 'long' else triggers.argsort()
        triggers, tag_ave = triggers[sort_idx], tag_ave[sort_idx]
        count = np.arange(1, len(triggers) + 1)
        percentile = count / len(triggers) * 100
        ret_cumsum = np.cumsum(tag_ave)
        signal_data = np.array([count, percentile, triggers, tag_ave, ret_cumsum]).T

        # 寻找开仓阈值
        signal_index_df_open = signal_data[(signal_data[:, 0] >= 5) & (signal_data[:, 1] < 10)]  # 日均最小触发5次，小于5%分位数
        if signal_index_df_open.shape[0] == 0:
            open_trigger = 99999 if dir_ == 'long' else -99999
            return [open_trigger, 0]
        else:
            open_score = signal_index_df_open[:, 4] + signal_index_df_open[:, 0] * 0.2
            open_idx = np.argmax(open_score)
            open_trigger = signal_index_df_open[open_idx, 2]
            open_percentile = signal_index_df_open[signal_index_df_open[:, 2] == open_trigger, 1][0]

        # 寻找平仓阈值
        signal_index_df_close = signal_data[(signal_data[:, 1] > max(10, open_percentile + 1)) & (signal_data[:, 1] < 20)]
        if signal_index_df_close.shape[0] == 0:
            close_trigger = 0
        else:
            close_score = signal_index_df_close[:, 4] - signal_index_df_close[:, 0] * 0.8
            close_idx = np.argmax(close_score)
            close_trigger = signal_index_df_close[close_idx, 2]
        return [open_trigger, close_trigger]

    def get_signal_data(self):
        date_list = self.get_date_list()
        vt_name = '8.75min' if self.__is_add_sec else '8min'
        signal_data = SignalManager(self.code, date_list, self.signal_lib, tag_lib=self.tag_lib, is_add_tag=True, is_get_valid=True,
                                    is_add_mock=self.is_add_mock, vt_name=vt_name).get_signal_dict()
        if len(signal_data) == 0:
            return pd.DataFrame(), []
        signal_data_df = pd.concat(signal_data, axis=0).dropna(axis=0)
        if self.__is_add_sec:
            rename_col = {'15secLong': '0.25minLong', '15secShort': '0.25minShort', '30secLong': '0.5minLong', '30secShort': '0.5minShort',
                          'tag15secLong': 'tag0.25minLong', 'tag15secShort': 'tag0.25minShort',
                          'tag30secLong': 'tag0.5minLong', 'tag30secShort': 'tag0.5minShort'}
            signal_data_df = signal_data_df.rename(columns=rename_col)

        signal_dict = get_voting_dict([0.25, 0.5, 1, 2, 5])
        for tag_name in self.tag_list:
            if tag_name not in [0.25, 0.5, 1, 2, 5]:
                signal_data_df[f'{tag_name}minLong'] = signal_data_df[[f'{t}minLong' for t in signal_dict[tag_name]]].mean(axis=1)
                signal_data_df[f'{tag_name}minShort'] = signal_data_df[[f'{t}minShort' for t in signal_dict[tag_name]]].mean(axis=1)
                signal_data_df[f'tag{tag_name}minLong'] = signal_data_df[[f'tag{t}minLong' for t in signal_dict[tag_name]]].mean(axis=1)
                signal_data_df[f'tag{tag_name}minShort'] = signal_data_df[[f'tag{t}minShort' for t in signal_dict[tag_name]]].mean(axis=1)
        date_list = list(sorted(set(date_list).intersection(set([x_[0] for x_ in signal_data_df.index]))))
        return signal_data_df, date_list

    def get_date_list(self):
        # 获取交易日的数据，剔除涨停/临停的交易日
        date_list_p = trading_day(trading_day_gap(self.st_date, -100), self.ed_date)
        data = load_lib_data(self.code, ['20200102'], 'ZeusDataLib', ['D_Date', 'D_HighPrice', 'D_LowPrice', 'D_PreviousClose']).set_index('D_Date')
        data = data.loc[date_list_p]
        data = data[(data['D_HighPrice'] < data['D_PreviousClose'] * 1.2) & (data['D_LowPrice'] > data['D_PreviousClose'] * 0.8)]
        date_array = np.array(data.index)
        date_list = []
        if len(date_array) > 0:
            if date_array[0] >= self.st_date:
                date_list = list(date_array)
            else:
                st_idx = max(0, np.argwhere(date_array < self.st_date)[-1][-1] - self.n + 1)
                date_list = list(date_array[st_idx:])
        return date_list

    def __add_sec(self):
        remainder = set([x % 1 for x in self.tag_list])
        is_add_sec = remainder != {0}
        return is_add_sec


class Task:
    def __init__(self, code_list, st_date, ed_date, signal_lib, tag_lib, save_path, is_add_mock):
        self.code_list = code_list
        self.st_date = st_date
        self.ed_date = ed_date
        self.signal_lib = signal_lib
        self.tag_lib = tag_lib
        self.save_path = save_path
        self.is_add_mock = is_add_mock

    def start(self, mode='local'):
        if mode == 'local':
            self.single_task(self.code_list)
        elif mode == 'multi_processing':
            main_multiprocess(self.single_task, self.code_list, multiprocess_nums=20, is_sum_result=False)
        elif mode == 'spark':
            main_spark(self.single_task_spark, self.code_list)
            if self.save_path != 'lib':
                transfer_file(self.save_path.replace('/data/user/011668/', ''), self.save_path)
        else:
            raise ValueError

    def single_task(self, code_list):
        for code in code_list:
            signal_cv = SignalCV(self.st_date, self.ed_date, code, self.signal_lib, self.tag_lib, self.save_path, self.is_add_mock)
            signal_cv.start()

    def single_task_spark(self, context, code):
        dfs = context.get_hdfs()
        save_path_spark = self.save_path.replace('/data/user/', '')
        signal_cv = SignalCV(self.st_date, self.ed_date, code, self.signal_lib, self.tag_lib, save_path_spark, self.is_add_mock, dfs=dfs)
        signal_cv.start()
