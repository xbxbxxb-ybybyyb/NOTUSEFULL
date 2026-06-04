"""实盘策略（Albest, Everest, Kunlun_mix, Kunlun_pure）回测跟踪程序（新增l2p跟踪），按组合和市场区分的结果——update @2021.10.31"""

from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams
from DataAPI.GetCodeVol import GetCodeVol
from DataAPI.TradingDay import trading_day
from DataAPI.DataToolsCbond import get_cbond_stock_map
from DataAPI.DataView import load_json_file


def main():
    date_list = trading_day('20220808', '20220812')  # '20220617', '20220720'
    triggers(date_list)
    bt(date_list)


def bt(date_list):
    mode = 'spark'  # local, spark, ray

    strategy_params = StrategyParams(mode, bt_type='sp')
    for bt_date in date_list:  # '20220617', '20220720'
        for signal_lib in ['Albest20211101Order1Signals', 'Albest20220201Order1Signals']:
            stock_sp_config_1s(signal_lib, 'Everest1S', bt_date, strategy_params, bt_mode='res')
    sp_track = RunBT(strategy_params.strategy_params, mode, bt_type='sp')
    sp_track.start_bt()
    sp_track.analyze_result(is_transfer_file=False, is_classify_res=True, multiprocess_nums=1)


def triggers(date_list):
    from BT.Dy_Triggers.SignalCVIntra import Task

    for bt_date in date_list:
        code_vol_dict = GetCodeVol(bt_date, bt_date).get_sp_code(f'Everest1S_sp')
        code_list = list(code_vol_dict.keys())
        mock_lib = 'Channel1STickDataLib'
        strategy = 'Albest'
        for signal_lib in ['Albest20211101Order1Signals', 'Albest20220201Order1Signals']:
            save_path = f'/data/user/011668/CVTriggers/{strategy}Track/{signal_lib}/{bt_date}'
            Task(code_list, bt_date, bt_date, strategy, signal_lib, save_path, time_list=['10:00:00'],
                 tag_lib=signal_lib, mock_lib=mock_lib, is_add_mock=False, overwrite_params={'min_triggers': 15}).start(mode='spark')  # local, multi_processing, spark


def stock_sp_config_1s(signal_lib, strategy, bt_date, strategy_params, bt_mode='all'):
    """bt_mode为bt的类型，all为同时pro+res，pro或者res为单独的"""
    executor_stock = {'Everest1S': 'ExecutorAlbestSP1SIntra'}
    param_dir_stock = {'Everest1S': f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{bt_date}/JsonParam/'}
    freq = '1s' if strategy.endswith('1S') else '3s'
    code_vol_dict = GetCodeVol(bt_date, bt_date).get_sp_code(f'{strategy}_sp')
    code_vol_dict_sh, code_vol_dict_sz, code_vol_dict_cyb = split_code_vol_dict_by_market(strategy, code_vol_dict)

    out_dir = f'BT_Track_EverestCP/{strategy}'

    params = {
        'bt_type': 'sp',
        'st_date': bt_date,
        'ed_date': bt_date,
        'strategy': strategy,
        'executor_str': 'Executor.' + executor_stock[strategy],
        'freq': freq,
        'param_dir': param_dir_stock[strategy],  # 实盘参数路径
        'param_dir_bt': f'SP_Params/{strategy}_sp/Params_{bt_date}',
        'out_dir': out_dir,  # 输出结果路径
    }

    params_list = []
    if 'all' in bt_mode or 'res' in bt_mode:
        s_res = '' if freq == '3s' else '_l2p'
        params_list += [
            [f'{strategy}_sp{s_res}', code_vol_dict_sz, signal_lib, f'res_1s_delay80_{signal_lib}'],
            [f'{strategy}_sp{s_res}', code_vol_dict_cyb, signal_lib, f'res_1s_delay80_{signal_lib}'],
        ]

    for [portfolio, code_vol_dict_sub, signal_lib_sub, suffix_sub] in params_list:
        if len(code_vol_dict_sub) > 0:
            overwrite_params_by_code = {}
            triggers_path = f'/data/user/011668/CVTriggers/AlbestTrack/{signal_lib}/{bt_date}'
            for code in code_vol_dict_sub.keys():
                trigger_code = load_json_file(f'{triggers_path}/{code}.json')
                overwrite_params_by_code.update({code: {'triggers_by_date': trigger_code}})
            params_new = params.copy()
            params_new.update({
                'portfolio': portfolio,
                'code_vol_dict': code_vol_dict_sub,
                'signal_lib': signal_lib_sub,
                'output_dir_name': suffix_sub,
                'overwrite_params': {'is_holo': False},
                'overwrite_params_by_code': overwrite_params_by_code
            })
            if portfolio.endswith('l2p') and strategy != 'Everest1S':
                params_new.update({'freq': '3s_l2p'})
            if strategy == 'Everest1S':
                params_new.update({'freq': '1s'})
                params_new['overwrite_params'].update({'time_list': ['09:30:00', '10:00:00']})
            strategy_params.add_params(params_new)


def split_code_vol_dict_by_market(strategy, code_vol_dict):
    # 按交易所来看
    code_vol_dict_sh, code_vol_dict_sz, code_vol_dict_cyb = {}, {}, {}
    if strategy in ['Albest', 'Everest', 'Everest1S', 'Barwa']:
        code_vol_dict_sh = dict([(x, y) for (x, y) in code_vol_dict.items() if x.startswith('6')])
        code_vol_dict_sz = dict([(x, y) for (x, y) in code_vol_dict.items() if x.startswith('0')])
        code_vol_dict_cyb = dict([(x, y) for (x, y) in code_vol_dict.items() if x.startswith('3')])
    elif strategy in ['Kunlun_mix', 'Kunlun_pure']:
        all_code = list(code_vol_dict.keys())
        if len(all_code) > 0:
            cb_dict = get_cbond_stock_map(all_code)
            code_vol_dict_sh = dict([(x, y) for (x, y) in code_vol_dict.items() if cb_dict[x].startswith('6')])
            code_vol_dict_sz = dict([(x, y) for (x, y) in code_vol_dict.items() if cb_dict[x].startswith('0')])
            code_vol_dict_cyb = dict([(x, y) for (x, y) in code_vol_dict.items() if cb_dict[x].startswith('3')])
    return code_vol_dict_sh, code_vol_dict_sz, code_vol_dict_cyb


if __name__ == '__main__':
    main()
