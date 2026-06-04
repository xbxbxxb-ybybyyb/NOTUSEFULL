"""Albest策略（股票策略）回测main函数——update@2021.3.26"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, load_order_capacity
from DataAPI.GetCodeVol import get_all_code
from DataAPI.TradingDay import trading_day
from BT.Dy_Triggers.SignalCVIntra import Task


mode = 'spark'  # spark, local


st_date, ed_date = '20210101', '20210331'

signal_lib = 'algo_20201101_20201123'


def main():
    code_list_all = get_code_list(st_date, ed_date, gap=1)
    # triggers(code_list_all, st_date, ed_date)
    run_single_date(code_list_all)


def run_single_date(code_list):
    oc_all = order_capacity_all(code_list, st_date, ed_date, 'Albest')
    strategy_params = StrategyParams(mode, 'bt')
    for bt_date in trading_day(st_date, ed_date):
        get_config_albest_dynamic(strategy_params, bt_date, oc_all)
        print('Finish: ', bt_date)
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    bt.start_bt()
    # bt.analyze_result(multiprocess_nums=20, is_transfer_file=False)


def get_config_albest_dynamic(strategy_params, bt_date, oc_all):
    strategy, portfolio = 'Albest', 'margin'  # 策略与组合
    code_list = get_code_list(bt_date, bt_date)
    code_vol_dict = dict([(code, 1e10) for code in code_list])
    overwrite_params_by_code = combine_params(oc_all, code_vol_dict, bt_date, bt_date)

    params_dynamic = {
        'st_date': bt_date,
        'ed_date': bt_date,
        'strategy': strategy,
        'portfolio': portfolio,
        'trigger_lib': 'DynamicTriggers1000',
        'executor_str': 'Executor.ExecutorAlbestSPIntra',
        'param_dir_bt': f'MarginSelect/Params/bt-{bt_date}-{bt_date}/params',
        'out_dir': f'MarginSelect/{strategy}Daily',
        'overwrite_params': {'order_capacity_ratio': 0.3},
        'suffix_name': '',
        'code_vol_dict': code_vol_dict,
        'signal_lib': signal_lib,
        'overwrite_params_by_code': overwrite_params_by_code,
    }
    strategy_params.add_params(params_dynamic)


def get_code_list(st_date, ed_date, gap=None):
    date_list = trading_day(st_date, ed_date)
    if gap is None:
        key_date = [date_list[0], date_list[-1]]
    else:
        key_date = date_list[::gap]
    code_list = []
    for key_date_sub in key_date:
        code_list += get_all_code(key_date_sub, type='stock')
    code_list = list(sorted(set(code_list)))
    return code_list


def triggers(code_list, st_date, ed_date):
    save_path = 'lib'
    Task(code_list, st_date, ed_date, 'Albest', signal_lib, save_path=save_path, time_list=['10:00:00']).start(mode=mode)


def order_capacity_all(code_list, st_date, ed_date, strategy):
    oc_by_code = {}
    for code in code_list:
        order_capacity = load_order_capacity(code, st_date, ed_date, strategy)
        oc_by_code.update({code: order_capacity})
    return oc_by_code


def combine_params(oc_all, code_vol_dict, st_date, ed_date):
    code_list = list(code_vol_dict.keys())
    overwrite_params_by_code = {}
    for code in code_list:
        date_list = list(sorted(set(trading_day(st_date, ed_date)).intersection(set(oc_all[code]['OrderCapacity'].keys()))))
        params_code = {
            'code': code,
            'init_qty': code_vol_dict[code],
            'order_capacity': dict([(x, oc_all[code]['OrderCapacity'][x]) for x in date_list]),
            'high_vol': dict([(x, oc_all[code]['HighVol'][x]) for x in date_list]),
        }
        overwrite_params_by_code.update({code: params_code})
    return overwrite_params_by_code


if __name__ == '__main__':
    main()
