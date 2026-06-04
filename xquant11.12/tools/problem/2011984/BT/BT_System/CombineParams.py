"""参数处理——update @2021.10.31"""

import os
import json
from BT.BT_System.StrategyParams import load_order_capacity
from DataAPI.DataView import file_exist, load_json_file, save_json_file
from DataAPI.TradingDay import trading_day
from SP.UtilsSP.getSignalNameMap import getSignalNameMap


class CombineParams:
    def __init__(self, portfolio, code_vol_dict, start_date, end_date, param_dir_bt, output_dir, unique_dir=None):
        self.portfolio = portfolio
        self.all_code = list(code_vol_dict.keys())
        self.code_vol_dict = code_vol_dict
        self.start_date = str(start_date)
        self.end_date = str(end_date)
        self.all_trading_days = trading_day(self.start_date, self.end_date)
        self.unique_dir = unique_dir  # sp和bt为origin_param_dir，cv为dir_path
        self.output_dir = output_dir
        self.param_dir_bt = param_dir_bt
        os.makedirs(self.param_dir_bt, exist_ok=True)

    # ---------------------------------------------------------------------------------------
    # bt参数处理
    def params_bt(self):
        print("Start Combine Params".center(60, '*'))
        for code in self.all_code:
            order_capacity = load_order_capacity(code, self.start_date, self.end_date)
            params = {
                'code': code,
                'init_qty': self.code_vol_dict[code],
                'order_capacity': order_capacity['OrderCapacity'],
                'high_vol': order_capacity['HighVol'],
            }

            param_path = f'{self.unique_dir}/{code}/triggerRatio.json'
            if file_exist(param_path):
                code_params_data = load_json_file(param_path)
                params.update({'triggers': {
                    'longTriggerRatio': code_params_data['longTriggerRatio'],
                    'shortTriggerRatio': code_params_data['shortTriggerRatio'],
                    'longCloseRatio': code_params_data['longCloseRatio'],
                    'longRiskRatio': code_params_data['longRiskRatio'],
                    'shortCloseRatio': code_params_data['shortCloseRatio'],
                    'shortRiskRatio': code_params_data['shortRiskRatio']}
                })
            else:
                print(f'{code} {self.start_date}-{self.end_date} No Trigger Ratio File')
            save_json_file(params, f'{self.param_dir_bt}/{code}.json')

    def params_bt_voting(self):
        print("Start Combine Params".center(60, '*'))
        for code in self.all_code:
            order_capacity = load_order_capacity(code, self.start_date, self.end_date)
            params = {
                'code': code,
                'init_qty': self.code_vol_dict[code],
                'order_capacity': order_capacity['OrderCapacity'],
                'high_vol': order_capacity['HighVol'],
            }

            vt_triggers = dict()
            non_existing_name_list = []
            for vt_name, vt_dir in self.unique_dir.items():
                param_path = f'{vt_dir}/{code}/triggerRatio.json'
                if file_exist(param_path):
                    code_params_data = load_json_file(param_path)
                    vt_triggers.update({vt_name: {
                        'longTriggerRatio': code_params_data['longTriggerRatio'],
                        'shortTriggerRatio': code_params_data['shortTriggerRatio'],
                        'longCloseRatio': code_params_data['longCloseRatio'],
                        'longRiskRatio': code_params_data['longRiskRatio'],
                        'shortCloseRatio': code_params_data['shortCloseRatio'],
                        'shortRiskRatio': code_params_data['shortRiskRatio'],
                    }})
                else:
                    non_existing_name_list.append(vt_name)
            if len(vt_triggers) == len(self.unique_dir):
                params.update({'vt_triggers': vt_triggers})
                save_json_file(params, f'{self.param_dir_bt}/{code}.json')
            elif 0 < len(vt_triggers) < len(self.unique_dir):
                print(f'Please Check: {code} {non_existing_name_list} {self.start_date}-{self.end_date}')
                continue
            else:
                print(f'{code} {self.start_date}-{self.end_date} No Param Data File')
                continue

    # ---------------------------------------------------------------------------------------
    # cv参数处理
    def params_cv(self, mode, cv_type, vt_name):
        """cv_type为cv或者cv_cross，后者进行交叉验证"""
        from Manager.UtilsCV.GenerateTriggers import GenerateTriggers
        print("Start Combine Params".center(60, '*'))
        task_metas = []
        for code in self.all_code:
            order_capacity = load_order_capacity(code, self.start_date, self.end_date)
            params = {
                'code': code,
                'init_qty': self.code_vol_dict[code],
                'order_capacity': order_capacity['OrderCapacity'],
                'high_vol': order_capacity['HighVol'],
            }
            save_json_file(params, f'{self.param_dir_bt}/{code}.json')
            gene_triggers = GenerateTriggers(code, self.unique_dir['signal_lib'], self.unique_dir['origin_data_dir'],
                                             self.unique_dir['output_dir'], cv_type, vt_name=vt_name)
            task_metas.append(gene_triggers)

        print("Start Generate Triggers".center(60, '*'))
        if mode == 'local':
            total_len = len(task_metas)
            for i, gene_triggers in enumerate(task_metas):
                self.single_task_generate_triggers(None, gene_triggers)
                print('Finish: {}/{} - {}'.format(i + 1, total_len, gene_triggers.code))

        elif mode == 'spark':
            from Utils.MultiTasks import main_spark
            main_spark(self.single_task_generate_triggers, task_metas)

    @staticmethod
    def single_task_generate_triggers(context, gene_triggers):
        dfs = context.get_hdfs() if context is not None else None
        triggers = gene_triggers.generate_triggers_set()
        if triggers is not None:
            save_json_file(triggers, f'{gene_triggers.output_dir}/triggers/{gene_triggers.code}.json', dfs=dfs)

    # ---------------------------------------------------------------------------------------
    # 实盘参数处理
    def params_sp(self, is_vt=False):
        for code in self.all_code:
            init_qty = self.code_vol_dict[code]
            param_path = f'{self.unique_dir}/{code}.json'
            if os.path.exists(param_path):
                params = {
                    'code': code,
                    'init_qty': init_qty,
                }

                # 独有的参数文件处理
                code_params_data = load_json_file(param_path)
                if self.portfolio in ['Albest_sp', 'Albest_sp_l2p']:
                    strategy_param = self.params_sp_albest(code_params_data, code)
                elif self.portfolio in ['Everest_sp', 'Everest_sp_l2p']:
                    strategy_param = self.params_sp_everest_old(code_params_data)
                elif self.portfolio in ['Everest1S_sp', 'Everest1S_sp_l2p']:
                    strategy_param = self.params_sp_everest_1s(code_params_data)
                elif self.portfolio in ['Kunlun_sp', 'Kunlun_sp_l2p', 'Kunlun_mix', 'Kunlun_pure', 'Kunlun_mix_l2p', 'Kunlun_pure_l2p',
                                        'Kunlun_SHJS_mix', 'Kunlun_SHJS_pure']:
                    strategy_param = self.params_sp_kunlun(code_params_data, is_vt)
                else:
                    raise ValueError
                params.update(strategy_param)
                save_json_file(params, f'{self.param_dir_bt}/{code}.json')
            else:
                print(f'{code} {self.start_date}-{self.end_date} No Param Data File')
                continue

    def params_sp_albest(self, code_params_data, code):
        trade_date = code_params_data['交易日期'].replace('-', '')
        trigger_data = code_params_data['阈值参数']
        trigger_data1, trigger_data2 = trigger_data
        for t in trigger_data:
            if t['开始时间'] == '09:30:00':
                trigger_data1 = t
            if t['结束时间'] == '15:00:00':
                trigger_data2 = t
        params = {
            'trading_start_morning': code_params_data['上午执行开始时间'],
            'trading_start_afternoon': code_params_data['下午执行开始时间'],
            'close_time_morning': code_params_data['上午平仓时间'],
            'close_time_afternoon': code_params_data['下午平仓时间'],

            'stop_loss_ratio': int(code_params_data['Inner']),
            'open_long_coef': 1 + float(code_params_data['priceMulti']),  # 开多冲击成本
            'open_short_coef': 1 - float(code_params_data['priceMulti']),  # 开空冲击成本
            'close_short_coef': 1 + float(code_params_data['priceMulti']),  # 平空冲击成本
            'close_long_coef': 1 - float(code_params_data['priceMulti']),  # 平多冲击成本
            'max_price_deviate_ratio': float(code_params_data['下单价格最大偏离度']),
            'maxTurnoverPerOrder': int(code_params_data['每笔最大委托金额']),
            'maxExposure': int(code_params_data['单边总金额暴露']),
            'check_trade_vol_percentage_count': int(code_params_data['风控成交量统计范围秒数']),
            'check_trade_vol_percentage_limit_ratio': float(code_params_data['成交量占比上限']),
            'check_is_double_side_control': code_params_data['是否控制双边量'] == 'true',
            'check_is_close_control': code_params_data['是否控制平仓量'] == 'true',

            'wait_for_normal_count': int(code_params_data['涨跌停价格回落TICK数目']),
            'open_forbidden_pct': float(code_params_data['第一档涨跌停平仓价格幅度']),
            'order_capacity': {}.fromkeys(self.all_trading_days, float(code_params_data['OrderCapacity'])),
            'triggers_by_date': {
                f'{trade_date}_09:30:00': trigger_data1,
                f'{trade_date}_10:00:00': trigger_data2
            }
        }
        return params

    def params_sp_everest_1s(self, code_params_data):
        trade_date = code_params_data['交易日期'].replace('-', '')
        trigger_data = code_params_data['阈值参数']
        trigger_data1, trigger_data2 = trigger_data
        for t in trigger_data:
            if t['开始时间'] == '09:30:00':
                trigger_data1 = t
            if t['结束时间'] == '15:00:00':
                trigger_data2 = t
        params = {
            'trading_start_morning': code_params_data['上午允许开仓开始时间'],
            'trading_start_afternoon': code_params_data['下午允许开仓开始时间'],
            'close_time_morning': code_params_data['上午允许开仓结束时间'],
            'easy_close_time_morning': code_params_data['上午加大力度强平开始时间'],
            'close_time_afternoon': code_params_data['下午允许开仓结束时间'],
            'easy_close_time_afternoon': code_params_data['下午加大力度强平开始时间'],

            'stop_loss_ratio': int(code_params_data['止损线']),
            'open_long_coef': float(code_params_data['开多价格系数']),  # 开多冲击成本
            'open_short_coef': float(code_params_data['开空价格系数']),  # 开空冲击成本
            'close_short_coef': float(code_params_data['平空价格系数']),  # 平空冲击成本
            'close_long_coef': float(code_params_data['平多价格系数']),  # 平多冲击成本
            'regular_close_long_coef': float(code_params_data['止损多价格系数']),  # 止损多价格系数
            'regular_close_short_coef': float(code_params_data['止损空价格系数']),  # 止损空价格系数
            'maxTurnoverPerOrder': int(code_params_data['单笔最大订单金额']),
            'check_trade_vol_percentage_count': int(code_params_data['风控成交量统计范围秒数']),
            'check_trade_vol_percentage_limit_ratio': float(code_params_data['成交量占比上限']),
            'check_is_double_side_control': code_params_data['是否控制双边量'] == 'true',
            'check_is_close_control': code_params_data['是否控制平仓量'] == 'true',

            'wait_for_normal_count': int(code_params_data['涨跌停价格回落TICK数目']),
            'open_forbidden_pct': float(code_params_data['第一档涨跌停平仓价格幅度']),

            'check_drive_interval': float(code_params_data['撤单等待秒数']),
            'max_order_volume': int(code_params_data['单笔最大下单量']),
            'order_capacity': {}.fromkeys(self.all_trading_days, float(code_params_data['每笔委托最大量'])),
            'triggers_by_date': {
                f'{trade_date}_09:30:00': trigger_data1,
                f'{trade_date}_10:00:00': trigger_data2
            }
        }
        return params

    def params_sp_everest_old(self, code_params_data):
        params = {
            'trading_start_morning': code_params_data['上午允许开仓开始时间'],
            'trading_start_afternoon': code_params_data['下午允许开仓开始时间'],
            'close_time_morning': code_params_data['上午允许开仓结束时间'],
            'easy_close_time_morning': code_params_data['上午加大力度强平开始时间'],
            'close_time_afternoon': code_params_data['下午允许开仓结束时间'],
            'easy_close_time_afternoon': code_params_data['下午加大力度强平开始时间'],

            'stop_loss_ratio': int(code_params_data['止损线']),
            'open_long_coef': float(code_params_data['开多价格系数']),  # 开多冲击成本
            'open_short_coef': float(code_params_data['开空价格系数']),  # 开空冲击成本
            'close_short_coef': float(code_params_data['平空价格系数']),  # 平空冲击成本
            'close_long_coef': float(code_params_data['平多价格系数']),  # 平多冲击成本
            # 'max_price_deviate_ratio': float(code_params_data['下单价格最大偏离度']),
            'maxTurnoverPerOrder': int(code_params_data['单笔最大订单金额']),
            'check_trade_vol_percentage_count': int(code_params_data['风控成交量统计范围秒数']),
            'check_trade_vol_percentage_limit_ratio': float(code_params_data['成交量占比上限']),
            'check_is_double_side_control': code_params_data['是否控制双边量'] == 'true',
            'check_is_close_control': code_params_data['是否控制平仓量'] == 'true',

            'wait_for_normal_count': int(code_params_data['涨跌停价格回落TICK数目']),
            'open_forbidden_pct': float(code_params_data['第一档涨跌停平仓价格幅度']),

            'order_capacity': {}.fromkeys(self.all_trading_days, float(code_params_data['每笔委托最大量'])),
            'high_vol': {}.fromkeys(self.all_trading_days, float(code_params_data['历史成交活跃度'])),
            'triggers': {
                'longTriggerRatio': float(code_params_data['开多阈值']),
                'shortTriggerRatio': float(code_params_data['开空阈值']),
                'longCloseRatio': float(code_params_data['平多阈值']),
                'longRiskRatio': float(code_params_data['严格平多阈值']),
                'shortCloseRatio': float(code_params_data['平空阈值']),
                'shortRiskRatio': float(code_params_data['严格平空阈值']),
            }
        }
        return params

    def params_sp_everest_1s_old(self, code_params_data):
        params = self.params_sp_everest_old(code_params_data)
        params.update({
            'check_drive_interval': float(code_params_data['撤单等待秒数']),
            'max_order_volume': int(code_params_data['单笔最大下单量']),
        })
        return params

    @staticmethod
    def params_sp_kunlun(code_params_data, is_vt):
        if not is_vt:
            if len(code_params_data) > 1:
                params_select = list(filter(lambda x: x['信号组合名称'] == '1-2-5', code_params_data['信号参数列表']))[0]
            else:
                params_select = code_params_data['信号参数列表'][0]
            params = {'triggers': {
                'longTriggerRatio': float(params_select['longTriggerRatio']),
                'shortTriggerRatio': float(params_select['shortTriggerRatio']),
                'longCloseRatio': float(params_select['longCloseRatio']),
                'longRiskRatio': float(params_select['longCloseRatio']) - 0.2,
                'shortCloseRatio': float(params_select['shortCloseRatio']),
                'shortRiskRatio': float(params_select['shortCloseRatio']) + 0.2,
            }}
        else:
            vt_triggers = code_params_data['信号参数列表']
            # vt_key_dict = {'1-2-5': '8min', '1-2': '3min', '2-5': '7min', '1-5': '6min', '1': '1min', '2': '2min', '5': '5min'}
            params = {
                'vt_params': {
                    'vt_name_list': [],
                    'open_counter': int(code_params_data['买入投票基准']),
                    'buy_price_method': code_params_data['计算买入价格方法'],
                    'buy_vol_method': code_params_data['计算买入数量方法'],
                    'close_counter': int(code_params_data['卖出投票基准']),
                    'sell_price_method': code_params_data['计算卖出价格方法'],
                    'sell_vol_method': code_params_data['计算卖出数量方法'],
                },
                'vt_triggers': {},
            }
            dict_to_num = {'1min': 1, '2min': 2, '5min': 5, '15sec': 0.25, '30sec': 0.5}
            for vt_trigger_single in vt_triggers:
                signal_all = vt_trigger_single['信号组合名称']
                signal_name_map = getSignalNameMap(code_params_data['模型目录'], code_params_data['RegressionName'])
                vt_name = str(sum([dict_to_num[signal_name_map[x]] for x in signal_all.split('-')])) + 'min'
                # vt_name = vt_key_dict[signal_all]
                params['vt_triggers'].update({
                    vt_name: {
                        'longTriggerRatio': float(vt_trigger_single['longTriggerRatio']),
                        'shortTriggerRatio': float(vt_trigger_single['shortTriggerRatio']),
                        'longCloseRatio': float(vt_trigger_single['longCloseRatio']),
                        'longRiskRatio': float(vt_trigger_single['longCloseRatio']) - 0.2,
                        'shortCloseRatio': float(vt_trigger_single['shortCloseRatio']),
                        'shortRiskRatio': float(vt_trigger_single['shortCloseRatio']) + 0.2,
                    }
                })
                params['vt_params']['vt_name_list'].append(vt_name)

        vt_name = '8min'
        if 'regression_six' in code_params_data['RegressionName']:
            vt_name = '8min'
        elif 'regression_eight' in code_params_data['RegressionName']:
            vt_name = '3.75min'
        elif 'regression_ten' in code_params_data['RegressionName']:
            vt_name = '8.75min'

        params.update({
            'trading_start_morning': max(code_params_data['策略开始时间'], code_params_data['信号有效上午开始时间']),
            'trading_start_afternoon': code_params_data['信号有效下午开始时间'],
            'close_time_morning': code_params_data['午盘平仓开始时间'],
            'easy_close_time_morning': code_params_data['午盘轻松平仓时间'],
            'close_time_afternoon': code_params_data['闭市平仓开始时间'],
            'easy_close_time_afternoon': code_params_data['闭市轻松平仓时间'],
            'high_vol_start_time': code_params_data['活跃度指标开始使用时间'],

            'allow_open_tick': int(code_params_data['ChaosNum']),
            'stop_loss_ratio': int(code_params_data['止损参数']),
            'max_price_deviate_ratio': float(code_params_data['最大价格偏离度']),
            'maxTurnoverPerOrder': int(code_params_data['最大单笔委托金额']),
            'maxExposure': int(code_params_data['最大单边总金额暴露']),
            'check_trade_vol_percentage_count': int(code_params_data['风控成交量统计范围秒数']),
            'check_trade_vol_percentage_limit_ratio': float(code_params_data['成交量占比上限']),
            'check_trade_amt_percentage_count': int(code_params_data['风控成交额统计范围秒数']),
            'check_trade_amt_percentage_limit_amt': int(code_params_data['限时成交额上限']),
            'check_is_double_side_control': code_params_data['是否控制双边量额'] == 'true',
            'check_is_close_control': code_params_data['是否控制平仓量额'] == 'true',
            'high_vol': float(code_params_data['活跃度指标']),
            'unallowed_open_loss_ratio': float(code_params_data['unallowedOpenLossRatio']),
            'close_reset_interval': int(code_params_data['平多阈值重置Tick数目']),
            'close_decrease_interval': int(code_params_data['初始平多阈值重置Tick数目']),
            'open_long_coef': float(code_params_data['openLongCoef']),
            'close_long_coef': float(code_params_data['closeLongCoef']),
            'is_conservative_mode': code_params_data['isConservativeMode'] == 'true',
            'open_filter_tick_num': int(code_params_data['开仓过滤tick数目']),
            'open_filter_pct': float(code_params_data['价格回撤幅度']),
            'initial_open_long_limit_coef': float(code_params_data['初次开仓价格系数']),
            'multi_open_long_limit_coef': float(code_params_data['多次开仓价格系数']),
            'close_long_limited_coef': float(code_params_data['平仓价格系数']),
            'stop_loss_limit_coef': float(code_params_data['止损平仓价格系数']),
            'liquidity_ratio': float(code_params_data['流动性系数']),
            'limit_vol_open_ratio': float(code_params_data['limitVol开仓系数']),
            'limit_vol_close_ratio': float(code_params_data['limitVol平仓系数']),
            'ema2_ratio': float(code_params_data['ema2系数']),
            'limit': {
                'up_offset': float(code_params_data['upOffset']),
                'down_offset': float(code_params_data['downOffset']),
                'limit_recover_counter': int(code_params_data['临停结束等待TICK数目']),
                'price_limit_clear_aggressive_coef': float(code_params_data['临停清仓激进系数']),
                'price_limit_clear_passive_coef': float(code_params_data['临停清仓保守系数']),
            },
            'vt_name': vt_name
        })
        return params
