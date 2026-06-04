"""Albest策略（股票策略）回测main函数——update@2021.3.26"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import get_all_code
from DataAPI.TradingDay import trading_day
from BT.UtilsBT import check_lib_list
from BT.Dy_Triggers.SignalCVIntra import Task


mode = 'spark'  # spark, local


st_date, ed_date = '20220527', '20220527'

signal_lib_sh, signal_lib_sz = 'ray_albest_20211101_20211116', 'ray_albest_20211101_20211116_order'


def main():
    triggers(st_date, ed_date)
    run_single_date()


def run_single_date():
    strategy_params = StrategyParams(mode, 'bt')
    for bt_date in trading_day(st_date, ed_date):
        get_config_albest_dynamic(strategy_params, bt_date)
        print('Finish: ', bt_date)
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    bt.start_bt()
    bt.analyze_result(multiprocess_nums=1, is_transfer_file=False)


def get_config_albest_dynamic(strategy_params, bt_date):
    strategy, portfolio = 'Albest', 'margin'  # 策略与组合
    code_list = get_code_list(bt_date, bt_date)
    code_list_sh, code_list_sz = [x for x in code_list if x.endswith('.SH')], [x for x in code_list if x.endswith('.SZ')]

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
    }

    params_dynamic_sh = params_dynamic.copy()
    code_vol_dict_sh = dict([(code, 1e10) for code in code_list_sh])
    overwrite_params_by_code_sh = combine_params(code_vol_dict_sh, bt_date, bt_date, signal_lib_sh, strategy='Albest', add_trigger=False)
    params_dynamic_sh.update(
        {
            'code_vol_dict': dict([(code, 1e10) for code in code_list_sh]),
            'signal_lib': signal_lib_sh,
            'overwrite_params_by_code': overwrite_params_by_code_sh,
        }
    )
    strategy_params.add_params(params_dynamic_sh)

    params_dynamic_sz = params_dynamic.copy()
    code_vol_dict_sz = dict([(code, 1e10) for code in code_list_sz])
    overwrite_params_by_code_sz = combine_params(code_vol_dict_sz, bt_date, bt_date, signal_lib_sz, strategy='Albest', add_trigger=False)
    params_dynamic_sz.update(
        {
            'code_vol_dict': dict([(code, 1e10) for code in code_list_sz]),
            'signal_lib': signal_lib_sz,
            'overwrite_params_by_code': overwrite_params_by_code_sz,
        }
    )
    strategy_params.add_params(params_dynamic_sz)


def get_code_list(st_date, ed_date):
    key_st_date = trading_day(st_date, ed_date)[0]
    key_ed_date = trading_day(st_date, ed_date)[-1]
    code_list1 = get_all_code(key_st_date, type='stock')
    code_list2 = get_all_code(key_ed_date, type='stock')
    code_list = list(sorted(set(code_list1 + code_list2)))
    return code_list


def triggers(st_date, ed_date):
    code_list = get_code_list(st_date, ed_date)
    code_list_sh = [x for x in code_list if x.endswith('.SH')]
    code_list_sz = [x for x in code_list if x.endswith('.SZ')]
    Task(code_list_sh, st_date, ed_date, 'Albest', signal_lib_sh, save_path='lib', time_list=['10:00:00']).start(mode=mode)
    Task(code_list_sz, st_date, ed_date, 'Albest', signal_lib_sz, save_path='lib', time_list=['10:00:00']).start(mode=mode)


if __name__ == '__main__':
    main()
