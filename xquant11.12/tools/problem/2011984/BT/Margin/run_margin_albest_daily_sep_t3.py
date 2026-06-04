"""Albest策略（股票策略）回测main函数——update@2021.3.26"""

import datetime
import pandas as pd
from BT.RunBT import RunBT
from BT.BT_System.StrategyParams import StrategyParams, combine_params
from DataAPI.GetCodeVol import get_all_code
from DataAPI.TradingDay import trading_day
from DataAPI.DataView import file_exist, load_excel_file
from BT.UtilsBT import check_lib_code_existing
from BT.Dy_Triggers.SignalCVIntra import Task
from Utils.LinkMessage import LinkMessage


mode = 'spark'  # spark, local


signal_lib_sh, signal_lib_sz = 'ray_barwa_20220201_20220414', 'ray_barwa_20220201_20220414_order'
signal_lib_l2p = 'Albest20211101Order036Signals'  # Albest20220201Order036Signals


def main():
    if datetime.datetime.now().hour < 12:
        n_list = [10, 9, 8, 7, 6, 5, 4, 3, 2]
    else:
        n_list = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

    for n in n_list:
        trade_date = is_update(n=n)
        if trade_date:
            print('开始更新：', trade_date)
            code_list = get_code_list_date(trade_date)
            if check_signal(trade_date, code_list):
                if check_file_existing(trade_date):
                    print(f'{trade_date} Barwa BT 已更新')
                else:
                    triggers(trade_date, trade_date)
                    run_single_date(trade_date, trade_date)
                    check_final(trade_date, code_list)
            else:
                lm = LinkMessage()
                lm.sendMessage("011668", f"{trade_date} Barwa bt 缺失信号")
            if not check_file_existing(trade_date):
                lm = LinkMessage()
                lm.sendMessage("011668", f"{trade_date} Barwa bt 更新失败")
        else:
            print(f'今天不需要更新：', trade_date)


def check_final(trade_date, code_list):
    code_list_sh = [x for x in code_list if x.endswith('.SH')]
    code_list_sz = [x for x in code_list if x.endswith('.SZ')]
    abs_path = f'/data/user/011668/MarginSelect/AlbestDaily/bt-{trade_date}'
    data_sh = pd.read_excel(f'{abs_path}/margin-ExecutorAlbestSPIntra-{signal_lib_sh}/TotalSummary.xls', index_col=0)
    sh_no_list = set(code_list_sh) - set(data_sh.index)
    data_sz = pd.read_excel(f'{abs_path}/margin-ExecutorAlbestSPIntra-{signal_lib_sz}/TotalSummary.xls', index_col=0)
    sz_no_list = set(code_list_sz) - set(data_sz.index)
    data_l2p = pd.read_excel(f'{abs_path}/margin-ExecutorAlbestSPIntra-{signal_lib_l2p}/TotalSummary.xls', index_col=0)
    l2p_no_list = set(code_list_sz) - set(data_l2p.index)
    lm = LinkMessage()
    if len(sh_no_list) == 0 and len(sz_no_list) == 0 and len(l2p_no_list) == 0:
        lm.sendMessage("011668", f"{trade_date} Barwa bt已更新")
        lm.sendMessage("015619", f"{trade_date} Barwa bt已更新")
        lm.sendMessage("018106", f"{trade_date} Barwa bt已更新")
    else:
        txt = ''
        if len(sh_no_list) > 0:
            txt += f'上海主板缺失{len(sh_no_list)}只标的{"" if len(sh_no_list) > 20 else sh_no_list}；'
        if len(sz_no_list) > 0:
            txt += f'深圳主板缺失{len(sz_no_list)}只标的{"" if len(sz_no_list) > 20 else sz_no_list}；'
        if len(l2p_no_list) > 0:
            txt += f'深圳l2p缺失{len(l2p_no_list)}只标的{"" if len(l2p_no_list) > 20 else l2p_no_list}；'
        lm.sendMessage("011668", f"{trade_date} Barwa bt已更新但有缺失。{txt}")


def check_signal(trade_date, code_list):
    code_list_sh = [x for x in code_list if x.endswith('.SH')]
    code_list_sz = [x for x in code_list if x.endswith('.SZ')]

    no_existing_list_sh = check_lib_code_existing(signal_lib_sh, trade_date, code_list_sh)
    no_existing_list_sz = check_lib_code_existing(signal_lib_sz, trade_date, code_list_sz)
    no_existing_list_l2p = check_lib_code_existing(signal_lib_l2p, trade_date, code_list_sz)

    if len(no_existing_list_sh) == 0 and len(no_existing_list_sz) == 0 and len(no_existing_list_l2p) == 0:
        return True
    print(f'{signal_lib_sh}缺失{len(no_existing_list_sh)}只：', no_existing_list_sh)
    print(f'{signal_lib_sz}缺失{len(no_existing_list_sz)}只：', no_existing_list_sz)
    print(f'{no_existing_list_l2p}缺失{len(no_existing_list_l2p)}只：', no_existing_list_sz)

    lm = LinkMessage()
    txt_add = ''
    if len(no_existing_list_sh) > 0:
        txt_add += f'{signal_lib_sh}缺失{len(no_existing_list_sh)}只：{no_existing_list_sh}'
    if len(no_existing_list_sz) > 0:
        txt_add += f'{signal_lib_sz}缺失{len(no_existing_list_sz)}只：{no_existing_list_sz}'
    if len(no_existing_list_l2p) > 0:
        txt_add_l2p = f'{signal_lib_l2p}缺失{len(no_existing_list_l2p)}只：{no_existing_list_l2p}'
        txt_add += txt_add_l2p
        lm.sendMessage("015629", f"{trade_date} Barwa bt 缺失信号。{txt_add_l2p}")

    lm.sendMessage("011668", f"{trade_date} Barwa bt 缺失信号。{txt_add}")
    lm.sendMessage("015390", f"{trade_date} Barwa bt 缺失信号。{txt_add}")
    lm.sendMessage("015619", f"{trade_date} Barwa bt 缺失信号。{txt_add}")
    lm.sendMessage("018106", f"{trade_date} Barwa bt 缺失信号。{txt_add}")
    return False


def check_file_existing(trade_date):
    path_sh = f'/data/user/011668/MarginSelect/AlbestDaily/bt-{trade_date}/margin-ExecutorAlbestSPIntra-{signal_lib_sh}/result_daily.xls'
    path_sz = f'/data/user/011668/MarginSelect/AlbestDaily/bt-{trade_date}/margin-ExecutorAlbestSPIntra-{signal_lib_sz}/result_daily.xls'
    path_l2p = f'/data/user/011668/MarginSelect/AlbestDaily/bt-{trade_date}/margin-ExecutorAlbestSPIntra-{signal_lib_l2p}/result_daily.xls'
    for path_ in [path_sh, path_sz, path_l2p]:
        if file_exist(path_):
            data_ = load_excel_file(path_)
            if data_.empty or data_.loc[0, '总盈利'] == 0:
                return False
        else:
            return False
    return True


def run_single_date(st_date, ed_date):
    strategy_params = StrategyParams(mode, 'bt')
    for bt_date in trading_day(st_date, ed_date):
        code_list = get_code_list_date(bt_date)
        get_config_albest_dynamic(strategy_params, bt_date, code_list)
        get_config_albest_dynamic_l2p(strategy_params, bt_date, code_list)
        print('Finish: ', bt_date)
    bt = RunBT(strategy_params.strategy_params, mode, 'bt', max_tasks=600)
    bt.start_bt()
    bt.analyze_result(multiprocess_nums=1, is_transfer_file=False)


def get_config_albest_dynamic(strategy_params, bt_date, code_list):
    strategy, portfolio = 'Albest', 'margin'  # 策略与组合
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


def get_config_albest_dynamic_l2p(strategy_params, bt_date, code_list):
    strategy, portfolio = 'Albest', 'margin'  # 策略与组合
    code_list_sz = [x for x in code_list if x.endswith('.SZ')]

    code_vol_dict_sz = dict([(code, 1e10) for code in code_list_sz])
    overwrite_params_by_code_sz = combine_params(code_vol_dict_sz, bt_date, bt_date, signal_lib_l2p, strategy='Albest', add_trigger=False)

    params_dynamic = {
        'st_date': bt_date,
        'ed_date': bt_date,
        'strategy': strategy,
        'portfolio': portfolio,
        'trigger_lib': 'DynamicTriggers1000',
        'freq': '3s_l2p',
        'l2p_lib': 'Channel036STickDataLib',
        'executor_str': 'Executor.ExecutorAlbestSPIntra',
        'param_dir_bt': f'MarginSelect/Params/bt-{bt_date}-{bt_date}/params',
        'out_dir': f'MarginSelect/{strategy}Daily',
        'overwrite_params': {'order_capacity_ratio': 0.3},
        'suffix_name': '',
        'code_vol_dict': dict([(code, 1e10) for code in code_list_sz]),
        'signal_lib': signal_lib_l2p,
        'overwrite_params_by_code': overwrite_params_by_code_sz,
    }

    strategy_params.add_params(params_dynamic)


def get_code_list(st_date, ed_date):
    key_st_date = trading_day(st_date, ed_date)[0]
    key_ed_date = trading_day(st_date, ed_date)[-1]
    code_list1 = get_all_code(key_st_date, type='stock')
    code_list2 = get_all_code(key_ed_date, type='stock')
    code_list = list(sorted(set(code_list1 + code_list2))) + ['689009.SH']
    return code_list


def get_code_list_date(trade_date):
    from xquant.factordata import FactorData
    fd = FactorData()
    code_list = get_all_code(trade_date, type='stock') + ['689009.SH']
    df1 = fd.get_factor_value("Basic_factor", code_list, [trade_date], ["trade_status"])
    df2 = df1[(df1['trade_status'] != 'N') & (df1['trade_status'] != '停牌')]
    code_list_valid = list(sorted(df2.loc[trade_date].index))
    return code_list_valid


def triggers(st_date, ed_date):
    code_list = get_code_list(st_date, ed_date)
    code_list_sh = [x for x in code_list if x.endswith('.SH')]
    code_list_sz = [x for x in code_list if x.endswith('.SZ')]
    Task(code_list_sh, st_date, ed_date, 'Albest', signal_lib_sh, save_path='lib', time_list=['10:00:00']).start(mode=mode)
    Task(code_list_sz, st_date, ed_date, 'Albest', signal_lib_sz, save_path='lib', time_list=['10:00:00']).start(mode=mode)
    Task(code_list_sz, st_date, ed_date, 'Albest', signal_lib_l2p, save_path='lib', time_list=['10:00:00'],
         tag_lib=signal_lib_l2p, mock_lib='Channel036STickDataLib', is_add_mock=False).start(mode=mode)


def is_update(n=2):
    # n 为 T - N 日
    from xquant.factordata import FactorData

    fa = FactorData()
    trade_date = datetime.datetime.now().strftime("%Y%m%d")
    trading_list = fa.tradingday(fa.tradingday(trade_date, -60)[0], trade_date)
    date_list = fa.tradingday(fa.tradingday(trade_date, -60)[0], trade_date, dateType='ALLDAYS')
    if date_list[-n - 1] in trading_list:
        return date_list[-n - 1]
    else:
        return False


if __name__ == '__main__':
    main()
