"""Albest策略（股票策略）动态阈值回测main函数——update@2021.8.31"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import GetCodeVol, get_index_code
from BT.UtilsBT import check_lib_list


mode = 'spark'  # spark, local


def main():
    st_date, ed_date = '20220301', '20220520'
    signal_lib_list = ['ray_albest_20211101_20211116_order', 'ray_albest_20220201_20220414_order_new']
    # check_lib_list(signal_lib_list, get_index_code('hs300', '20220104'), st_date, ed_date)
    # triggers(st_date, ed_date, signal_lib_list)
    # start_bt(st_date, ed_date, signal_lib_list)
    xd_compare(st_date, ed_date, signal_lib_list)


def triggers(st_date, ed_date, signal_lib_list):
    from BT.Dy_Triggers.SignalCVIntra import Task
    # from BT.Dy_Triggers.SignalCV import Task
    code_list = list(sorted(get_index_code('1800', base_date='20220104', market='sz')))
    suffix = '_0523'
    for signal_lib in signal_lib_list:
        save_path = f'/data/user/011668/CVTriggers/Albest/{signal_lib}{suffix}'
        Task(code_list, st_date, ed_date, 'Albest', signal_lib, save_path, time_list=['10:00:00']).start(mode=mode)  # local, multi_processing, spark
        # Task(code_list, st_date, ed_date, 'Albest', signal_lib, save_path, ).start(mode=mode)  # local, multi_processing, spark


def start_bt(st_date, ed_date, signal_lib_list):
    strategy_params = StrategyParams(mode, 'bt')
    get_config(strategy_params, st_date, ed_date, signal_lib_list)
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    # bt.start_bt()
    bt.analyze_result(multiprocess_nums=20, is_classify_res=True, is_transfer_file=False)


def get_config(strategy_params, st_date, ed_date, signal_lib_list):
    for portfolio in ['1800']:
        for signal_lib in signal_lib_list:
            for index_size in [10]:
                suffix = '_0523'
                code_vol_dict = GetCodeVol(st_date, ed_date, market='sz').get_index_code(portfolio, base_date=20220104, index_size=index_size * 3 * 1e8)
                overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, 'Albest', suffix=suffix)
                params_dynamic = {
                    'st_date': st_date,
                    'ed_date': ed_date,
                    'strategy': 'Albest',
                    'portfolio': portfolio,
                    'code_vol_dict': code_vol_dict,
                    'executor_str': 'Executor.ExecutorAlbestSPIntra',  # ExecutorAlbestSP
                    'signal_lib': signal_lib,
                    'out_dir': f'bt_test/Albest',
                    'overwrite_params': {'order_capacity_ratio': 0.3},
                    'overwrite_params_by_code': overwrite_params_by_code,
                    'suffix_name': f'-dy{index_size}{suffix}',
                }
                strategy_params.add_params(params_dynamic)


def xd_compare(st_date, ed_date, signal_lib_list):
    from Analyzer.MultiStrategyReport import MultiStrategyReport
    from Analyzer.AnalyzerTools.ResultLayer import plot_layer

    size = 10
    index_name = 'hs300'
    abs_path_bt = f'/data/user/011668/bt_test/Albest/bt-{st_date}-{ed_date}/'
    abs_path_list = [f'{abs_path_bt}/1800-ExecutorAlbestSPIntra-{signal_lib}-dy{size}_0523' for signal_lib in signal_lib_list]
    tags = signal_lib_list

    plot_layer(abs_path_list, tags, is_add_index=True)

    # index_dict = {'hs300': '000300.SH', 'zz500': '000905.SH', 'zz1000': '000852.SH', 'kunlun': '000832.SH'}
    # report = MultiStrategyReport(st_date, ed_date, abs_path_list, tags, index_dict[index_name])
    # report.generate_report(split_by_month=True, is_print=False, classify='')


if __name__ == '__main__':
    main()
