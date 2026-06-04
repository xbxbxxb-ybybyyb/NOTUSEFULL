"""Albest与Everest策略对hs300和zz500的跟踪——Update @2021.3.25"""

import pandas as pd
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from BT.UtilsBT import check_lib, check_triggers
from DataAPI.GetCodeVol import GetCodeVol, get_index_code, trading_day_gap
from DataAPI.DataView import file_list_dir
from SP.SP_Params import get_sp_lib


mode = 'spark'  # spark, local


def main():
    # 对某一天的结果进行回测
    bt_date = '20220126'
    triggers(bt_date, mode)
    start_bt(bt_date)


def triggers(trade_date, mode):
    code_list = get_code_list(trade_date)
    check(trade_date, code_list)
    check_cb(trade_date)

    # Albest
    from BT.Dy_Triggers.SignalCVIntra import Task
    code_select_sh = [x for x in code_list if x.endswith('.SH')]
    signal_lib_sh = get_sp_lib(trade_date, 'Albest', 'res_sh')
    save_path_sh = f'/data/user/011668/CVTriggers/SPTriggersTrack/Albest/{trade_date}/{signal_lib_sh}'
    time_list = ['10:00:00']
    while len(code_select_sh) > 0:
        print(f'{len(code_select_sh)}只上海标的需要计算')
        Task(code_select_sh, trade_date, trade_date, 'Albest', signal_lib_sh, save_path_sh, time_list=time_list).start(mode=mode)
        code_select_sh = list(sorted(set(code_select_sh) - set([x[:-5] for x in file_list_dir(save_path_sh)])))
    check_triggers(code_select_sh, save_path_sh)

    code_select_sz = [x for x in code_list if x.endswith('.SZ')]
    signal_lib_sz = get_sp_lib(trade_date, 'Albest', 'res_sz')
    save_path_sz = f'/data/user/011668/CVTriggers/SPTriggersTrack/Albest/{trade_date}/{signal_lib_sz}'
    time_list = ['10:00:00']
    while len(code_select_sz) > 0:
        print(f'{len(code_select_sz)}只深圳标的需要计算')
        Task(code_select_sz, trade_date, trade_date, 'Albest', signal_lib_sz, save_path_sz, time_list=time_list).start(mode=mode)
        code_select_sz = list(sorted(set(code_select_sz) - set([x[:-5] for x in file_list_dir(save_path_sz)])))
    check_triggers(code_select_sz, save_path_sz)

    # Everest
    print('Start Everest'.center(100, '*'))
    from BT.Dy_Triggers.SignalCV import Task
    signal_lib = get_sp_lib(trade_date, 'Everest', 'res')
    save_path = f'/data/user/011668/CVTriggers/SPTriggersTrack/Everest/{trade_date}/{signal_lib}'
    while len(code_list) > 0:
        print(f'{len(code_list)}只标的需要计算')
        Task(code_list, trade_date, trade_date, 'Everest', signal_lib, save_path).start(mode=mode)
        code_list = list(sorted(set(code_list) - set([x[:-5] for x in file_list_dir(save_path)])))
    check_triggers(code_list, save_path)

    # Everest1S
    strategy = 'Everest1S'
    print(f'Start {strategy}'.center(100, '*'))
    signal_lib = get_sp_lib(trade_date, strategy, 'res')
    save_path = f'/data/user/011668/CVTriggers/SPTriggersTrack/{strategy}/{trade_date}/{signal_lib}'
    code_list_1s = list(sorted(GetCodeVol(trade_date, trade_date).get_sp_code(f'{strategy}_sp').keys()))
    while len(code_list_1s) > 0:
        print(f'{len(code_list_1s)}只标的需要计算')
        mock_lib = 'Channel1STickDataLib'
        Task(code_list_1s, trade_date, trade_date, 'Albest', signal_lib, save_path,
             tag_lib=signal_lib, mock_lib=mock_lib, is_add_mock=False, overwrite_params={'min_triggers': 15}).start(mode=mode)
        code_list_1s = list(sorted(set(code_list_1s) - set([x[:-5] for x in file_list_dir(save_path)])))
    check_triggers(code_list_1s, save_path)

    # Kunlun
    print('Start Kunlun'.center(100, '*'))
    from BT.Dy_Triggers.SignalCV_CB_Voting import Task
    from DataAPI.GetCodeVol import get_cb_code
    code_select = get_cb_code(trading_day_gap(trade_date, -60), trade_date)
    signal_lib = get_sp_lib(trade_date, 'Kunlun_mix', 'res')
    save_path = f'/data/user/011668/CVTriggers/SPTriggersTrack/Kunlun/{trade_date}/{signal_lib}'
    while len(code_select) > 0:
        print(f'{len(code_select)}只标的需要计算')
        Task(code_select, trade_date, trade_date, signal_lib, tag_lib=None, save_path=save_path, is_add_mock=False).start(mode=mode)
        code_select = list(sorted(set(code_select) - set([x[:-5] for x in file_list_dir(save_path)])))
    # check_triggers(code_select, save_path)


def start_bt(bt_date):
    strategy_params = StrategyParams(mode, 'bt')
    get_config_albest(strategy_params, bt_date)
    get_config_everest(strategy_params, bt_date)
    sp_track = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    sp_track.start_bt()
    sp_track.analyze_result(multiprocess_nums=1, is_classify_res=False, is_transfer_file=False)


def get_config_albest(strategy_params, bt_date):
    strategy = 'Albest'
    signal_lib_sh = get_sp_lib(bt_date, strategy, 'res_sh')
    signal_lib_sz = get_sp_lib(bt_date, strategy, 'res_sz')

    for portfolio in ['hs300', 'zz500', 'zz1000']:
        for index_size in [10, 20, 40]:
            code_vol_dict = GetCodeVol(bt_date, bt_date).get_index_code(portfolio, base_date=bt_date, index_size=index_size * 1e8)
            code_vol_dict_sh = dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SH')])
            code_vol_dict_sz = dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SZ')])

            params_dynamic = {
                'st_date': bt_date,
                'ed_date': bt_date,
                'strategy': strategy,
                'portfolio': portfolio,
                'executor_str': 'Executor.ExecutorAlbestSPIntra',
                'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
                'overwrite_params': {'order_capacity_ratio': 0.3},
                'output_dir_name': f'track_{portfolio}_size{index_size}',
            }

            params_dynamic_sh = params_dynamic.copy()
            cv_trigger_path_sh = f'/data/user/011668/CVTriggers/SPTriggersTrack/{strategy}/{bt_date}/{signal_lib_sh}'
            overwrite_params_by_code = combine_params(code_vol_dict_sh, bt_date, bt_date, signal_lib_sh, strategy, suffix='',
                                                      cv_triggers_path=cv_trigger_path_sh)
            params_dynamic_sh.update({
                'code_vol_dict': code_vol_dict_sh,
                'signal_lib': signal_lib_sh,
                'overwrite_params_by_code': overwrite_params_by_code,
            })
            strategy_params.add_params(params_dynamic_sh)

            params_dynamic_sz = params_dynamic.copy()
            cv_trigger_path_sz = f'/data/user/011668/CVTriggers/SPTriggersTrack/{strategy}/{bt_date}/{signal_lib_sz}'
            overwrite_params_by_code = combine_params(code_vol_dict_sz, bt_date, bt_date, signal_lib_sz, strategy, suffix='',
                                                      cv_triggers_path=cv_trigger_path_sz)
            params_dynamic_sz.update({
                'code_vol_dict': code_vol_dict_sz,
                'signal_lib': signal_lib_sz,
                'overwrite_params_by_code': overwrite_params_by_code,
            })
            strategy_params.add_params(params_dynamic_sz)


def get_config_everest(strategy_params, bt_date):
    strategy = 'Everest'
    signal_lib = get_sp_lib(bt_date, strategy, 'res')

    for portfolio in ['hs300', 'zz500', 'zz1000']:
        for index_size in [10, 20, 40]:
            code_vol_dict = GetCodeVol(bt_date, bt_date).get_index_code(portfolio, base_date=bt_date, index_size=index_size * 1e8)
            cv_trigger_path = f'/data/user/011668/CVTriggers/SPTriggersTrack/{strategy}/{bt_date}/{signal_lib}'
            overwrite_params_by_code = combine_params(code_vol_dict, bt_date, bt_date, signal_lib, strategy, suffix='',
                                                      cv_triggers_path=cv_trigger_path)
            params_dynamic = {
                'st_date': bt_date,
                'ed_date': bt_date,
                'strategy': strategy,
                'portfolio': portfolio,
                'code_vol_dict': code_vol_dict,
                'executor_str': 'Executor.ExecutorEverestSP',
                'signal_lib': signal_lib,
                'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
                'overwrite_params': {'order_capacity_ratio': 0.3},
                'overwrite_params_by_code': overwrite_params_by_code,
                'output_dir_name': f'track_{portfolio}_size{index_size}',
            }
            strategy_params.add_params(params_dynamic)


def get_config_sp_all(strategy_params, bt_date):
    from DataAPI.DataView import load_json_file
    strategy_list = load_json_file(f'/data/user/011668/SP_Data/DailyReport/{bt_date}/strategy_list.json')
    code_vol_list = []
    if 'Albest' in strategy_list:
        code_vol_dict_albest = GetCodeVol(bt_date, bt_date).get_sp_code('Albest_sp')
        code_vol_list.append(pd.Series(code_vol_dict_albest))
    if 'Everest' in strategy_list:
        code_vol_dict_everest = GetCodeVol(bt_date, bt_date).get_sp_code('Everest_sp')
        code_vol_list.append(pd.Series(code_vol_dict_everest))
    code_vol_dict = pd.concat(code_vol_list).reset_index().groupby('index').sum()[0].to_dict()
    code_vol_dict_sh = dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SH')])
    code_vol_dict_sz = dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SZ')])

    for strategy in ['Albest', 'Everest']:
        signal_lib_sh = get_sp_lib(bt_date, strategy, 'res_sh')
        signal_lib_sz = get_sp_lib(bt_date, strategy, 'res_sz')

        params_dynamic = {
            'st_date': bt_date,
            'ed_date': bt_date,
            'strategy': strategy,
            'portfolio': 'stock_sp',
            'executor_str': 'Executor.ExecutorAlbestSPIntra' if strategy == 'Albest' else 'Executor.ExecutorEverestSP',
            'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
            'overwrite_params': {'order_capacity_ratio': 0.3},
            'output_dir_name': f'track_stock_sp',
        }

        params_dynamic_sh = params_dynamic.copy()
        cv_trigger_path_sh = f'/data/user/011668/CVTriggers/SPTriggersTrack/{strategy}/{bt_date}/{signal_lib_sh}'
        overwrite_params_by_code = combine_params(code_vol_dict_sh, bt_date, bt_date, signal_lib_sh, strategy, suffix='',
                                                  cv_triggers_path=cv_trigger_path_sh)
        params_dynamic_sh.update({
            'code_vol_dict': code_vol_dict_sh,
            'signal_lib': signal_lib_sh,
            'overwrite_params_by_code': overwrite_params_by_code,
        })
        strategy_params.add_params(params_dynamic_sh)

        params_dynamic_sz = params_dynamic.copy()
        cv_trigger_path_sz = f'/data/user/011668/CVTriggers/SPTriggersTrack/{strategy}/{bt_date}/{signal_lib_sz}'
        overwrite_params_by_code = combine_params(code_vol_dict_sz, bt_date, bt_date, signal_lib_sz, strategy, suffix='',
                                                  cv_triggers_path=cv_trigger_path_sz)
        params_dynamic_sz.update({
            'code_vol_dict': code_vol_dict_sz,
            'signal_lib': signal_lib_sz,
            'overwrite_params_by_code': overwrite_params_by_code,
        })
        strategy_params.add_params(params_dynamic_sz)


def check(bt_date, code_list):
    code_list_sh = [x for x in code_list if x.endswith('.SH')]
    code_list_sz = [x for x in code_list if x.endswith('.SZ')]
    check_lib(get_sp_lib(bt_date, 'Albest', 'res_sh'), code_list_sh, bt_date, bt_date)
    check_lib(get_sp_lib(bt_date, 'Albest', 'res_sz'), code_list_sz, bt_date, bt_date)
    check_lib(get_sp_lib(bt_date, 'Everest', 'res'), code_list, bt_date, bt_date)

    code_list_1s = list(sorted(GetCodeVol(bt_date, bt_date).get_sp_code(f'Everest1S_sp').keys()))
    check_lib(get_sp_lib(bt_date, 'Everest1S', 'res'), code_list_1s, bt_date, bt_date)


def check_cb(bt_date):
    fz_lib = 'WuKongFZSignals'
    code_s = list(GetCodeVol(bt_date, bt_date).get_sp_code('Kunlun_sp_mix').keys())
    check_lib(fz_lib, code_s, bt_date, bt_date)


def get_code_list(trade_date):
    code_select = []
    code_select += pd.read_excel(f'/data/user/011477/order/T0/T0_CV_Split/{trade_date}/{trade_date}_easy.xlsx')['证券代码'].to_list()
    code_select += list(get_index_code('1800', base_date=trade_date))
    code_select = list(sorted(set(code_select)))
    return code_select


if __name__ == '__main__':
    main()
