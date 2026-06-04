"""Albest的深交所标的，都给Everest交易的结果"""

import pandas as pd
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams
from DataAPI.GetCodeVol import GetCodeVol
from DataAPI.TradingDay import trading_day
from SP.SP_Params import get_sp_lib


def main():
    bt_date = '20220525'
    start_bt(bt_date)
    # sum_res(bt_date)
    # st_date, ed_date = '20220510', '20220513'
    # sum_multi_day(st_date, ed_date)


def sum_multi_day(st_date, ed_date):
    all_trading_day = trading_day(st_date, ed_date)
    multi_res = []
    for bt_date in all_trading_day:
        data = sum_res(bt_date)
        multi_res.append(data[['总盈利']].rename(columns={'总盈利': bt_date}))
    multi_df = pd.concat(multi_res, axis=1).T
    multi_df.loc['Total'] = multi_df.sum()
    return multi_df


def sum_res(bt_date):
    from SP.UtilsSP.resolve_result import summary_sp_data, summary_resolve_result
    from SP.TrackSP.DailyResultTotal import get_bt_summary_result, bt_format

    select_cols = ["总盈利", "交易次数", "获利次数", "胜率", "平均收益率", "交易总市值",
                   "获利收益率", "亏损收益率", "盈亏比", "最大单笔亏损", "平均持仓时间"]
    code_list = list(GetCodeVol(bt_date, bt_date).get_sp_code(f'Everest1S_sp').keys())
    sp_result_everest = pd.DataFrame(summary_resolve_result(bt_date, 'Everest1S', select_code_list=code_list), columns=['Everest1S_sp'])
    sp_data = pd.read_csv(f'/data/user/011668/SP_Data/ResolveData/Albest/{bt_date}_trade.csv', index_col=['code'])
    sp_data = sp_data[(sp_data['portfolio'] == 5160503) | (sp_data['portfolio'] == 5160803) | (sp_data['portfolio'] == 5161206)].loc[code_list]
    sp_result_albest = pd.DataFrame(summary_sp_data(sp_data), columns=['Albest_sp'])

    bt_result = get_bt_summary_result(f'/data/user/011668/BT_Track/Everest_Albest_compare/bt-{bt_date}')
    bt_result = bt_format(bt_result.loc[select_cols])

    data_sum = pd.concat([sp_result_albest, sp_result_everest, bt_result], axis=1)[['Albest_sp', 'Albest_pro', 'Albest_res',
                                                                                    'Everest1S_sp', 'Everest1S_pro', 'Everest1S_res']].T
    return data_sum


def start_bt(bt_date):
    mode = 'local'  # local, spark, ray

    strategy_params = StrategyParams(mode, bt_type='sp')
    for bt_date in trading_day(bt_date, bt_date):
        stock_sp_config('Albest', bt_date, strategy_params)
        stock_sp_config('Everest1S', bt_date, strategy_params)

    sp_track = RunBT(strategy_params.strategy_params, mode, bt_type='sp')
    sp_track.start_bt()
    sp_track.analyze_result(is_transfer_file=False, is_classify_res=True, multiprocess_nums=1)


def stock_sp_config(strategy, bt_date, strategy_params):
    """bt_mode为bt的类型，all为同时pro+res，pro或者res为单独的"""
    executor_stock = {'Albest': 'ExecutorAlbestSPIntra', 'Everest': 'ExecutorEverestSP', 'Everest1S': 'ExecutorAlbestSP1S'}
    param_dir_stock = {'Albest': f'/data/user/666888/Algo/parameters/Algo_{bt_date}',
                       'Everest': f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{bt_date}/JsonParam/',
                       'Everest1S': f'/data/user/011668/SP_Data/SP_Params/LiveParams/Everest/Easy_{bt_date}/JsonParam/',}
    signal_lib_dict = {'res_SH': get_sp_lib(bt_date, strategy, 'res_sh'), 'res_SZ': get_sp_lib(bt_date, strategy, 'res_sz'),
                       'pro': get_sp_lib(bt_date, strategy, 'pro')}
    freq = '1s' if strategy.endswith('1S') else '3s'
    code_vol_dict = GetCodeVol(bt_date, bt_date).get_sp_code(f'Everest1S_sp')

    params = {
        'bt_type': 'sp',
        'st_date': bt_date,
        'ed_date': bt_date,
        'strategy': strategy,
        'executor_str': 'Executor.' + executor_stock[strategy],
        'freq': freq,
        'param_dir': param_dir_stock[strategy],  # 实盘参数路径
        'param_dir_bt': f'SP_Params/{strategy}_sp/Params_{bt_date}',
        'out_dir': 'BT_Track/Everest_Albest_compare',  # 输出结果路径
    }

    s_res = '' if freq == '3s' else '_l2p'
    params_list = [
        [f'{strategy}_sp_l2p', code_vol_dict, signal_lib_dict['pro'], f'{strategy}_pro'],
        [f'{strategy}_sp{s_res}', code_vol_dict, signal_lib_dict['res_SZ'], f'{strategy}_res'],
    ]

    for [portfolio, code_vol_dict_sub, signal_lib_sub, output_dir_name] in params_list:
        if len(code_vol_dict_sub) > 0:
            params_new = params.copy()
            params_new.update({
                'portfolio': portfolio,
                'code_vol_dict': code_vol_dict_sub,
                'signal_lib': signal_lib_sub,
                'output_dir_name': output_dir_name,
                'overwrite_params': {'is_holo': False}
            })
            if portfolio.endswith('l2p'):
                params_new['overwrite_params'].update({'delay': [0.04, 0.04]})
            strategy_params.add_params(params_new)


if __name__ == '__main__':
    main()
