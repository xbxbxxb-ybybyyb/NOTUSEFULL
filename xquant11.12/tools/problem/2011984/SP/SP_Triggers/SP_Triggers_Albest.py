"""实盘Albest策略动态阈值生成程序"""

import os
import json
import shutil
import datetime
import numpy as np
import pandas as pd
from itertools import combinations
from xquant.factordata import FactorData
from xquant.xqutils.xqfile import HDFSFile


def main():
    mode = 'multi_processing'  # local, multi_processing
    trade_date = datetime.datetime.now().strftime("%Y%m%d")
    # trade_date = '20220301'
    user_id = '011668'
    code_select = []
    code_select += pd.read_excel(f'/data/user/011477/order/T0/T0_CV_Split/{trade_date}/{trade_date}_easy.xlsx')['证券代码'].to_list()
    code_select = list(sorted(set(code_select)))

    code_select_sh = [x for x in code_select if x.endswith('.SH')]
    signal_lib_sh = 'ray_albest_20220201_20220414_new'
    save_path_sh = f'/data/user/{user_id}/CVTriggers/SPTriggers/Albest/{trade_date}/{signal_lib_sh}'
    time_list = ['10:00:00']
    while len(code_select_sh) > 0:
        print(f'{len(code_select_sh)}只上海标的需要计算')
        Task(code_select_sh, trade_date, trade_date, 'Albest', signal_lib_sh, save_path_sh, time_list=time_list).start(mode=mode)
        code_select_sh = list(sorted(set(code_select_sh) - set([x[:-5] for x in file_list_dir(save_path_sh)])))

    code_select_sz = [x for x in code_select if x.endswith('.SZ')]
    signal_lib_sz = 'ray_albest_20211101_20211116_order'
    save_path_sz = f'/data/user/{user_id}/CVTriggers/SPTriggers/Albest/{trade_date}/{signal_lib_sz}'
    time_list = ['10:00:00']
    while len(code_select_sz) > 0:
        print(f'{len(code_select_sz)}只深圳标的需要计算')
        Task(code_select_sz, trade_date, trade_date, 'Albest', signal_lib_sz, save_path_sz, time_list=time_list).start(mode=mode)
        code_select_sz = list(sorted(set(code_select_sz) - set([x[:-5] for x in file_list_dir(save_path_sz)])))


class SignalCV:
    def __init__(self, st_date, ed_date, code, strategy, signal_lib, save_path='lib', time_list=None, vt_name='8min', dfs=None):
        self.st_date = st_date
        self.ed_date = ed_date
        self.code = code
        self.strategy = strategy
        self.signal_lib = signal_lib
        self.n = 10  # 过去N日
        if time_list is not None:
            self.__time_list = ['09:30:00'] + list(sorted(time_list)) + ['15:00:00']
        else:
            self.__time_list = ['09:30:00', '15:00:00']
        self.__vt_name = vt_name
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
            signal_data_df_select = signal_data_df.loc[trade_date]
            long_trigger_ratio = self.select_best_triggers(signal_data_df_select, dir_='long', min_triggers=5)
            short_trigger_ratio = self.select_best_triggers(signal_data_df_select, dir_='short', min_triggers=5)
            trigger_ratio_by_date.update({trade_date: long_trigger_ratio + short_trigger_ratio})

            if self.__time_list is not None:
                for i in range(len(self.__time_list) - 1):
                    signal_data_df_select_i = signal_data_df_select[(signal_data_df_select['Ticktime'] > self.__time_list[i]) &
                                                                    (signal_data_df_select['Ticktime'] <= self.__time_list[i + 1])]
                    long_trigger_ratio_i = self.select_best_triggers(signal_data_df_select_i, dir_='long')
                    short_trigger_ratio_i = self.select_best_triggers(signal_data_df_select_i, dir_='short')
                    trigger_ratio_by_date.update({f'{trade_date}_{self.__time_list[i]}': long_trigger_ratio_i + short_trigger_ratio_i})
        trigger_ratio_by_date_df = pd.DataFrame(trigger_ratio_by_date).T

        trigger_ratio_all_date = dict()
        all_date_list = FactorData().tradingday(self.st_date, self.ed_date)
        for trade_date in all_date_list:
            select_date_list = []
            if len(valid_date_list) != 0:
                if trade_date <= valid_date_list[0]:
                    trigger_dict = {'longTriggerRatio': 99999, 'shortTriggerRatio': -99999, 'longCloseRatio': 0, 'shortCloseRatio': 0,
                                    'longRiskRatio': -0.2, 'shortRiskRatio': 0.2}
                    trigger_ratio_single_date = {trade_date: trigger_dict}
                    for i in range(len(self.__time_list) - 1):
                        trigger_ratio_single_date.update({f'{trade_date}_{self.__time_list[i]}': trigger_dict})
                    trigger_ratio_all_date.update(trigger_ratio_single_date)
                    if self.save_path == 'lib':
                        trigger_fa = pd.DataFrame({self.signal_lib: trigger_ratio_single_date})
                        self.fa.update_factor_value('DynamicTriggers', trigger_fa, self.code, trade_date)
                    continue
                ed_idx = np.argwhere(np.array(valid_date_list) < trade_date)[-1][-1] + 1
                select_date_list = valid_date_list[:ed_idx][-self.n:]
                if max(select_date_list) >= trade_date:
                    raise ValueError('！！！存在未来数据，请检查')
            trigger_dict = self.get_trigger_ratio(trigger_ratio_by_date_df, select_date_list)
            trigger_ratio_single_date = {trade_date: trigger_dict}
            for i in range(len(self.__time_list) - 1):
                trigger_dict_i = self.get_trigger_ratio(trigger_ratio_by_date_df, select_date_list, s=f'_{self.__time_list[i]}')
                trigger_ratio_single_date.update({f'{trade_date}_{self.__time_list[i]}': trigger_dict_i})
            if self.save_path == 'lib':
                trigger_fa = pd.DataFrame({self.signal_lib: trigger_ratio_single_date})
                self.fa.update_factor_value('DynamicTriggers', trigger_fa, self.code, trade_date)
            else:
                trigger_ratio_all_date.update(trigger_ratio_single_date)
        if self.save_path != 'lib':
            save_json_file(trigger_ratio_all_date, f'{self.save_path}/{self.code}.json', dfs=self.dfs)
        print('Finish ', self.code)

    @staticmethod
    def get_trigger_ratio(trigger_ratio_by_date_df, select_date_list, s=''):
        if len(select_date_list) < 5:
            long_trigger_ratio, short_close_ratio, short_trigger_ratio, long_close_ratio = 99999, 0, -99999, 0
        else:
            trigger_ratio_select_df = trigger_ratio_by_date_df.loc[[x + s for x in select_date_list]]
            long_trigger_ratio = trigger_ratio_select_df[0].sort_values().values[1:-1].mean()
            short_close_ratio = trigger_ratio_select_df[1].sort_values().values[1:-1].mean()
            short_trigger_ratio = trigger_ratio_select_df[2].sort_values().values[1:-1].mean()
            long_close_ratio = trigger_ratio_select_df[3].sort_values().values[1:-1].mean()
        trigger_dict = {'longTriggerRatio': long_trigger_ratio, 'shortTriggerRatio': short_trigger_ratio,
                        'longCloseRatio': long_close_ratio, 'shortCloseRatio': short_close_ratio,
                        'longRiskRatio': long_close_ratio - 0.2, 'shortRiskRatio': short_close_ratio + 0.2}
        return trigger_dict

    def select_best_triggers(self, signal_data_df_select, dir_, min_triggers=1):
        if signal_data_df_select.empty:
            return [99999.0, 0.0] if dir_ == 'long' else [-99999.0, 0.0]

        triggers = signal_data_df_select[f'ave_{dir_}'].values
        tag_ave = signal_data_df_select[f'tag_ave_{dir_}'].values
        sort_idx = triggers.argsort()[::-1] if dir_ == 'long' else triggers.argsort()
        triggers, tag_ave = triggers[sort_idx], tag_ave[sort_idx]
        count = np.arange(1, len(triggers) + 1)
        percentile = count / len(triggers) * 100
        ret_cumsum = np.cumsum(tag_ave)
        signal_data = np.array([count, percentile, triggers, tag_ave, ret_cumsum]).T

        params = {'min_triggers': min_triggers, 'open_p': 5, 'open_coef': -1.0, 'close_p1': 5, 'close_p2': 10, 'close_coef': 0.0, 'close_slip': 0}
        if self.strategy == 'Albest':
            params.update({'close_slip': 0.2})
        elif self.strategy == 'Kunlun':
            params.update({'open_coef': 0.2, 'close_p1': 10, 'close_p2': 20, 'close_coef': -0.8})

        # 寻找开仓阈值
        signal_index_df_open = signal_data[(signal_data[:, 0] >= params['min_triggers']) & (signal_data[:, 1] < params['open_p'])]
        if signal_index_df_open.shape[0] == 0:
            open_trigger = 99999 if dir_ == 'long' else -99999
            return [open_trigger, 0]
        else:
            open_score = signal_index_df_open[:, 4] + signal_index_df_open[:, 0] * params['open_coef']
            open_idx = np.argmax(open_score)
            open_trigger = signal_index_df_open[open_idx, 2]
            open_percentile = signal_index_df_open[signal_index_df_open[:, 2] == open_trigger, 1][0]

        # 寻找平仓阈值
        signal_index_df_close = signal_data[(signal_data[:, 1] > max(params['close_p1'], open_percentile + 1)) &
                                            (signal_data[:, 1] < params['close_p2'])]
        dir_int = 1 if dir_ == 'long' else -1
        if signal_index_df_close.shape[0] == 0:
            close_trigger = 0
        else:
            close_score = signal_index_df_close[:, 4] + signal_index_df_close[:, 0] * params['close_coef']
            close_idx = np.argmax(close_score)
            close_trigger = signal_index_df_close[close_idx, 2]
        return [open_trigger, close_trigger + params['close_slip'] * dir_int]

    def get_signal_data(self):
        date_list = self.get_date_list()
        signal_data = SignalManager(self.code, date_list, self.signal_lib, vt_name=self.__vt_name,
                                    is_add_tag=True, is_get_valid=True, is_add_mock=False).get_signal_dict()
        if len(signal_data) == 0:
            return pd.DataFrame(), []
        signal_data_df = pd.concat(signal_data, axis=0).dropna(axis=0)
        signal_data_df['tag_ave_long'] = signal_data_df[[f'tag{x}Long' for x in split_col_names(self.__vt_name)]].mean(axis=1)
        signal_data_df['tag_ave_short'] = -signal_data_df[[f'tag{x}Short' for x in split_col_names(self.__vt_name)]].mean(axis=1)
        date_list = list(sorted(set(date_list).intersection(set([x_[0] for x_ in signal_data_df.index]))))
        return signal_data_df, date_list

    def get_date_list(self):
        # 获取交易日的数据，剔除涨停/临停的交易日
        fa = FactorData()
        date_list_p = fa.tradingday(fa.tradingday(self.st_date, -100)[0], self.ed_date)
        if self.strategy in ['Albest', 'Everest']:
            sel_cols = ['D_Date', 'D_MaxPrice', 'D_MinPrice', 'D_HighPrice', 'D_LowPrice']
            data = load_lib_data(self.code, ['20200102'], 'ZeusDataLib', sel_cols).set_index('D_Date')
            data = data.loc[date_list_p]
            data = data[(data['D_HighPrice'] < data['D_MaxPrice']) & (data['D_LowPrice'] > data['D_MinPrice']) &
                        (data['D_HighPrice'] > data['D_LowPrice'])]
        elif self.strategy in ['Kunlun']:
            sel_cols = ['D_Date', 'D_HighPrice', 'D_LowPrice', 'D_PreviousClose']
            data = load_lib_data(self.code, ['20200102'], 'ZeusDataLib', sel_cols).set_index('D_Date')
            data = data.loc[date_list_p]
            data = data[(data['D_HighPrice'] < data['D_PreviousClose'] * 1.2) & (data['D_LowPrice'] > data['D_PreviousClose'] * 0.8) &
                        (data['D_HighPrice'] > data['D_LowPrice'])]
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
    def __init__(self, code_list, st_date, ed_date, strategy, signal_lib, save_path='lib', time_list=None, vt_name='8min'):
        self.code_list = code_list
        self.st_date = st_date
        self.ed_date = ed_date
        self.strategy = strategy
        self.signal_lib = signal_lib
        self.save_path = save_path
        self.vt_name = vt_name
        self.time_list = time_list

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
            signal_cv = SignalCV(self.st_date, self.ed_date, code, self.strategy, self.signal_lib, self.save_path,
                                 time_list=self.time_list, vt_name=self.vt_name)
            signal_cv.start()

    def single_task_spark(self, context, code):
        dfs = context.get_hdfs()
        save_path_spark = self.save_path.replace('/data/user/', '')
        signal_cv = SignalCV(self.st_date, self.ed_date, code, self.strategy, self.signal_lib, save_path_spark,
                             time_list=self.time_list, vt_name=self.vt_name, dfs=dfs)
        signal_cv.start()


class SignalManager:
    def __init__(self, code, date_list, signal_lib, vt_name='8min', signal_col_names=None,
                 is_add_tag=False, is_get_valid=False, is_add_mock=True):
        # signal_col_names为制定输出的列明（None为输出ave_long和ave_short
        # is_add_tag为是否输出结果加入tag列，默认False为不加入
        # is_get_valid为是否剔除午盘（11:25-11:30）和尾盘（14:50-15:00）数据，默认False为不剔除
        # is_add_mock为是否加入补的tick数据，默认True为包括
        self.__code = code
        self.__date_list = date_list
        self.__signal_lib = signal_lib
        self.__vt_name = vt_name
        self.__signal_col_names = ['Timestamp', 'ave_long', 'ave_short'] if signal_col_names is None else signal_col_names
        if is_add_tag:
            self.__signal_col_names += ['tag1minLong', 'tag2minLong', 'tag5minLong', 'tag1minShort', 'tag2minShort', 'tag5minShort']
        self.__is_add_tag = is_add_tag  # 是否加入tag数据
        self.__is_add_mock = is_add_mock  # 是否加入补的tick数据
        self.__is_add_sec = float(self.__vt_name[:-3]) % 1 in [0.25, 0.5, 0.75]  # 是否加入秒频（15s和30s）信号预测值
        self.__valid_date_list, self.__signal_data_list = self.__load_signal_data(is_get_valid)

    def __load_signal_data(self, is_get_valid):
        signal_data_list = []
        valid_date_list = []
        for trade_date in self.__date_list:
            fa = FactorData()
            try:
                prediction_names = ['timestamp', 'ticktime', 'prediction1minLong', 'prediction2minLong', 'prediction5minLong',
                                    'prediction1minShort', 'prediction2minShort', 'prediction5minShort']
                if self.__is_add_sec:
                    # prediction_names += ['prediction15secLongAll', 'prediction15secShortAll', 'prediction30secLongAll', 'prediction30secShortAll']
                    prediction_names += ['prediction15secLong', 'prediction15secShort', 'prediction30secLong', 'prediction30secShort']
                data = fa.get_factor_value(self.__signal_lib, self.__code, trade_date, prediction_names)
                rename_dict = {'timestamp': 'Timestamp', 'ticktime': 'Ticktime'}
                rename_dict.update(dict([(x, x.replace('prediction', '').replace('All', '')) for x in prediction_names[2:]]))
                data = data.rename(columns=rename_dict)

                column_long = data[[x + 'Long' for x in split_col_names(self.__vt_name)]].mean(axis=1)
                data = data.assign(ave_long=column_long)
                column_short = data[[x + 'Short' for x in split_col_names(self.__vt_name)]].mean(axis=1)
                data = data.assign(ave_short=column_short)

                if is_get_valid:
                    data = data[(('09:30:00' < data['Ticktime']) & (data['Ticktime'] < '11:25:00')) |
                                ('13:00:00' < data['Ticktime']) & (data['Ticktime'] < '14:50:00')]
                elif code_classify(self.__code) != 'cb' and self.__vt_name == '8min':
                    data = self.average_special_time(data, '11:25:00', '11:28:00', '11:30:00')
                    data = self.average_special_time(data, '14:52:00', '14:55:00', '14:57:00')

                if self.__is_add_tag:
                    tag_names = ['timestamp'] + [x.replace('prediction', 'tag').replace('All', '')
                                                 for x in prediction_names if x.startswith('prediction')]
                    tag_lib = 'Factor_Zeus_Plus' if code_classify(self.__code) != 'cb' else 'CBFactor_Zeus_Super'
                    data_tag = fa.get_factor_value(tag_lib, self.__code, trade_date, tag_names).rename(columns={'timestamp': 'Timestamp'})
                    if self.__is_add_mock:
                        data = pd.concat([data.set_index('Timestamp'), data_tag.set_index('Timestamp') * 1000], axis=1).reset_index()
                    else:  # 剔除补的数据
                        data2 = fa.get_factor_value('ZeusDataLib', self.__code, trade_date, ['T_Timestamp', 'T_IsMock']). \
                            rename(columns={'T_Timestamp': 'Timestamp'}).set_index('Timestamp')
                        data = pd.concat([data.set_index('Timestamp'), data_tag.set_index('Timestamp') * 1000, data2], axis=1).reset_index()
                        data = data[data['T_IsMock'] == 0]
                valid_date_list.append(trade_date)
                signal_data_list.append(data)
            except:
                continue
        return valid_date_list, signal_data_list

    @staticmethod
    def average_special_time(data, time1, time2, time3):
        """临近午盘和尾盘收盘时的信号平均特殊处理"""
        filter1 = (data['Ticktime'] >= time1) & (data['Ticktime'] < time2)
        index1 = data.loc[filter1, 'Ticktime'].index
        ave_long1 = (data.loc[index1, '1minLong'] + data.loc[index1, '2minLong']) / 2
        ave_short1 = (data.loc[index1, '1minShort'] + data.loc[index1, '2minShort']) / 2
        data.loc[index1, 'ave_long'] = ave_long1
        data.loc[index1, 'ave_short'] = ave_short1

        filter2 = (data['Ticktime'] >= time2) & (data['Ticktime'] < time3)
        index2 = data.loc[filter2, 'Ticktime'].index
        ave_long2 = data.loc[index2, '1minLong']
        ave_short2 = data.loc[index2, '1minShort']
        data.loc[index2, 'ave_long'] = ave_long2
        data.loc[index2, 'ave_short'] = ave_short2
        return data

    def get_signals(self):
        if len(self.__signal_data_list) > 0:
            signals = pd.concat(self.__signal_data_list, axis=0)[self.__signal_col_names].dropna(axis=0)
            signals.index = range(signals.shape[0])
            return signals

    def get_signals_split(self):
        if len(self.__signal_data_list) > 1:
            half = int(len(self.__signal_data_list) / 2)
            signals_first = pd.concat(self.__signal_data_list[:half], axis=0)[self.__signal_col_names]
            signals_second = pd.concat(self.__signal_data_list[half:], axis=0)[self.__signal_col_names]
            return signals_first, signals_second
        else:
            return None, None

    def get_signal_dict(self):
        # 获取按天来汇总的信号矩阵（输出为字典，key为日期，value为当日的信号矩阵）
        return dict(zip(self.__valid_date_list, self.__signal_data_list))


def load_lib_data(code, all_trading_days, signal_lib, columns):
    """原始tick行情数据库为：ZeusDataLib"""
    fa = FactorData()
    all_data = []
    for trade_date in all_trading_days:
        try:
            data = fa.get_factor_value(signal_lib, code, str(trade_date), columns)
            all_data.append(data)
        except:
            print("no signal data for {} in date {} in library {}".format(code, trade_date, signal_lib))
            continue
    if len(all_data) > 0:
        return pd.concat(all_data)
    return pd.DataFrame()


def transfer_file(hdfs_dir, nas_dir):
    from xquant.xqutils.xqfile import Pyfile
    if os.path.exists(nas_dir):
        shutil.rmtree(nas_dir)
    os.makedirs(nas_dir, exist_ok=True)
    Pyfile().download(nas_dir, hdfs_dir)


def get_split_params(all_params, process_nums):
    split_params = list()
    for i in range(process_nums):
        split_params.append([])
    for j in range(len(all_params)):
        split_params[j % process_nums].append(all_params[j])
    return split_params


def main_multiprocess(task_single, para_list, multiprocess_nums=1, is_sum_result=True):
    multiprocess_nums = min(len(para_list), multiprocess_nums)
    if multiprocess_nums > 1:  # 并行化运算
        import multiprocessing as mp
        print('MultiProcess Starts: {} Multi Tasks'.format(multiprocess_nums))
        split_params_all = get_split_params(para_list, multiprocess_nums)
        pool = mp.Pool(processes=multiprocess_nums)
        multi_process_result = []
        for split_params in split_params_all:
            result = pool.apply_async(task_single, [split_params], )
            multi_process_result.append(result)
        pool.close()
        pool.join()
        if is_sum_result:
            summary_result = []
            for kk in multi_process_result:
                summary_result_single = kk.get()
                summary_result.append(summary_result_single)
            return summary_result
    else:  # 非并行化运算
        summary_result = task_single(para_list)
        if is_sum_result:
            return summary_result


def main_spark(task_single, para_list, multiprocess_nums=600):
    multiprocess_nums = min(len(para_list), multiprocess_nums, 600)
    if multiprocess_nums > 1:
        from QuantFramework import Job
        from QuantFramework import Configuration
        config = Configuration()
        config.set_app_name('_BackTest')
        config.set_dst_dir('tmp')
        config.set_env_dir('/home/appadmin/HFTrading')
        config.set_executor_instances(str(multiprocess_nums))
        config.set_executor_memory('4G')
        job = Job(config, 'Overwrite')
        job.add_tasks(para_list)
        job.set_func(task_single)
        job.start()
    else:
        for para in para_list:
            task_single('', para)


def get_voting_dict(all_tags):
    res_dict = {}
    for i in range(1, len(all_tags) + 1):
        c_ = list(combinations(all_tags, i))
        for c_sub in c_:
            res_dict.update({sum(c_sub): list(c_sub)})
    return res_dict


def split_col_names(vt_name='8min'):
    voting_dict = get_voting_dict([0.25, 0.5, 1, 2, 5])
    col_list = voting_dict[float(vt_name[:-3])]
    out_col_list = []
    for i in col_list:
        if i in [0.25, 0.5]:
            out_col_list.append(f'{int(i * 60)}sec')
        else:
            out_col_list.append(f'{i}min')
    return out_col_list


def code_classify(code):
    """判定股票所属的类别（股票/可转债）"""
    if code.startswith('1'):
        return "cb"
    elif code.startswith('0') or code.startswith('3') or code.startswith('6'):
        return 'stock'
    else:
        raise ValueError


def save_json_file(data, file_name, dfs=None):
    if file_name.startswith('/data/user/'):  # NFS
        with open(file_name, 'w') as f:
            json.dump(data, f)
    else:
        py = HDFSFile(dfs)
        with py.open(file_name, 'wb') as f:  # HDFS
            json.dump(data, f)


def make_dir(file_dir, dfs=None):
    if file_dir.startswith('/data/user/'):  # NFS
        os.makedirs(file_dir, exist_ok=True)
    else:  # HDFS
        py = HDFSFile(dfs)
        py.mkdir(file_dir)


def file_list_dir(file_dir, dfs=None):
    if file_dir.startswith('/data/user/'):  # NFS
        return os.listdir(file_dir)
    else:  # HDFS
        py = HDFSFile(dfs)
        return py.listdir(file_dir)


if __name__ == '__main__':
    main()
