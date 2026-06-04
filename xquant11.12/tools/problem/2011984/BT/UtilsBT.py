import numpy as np
from DataAPI.DataView import file_list_dir, load_json_file
from DataAPI.TradingDay import trading_day
from DataAPI.DataTools import check_lib_code_existing


def check_lib_list(signal_lib_list, code_list, st_date, ed_date, exist_print=False):
    for signal_lib in signal_lib_list:
        print('Check: ', signal_lib)
        for trade_date in trading_day(st_date, ed_date):
            no_existing_list = check_lib_code_existing(signal_lib, trade_date, code_list)
            if len(no_existing_list) > 0:
                print(signal_lib, trade_date, no_existing_list)
            elif exist_print:
                print(f'{signal_lib} {trade_date} √')


def check_lib(signal_lib, code_list, st_date, ed_date):
    res = True
    for trade_date in trading_day(st_date, ed_date):
        no_existing_list = check_lib_code_existing(signal_lib, trade_date, code_list)
        rat = f'{len(code_list) - len(no_existing_list)}/{len(code_list)}'
        if len(no_existing_list) > 0:
            no_existing_print = str(no_existing_list) if len(no_existing_list) <= 5 else f'{str(no_existing_list[:5])[:-1]}...'
            print(f'Check: {signal_lib} {trade_date} {rat} 缺失{len(no_existing_list)}只标的 {no_existing_print}')
            res = False
        else:
            print(f'Check: {signal_lib} {rat} √')
    return res


def overwrite_dy_triggers(trigger_path, code_list):
    # 更新动态阈值
    overwrite_params_by_code = {}
    all_code_file = file_list_dir(trigger_path)
    for code in code_list:
        if f'{code}.json' in all_code_file:
            code_trigger = load_json_file(f'{trigger_path}/{code}.json')
            overwrite_params_by_code.update({code: {'triggers_by_date': code_trigger}})
        else:
            print('No Triggers: ', code)
            overwrite_params_by_code.update({code: {'triggers': {'longTriggerRatio': 99999, 'shortTriggerRatio': -99999, 'longCloseRatio': 0,
                                                                 'shortCloseRatio': 0, 'longRiskRatio': -0.2, 'shortRiskRatio': 0.2}}})
    return overwrite_params_by_code


def check_triggers(code_list, save_path):
    all_file = file_list_dir(save_path)
    invalid_code_list = []
    for f in all_file:
        triggers = load_json_file(f'{save_path}/{f}')
        for i, j in triggers.items():
            if np.abs(j['longTriggerRatio']) > 100 or np.abs(j['shortTriggerRatio']) > 100:
                invalid_code_list.append(f[:-5])
                break
    print(f'{len(set(all_file))} / {len(set(code_list))}, 99999数量：{len(invalid_code_list)}')
    if len(invalid_code_list) > 0:
        print(invalid_code_list)
    return invalid_code_list
