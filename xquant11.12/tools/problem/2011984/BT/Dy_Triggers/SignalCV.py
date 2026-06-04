"""动态阈值选取逻辑—————update @2021.11.30"""

import numpy as np
import pandas as pd
from DataAPI.DataTools import load_lib_data
from DataAPI.DataView import save_json_file, make_dir
from DataAPI.TradingDay import trading_day_gap, trading_day
from Manager.SignalManager import SignalManager, split_col_names
from Utils.UtilsFile import transfer_file
from Utils.MultiTasks import main_multiprocess, main_spark
from xquant.factordata import FactorData


class SignalCV:
    def __init__(self, st_date, ed_date, code, strategy, signal_lib, save_path='lib', vt_name='8min', tag_lib=None, mock_lib=None,
                 is_add_mock=False, overwrite_params=None, dfs=None):
        self.st_date = st_date
        self.ed_date = ed_date
        self.code = code
        self.strategy = strategy
        self.signal_lib = signal_lib
        self.n = 10  # 过去N日
        self.__vt_name = vt_name
        self.dfs = dfs
        self.save_path = save_path
        self.__tag_lib = tag_lib
        self.__mock_lib = mock_lib
        self.__is_add_mock = is_add_mock
        self._params = self.get_params(overwrite_params)
        if save_path != 'lib':
            make_dir(self.save_path, dfs=dfs)
        else:
            self.fa = FactorData()
        self.__trigger_save_lib = 'DynamicTriggers'

    def start(self):
        signal_data_df, valid_date_list = self.get_signal_data()

        trigger_ratio_by_date = dict()
        for trade_date in valid_date_list:
            signal_data_df_select = signal_data_df.loc[trade_date]
            if signal_data_df_select.empty:
                long_trigger_ratio, short_trigger_ratio = [99999.0, 0.0], [-99999.0, 0.0]
            else:
                long_trigger_ratio = self.select_best_triggers(signal_data_df_select, dir_='long')
                short_trigger_ratio = self.select_best_triggers(signal_data_df_select, dir_='short')
            trigger_ratio_by_date.update({trade_date: long_trigger_ratio + short_trigger_ratio})
        trigger_ratio_by_date_df = pd.DataFrame(trigger_ratio_by_date).T

        trigger_ratio_all_date = dict()
        all_date_list = trading_day(self.st_date, self.ed_date)
        for trade_date in all_date_list:
            select_date_list = []
            if len(valid_date_list) != 0:
                if trade_date <= valid_date_list[0]:
                    trigger_dict = {'longTriggerRatio': 99999, 'shortTriggerRatio': -99999, 'longCloseRatio': 0, 'shortCloseRatio': 0,
                                    'longRiskRatio': -0.2, 'shortRiskRatio': 0.2}
                    trigger_ratio_all_date.update({trade_date: trigger_dict})
                    if self.save_path == 'lib':
                        trigger_fa = pd.DataFrame({self.signal_lib: trigger_dict})
                        self.fa.update_factor_value(self.__trigger_save_lib, trigger_fa, self.code, trade_date)
                    continue
                ed_idx = np.argwhere(np.array(valid_date_list) < trade_date)[-1][-1] + 1
                select_date_list = valid_date_list[:ed_idx][-self.n:]
                if max(select_date_list) >= trade_date:
                    raise ValueError('！！！存在未来数据，请检查')
            trigger_dict = self.get_trigger_ratio(trigger_ratio_by_date_df, select_date_list)
            trigger_ratio_all_date.update({trade_date: trigger_dict})
            if self.save_path == 'lib':
                trigger_fa = pd.DataFrame({self.signal_lib: trigger_dict})
                self.fa.update_factor_value(self.__trigger_save_lib, trigger_fa, self.code, trade_date)
        if self.save_path != 'lib':
            save_json_file(trigger_ratio_all_date, f'{self.save_path}/{self.code}.json', dfs=self.dfs)
        print('Finish ', self.code)

    @staticmethod
    def get_trigger_ratio(trigger_ratio_by_date_df, select_date_list):
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
        return trigger_dict

    def select_best_triggers(self, signal_data_df_select, dir_):
        triggers = signal_data_df_select[f'ave_{dir_}'].values
        tag_ave = signal_data_df_select[f'tag_ave_{dir_}'].values
        sort_idx = triggers.argsort()[::-1] if dir_ == 'long' else triggers.argsort()
        triggers, tag_ave = triggers[sort_idx], tag_ave[sort_idx]
        count = np.arange(1, len(triggers) + 1)
        percentile = count / len(triggers) * 100
        ret_cumsum = np.cumsum(tag_ave)
        signal_data = np.array([count, percentile, triggers, tag_ave, ret_cumsum]).T

        # 寻找开仓阈值
        signal_index_df_open = signal_data[(signal_data[:, 0] >= self._params['min_triggers']) & (signal_data[:, 1] < self._params['open_p'])]
        if signal_index_df_open.shape[0] == 0:
            open_trigger = 99999 if dir_ == 'long' else -99999
            return [open_trigger, 0]
        else:
            open_score = signal_index_df_open[:, 4] + signal_index_df_open[:, 0] * self._params['open_coef']
            open_idx = np.argmax(open_score)
            open_trigger = signal_index_df_open[open_idx, 2]
            open_percentile = signal_index_df_open[signal_index_df_open[:, 2] == open_trigger, 1][0]

        # 寻找平仓阈值
        signal_index_df_close = signal_data[(signal_data[:, 1] > max(self._params['close_p1'], open_percentile + 1)) &
                                            (signal_data[:, 1] < self._params['close_p2'])]
        dir_int = 1 if dir_ == 'long' else -1
        if signal_index_df_close.shape[0] == 0:
            close_trigger = 0
        else:
            close_score = signal_index_df_close[:, 4] + signal_index_df_close[:, 0] * self._params['close_coef']
            close_idx = np.argmax(close_score)
            close_trigger = signal_index_df_close[close_idx, 2]
        return [open_trigger, close_trigger + self._params['close_slip'] * dir_int]

    def get_params(self, overwrite_params):
        params = {'min_triggers': 5, 'open_p': 5, 'open_coef': -1.0, 'close_p1': 5, 'close_p2': 10, 'close_coef': 0.0, 'close_slip': 0}
        if self.strategy.startswith('Albest'):
            params.update({'close_slip': 0.2})
        if self.strategy.startswith('Everest'):
            params.update({'close_p1': 5, 'close_p2': 10, 'close_slip': 0})
        elif self.strategy == 'Kunlun':
            params.update({'open_coef': 0.2, 'close_p1': 10, 'close_p2': 20, 'close_coef': -0.8})

        if overwrite_params is not None:
            params.update(overwrite_params)
        return params

    def get_signal_data(self):
        date_list = self.get_date_list()
        signal_data = SignalManager(self.code, date_list, self.signal_lib, mock_lib=self.__mock_lib, vt_name=self.__vt_name,
                                    is_add_tag=True, is_get_valid=True, is_add_mock=self.__is_add_mock, tag_lib=self.__tag_lib).get_signal_dict()
        if len(signal_data) == 0:
            return pd.DataFrame(), []
        signal_data_df = pd.concat(signal_data, axis=0).dropna(axis=0)
        signal_data_df['tag_ave_long'] = signal_data_df[[f'tag{x}Long' for x in split_col_names(self.__vt_name)]].mean(axis=1)
        signal_data_df['tag_ave_short'] = -signal_data_df[[f'tag{x}Short' for x in split_col_names(self.__vt_name)]].mean(axis=1)
        date_list = list(sorted(set(date_list).intersection(set([x_[0] for x_ in signal_data_df.index]))))
        return signal_data_df, date_list

    def get_date_list(self):
        # 获取交易日的数据，剔除涨停/临停的交易日
        date_list_p = trading_day(trading_day_gap(self.st_date, -100), self.ed_date)
        if self.strategy in ['Albest', 'Everest']:
            sel_cols = ['D_Date', 'D_MaxPrice', 'D_MinPrice', 'D_HighPrice', 'D_LowPrice']
            data = load_lib_data(self.code, ['20200102'], 'ZeusDataLib', sel_cols).set_index('D_Date')
            data = data.loc[date_list_p]
            data = data[(data['D_HighPrice'] < data['D_MaxPrice']) & (data['D_LowPrice'] > data['D_MinPrice'])]
        elif self.strategy in ['Kunlun']:
            sel_cols = ['D_Date', 'D_HighPrice', 'D_LowPrice', 'D_PreviousClose']
            data = load_lib_data(self.code, ['20200102'], 'ZeusDataLib', sel_cols).set_index('D_Date')
            data = data.loc[date_list_p]
            data = data[(data['D_HighPrice'] < data['D_PreviousClose'] * 1.2) & (data['D_LowPrice'] > data['D_PreviousClose'] * 0.8)]
        else:
            raise ValueError
        date_array = np.array(data.index)
        date_list = []
        if len(date_array) > 0:
            if date_array[0] >= self.st_date:
                st_idx = 0
            else:
                st_idx = max(np.argwhere(date_array < self.st_date)[-1][-1] - self.n + 1, 0)
            date_list = list(date_array[st_idx:])
        return date_list


class Task:
    def __init__(self, code_list, st_date, ed_date, strategy, signal_lib,
                 save_path='lib', vt_name='8min', tag_lib=None, mock_lib=None, is_add_mock=False, overwrite_params=None):
        self.code_list = code_list
        self.st_date = st_date
        self.ed_date = ed_date
        self.strategy = strategy
        self.signal_lib = signal_lib
        self.save_path = save_path
        self.vt_name = vt_name
        self.tag_lib = tag_lib
        self.mock_lib = mock_lib
        self.is_add_mock = is_add_mock
        self.overwrite_params = overwrite_params

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
            signal_cv = SignalCV(self.st_date, self.ed_date, code, self.strategy, self.signal_lib, self.save_path, vt_name=self.vt_name, 
                                 tag_lib=self.tag_lib, mock_lib=self.mock_lib, is_add_mock=self.is_add_mock, overwrite_params=self.overwrite_params)
            signal_cv.start()

    def single_task_spark(self, context, code):
        try:
            dfs = context.get_hdfs()
            save_path_spark = self.save_path.replace('/data/user/', '')
            signal_cv = SignalCV(self.st_date, self.ed_date, code, self.strategy, self.signal_lib, save_path_spark, vt_name=self.vt_name,
                                 tag_lib=self.tag_lib, mock_lib=self.mock_lib, is_add_mock=self.is_add_mock, overwrite_params=self.overwrite_params,
                                 dfs=dfs)
            signal_cv.start()
        except:
            raise ValueError(f'{code}_{self.st_date}_{self.ed_date}')
