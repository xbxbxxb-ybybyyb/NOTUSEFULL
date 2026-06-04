"""生成策略需要的参数，update @2021.11.8"""

from copy import deepcopy
from BT.BT_System.CombineData import get_origin_data_list
from DataAPI.DataView import load_json_file, file_exist
from DataAPI.DataTools import check_lib_existing, check_lib_code_existing
from DataAPI.TradingDay import trading_day
from Utils.UtilsCode import code_classify
from xquant.factordata import FactorData


class StrategyParams:
    def __init__(self, mode, bt_type='bt'):
        self.mode = mode
        self.type = bt_type
        self.strategy_params = []
        self.__signal_lib_code_dict = {}

    def add_params(self, single_strategy_param, sep_by_l2p=False):
        strategy_params = {
            'bt_type': 'bt',
            'st_date': '',  # 开始日期
            'ed_date': '',  # 结束日期
            'strategy': '',  # 策略名
            'portfolio': '',  # 组合名
            'freq': '3s',  # 频率
            'code_vol_dict': dict(),  # 股票与初始额度的dict
            'trigger_lib': '',
            'executor_str': '',  # 下单文件
            'signal_lib': '',  # 信号库
            'param_dir': '',   # 原始参数文件路径
            'param_dir_bt': '',  # 用于bt的参数文件路径
            'dir_path': dict(),
            'out_dir': '',
            'output_dir': '',  # 输出文件路径
            'suffix_name': '',
            'overwrite_params': dict(),  # 重新写入的参数
            'overwrite_params_by_code': dict(),  # 重新写入的参数（按股票来）
        }

        portfolio = single_strategy_param['portfolio']
        st_date = single_strategy_param['st_date']
        ed_date = single_strategy_param['ed_date']
        bt_date = f'{st_date}-{ed_date}' if st_date != ed_date else str(st_date)
        signal_lib = single_strategy_param['signal_lib']
        if signal_lib not in self.__signal_lib_code_dict.keys():
            self.__signal_lib_code_dict.update({signal_lib: []})
        self.__signal_lib_code_dict[signal_lib] += list(single_strategy_param['code_vol_dict'].keys())
        out_dir = single_strategy_param['out_dir']
        executor_str = single_strategy_param['executor_str'].split('.')[-1]
        suffix_name = single_strategy_param['suffix_name'] if 'suffix_name' in single_strategy_param.keys() else ''
        path_prefix = '011668/' if self.mode == 'spark' else ''
        bt_type = 'bt' if self.type == 'sp' else self.type
        if 'output_dir_name' in single_strategy_param.keys():
            output_dir = f'{out_dir}/{bt_type}-{bt_date}/{single_strategy_param["output_dir_name"]}'
        else:
            output_dir = f'{out_dir}/{bt_type}-{bt_date}/{portfolio}-{executor_str}-{signal_lib}{suffix_name}'
        data_dir_map = {'Albest_sp': 'stock_sp', 'Everest_sp': 'stock_sp',
                        'Kunlun_mix': 'cb_sp', 'Kunlun_pure': 'cb_sp',
                        'Albest_sp_l2p': 'stock_sp_l2p', 'Everest_sp_l2p': 'stock_sp_l2p',
                        'Kunlun_mix_l2p': 'cb_sp_l2p', 'Kunlun_pure_l2p': 'cb_sp_l2p',
                        'Kunlun_SHJS_mix': 'cb_sp', 'Kunlun_SHJS_pure': 'cb_sp',
                        }
        bt_data_name = data_dir_map[portfolio] if portfolio in data_dir_map.keys() else portfolio
        origin_data_list = get_origin_data_list(bt_data_name, st_date, ed_date)
        if 'param_dir_bt' in single_strategy_param.keys():
            param_dir = single_strategy_param['param_dir_bt']
        else:
            param_dir = f'{output_dir}/params'
        dir_path = {
            'signal_lib': signal_lib,  # 信号库
            # 'origin_data_dir': f'{path_prefix}BT_Data/{bt_data_name}/{bt_date}/',  # 原始数据路径
            'origin_data_list': [f'{path_prefix}{x_}' for x_ in origin_data_list],
            'param_dir': f'{path_prefix}{param_dir}' if param_dir is not None else None,
            'output_dir': f'{path_prefix}{output_dir}',  # 输出结果路径
        }
        single_strategy_param.update({'param_dir_bt': param_dir, 'dir_path': dir_path, 'output_dir': output_dir})

        strategy_params.update(single_strategy_param)
        if not sep_by_l2p:
            self.strategy_params.append(strategy_params)
        else:
            code_vol_dict = strategy_params['code_vol_dict']
            code_vol_dict_l2p = dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SZ')])
            code_vol_dict_nl2p = dict([(x, y) for (x, y) in code_vol_dict.items() if x.endswith('.SH')])
            strategy_params_l2p = deepcopy(strategy_params)
            strategy_params_nl2p = deepcopy(strategy_params)
            strategy_params_nl2p.update({'code_vol_dict': code_vol_dict_nl2p})
            strategy_params_l2p.update({'code_vol_dict': code_vol_dict_l2p})
            strategy_params_l2p['dir_path']['origin_data_list'] = [x.replace('_sp', '_sp_l2p')
                                                                   for x in strategy_params_l2p['dir_path']['origin_data_list']]
            strategy_params_l2p['overwrite_params'].update({'delay': [0.08, 0.08]})
            # if strategy_params['strategy'] == 'Everest1S':
            #     strategy_params_l2p['overwrite_params'].update({'delay': [0.3, 0.3]})
            self.strategy_params.append(strategy_params_l2p)
            self.strategy_params.append(strategy_params_nl2p)

    def check_sp_existing_code(self, trade_date):
        for (signal_lib, code_list) in self.__signal_lib_code_dict.items():
            no_existing_list = check_lib_code_existing(signal_lib, trade_date, list(sorted(set(code_list))))
            status = '√' if len(no_existing_list) == 0 else '×'
            print(f'{trade_date} - {signal_lib}  {" " * (40 - len(signal_lib))} {status} {len(code_list) - len(no_existing_list)}/{len(code_list)}')
            if len(no_existing_list) > 0:
                str_ = f'{str(no_existing_list[0: 5])[:-1]} ......' if len(no_existing_list) > 5 else str(no_existing_list)
                print(f'{" " * 10}{len(no_existing_list)}只信号缺失 {str_}')

    def check_bt_lib(self):
        for signal_lib in self.__signal_lib_code_dict.keys():
            check_lib_existing(signal_lib)

    def reset_signal_lib_code_dict(self):
        self.__signal_lib_code_dict = {}


def load_order_capacity(code, start_date, end_date, strategy):
    if code_classify(code) == 'stock':  # 股票
        order_capacity_dir = f'/data/user/666888/OrderCapacity'
        # if strategy == 'Everest':
        #     order_capacity_dir = f'/data/user/015629/OrderCapacity'
        high_vol_dir = f'/data/user/015629/OrderCapacity'
        if file_exist(f'{order_capacity_dir}/{code}/OrderCapacity.json'):
            order_capacity = load_json_file(f'{order_capacity_dir}/{code}/OrderCapacity.json')['OrderCapacity']
            order_capacity2 = dict([(k, v) for k, v in order_capacity.items() if start_date <= k <= end_date])
        else:
            print(f'No Order Capacity Data for {code}')
            order_capacity2 = []

        if file_exist(f'{high_vol_dir}/{code}/HighVol.json'):
            high_vol = load_json_file(f'{high_vol_dir}/{code}/HighVol.json')['HighVol']
            high_vol2 = dict([(k, v) for k, v in high_vol.items() if start_date <= k <= end_date])
        else:
            print(f'No High Vol Data for {code}')
            high_vol2 = []
        return {'OrderCapacity': order_capacity2, 'HighVol': high_vol2}
    else:
        return {'OrderCapacity': dict(), 'HighVol': 0.0}


def load_dynamic_triggers2(code, start_date, end_date, signal_lib, vt_name_list=None, factor_lib=None):
    fa = FactorData()
    dy_triggers2 = {}
    for trade_date in trading_day(start_date, end_date):
        try:
            triggers = fa.get_factor_value(factor_lib, code, str(trade_date), [signal_lib])[signal_lib].to_dict()
            if vt_name_list is not None:
                triggers = dict([(v1, v2) for (v1, v2) in triggers.items() if v1 in vt_name_list])
            dy_triggers2.update(triggers)
        except:
            print("no signal data for {} in date {} in library {}".format(code, trade_date, 'DynamicTriggers'))
            continue
    return dy_triggers2


def load_dynamic_triggers(code, start_date, end_date, signal_lib, strategy, vt_name_list=None, suffix='', cv_triggers_path=None):
    prefix = 'voting-' if vt_name_list else ''
    if cv_triggers_path is None:
        cv_triggers_path = f'/data/user/011668/CVTriggers/{strategy}/{prefix}{signal_lib}{suffix}'
    dy_triggers = load_json_file(f'{cv_triggers_path}/{code}.json')
    if set(dy_triggers.keys()) == {'longTriggerRatio', 'shortTriggerRatio', 'longRiskRatio', 'longCloseRatio', 'shortCloseRatio', 'shortRiskRatio'}:
        dy_triggers2 = dict([(x, dy_triggers) for x in trading_day(str(start_date), str(end_date))])
    else:
        dy_triggers2 = dict([(k, v) for k, v in dy_triggers.items() if str(int(start_date) - 1) < k < str(int(end_date) + 1)])
    if vt_name_list is not None:
        dy_triggers2 = dict([(k, dict([v1, v2] for v1, v2 in v.items() if v1 in vt_name_list)) for k, v in dy_triggers2.items()])
    return dy_triggers2


def combine_params(code_vol_dict, st_date, ed_date, signal_lib, strategy, vt_name_list=None, suffix='', cv_triggers_path=None, add_trigger=True):
    code_list = list(code_vol_dict.keys())
    overwrite_params_by_code = {}
    for code in code_list:
        order_capacity = load_order_capacity(code, st_date, ed_date, strategy)
        params_code = {
            'code': code,
            'init_qty': code_vol_dict[code],
            'order_capacity': order_capacity['OrderCapacity'],
            'high_vol': order_capacity['HighVol'],
        }

        if add_trigger:  # 传入阈值
            try:
                triggers = load_dynamic_triggers(code, st_date, ed_date, signal_lib, strategy, vt_name_list=vt_name_list, suffix=suffix,
                                                 cv_triggers_path=cv_triggers_path)
                # triggers = load_dynamic_triggers2(code, st_date, ed_date, signal_lib, vt_name_list=vt_name_list, factor_lib=factor_lib)
                params_code.update({'triggers_by_date': triggers})

            except:
                print(f'{code} 阈值不存在')
                continue

        overwrite_params_by_code.update({code: params_code})
    return overwrite_params_by_code
