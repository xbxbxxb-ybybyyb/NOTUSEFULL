"""寻找最优的CV阈值组合——update @2021.2.22"""

import json
import numpy as np
import pandas as pd
from DataAPI.DataView import load_json_file, file_list_dir
from xquant.xqutils.xqfile import HDFSFile
from Utils.UtilsCode import code_classify


class FindBestTriggers:
    def __init__(self, code, output_dir, cv_type):
        self.code = code
        self.output_dir = output_dir
        self.cv_results_path = f'{output_dir}/cv_results'
        self.type = cv_type  # cv, cv_cross

        self.__param_result_mat = dict()
        self.__open_triggers = list()
        self.__close_triggers = list()

    def start(self, dfs=None):
        all_file = file_list_dir(self.cv_results_path)
        code_file_all = list(filter(lambda x: x.startswith(self.code), all_file))
        if len(code_file_all) == 0:
            return
        if self.type == 'cv':
            results_all = []
            for code_file in code_file_all:
                [result_all] = load_json_file(f'{self.cv_results_path}/{code_file}')
                results_all += result_all
            self.set_results_for_symbol(results_all)
            trigger_dict = self.find_best_param('all', dfs=dfs)
            best_open_trigger_first = trigger_dict['longTriggerRatio']
            best_close_trigger_first = trigger_dict['longCloseRatio']
            best_trigger_dict = self.__generate_trigger_dict(best_open_trigger_first, best_close_trigger_first)
            return [best_trigger_dict]
        elif self.type == 'cv_cross':
            results_first, results_second = [], []
            for code_file in code_file_all:
                [result_first, result_second] = load_json_file(f'{self.cv_results_path}/{code_file}')
                results_first += result_first
                results_second += result_second

            self.set_results_for_symbol(results_first)
            trigger_dict_first = self.find_best_param('first', dfs=dfs)
            best_open_trigger_first = trigger_dict_first['longTriggerRatio']
            best_close_trigger_first = trigger_dict_first['longCloseRatio']
            best_trigger_dict_first = self.__generate_trigger_dict(best_open_trigger_first, best_close_trigger_first)

            self.set_results_for_symbol(results_second)
            trigger_dict_second = self.find_best_param('second', dfs=dfs)
            best_open_trigger_second = trigger_dict_second['longTriggerRatio']
            best_close_trigger_second = trigger_dict_second['longCloseRatio']
            best_trigger_dict_second = self.__generate_trigger_dict(best_open_trigger_second, best_close_trigger_second)
            return [best_trigger_dict_first, best_trigger_dict_second]

    def set_results_for_symbol(self, results):
        open_triggers_list = sorted(list(set([result['longTriggerRatio'] for result in results])))
        close_triggers_list = sorted(list(set([result['longCloseRatio'] for result in results])))
        self.__open_triggers = open_triggers_list
        self.__close_triggers = close_triggers_list

        for key in ['annualReturnMV', 'averageTradingReturnRate', 'winRate', 'averagePositionTime', 'dayWinningRate', 'timesPerDay']:
            matrix = np.full((len(open_triggers_list), len(close_triggers_list)), np.nan)
            for result in results:
                open_index = open_triggers_list.index(result['longTriggerRatio'])
                close_index = close_triggers_list.index(result['longCloseRatio'])
                matrix[open_index, close_index] = result[key]
            self.__param_result_mat.update({key: matrix})

    def find_best_param(self, suffix=None, dfs=None):
        import warnings
        warnings.filterwarnings('ignore')
        best_param = self.__find_by_method()
        if self.output_dir is not None and suffix is not None:
            self.__output_param_mat(best_param, suffix, dfs=dfs)
            if 'condition' in best_param and best_param['condition'] == 'condition_rest':
                best_param = {'longTriggerRatio': 999999, 'longCloseRatio': 0, 'condition': 'condition_rest'}
        return best_param

    def __find_by_method(self):
        win_rate_mat = self.__param_result_mat['winRate']
        position_time_mat = self.__param_result_mat['averagePositionTime']
        day_winning_rate_mat = self.__param_result_mat['dayWinningRate']
        annual_return_mat = self.__param_result_mat['annualReturnMV']
        average_return_mat = self.__param_result_mat['averageTradingReturnRate']
        times_daily_mat = self.__param_result_mat['timesPerDay']

        win_rate_threshold = 0.45 if code_classify(self.code) == 'stock' else 0.40  # 胜率阈值
        day_winning_rate_threshold = 0.45  # 日胜率阈值
        annual_return_mask = annual_return_mat > 0
        if np.nansum(annual_return_mask) == 0:
            annual_return_mask = np.ones(annual_return_mask.shape) == 1
        position_time_threshold = np.nanmean(position_time_mat[annual_return_mask])
        position_time_threshold = max(min(35.0, float(position_time_threshold)), 12.0)  # 持仓时间阈值
        times_daily_threshold = np.nanmedian(times_daily_mat[annual_return_mask])  # 日均触发次数阈值

        position_time_condition = position_time_mat <= position_time_threshold
        win_rate_condition = win_rate_mat >= win_rate_threshold
        day_winning_rate_condition = day_winning_rate_mat >= day_winning_rate_threshold
        times_daily_condition = times_daily_mat >= times_daily_threshold

        if np.nanmax(np.abs(annual_return_mat)) > 0:
            annual_return_score = annual_return_mat / np.nanmax(np.abs(annual_return_mat))
        else:
            annual_return_score = np.zeros(annual_return_mat.shape, np.float32)
        if np.nanmax(np.abs(average_return_mat)) > 0:
            average_return_score = average_return_mat / np.nanmax(np.abs(average_return_mat))
            times_daily_weight = times_daily_mat / np.nanmax(times_daily_mat)
            average_return_score = times_daily_weight * average_return_score / np.nansum(times_daily_weight * average_return_score)
        else:
            average_return_score = np.zeros(average_return_mat.shape, np.float32)
        total_score = annual_return_score + average_return_score

        condition1 = win_rate_condition & day_winning_rate_condition & times_daily_condition & position_time_condition & annual_return_mask
        condition2 = day_winning_rate_condition & times_daily_condition & position_time_condition & annual_return_mask
        condition3 = day_winning_rate_condition & position_time_condition & annual_return_mask
        condition4 = day_winning_rate_condition & annual_return_mask
        condition5 = annual_return_mat > 0

        if condition1.any():
            best_index = self.__my_best_index(condition1, total_score)
            text = 'condition_1'
        elif condition2.any():
            best_index = self.__my_best_index(condition2, total_score)
            text = 'condition_2'
        elif condition3.any():
            best_index = self.__my_best_index(condition3, total_score)
            text = 'condition_3'
        elif condition4.any():
            best_index = self.__my_best_index(condition4, total_score)
            text = 'condition_4'
        elif condition5.any():
            best_index = self.__my_best_index(condition5, total_score)
            text = 'condition_5'
        else:
            condition = ~np.isnan(annual_return_mat)
            best_index = self.__my_best_index(condition, total_score)
            text = 'condition_rest'

        return {'longTriggerRatio': self.__open_triggers[best_index[0]],
                'longCloseRatio': self.__close_triggers[best_index[1]], 'condition': text}

    def __output_param_mat(self, best_param, suffix, dfs):
        best_open_index = self.__open_triggers.index(best_param['longTriggerRatio'])
        best_close_index = self.__close_triggers.index(best_param['longCloseRatio'])
        best_value_dict = {}
        temp = {}
        for key in self.__param_result_mat.keys():
            best_value = self.__param_result_mat[key][best_open_index, best_close_index]
            data = pd.DataFrame(self.__param_result_mat[key], index=self.__open_triggers, columns=self.__close_triggers)
            temp.update({key: data})
            best_value_dict.update({key: best_value})
        py = HDFSFile(dfs=dfs)
        xls_dir = '{}/{}/selection_from_{}.xlsx'.format(self.output_dir, self.code, suffix)
        if py.exists(xls_dir):
            py.delete(xls_dir)
        with py.open(xls_dir, 'wb') as f:
            writer = pd.ExcelWriter(f, engine='xlsxwriter')
            bold_format = writer.book.add_format({'bold': True})
            for key in temp.keys():
                temp[key].to_excel(writer, sheet_name=key)
                writer.sheets[key].conditional_format(1, 1, len(self.__open_triggers), len(self.__close_triggers), {'type': '3_color_scale'})
                writer.sheets[key].write(0, 0, 'open_thresholds\\close_thresholds')
                writer.sheets[key].write(best_open_index + 1, best_close_index + 1, best_value_dict[key], bold_format)
            writer.save()
        if 'condition' in best_param:
            file_name = '{}/{}/condition_from_{}.json'.format(self.output_dir, self.code, suffix)
            if py.exists(file_name):
                py.delete(file_name)
            with py.open(file_name, 'wb') as f:
                json.dump(best_param['condition'], f)

    @staticmethod
    def __my_best_index(condition, total_score):
        index = np.nonzero(condition)
        valid = total_score[index]
        max_index = np.nanargmax(valid)
        return index[0][max_index], index[1][max_index]

    @staticmethod
    def __generate_trigger_dict(open_trigger, close_trigger):
        trigger_dict = {'longTriggerRatio': open_trigger, 'shortTriggerRatio': -open_trigger,
                        'longCloseRatio': close_trigger, 'shortCloseRatio': -close_trigger,
                        'longRiskRatio': close_trigger - 0.2, 'shortRiskRatio': -close_trigger + 0.2}
        return trigger_dict
