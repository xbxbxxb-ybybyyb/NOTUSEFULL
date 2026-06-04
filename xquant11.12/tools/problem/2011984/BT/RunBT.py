"""bt回测的main函数——update @2021.12.1"""

import os
from Analyzer.BTAnalyzer.AnalyzeBTResult import AnalyzeResult
from BT.BT_System.CombineData import CombineData, check_non_existing_codes
from BT.BT_System.CombineParams import CombineParams
from DataAPI.ARootPath import get_asset_class
from Manager.InputManager import InputManager
from Utils.MultiTasks import main_spark, main_multiprocess


class RunBT:
    def __init__(self, strategy_params, mode, bt_type='bt', max_tasks=600):
        self.strategy_params = strategy_params
        self.mode = mode  # spark, local
        self.type = bt_type  # sp, bt
        self.max_tasks = max_tasks
        self.__is_transfer_file = False  # 是否将文件从HDFS移动到NAS上
        self.__is_classify_res = False  # 是否分层统计结果（多空统计，按板块统计）

    def start_bt(self):
        task_metas = self.generate_task_metas()
        print(f'Start BT: {len(task_metas)} tasks'.center(60, '*'))
        self.run_main(task_metas, single_task_separate)

    def run_main(self, task_metas, single_task_func):
        if self.mode == 'local':
            total_len = len(task_metas)
            for i, input_manager in enumerate(task_metas):
                single_task_func('', input_manager)
                print('Finish: {}/{} - {}'.format(i + 1, total_len, input_manager.code))
        elif self.mode == 'spark':
            main_spark(single_task_func, task_metas, self.max_tasks)

    def combine_data_and_params(self, multi_process_nums=20):
        self.combine_data(multi_process_nums)
        self.combine_params()

    def combine_data(self, multi_process_nums=20):
        print('Start Combine Data'.center(60, '*'))
        combine_data_params = dict()
        for single_strategy_param in self.strategy_params:
            if single_strategy_param['freq'] == '1s':  # 1s频策略不需要combine data
                continue
            portfolio = single_strategy_param['portfolio']
            if self.type == 'sp':
                data_dir_map = {'Albest_sp': 'stock_sp', 'Everest_sp': 'stock_sp',
                                'Kunlun_mix': 'cb_sp', 'Kunlun_pure': 'cb_sp',
                                'Albest_sp_l2p': 'stock_sp_l2p', 'Everest_sp_l2p': 'stock_sp_l2p',
                                'Kunlun_mix_l2p': 'cb_sp_l2p', 'Kunlun_pure_l2p': 'cb_sp_l2p',
                                'Kunlun_SHJS_mix': 'cb_sp', 'Kunlun_SHJS_pure': 'cb_sp',
                                }
                data_name = data_dir_map[portfolio]
            else:
                data_name = portfolio
            bt_date = single_strategy_param['st_date'] + '-' + single_strategy_param['ed_date']
            code_list = list(single_strategy_param['code_vol_dict'].keys())
            key_name = f'{data_name}-{bt_date}'
            if key_name in combine_data_params.keys():
                code_list = list(set(code_list + combine_data_params[key_name]))
            combine_data_params.update({key_name: code_list})
        if self.type == 'sp':
            for key_name, code_list in combine_data_params.items():
                data_name, st_date, ed_date = key_name.split('-')
                check_non_existing_codes(code_list, st_date, data_name)
        for key_name, code_list in combine_data_params.items():
            data_name, st_date, ed_date = key_name.split('-')
            is_calc_vol_limit = False  # 是否计算OrderCapacity和HighVolume
            if self.type == 'sp' or get_asset_class(data_name) == 'cb':  # 实盘不用计算，转债策略不用计算
                is_calc_vol_limit = False

            CombineData(data_name, code_list, st_date, ed_date, is_calc_vol_limit).start(multi_process_nums=multi_process_nums)

    def combine_params(self):
        print('Start Combine Params'.center(60, '*'))
        for single_strategy_param in self.strategy_params:
            portfolio = single_strategy_param['portfolio']
            st_date = single_strategy_param['st_date']
            ed_date = single_strategy_param['ed_date']
            code_vol_dict = single_strategy_param['code_vol_dict']
            param_dir_bt = single_strategy_param['param_dir_bt']
            output_dir = single_strategy_param['output_dir']
            origin_param_dir = single_strategy_param['param_dir']
            if self.type == 'sp':
                is_vt = 'Voting' in single_strategy_param['executor_str']
                CombineParams(portfolio, code_vol_dict, st_date, ed_date, param_dir_bt, output_dir, origin_param_dir).params_sp(is_vt)
            elif self.type == 'bt':
                CombineParams(portfolio, code_vol_dict, st_date, ed_date, param_dir_bt, output_dir, origin_param_dir).params_bt()
            elif self.type == 'bt_voting':
                CombineParams(portfolio, code_vol_dict, st_date, ed_date, param_dir_bt, output_dir, origin_param_dir).params_bt_voting()

    def analyze_result(self, is_transfer_file=False, is_classify_res=False, multiprocess_nums=1):
        self.__is_transfer_file = is_transfer_file
        self.__is_classify_res = is_classify_res
        print('Start Analyze Results'.center(60, '*'))
        all_output_dir = [x['output_dir'] for x in self.strategy_params]
        all_output_dir = list(sorted(set(all_output_dir)))
        main_multiprocess(self.single_task_analyzer, all_output_dir, multiprocess_nums, False)

    def single_task_analyzer(self, output_dir_list):
        for output_dir in output_dir_list:
            if self.__is_transfer_file:
                AnalyzeResult(output_dir).transfer_file()  # 将文件从HDFS上传到NAS上
            AnalyzeResult(output_dir).analyze(is_classify=self.__is_classify_res)
            print(f'Finish: /data/user/011668/{output_dir}')

    def generate_task_metas(self):
        task_metas = []
        for single_strategy_param in self.strategy_params:
            code_vol_dict = single_strategy_param['code_vol_dict']
            st_date = single_strategy_param['st_date']
            ed_date = single_strategy_param['ed_date']
            executor_str = single_strategy_param['executor_str']
            trigger_lib = single_strategy_param['trigger_lib']
            freq = single_strategy_param['freq']
            dir_path = single_strategy_param['dir_path']
            overwrite_params = single_strategy_param['overwrite_params']
            overwrite_params_by_code = single_strategy_param['overwrite_params_by_code']
            for code in list(code_vol_dict.keys()):
                overwrite_params_code = overwrite_params.copy()
                if len(overwrite_params_by_code) > 0 and code in overwrite_params_by_code.keys():
                    overwrite_params_code.update(overwrite_params_by_code[code])

                input_manager = InputManager(code, st_date, ed_date, executor_str, dir_path, overwrite_params_code,
                                             single_strategy_param['bt_type'], freq=freq, trigger_lib=trigger_lib)
                task_metas.append(input_manager)
        return task_metas


def single_task_separate(context, input_manager):
    """单个task_meta的bt回测程序"""
    print(input_manager.code)
    is_executor = "RPC_DRIVER_HOST" in os.environ and "RPC_DRIVER_PORT" in os.environ
    dfs = context.get_hdfs() if is_executor else None

    input_manager.load_param_dict(dfs=dfs)
    code = input_manager.code
    params_dict = input_manager.params_dict
    if len(params_dict) == 0:
        print('No Params for ' + code)
        return

    input_manager.load_origin_data(dfs=dfs)
    tick_data = input_manager.tick_data
    transaction_data = input_manager.transaction_data
    tick_dict = input_manager.tick_dict
    tick_dict_freq = input_manager.tick_dict_freq
    pre_close_dict = input_manager.pre_close_dict
    if tick_data is None or len(tick_data) == 0:
        print('No Origin Data for ' + code)
        return

    input_manager.load_signal_data()
    signal_data = input_manager.signal_data
    if signal_data is None or signal_data.empty:
        print('No Signal Data for ' + code)
        return

    executor_str = input_manager.executor_str
    output_path = input_manager.output_path

    if 'Voting' in executor_str:
        from Executor.SignalEvaluateVoting import SignalEvaluateVoting
        se = SignalEvaluateVoting(code, executor_str, tick_data, transaction_data, tick_dict, output_path, [(signal_data, params_dict)])
    else:
        if input_manager.freq in ['3s', '3s_l2p']:
            from Executor.SignalEvaluate import SignalEvaluate
            se = SignalEvaluate(code, executor_str, tick_data, transaction_data, tick_dict, output_path, [(signal_data, params_dict)])
        elif input_manager.freq == '1s':
            from Executor.SignalEvaluate1S import SignalEvaluate1S
            se = SignalEvaluate1S(code, executor_str, tick_data, transaction_data, tick_dict, tick_dict_freq, pre_close_dict,
                                  output_path, [(signal_data, params_dict)])
        else:
            raise ValueError
    se.evaluate(show='all', dfs=dfs)
