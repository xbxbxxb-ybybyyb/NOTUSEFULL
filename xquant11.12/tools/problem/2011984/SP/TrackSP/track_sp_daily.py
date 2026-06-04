"""跟踪转债不同规模与不同开仓时间结果——update @2021.4.20"""

import os
import pandas as pd
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams
from BT.UtilsBT import check_lib
from DataAPI.DataView import load_json_file
from DataAPI.GetCodeVol import GetCodeVol
from DataAPI.TradingDay import trading_day
from SP.UtilsSP.LoadSPFile import load_sp_daily_result, strategy_sp_trading
from SP.SP_Params import get_sp_lib


def main():
    mode = 'spark'  # local, spark, ray
    bt_date = '20220126'
    tp = TrackDiffParams(bt_date, mode)

    strategy_params = StrategyParams(mode, bt_type='sp')
    tp.stock_pro_bt(strategy_params, bt_date)
    tp.track_stock_diff_mv(strategy_params, bt_date)
    tp.track_stock_diff_oc(strategy_params, bt_date)
    tp.track_stock_diff_open_time(strategy_params, bt_date)
    tp.cb_pro_bt(strategy_params, bt_date)
    tp.track_kunlun_diff_size(strategy_params, bt_date)
    tp.track_kunlun_diff_open_time(strategy_params, bt_date)
    tp.track_kunlun_diff_liquidity_ratio(strategy_params, bt_date)
    tp.track_kunlun_mix_voting(strategy_params, bt_date)

    sp_track = RunBT(strategy_params.strategy_params, mode, bt_type='sp', max_tasks=600)
    sp_track.start_bt()
    # sp_track.analyze_result(multiprocess_nums=20)


class TrackDiffParams:
    def __init__(self, bt_date, mode='local'):
        self.bt_date = bt_date
        self.all_oc = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
        self.all_size = ['10_20', '25_50', '50_100', '75_150', '100_200', '150_300', '200_400', '250_500']
        self.all_open_time_stock = ['093045', '093115', '093200', '093300', '093400', '093500', '094000', '094500', '095000', '100000']
        self.all_open_time_cb = ['093115', '093200', '093300', '093400', '093500', '094000', '094500', '095000', '100000']
        self.all_liquidity_ratio = [0.01, 0.03, 0.05, 0.1, 0.15, 0.2]
        self.mode = mode

    def stock_pro_bt(self, strategy_params, bt_date):
        for strategy in ['Albest', 'Everest', 'Everest1S']:
            if not strategy_sp_trading(strategy, bt_date):
                continue
            params_stock = init_stock_params(bt_date, strategy, 'pro')
            params_stock.update({
                'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
                'output_dir_name': f'sp_pro',
            })
            strategy_params.add_params(params_stock, sep_by_l2p=True)

    def track_stock_diff_oc(self, strategy_params, bt_date):
        for strategy in ['Albest', 'Everest', 'Everest1S']:
            if not strategy_sp_trading(strategy, bt_date):
                continue
            code_vol_dict = GetCodeVol(bt_date, bt_date).get_sp_code(f'{strategy}_sp')
            order_capacity = generate_order_capacity(list(code_vol_dict.keys()), bt_date, strategy)
            params_stock = init_stock_params(bt_date, strategy, 'pro')
            for order_capacity_ratio in self.all_oc:
                params_stock.update({
                    'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
                    'overwrite_params': {'order_capacity_ratio': order_capacity_ratio},
                    'overwrite_params_by_code': dict({x: {'order_capacity': y} for (x, y) in order_capacity.items()}),
                    'output_dir_name': f'diff_oc_{order_capacity_ratio}',
                })
                strategy_params.add_params(params_stock, sep_by_l2p=True)

    def track_stock_diff_open_time(self, strategy_params, bt_date):
        for strategy in ['Albest', 'Everest']:
            if not strategy_sp_trading(strategy, bt_date):
                continue
            for diff_open_time in self.all_open_time_stock:
                params_stock = init_stock_params(bt_date, strategy)
                params_stock.update({
                    'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
                    'overwrite_params': {'trading_start_morning': f'{diff_open_time[0:2]}:{diff_open_time[2:4]}:{diff_open_time[4:6]}'},
                    'output_dir_name': f'open_time_{diff_open_time}',
                })
                strategy_params.add_params(params_stock, sep_by_l2p=True)

    def track_stock_diff_mv(self, strategy_params, bt_date):
        for strategy in ['Albest', 'Everest']:
            if not strategy_sp_trading(strategy, bt_date):
                continue
            code_vol_dict = GetCodeVol(bt_date, bt_date).get_sp_code(f'{strategy}_sp')
            params_stock = init_stock_params(bt_date, strategy, 'pro')
            params_stock.update({
                'out_dir': f'BT_Track_Daily/{strategy}',  # 输出结果路径
                'overwrite_params_by_code': dict({x: {'init_qty': 1e10} for (x, y) in code_vol_dict.items()}),
                'output_dir_name': f'mv_infinite',
            })
            strategy_params.add_params(params_stock, sep_by_l2p=True)

    def cb_pro_bt(self, strategy_params, bt_date):
        for strategy in ['Kunlun_mix', 'Kunlun_pure']:
            if not strategy_sp_trading(strategy, bt_date):
                continue
            params_cb = init_cb_params(bt_date, strategy)
            params_cb.update({
                'executor_str': 'Executor.ExecutorKunlunSPVoting',
                'out_dir': f'BT_Track_Daily/{strategy}',
                'output_dir_name': f'sp_pro',
            })
            strategy_params.add_params(params_cb, sep_by_l2p=True)

    def track_kunlun_diff_size(self, strategy_params, bt_date):
        for strategy in ['Kunlun_mix']:  # 'Kunlun_mix', 'Kunlun_pure'
            if not strategy_sp_trading(strategy, bt_date):
                continue
            for diff_size in self.all_size:
                params_cb = init_cb_params(bt_date, strategy)
                params_cb.update({
                    'executor_str': 'Executor.ExecutorKunlunSPVoting',
                    'out_dir': f'BT_Track_Daily/{strategy}',
                    'overwrite_params': {'maxTurnoverPerOrder': int(diff_size.split('_')[0]) * 1e4,
                                         'maxExposure': int(diff_size.split('_')[1]) * 1e4},
                    'output_dir_name': f'diff_size_{diff_size}',
                })
                strategy_params.add_params(params_cb, sep_by_l2p=True)

    def track_kunlun_diff_open_time(self, strategy_params, bt_date):
        for strategy in ['Kunlun_mix']:  # 'Kunlun_mix', 'Kunlun_pure'
            if not strategy_sp_trading(strategy, bt_date):
                continue
            for diff_open_time in self.all_open_time_cb:
                params_cb = init_cb_params(bt_date, strategy)
                params_cb.update({
                    'executor_str': 'Executor.ExecutorKunlunSPVoting',
                    'out_dir': f'BT_Track_Daily/{strategy}',
                    'overwrite_params': {'trading_start_morning': f'{diff_open_time[0:2]}:{diff_open_time[2:4]}:{diff_open_time[4:6]}'},
                    'output_dir_name': f'open_time_{diff_open_time}',
                })
                strategy_params.add_params(params_cb, sep_by_l2p=True)

    def track_kunlun_diff_liquidity_ratio(self, strategy_params, bt_date):
        for strategy in ['Kunlun_mix']:  # 'Kunlun_mix', 'Kunlun_pure'
            if not strategy_sp_trading(strategy, bt_date):
                continue
            for diff_liquidity_ratio in self.all_liquidity_ratio:
                params_cb = init_cb_params(bt_date, strategy)
                params_cb.update({
                    'executor_str': 'Executor.ExecutorKunlunSPVoting',
                    'out_dir': f'BT_Track_Daily/{strategy}',
                    'overwrite_params': {'liquidity_ratio': diff_liquidity_ratio},
                    'output_dir_name': f'diff_liquidity_{diff_liquidity_ratio}',
                })
                strategy_params.add_params(params_cb, sep_by_l2p=True)

    def track_kunlun_mix_voting(self, strategy_params, bt_date):
        strategy = 'Kunlun_mix'
        fz_lib = 'WuKongFZSignals'
        if not strategy_sp_trading(strategy, bt_date):
            return
        params_cb = init_cb_params(bt_date, strategy)

        overwrite_params_by_code = {}
        code_s = list(params_cb['code_vol_dict'].keys())
        # if not check_lib(fz_lib, code_s, bt_date, bt_date):
        #     raise ValueError(f'{fz_lib} 信号缺失，请检查')
        lib_res = get_sp_lib(bt_date, 'Kunlun_mix', 'res')

        for code in code_s:
            code_trigger = \
            load_json_file(f'/data/user/011668/CVTriggers/SPTriggers/Kunlun/{bt_date}/{lib_res}/{code}.json')[bt_date]
            overwrite_params_by_code.update({code: {'vt_triggers': code_trigger}})

        params_cb.update({
            'executor_str': 'Executor.ExecutorKunlunSPVoting',
            'signal_lib': fz_lib,
            'out_dir': f'BT_Track_Daily/{strategy}',
            'overwrite_params_by_code': overwrite_params_by_code,
        })

        params_cb_7v4 = params_cb.copy()
        params_cb_7v4.update({
            'overwrite_params': {'vt_params': {'vt_name_list': ['1min', '2min', '3min', '5min', '6min', '7min', '8min'], 'open_counter': 4}},
            'output_dir_name': 'voting_7v4',
        })
        strategy_params.add_params(params_cb_7v4, sep_by_l2p=True)

        params_cb_10v5 = params_cb.copy()
        params_cb_10v5.update({
            'overwrite_params': {'vt_params': {'vt_name_list': ['1.75min', '2.75min', '3.25min', '3.5min', '5.75min',
                                                                '6.25min', '6.5min', '7.25min', '7.5min', '8min'], 'open_counter': 5},
                                 'vt_name': '8.75min'},
            'output_dir_name': 'voting_10v5',
        })
        strategy_params.add_params(params_cb_10v5, sep_by_l2p=True)


def generate_order_capacity(code_list, bt_date, strategy):
    order_capacity_dict = {}
    for code in code_list:
        try:
            if strategy == 'Albest':
                order_capacity2_dir = f'/data/user/666888/OrderCapacity/{code}/OrderCapacity.json'
            else:  # strategy == 'Everest':
                order_capacity2_dir = f'/data/user/015629/OrderCapacity/{code}/OrderCapacity.json'
            order_capacity2 = load_json_file(order_capacity2_dir)['OrderCapacity']
            order_capacity2 = {bt_date: order_capacity2[bt_date]}
            order_capacity_dict.update({code: order_capacity2})
        except:
            continue
    return order_capacity_dict


def init_stock_params(bt_date, stock_type='Albest', bt_type='pro'):
    params = {
        'bt_type': 'sp',
        'st_date': bt_date,
        'ed_date': bt_date,
        'overwrite_params': {'is_holo': False}
    }
    if stock_type == 'Albest':
        params_albest = params.copy()
        params_albest.update({
            'strategy': 'Albest',
            'portfolio': 'Albest_sp',
            'executor_str': 'Executor.ExecutorAlbestSPIntra',
            'signal_lib': get_sp_lib(bt_date, 'Albest', bt_type),
            'code_vol_dict': GetCodeVol(bt_date, bt_date).get_sp_code('Albest_sp'),
            'param_dir': f'/data/user/666888/Algo/parameters/Algo_{bt_date}',  # 实盘参数路径
            'param_dir_bt': f'SP_Params/Albest_sp/Params_{bt_date}',
        })
        return params_albest
    elif stock_type == 'Everest':
        params_everest = params.copy()
        params_everest.update({
            'strategy': 'Everest',
            'portfolio': 'Everest_sp',
            'executor_str': 'Executor.ExecutorEverestSP',
            'signal_lib': get_sp_lib(bt_date, 'Everest', bt_type),
            'code_vol_dict': GetCodeVol(bt_date, bt_date).get_sp_code('Everest_sp'),
            'param_dir': f'/data/user/015629/Easy/productionParams/Easy_{bt_date}/JsonParam/',  # 实盘参数路径
            'param_dir_bt': f'SP_Params/Everest_sp/Params_{bt_date}',
        })
        return params_everest
    elif stock_type == 'Everest1S':
        params_everest = params.copy()
        params_everest.update({
            'strategy': 'Everest1S',
            'portfolio': 'Everest1S_sp',
            'freq': '1s',
            'executor_str': 'Executor.ExecutorAlbestSP1S',  # ExecutorEverestSP1S
            'signal_lib': get_sp_lib(bt_date, 'Everest1S', bt_type),
            'code_vol_dict': GetCodeVol(bt_date, bt_date).get_sp_code('Everest1S_sp'),
            'param_dir': f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{bt_date}/JsonParam/',  # 实盘参数路径
            'param_dir_bt': f'SP_Params/Everest1S_sp/Params_{bt_date}',
        })
        return params_everest


def init_cb_params(bt_date, cb_type='mix'):
    params = {
        'bt_type': 'sp',
        'st_date': bt_date,
        'ed_date': bt_date,
        'strategy': 'Kunlun',
        'executor_str': 'Executor.ExecutorKunlunSP',
    }
    if cb_type in ['mix', 'Kunlun_mix']:
        params_mix = params.copy()
        params_mix.update({
            'portfolio': 'Kunlun_mix',
            'code_vol_dict': GetCodeVol(bt_date, bt_date).get_sp_code('Kunlun_sp_mix'),
            'signal_lib': get_sp_lib(bt_date, 'Kunlun_mix', 'pro'),
            'param_dir': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}',  # 实盘参数路径
            'param_dir_bt': f'SP_Params/Kunlun_mix/Params_{bt_date}',
        })
        return params_mix
    elif cb_type in ['pure', 'Kunlun_pure']:
        params_pure = params.copy()
        params_pure.update({
            'portfolio': 'Kunlun_pure',
            'code_vol_dict': GetCodeVol(bt_date, bt_date).get_sp_code('Kunlun_sp_pure'),
            'signal_lib': get_sp_lib(bt_date, 'Kunlun_pure', 'pro'),
            'param_dir': f'/data/user/666888/WuKong/parameters/WuKong_{bt_date}_pure',  # 实盘参数路径
            'param_dir_bt': f'SP_Params/Kunlun_pure/Params_{bt_date}',
        })
        return params_pure


if __name__ == '__main__':
    main()
