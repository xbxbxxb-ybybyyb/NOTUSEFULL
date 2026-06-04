"""Kunlun投票策略（转债策略）动态阈值回测main函数——update@2021.3.21"""

from BT.RunBT import RunBT
from BT.Dy_Triggers.SignalCV_CB_Voting import Task
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import GetCodeVol, get_cb_code
from Manager.UtilsModel.VotingTriggers import *


mode = 'spark'  # spark, local


def main():
    st_date, ed_date = '20220301', '20220520'
    signal_lib_list = ['ray_cb_stock_20220201_20210506_sync', 'ray_cb_stock_20220201_20220401_sync']  # 'ray_cb_stock_20210501_20210506_sync', 'ray_cb_stock_20211001_20210506_sync'

    # dy_triggers(st_date, ed_date, signal_lib_list)
    # start_bt(st_date, ed_date, signal_lib_list)
    xd_compare(st_date, ed_date, signal_lib_list)


def start_bt(st_date, ed_date, signal_lib_list):
    strategy_params = StrategyParams(mode, 'bt_voting')

    vt_name_list_10 = ['1.75min', '2.75min', '3.25min', '3.5min', '5.75min', '6.25min', '6.5min', '7.25min', '7.5min', '8min']
    get_config(strategy_params, st_date, ed_date, signal_lib_list, vt_name_list_10, vt_nums=5)
    # vt_name_list_7 = ['1min', '2min', '3min', '5min', '6min', '7min', '8min']
    # get_config(strategy_params, st_date, ed_date, signal_lib_list, vt_name_list_7, vt_nums=4)

    bt = RunBT(strategy_params.strategy_params, mode, 'bt_voting', max_tasks=600)
    # bt.combine_data_and_params()
    bt.start_bt()
    bt.analyze_result(is_classify_res=True, is_transfer_file=False, multiprocess_nums=1)


def dy_triggers(st_date, ed_date, signal_lib_list):
    code_list = get_cb_code(st_date, ed_date)
    for signal_lib in signal_lib_list:
        save_path = f'/data/user/011668/CVTriggers/Kunlun/voting-{signal_lib}'
        Task(code_list, st_date, ed_date, signal_lib, tag_lib=None, save_path=save_path, is_add_mock=False).start(mode='spark')  # local, multi_processing, spark


def get_config(strategy_params, st_date, ed_date, signal_lib_list, vt_name_list, vt_nums):
    strategy, portfolio = 'Kunlun', 'Kunlun'  # 策略与组合
    code_vol_dict = GetCodeVol(st_date, ed_date).get_cb_code()
    for signal_lib in signal_lib_list:
        overwrite_params_by_code = combine_params(code_vol_dict, st_date, ed_date, signal_lib, vt_name_list=vt_name_list, strategy='Kunlun')
        # size_max_turnover, size_max_exposure, liquidity_ratio = 250, 500, 0.03
        size_max_turnover, size_max_exposure, liquidity_ratio = 100, 200, 0.02
        vt_name = '8min' if set([float(x[:-3]) % 1 for x in vt_name_list]) == {0.0} else '8.75min'

        params_dynamic = {
            'st_date': st_date,
            'ed_date': ed_date,
            'strategy': strategy,
            'portfolio': portfolio,
            'code_vol_dict': code_vol_dict,
            'executor_str': 'Executor.ExecutorKunlunSPVoting',
            'signal_lib': signal_lib,
            'out_dir': f'bt_test/{strategy}_voting',
            'overwrite_params': {'maxTurnoverPerOrder': size_max_turnover * 1e4, 'maxExposure': size_max_exposure * 1e4,
                                 'liquidity_ratio': liquidity_ratio, 'vt_name': vt_name,
                                 'delay': [0.04, 0.04],
                                 # 'open_filter_pct': -99999,
                                 'vt_params': {'vt_name_list': vt_name_list, 'open_counter': vt_nums,
                                               'buy_price_method': 'max', 'buy_vol_method': 'max', 'close_counter': 1,
                                               'sell_price_method': 'min', 'sell_vol_method': 'max'}},
            'overwrite_params_by_code': overwrite_params_by_code,
            'suffix_name': f'-{size_max_turnover}_{size_max_exposure}_{liquidity_ratio}_max{len(vt_name_list)}v{vt_nums}_delay40',
        }
        strategy_params.add_params(params_dynamic)


def xd_compare(st_date, ed_date, signal_lib_list):
    from Analyzer.MultiStrategyReport import MultiStrategyReport
    abs_path_bt = f'/data/user/011668/bt_test/Kunlun_voting/bt_voting-{st_date}-{ed_date}/'
    abs_path_list = [f'{abs_path_bt}/Kunlun-ExecutorKunlunSPVoting-{signal_lib}-100_200_0.02_max10v5_delay40' for signal_lib in signal_lib_list]
    tags = signal_lib_list
    index_code = "000832.SH"
    report = MultiStrategyReport(st_date, ed_date, abs_path_list, tags, index_code)
    report.generate_report(split_by_month=True, is_print=False, classify='')

# Finish: /data/user/011668/bt_test/Kunlun_voting/bt_voting-20220301-20220520/Kunlun-ExecutorKunlunSPVoting-ray_cb_stock_20220201_20210506_sync-100_200_0.02_max10v5_delay40
if __name__ == '__main__':
    main()
