"""生成CV回测的阈值组合——update @2021.3.21 加入投票策略模块"""

import gc
import numpy as np
from DataAPI.DataView import load_pickle_file
from Manager.SignalManager import SignalManager
from Utils.UtilsCode import code_classify


class GenerateTriggers:
    def __init__(self, code, signal_lib, origin_data_dir, output_dir, cv_type, vt_name='8min', signal_col_names=None):
        self.code = code
        self.market = code_classify(code)  # 所属市场：stock, cb
        self.__signal_lib = signal_lib
        self.__origin_data_dir = origin_data_dir
        self.output_dir = output_dir

        self.__open_triggers = []
        self.__close_triggers = []
        self.__set_triggers()  # 设置搜索阈值
        self.__param_reduction = True  # 是否过滤无效阈值（根据信号分位数）
        self.__cv_type = cv_type  # "cv"为直接搜索参数，"cv_cross"为交叉验证搜索参数
        self.vt_name = vt_name
        self.signal_col_names = signal_col_names

    def __set_triggers(self):
        """设置搜索阈值"""
        if self.market == 'stock':
            self.__open_triggers = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 2.0]
            self.__close_triggers = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        elif self.market == 'cb':
            self.__open_triggers = [-1.0, -0.9, -0.8, -0.7, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5]
            self.__close_triggers = [-0.4, -0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]

    def generate_triggers_set(self):
        """生成阈值"""
        if self.__param_reduction:
            valid_dates = load_pickle_file(f'{self.__origin_data_dir}/{self.code}/Dates.pickle')
            valid_dates = sorted(list(map(str, valid_dates)))
            signal_manager = SignalManager(self.code, valid_dates, self.__signal_lib, vt_name=self.vt_name, signal_col_names=self.signal_col_names)
            signal_data = signal_manager.get_signals()
            if signal_data is None:
                return

            triggers_not_found = [{'longTriggerRatio': 999999, 'longCloseRatio': 0, 'longRiskRatio': -0.2,
                                   'shortTriggerRatio': -999999, 'shortCloseRatio': 0, 'shortRiskRatio': 0.2}]  # 没搜出来的用这个参数替代
            if self.__cv_type == 'cv':
                all_triggers = self.__my_param_reduction(signal_data)
                if not all_triggers:
                    all_triggers = triggers_not_found
                return {'triggers': all_triggers}
            elif self.__cv_type == 'cv_cross':
                signal_data_first, signal_data_second = signal_manager.get_signals_split()
                if signal_data_first is None or signal_data_second is None:
                    return
                first_all_triggers = self.__my_param_reduction(signal_data_first)
                second_all_triggers = self.__my_param_reduction(signal_data_second)

                if not first_all_triggers and second_all_triggers:
                    print("no first triggers cv: ", self.code)
                    first_all_triggers = second_all_triggers
                elif first_all_triggers and not second_all_triggers:
                    print("no second triggers cv: ", self.code)
                    second_all_triggers = first_all_triggers
                elif not first_all_triggers and not second_all_triggers:
                    print("no first & second triggers cv: ", self.code)
                    first_all_triggers = second_all_triggers = triggers_not_found
                return {'triggers_first': first_all_triggers, 'triggers_second': second_all_triggers}
            del signal_manager
            gc.collect()

        else:
            all_triggers = []
            for open_trigger in self.__open_triggers:
                for close_trigger in self.__close_triggers:
                    trigger_dict = {'longTriggerRatio': open_trigger, 'shortTriggerRatio': -open_trigger,
                                    'longCloseRatio': close_trigger, 'shortCloseRatio': -close_trigger,
                                    'longRiskRatio': close_trigger - 0.2, 'shortRiskRatio': -close_trigger + 0.2}
                    all_triggers.append(trigger_dict)
            if self.__cv_type == 'cv':
                return {'triggers': all_triggers}
            elif self.__cv_type == 'cv_cross':
                return {'triggers_first': all_triggers, 'triggers_second': all_triggers}

    def __my_param_reduction(self, signal_data):
        """根据分位数，过滤一些无效参数"""
        ave_long = signal_data['ave_long']
        ave_short = signal_data['ave_short']
        max_trigger = np.percentile(ave_long, 99.999)
        min_trigger = np.percentile(ave_long, 95)
        min_close = np.percentile(ave_short, 0.001)
        max_close_percentile = {'stock': 5, 'cb': 15}
        max_close = np.percentile(ave_short, max_close_percentile[self.market])

        all_triggers_dict = []
        for trigger_ratio in self.__open_triggers:
            for close_ratio in self.__close_triggers:
                if trigger_ratio > max_trigger or trigger_ratio < min_trigger:
                    continue
                if close_ratio > max_close or close_ratio < min_close:
                    continue
                if -close_ratio >= trigger_ratio:
                    continue
                inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
                              'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': -trigger_ratio,
                              'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
                all_triggers_dict.append(inner_dict)

        if self.market == 'cb' and not all_triggers_dict:
            open_triggers = [0, 0.1, 0.2, 0.3, 0.4, 0.5]
            close_triggers = [-0.4, -0.3, -0.2, -0.1, 0]
            max_trigger = np.percentile(ave_long, 99.9999)
            max_close = np.percentile(ave_short, 20)
            min_trigger_open = max(round(min_trigger, 1) - 0.1, 0.6)
            max_trigger_open = min(3.0, round(max_trigger, 1))
            min_trigger_close = max(-2.9, round(min_close, 1))
            max_trigger_close = min(round(max_close, 1) + 0.1, -0.5)
            if round(max_close, 1) < min(close_triggers):
                close_triggers = []
            if round(min_trigger, 1) > max(open_triggers):
                open_triggers = []
            start = min_trigger_open
            while start <= max_trigger_open:
                if start not in open_triggers:
                    open_triggers.append(start)
                start += 0.1

            start = min_trigger_close
            while start <= max_trigger_close:
                if start not in close_triggers:
                    close_triggers.append(start)
                start += 0.1
            for trigger_ratio in open_triggers:
                for close_ratio in close_triggers:
                    if trigger_ratio > max_trigger or trigger_ratio < min_trigger:
                        continue
                    if close_ratio > max_close or close_ratio < min_close:
                        continue
                    if -close_ratio >= trigger_ratio:
                        continue
                    inner_dict = {'longTriggerRatio': trigger_ratio, 'longCloseRatio': close_ratio,
                                  'longRiskRatio': close_ratio - 0.2, 'shortTriggerRatio': -trigger_ratio,
                                  'shortCloseRatio': -close_ratio, 'shortRiskRatio': -close_ratio + 0.2}
                    all_triggers_dict.append(inner_dict)
        return all_triggers_dict
