"""Kunlun策略（转债策略）动态阈值回测main函数——update@2021.9.8"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import GetCodeVol, get_cb_code


mode = 'spark'  # spark, local
SIGNAL_DATE_LIST = [
    ("ray_cb_stock_20210201_20210506", "20210301", "20210731"),
    ("ray_cb_stock_20210501_20210506_sync", "20210801", "20211130"),
    ("ray_cb_stock_20211001_20210506_sync", "20211201", "20220228"),
]
# bt_test/Kunlun/bt-20211201-20220228/Kunlun-ExecutorKunlunSP-ray_cb_stock_20211001_20210506_sync-dy150_300_0.03_long


def main():
    (signal_lib, st_date, ed_date) = SIGNAL_DATE_LIST[2]
    signal_lib_list = [signal_lib]
    # st_date, ed_date = "20210301", "20210731"
    # signal_lib_list = ['ray_cb_stock_20210201_20210506']

    # triggers(st_date, ed_date, signal_lib_list)
    start_bt(st_date, ed_date, signal_lib_list)


def triggers(st_date, ed_date, signal_lib_list):
    from BT.Dy_Triggers.SignalCV import Task
    code_list = list(sorted(get_cb_code(st_date, ed_date)))
    suffix = ''
    for signal_lib in signal_lib_list:
        save_path = f'/data/user/011668/CVTriggers/Kunlun/{signal_lib}{suffix}'
        Task(code_list, st_date, ed_date, 'Kunlun', signal_lib, save_path).start(mode='multi_processing')  # local, multi_processing, spark


def start_bt(st_date, ed_date, signal_lib_list):
    strategy_params = StrategyParams(mode, 'bt')
    get_config(strategy_params, st_date, ed_date, signal_lib_list)
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    # bt.combine_data(multi_process_nums=20)
    bt.start_bt()
    bt.analyze_result(multiprocess_nums=1, is_classify_res=False, is_transfer_file=False)


def get_config(strategy_params, st_date, ed_date, signal_lib_list):
    for signal_lib in signal_lib_list:
        code_vol_dict = GetCodeVol(st_date, ed_date).get_cb_code()
        overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, 'Kunlun', suffix='')
        size_max_turnover, size_max_exposure, liquidity_ratio = 150, 300, 0.03
        params_dynamic = {
            'st_date': st_date,
            'ed_date': ed_date,
            'strategy': 'Kunlun',
            'portfolio': 'Kunlun',
            'code_vol_dict': code_vol_dict,
            'executor_str': 'Executor.ExecutorKunlunSP',  # ExecutorKunlunSP
            'signal_lib': signal_lib,
            'out_dir': f'bt_test/Kunlun',
            'overwrite_params': {'maxTurnoverPerOrder': size_max_turnover * 1e4, 'maxExposure': size_max_exposure * 1e4,
                                 'liquidity_ratio': liquidity_ratio},
            'overwrite_params_by_code': overwrite_params_by_code,
            'suffix_name': f'-dy{size_max_turnover}_{size_max_exposure}_{liquidity_ratio}_long',
        }
        strategy_params.add_params(params_dynamic)


if __name__ == '__main__':
    main()
