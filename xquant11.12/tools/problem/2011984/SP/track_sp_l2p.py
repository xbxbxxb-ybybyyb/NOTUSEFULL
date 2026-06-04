"""实盘策略（Albest, Everest, Kunlun_mix, Kunlun_pure）回测跟踪程序（新增l2p跟踪），按组合和市场区分的结果——update @2021.10.31"""

import os
import datetime
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams
from DataAPI.GetCodeVol import GetCodeVol
from DataAPI.DataView import save_json_file
from DataAPI.TradingDay import trading_day_gap
from SP.SP_Params import get_sp_lib, print_strategy_lib
from DataAPI.DataToolsCbond import get_cbond_stock_map
from SP.UtilsSP.CollectLiveParams import CollectLiveParams, EVEREST_DST_PATH


def main():
    mode = 'spark'  # local, spark, ray
    # bt_date = '20220601'
    today = datetime.datetime.now().strftime("%Y%m%d")
    bt_date = trading_day_gap(today, -1)
    print('BT Date, ', bt_date)

    strategy_list = ['Albest', 'Everest1S', 'Kunlun_mix', 'Kunlun_pure']
    report_path = f'/data/user/011668/SP_Data/DailyReport/{bt_date}'
    os.makedirs(f'{report_path}', exist_ok=True)
    save_json_file(strategy_list, f'{report_path}/strategy_list.json')

    CollectLiveParams('Everest', bt_date, bt_date, True, EVEREST_DST_PATH).run()
    print_strategy_lib(bt_date)
    strategy_params = StrategyParams(mode, bt_type='sp')
    stock_sp_config('Albest', bt_date, strategy_params, bt_mode='all')
    stock_sp_config('Everest1S', bt_date, strategy_params, bt_mode='all')
    kunlun_sp_voting_config('Kunlun_mix', bt_date, strategy_params, bt_mode='all')
    kunlun_sp_voting_config('Kunlun_pure', bt_date, strategy_params, bt_mode='all')
    strategy_params.check_sp_existing_code(bt_date)

    sp_track = RunBT(strategy_params.strategy_params, mode, bt_type='sp')
    # sp_track.combine_data()
    sp_track.combine_params()
    # sp_track.start_bt()
    # sp_track.analyze_result(is_transfer_file=False, is_classify_res=True, multiprocess_nums=1)


def stock_sp_config(strategy, bt_date, strategy_params, bt_mode='all', debug_code=None):
    """bt_mode为bt的类型，all为同时pro+res，pro或者res为单独的"""
    executor_stock = {'Albest': 'ExecutorAlbestSPIntra', 'Everest': 'ExecutorEverestSP', 'Everest1S': 'ExecutorAlbestSP1SIntra'}
    param_dir_stock = {'Albest': f'/data/user/666888/Algo/parameters/Algo_{bt_date}',
                       'Everest': f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{bt_date}/JsonParam/',
                       'Everest1S': f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{bt_date}/JsonParam/'}
    signal_lib_dict = {'res_SH': get_sp_lib(bt_date, strategy, 'res_sh'), 'res_SZ': get_sp_lib(bt_date, strategy, 'res_sz'),
                       'pro': get_sp_lib(bt_date, strategy, 'pro')}
    freq = '1s' if strategy.endswith('1S') else '3s'
    code_vol_dict = GetCodeVol(bt_date, bt_date).get_sp_code(f'{strategy}_sp')
    if debug_code is not None:
        code_vol_dict = {debug_code: code_vol_dict[debug_code]}
    code_vol_dict_sh, code_vol_dict_sz, code_vol_dict_cyb = split_code_vol_dict_by_market(strategy, code_vol_dict)

    out_dir = f'BT_Track/{strategy}' if debug_code is None else f'BT_Track_Debug/{strategy}'

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
    if 'all' in bt_mode or 'pro' in bt_mode:
        params_list += [
            [f'{strategy}_sp', code_vol_dict_sh, signal_lib_dict['pro'], f'-{strategy.lower()}_pro_sh'],
            [f'{strategy}_sp_l2p', code_vol_dict_sz, signal_lib_dict['pro'], f'-{strategy.lower()}_pro_sz'],
            [f'{strategy}_sp_l2p', code_vol_dict_cyb, signal_lib_dict['pro'], f'-{strategy.lower()}_pro_cyb'],
        ]
    if 'all' in bt_mode or 'res' in bt_mode:
        s_res = '' if freq == '3s' else '_l2p'
        params_list += [
            [f'{strategy}_sp{s_res}', code_vol_dict_sh, signal_lib_dict['res_SH'], f'-{strategy.lower()}_res_sh'],
            [f'{strategy}_sp{s_res}', code_vol_dict_sz, signal_lib_dict['res_SZ'], f'-{strategy.lower()}_res_sz'],
            [f'{strategy}_sp{s_res}', code_vol_dict_cyb, signal_lib_dict['res_SZ'], f'-{strategy.lower()}_res_cyb'],
        ]

    for [portfolio, code_vol_dict_sub, signal_lib_sub, suffix_sub] in params_list:
        if len(code_vol_dict_sub) > 0:
            params_new = params.copy()
            params_new.update({
                'portfolio': portfolio,
                'code_vol_dict': code_vol_dict_sub,
                'signal_lib': signal_lib_sub,
                'suffix_name': suffix_sub,
                'overwrite_params': {'is_holo': False}
            })
            if portfolio.endswith('l2p') and strategy != 'Everest1S':
                params_new.update({'freq': '3s_l2p'})
            if strategy == 'Everest1S':
                params_new.update({'freq': '1s'})
                params_new['overwrite_params'].update({'time_list': ['09:30:00', '10:00:00']})
            strategy_params.add_params(params_new)

    # 存储股票池列表
    if debug_code is None:
        code_list_save = {'signal_lib_SH': signal_lib_dict['res_SH'], 'signal_lib_SZ': signal_lib_dict['res_SZ'],
                          'code_list': code_vol_dict,
                          'code_list_sh': code_vol_dict_sh, 'code_list_sz': code_vol_dict_sz,
                          'code_list_cyb': code_vol_dict_cyb}
        os.makedirs(f'/data/user/011668/SP_Data/SP_Params/{strategy}_sp/CodeList', exist_ok=True)
        save_json_file(code_list_save, f'/data/user/011668/SP_Data/SP_Params/{strategy}_sp/CodeList/code_list_{bt_date}.json')


def kunlun_sp_voting_config(strategy, bt_date, strategy_params, bt_mode='all', debug_code=None):
    cb_type = strategy.split('_')[-1]
    signal_lib_dict = {'res': get_sp_lib(bt_date, strategy, 'res'), 'pro': get_sp_lib(bt_date, strategy, 'pro')}
    out_dir = 'BT_Track/Kunlun' if debug_code is None else 'BT_Track_Debug/Kunlun'
    params = {
        'bt_type': 'sp',
        'st_date': bt_date,
        'ed_date': bt_date,
        'strategy': 'Kunlun',
        'executor_str': 'Executor.ExecutorKunlunSPVoting',
        'param_dir_bt': f'SP_Params/{strategy}/Params_{bt_date}',
        'out_dir': out_dir,  # 输出结果路径
    }

    param_dir_list_cb = {'Kunlun_mix': {'o32': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_mix',
                                        'o45': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_mix_JS',
                                        'o45_sh': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_mix_JS_SH'},
                         'Kunlun_pure': {'o32': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_pure',
                                         'o45': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_pure_JS',
                                         'o45_sh': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_pure_JS_SH'}}
    param_dir_o32, param_dir_o45 = param_dir_list_cb[strategy]['o32'], param_dir_list_cb[strategy]['o45']
    param_dir_o45_sh = param_dir_list_cb[strategy]['o45_sh']
    code_vol_dict_o32 = GetCodeVol(bt_date, bt_date).get_sp_code(f'Kunlun_sp_{cb_type}_o32')
    code_vol_dict_o32_sh, code_vol_dict_o32_sz, code_vol_dict_o32_cyb = split_code_vol_dict_by_market(strategy, code_vol_dict_o32)
    code_vol_dict_o45_sjs = GetCodeVol(bt_date, bt_date).get_sp_code(f'Kunlun_sp_{cb_type}_o45')
    code_vol_dict_o45_sh, code_vol_dict_o45_sz, code_vol_dict_o45_cyb = split_code_vol_dict_by_market(strategy, code_vol_dict_o45_sjs)
    code_vol_dict_o45_sh = GetCodeVol(bt_date, bt_date).get_sp_code(f'Kunlun_sp_{cb_type}_o45_sh')

    params_list = []
    if 'all' in bt_mode or 'pro' in bt_mode:
        params_list += [
            [strategy, code_vol_dict_o32_sh, signal_lib_dict['pro'], param_dir_o32, f'-{strategy}_pro_sh'],
            [f'{strategy}_l2p', code_vol_dict_o32_sz, signal_lib_dict['pro'], param_dir_o32, f'-{strategy}_pro_sz'],
            [f'{strategy}_l2p', code_vol_dict_o32_cyb, signal_lib_dict['pro'], param_dir_o32, f'-{strategy}_pro_cyb'],
            [strategy, code_vol_dict_o45_sh, signal_lib_dict['pro'], param_dir_o45_sh, f'-{strategy}_JS_pro_sh'],
            [f'{strategy}_l2p', code_vol_dict_o45_sz, signal_lib_dict['pro'], param_dir_o45, f'-{strategy}_JS_pro_sz'],
            [f'{strategy}_l2p', code_vol_dict_o45_cyb, signal_lib_dict['pro'], param_dir_o45, f'-{strategy}_JS_pro_cyb'],
        ]
    if 'all' in bt_mode or 'res' in bt_mode:
        params_list += [
            [strategy, code_vol_dict_o32_sh, signal_lib_dict['res'], param_dir_o32, f'-{strategy}_res_sh'],
            [f'{strategy}', code_vol_dict_o32_sz, signal_lib_dict['res'], param_dir_o32, f'-{strategy}_res_sz'],
            [f'{strategy}', code_vol_dict_o32_cyb, signal_lib_dict['res'], param_dir_o32, f'-{strategy}_res_cyb'],
            [strategy, code_vol_dict_o45_sh, signal_lib_dict['res'], param_dir_o45_sh, f'-{strategy}_JS_res_sh'],
            [f'{strategy}', code_vol_dict_o45_sz, signal_lib_dict['res'], param_dir_o45, f'-{strategy}_JS_res_sz'],
            [f'{strategy}', code_vol_dict_o45_cyb, signal_lib_dict['res'], param_dir_o45, f'-{strategy}_JS_res_cyb'],
        ]

    for [portfolio, code_vol_dict_sub, signal_lib_sub, param_dir_sub, suffix_sub] in params_list:
        if len(code_vol_dict_sub) > 0:
            params_new = params.copy()
            params_new.update({
                'portfolio': portfolio,
                'code_vol_dict': code_vol_dict_sub,
                'signal_lib': signal_lib_sub,
                'param_dir': param_dir_sub,
                'suffix_name': suffix_sub,
            })
            if portfolio.endswith('l2p'):
                params_new.update({'freq': '3s_l2p'})
                # params_new.update({'overwrite_params': {'delay': [0.04, 0.04]}})
            strategy_params.add_params(params_new)

    if debug_code is None:
        code_list_kunlun = {'o32': {'code_list': list(code_vol_dict_o32.keys()), 'sh': list(code_vol_dict_o32_sh.keys()),
                                    'sz': list(code_vol_dict_o32_sz.keys()), 'cyb': list(code_vol_dict_o32_cyb.keys())},
                            'o45': {'code_list': list(code_vol_dict_o45_sh.keys()) + list(code_vol_dict_o45_sjs.keys()),
                                    'sh': list(code_vol_dict_o45_sh.keys()), 'sz': list(code_vol_dict_o45_sz.keys()),
                                    'cyb': list(code_vol_dict_o45_cyb.keys())}}
        os.makedirs('/data/user/011668/SP_Data/SP_Params/Kunlun_sp/CodeList', exist_ok=True)
        save_json_file(code_list_kunlun, f'/data/user/011668/SP_Data/SP_Params/Kunlun_sp/CodeList/code_list_{cb_type}_{bt_date}.json')


def split_code_vol_dict_by_market(strategy, code_vol_dict):
    # 按交易所来看
    code_vol_dict_sh, code_vol_dict_sz, code_vol_dict_cyb = {}, {}, {}
    if strategy in ['Albest', 'Everest', 'Everest1S']:
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
