"""参数管理器——update @2022.4.13"""

from Utils.UtilsCode import *


class ParamManager:
    def __init__(self, executor_str, freq='3s'):
        self.executor_str = executor_str
        self.freq = freq
        self.params_dict = {
            'code': '',   # 标的代码
            'init_qty': 0,  # 初始额度
            'vt_name': '8min',  # 哪几个信号取均值

            # 单笔单边额度与阈值
            'maxTurnoverPerOrder': 180 * 1e4,
            'maxExposure': 800 * 1e4,

            'order_capacity': dict(),
            'order_capacity_ratio': 1.0,
            'high_vol': 0.0,  # 活跃度指标
            'stop_loss_ratio': -10,  # 止损参数，单位是‰（一定是负值，直接跟return比较）
            'open_long_coef': 1.0002,  # 开多冲击成本
            'open_short_coef': 0.9998,  # 开空冲击成本
            'close_short_coef': 1.0002,  # 平空冲击成本
            'close_long_coef': 0.9998,  # 平多冲击成本

            'market_open_time': '09:30:00',  # 市场开始时间
            'market_close_time': '15:00:00',  # 市场结束时间
            'trading_start_morning': '09:31:15',  # 上午开始交易时间
            'trading_start_afternoon': '13:01:15',  # 下午开始交易时间
            'close_time_morning': '11:29:00',  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
            'easy_close_time_morning': '11:29:30',  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓
            'close_time_afternoon': '14:55:00',  # 尾盘平仓时间，从该时刻起进行平仓，且不发开仓委托单
            'easy_close_time_afternoon': '14:56:00',  # 尾盘轻松平仓时间，从尾盘平仓至该时刻，可用不激进的价格去平仓
            'high_vol_start_time': '09:41:15',  # 使用活跃度指标进行阈值调整

            # 风控指标
            'is_close_maxTurnoverPerOrder': True,  # 平仓是否受到最大单笔限额的限制
            'max_price_deviate_ratio': 0.012,  # 最大价格偏离度
            'check_trade_vol_percentage_count': 180,  # 【成交量占比风控】风控成交量统计范围秒数
            'check_trade_vol_percentage_limit_ratio': 0.2,  # 【成交量占比风控】成交量占比上限
            'check_trade_amt_percentage_count': 180,  # 【成交额占比风控】风控成交额统计范围秒数
            'check_trade_amt_percentage_limit_amt': 1000000,  # 【成交额占比风控】限时成交额上限
            'check_is_double_side_control': False,  # 【成交风控】是否控制双边量额
            'check_is_close_control': False,  # 【成交风控】是否控制平仓量额

            'triggers': {
                'longTriggerRatio': 999999,
                'shortTriggerRatio': -999999,
                'longCloseRatio': 0,
                'longRiskRatio': 0,
                'shortCloseRatio': 0,
                'shortRiskRatio': 0,
            }
        }
        self.__update_unique_params()

    def __update_unique_params(self):
        if self.freq in ['3s', '3s_l2p']:
            if 'albest' in self.executor_str.lower():
                self.update_params_albest()
            elif 'everest' in self.executor_str.lower():
                self.update_params_everest()
            elif 'kunlun' in self.executor_str.lower():
                self.update_params_kunlun()
            elif 'rocky' in self.executor_str.lower():
                self.update_params_rocky()
        elif self.freq == '1s':
            if 'albest' in self.executor_str.lower():
                self.update_params_albest_1s()
            elif 'everest' in self.executor_str.lower():
                self.update_params_everest_1s()

    def update_params_albest(self):
        """Albest独有的参数"""
        self.params_dict.update({
            'is_close_maxTurnoverPerOrder': False,
            'wait_for_normal_count': 241,  # 涨跌停价格回落Tick数目
        })

    def update_params_albest_1s(self):
        """Everest 1s策略独有的参数"""
        self.params_dict.update({
            'wait_for_normal_count': 101,  # 涨跌停价格回落Tick数目
            'check_drive_interval': 2.5,  # 撤单等待秒数
            'max_order_volume': 999900,   # 单笔最大下单量
            'is_reset_order_price': False,  # 是否根据一档盘口调整下单价格
            'ema_ratio_market_close': 4,   # 强平阶段EMA系数

        })

    def update_params_everest(self):
        """Everest独有的参数"""
        self.params_dict.update({
            'wait_for_normal_count': 241,  # 涨跌停价格回落Tick数目
        })

    def update_params_everest_1s(self):
        """Everest 1s策略独有的参数"""
        self.params_dict.update({
            'wait_for_normal_count': 101,  # 涨跌停价格回落Tick数目
            'check_drive_interval': 2.5,  # 撤单等待秒数
            'max_order_volume': 999900,   # 单笔最大下单量
        })

    def update_params_rocky(self):
        """Albest独有的参数"""
        self.params_dict.update({
            'is_close_maxTurnoverPerOrder': False,
            'wait_for_normal_count': 241,  # 涨跌停价格回落Tick数目
        })

    def update_params_kunlun(self):
        """Kunlun独有的参数"""
        self.params_dict.update({
            'maxTurnoverPerOrder': 50 * 1e4,
            'maxExposure': 100 * 1e4,
            # 'open_long_coef': 1.0003,  # 开多冲击成本
            # 'close_long_coef': 0.9997,  # 平多冲击成本
            'close_time_morning': '11:28:00',  # 午盘平仓时间，从该时刻起至11:30:00，进行平仓，且不发开仓委托单
            'easy_close_time_morning': '11:28:30',  # 午盘轻松平仓时间，从午盘平仓至该时刻，可用不激进的价格去平仓

            'allow_open_tick': 20,  # 有效tick数达到这个数值才开仓交易
            'unallowed_open_loss_ratio': -15,  # 针对盘口价差较大情况的开仓过滤，单位是‰
            'close_reset_interval': 50,  # 平多阈值重置tick数目
            'close_decrease_interval': 20,  # 初始平多阈值重置tick数目
            'is_conservative_mode': True,
            'open_filter_tick_num': 60,  # 开仓过滤tick数
            'open_filter_pct': -0.01,  # 开仓过滤价格回撤幅度
            'initial_open_long_limit_coef': 1.01,  # 初次开仓价格系数
            'multi_open_long_limit_coef': 1.01,  # 多次开仓价格系数
            'close_long_limited_coef': 0.98,  # 平仓价格系数
            'stop_loss_limit_coef': 0.98,  # 止损平仓价格系数
            'liquidity_ratio': 0.01,  # 流动性系数
            'limit_vol_open_ratio': 1.0,  # LimitVol开仓系数
            'limit_vol_close_ratio': 1.0,  # LimitVol平仓系数
            'ema2_ratio': 1.0,  # ema2系数
            'limit': {
                'up_offset': 5,  # 上涨接近临停的幅度，单位是‰
                'down_offset': 10,  # 下跌接近临停的幅度，单位是‰
                'limit_recover_counter': 21,  # 临停结束等待TICK数目
                'price_limit_clear_aggressive_coef': 0.999,  # 临停清仓激进系数
                'price_limit_clear_passive_coef': 0.995,  # 临停清仓保守系数
            },  # 临停参数
        })

    def update_params(self, updated_params):
        """更新参数"""
        for update_keys, update_items in updated_params.items():
            if update_keys == 'vt_params' and 'vt_params' in self.params_dict.keys():
                self.params_dict['vt_params'].update(updated_params['vt_params'])
            else:
                self.params_dict.update({update_keys: update_items})

    def update_code_default_param(self, code, st_date, ed_date, freq):
        """个股独有的参数"""
        param = {
            'code': code,
            'st_date': st_date,
            'ed_date': ed_date,
            'type': code_classify(code),   # 类别：[stock, cb]
            'is_holo': False,   # 是否为创业板的股票
            # 'cost_rate': get_cost_rate(code, 'bt'),  # 交易手续费
            'price_digits': get_price_digits(code),  # 股票价格小数点位
            'min_vol_qty': get_min_vol_qty(code),  # 一手代表的股数
            'min_vol_qty_sum': self.__min_vol_qty_sum(code),  # 一笔最少下的股数
            'open_forbidden_pct': self.__open_forbidden_pct(code),  # 禁止开仓的阈值
            'delay': self.__delay(code, freq)
        }
        self.params_dict.update(param)

    @staticmethod
    def __delay(code, freq='3s'):
        # send_delay, back_delay
        if freq == '3s':
            if code[-2:] == 'SH':  # 上海主板
                send_delay = 1
                back_delay = 0.4
            elif (code[-2:] == 'SZ') and code[0] == '3':  # 创业板
                send_delay = 0.4
                back_delay = 0.4
            else:  # 深圳主板
                send_delay = 0.4
                back_delay = 0.4
        elif freq in ['1s', '3s_l2p']:
            if code[-2:] == 'SH':  # 上海主板
                send_delay = 0.15
                back_delay = 0.15
            elif (code[-2:] == 'SZ') and code[0] == '3':  # 创业板
                send_delay = 0.08
                back_delay = 0.08
            else:  # 深圳主板
                send_delay = 0.08
                back_delay = 0.08
        else:
            raise ValueError
        return [send_delay, back_delay]

    @staticmethod
    def __min_vol_qty_sum(code):
        # 一笔最少下的股数，股票是100股，科创板是200股，转债是10张
        if code.startswith('68'):
            return 200
        else:
            return get_min_vol_qty(code)

    @staticmethod
    def __open_forbidden_pct(code):
        # 禁止开仓的涨跌幅
        if code.startswith("1"):  # 转债
            return 1000
        elif code.startswith('3') or code.startswith('688'):  # 创业板 / 科创板股票
            return 0.195
        else:  # 主板股票
            return 0.095
