"""Everest策略（股票策略）动态阈值回测main函数——update@2021.8.31"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import GetCodeVol, get_index_code


mode = 'local'  # spark, local


def main():
    st_date, ed_date = '20211101', '20220218'
    signal_lib_list = ['Everest20211001_20210515', 'Everest20210501_EmNonL2P_300Ex', 'Everest20210501_EmNonL2P_800Ex', 'Everest20211001_20211221_EmUnique']  # Everest20210201_20210515, Everest20211001_20210515

    # triggers(st_date, ed_date, signal_lib_list)
    start_bt(st_date, ed_date, signal_lib_list)
    # xd_compare(st_date, ed_date, signal_lib_list)


def triggers(st_date, ed_date, signal_lib_list):
    from BT.Dy_Triggers.SignalCV import Task
    code_list = list(sorted(get_index_code('1800', base_date='20220104')))
    suffix = '_everest'
    for signal_lib in signal_lib_list:
        save_path = f'/data/user/011668/CVTriggers/Everest/{signal_lib}{suffix}'
        Task(code_list, st_date, ed_date, 'Everest', signal_lib, save_path).start(mode=mode)  # local, multi_processing, spark


def start_bt(st_date, ed_date, signal_lib_list):
    strategy_params = StrategyParams(mode, 'bt')
    get_config(strategy_params, st_date, ed_date, signal_lib_list)
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    bt.start_bt()
    bt.analyze_result(multiprocess_nums=1, is_classify_res=False, is_transfer_file=False)


def get_config(strategy_params, st_date, ed_date, signal_lib_list):
    for portfolio in ['hs300', 'zz500', 'zz1000']:
        for signal_lib in signal_lib_list:
            for index_size in [20]:
                code_vol_dict = GetCodeVol(st_date, ed_date).get_index_code(portfolio, base_date=20220104, index_size=index_size * 1e8)
                overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, 'Everest', suffix='_everest')
                params_dynamic = {
                    'st_date': st_date,
                    'ed_date': ed_date,
                    'strategy': 'Everest',
                    'portfolio': portfolio,
                    'code_vol_dict': code_vol_dict,
                    'executor_str': 'Executor.ExecutorEverestSP',  # ExecutorEverestSP
                    'signal_lib': signal_lib,
                    'out_dir': f'bt_test/Everest',
                    'overwrite_params': {'order_capacity_ratio': 0.3},
                    'overwrite_params_by_code': overwrite_params_by_code,
                    'suffix_name': f'-dy{index_size}',
                }
                strategy_params.add_params(params_dynamic)


def xd_compare(st_date, ed_date, signal_lib_list):
    from Analyzer.MultiStrategyReport import MultiStrategyReport
    size = 20
    index_name = 'hs300'
    abs_path_bt = f'/data/user/011668/bt_test/Everest/bt-{st_date}-{ed_date}/'
    abs_path_list = [f'{abs_path_bt}/{index_name}-ExecutorEverestSP-{signal_lib}-dy{size}' for signal_lib in signal_lib_list]
    tags = signal_lib_list
    index_dict = {'hs300': '000300.SH', 'zz500': '000905.SH', 'zz1000': '000852.SH', 'kunlun': '000832.SH'}
    report = MultiStrategyReport(st_date, ed_date, abs_path_list, tags, index_dict[index_name])
    report.generate_report(split_by_month=True, is_print=False, classify='')


if __name__ == '__main__':
    main()
