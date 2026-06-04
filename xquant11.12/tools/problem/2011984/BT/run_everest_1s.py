"""Everest1S策略（股票策略）动态阈值回测main函数——update@2022.5.17"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import GetCodeVol, get_index_code
from BT.Dy_Triggers.SignalCVIntra import Task


mode = 'spark'  # spark, local


def main():
    st_date, ed_date = '20220615', '20220810'
    signal_lib_list = ['Albest20211101Order1Signals', 'Albest20220201Order1Signals', 'Albest20220601Order1Signals']

    triggers(st_date, ed_date, signal_lib_list, 'Albest')
    start_bt(st_date, ed_date, signal_lib_list)
    # xd_compare(st_date, ed_date, signal_lib_list)


def triggers(st_date, ed_date, signal_lib_list, strategy):
    code_list = list(sorted(get_index_code('1800', base_date='20220701', market='sz')))
    mock_lib = 'Channel1STickDataLib'
    suffix = '_0815'
    for signal_lib in signal_lib_list:
        save_path = f'/data/user/011668/CVTriggers/{strategy}/{signal_lib}{suffix}'
        Task(code_list, st_date, ed_date, strategy, signal_lib, save_path, time_list=['10:00:00'],
             tag_lib=signal_lib, mock_lib=mock_lib, is_add_mock=False, overwrite_params={'min_triggers': 15}).start(mode='spark')  # local, multi_processing, spark


def start_bt(st_date, ed_date, signal_lib_list):
    strategy_params = StrategyParams(mode, 'bt')
    get_config(strategy_params, st_date, ed_date, signal_lib_list, 'Albest')
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    bt.start_bt()
    bt.analyze_result(multiprocess_nums=1, is_classify_res=False, is_transfer_file=False)


def get_config(strategy_params, st_date, ed_date, signal_lib_list, strategy):
    for portfolio in ['1800']:
        for signal_lib in signal_lib_list:
            for index_size in [10]:
                for oc in [0.3]:
                    code_vol_dict = GetCodeVol(st_date, ed_date, market='sz').get_index_code(portfolio, base_date=20220701,
                                                                                             index_size=index_size * 3 * 1e8)
                    overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, strategy, suffix='_0815')
                    params_dynamic = {
                        'st_date': st_date,
                        'ed_date': ed_date,
                        'strategy': strategy,
                        'portfolio': portfolio,
                        'freq': '1s',
                        'code_vol_dict': code_vol_dict,
                        'executor_str': f'Executor.ExecutorAlbestSP1SIntra',
                        'signal_lib': signal_lib,
                        'out_dir': f'bt_test/Albest1S',
                        'overwrite_params': {'time_list': ['09:30:00', '10:00:00'], 'order_capacity_ratio': oc},
                        'overwrite_params_by_code': overwrite_params_by_code,
                        'suffix_name': f'-dy{index_size}_oc{oc}',
                    }
                    strategy_params.add_params(params_dynamic)


def xd_compare(st_date, ed_date, signal_lib_list):
    from Analyzer.MultiStrategyReport import MultiStrategyReport
    size = 10
    index_name = 'hs300'
    abs_path_bt = f'/data/user/011668/bt_test/Albest1S/bt-{st_date}-{ed_date}/'
    oc_all = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    abs_path_list = [f'{abs_path_bt}/1800-ExecutorAlbestSP1SIntra-{signal_lib_list[0]}-dy{size}_oc{x}' for x in oc_all]
    tags = oc_all

    abs_path_list = [
        '/data/user/011668/bt_test/Albest1S/bt-20220617-20220720/1800-ExecutorAlbestSP1SIntra-Albest20220201Order1Signals-dy10_oc0.3',
        '/data/user/011668/bt_test/Albest/bt-20220617-20220720/1800-ExecutorAlbestSPIntra-Albest20220201Order036Signals-dy10_0720',
    ]
    tags = ['1s', '3s']

    index_dict = {'hs300': '000300.SH', 'zz500': '000905.SH', 'zz1000': '000852.SH', 'kunlun': '000832.SH'}
    report = MultiStrategyReport(st_date, ed_date, abs_path_list, tags, index_dict[index_name])
    report.generate_report(split_by_month=True, is_print=False, classify='')


if __name__ == '__main__':
    main()
