"""实盘与回测结果汇总（总的结果，只看res与pro）——update @2021.11.15"""

from SP.UtilsSP.LoadSPFile import get_sp_file, load_sp_daily_result
from SP.UtilsSP.resolve_result import get_sp_resolve_summary_result
import pandas as pd
import os


def main():
    trade_date = 20211112
    res_stock = SummaryResult(trade_date).compare_result_strategy_stock()
    res_cb = SummaryResult(trade_date).compare_result_strategy_cb()
    return res_stock, res_cb


class SummaryResult:
    def __init__(self, trade_date):
        self.trade_date = trade_date

    def compare_result_strategy_stock(self):
        albest_result = self.compare_result(strategy="Albest")
        everest_result = self.compare_result(strategy="Everest")
        blank_col = pd.DataFrame("——", index=albest_result.index, columns=[''])
        res_albest = sorted_columns(albest_result, [f'Albest实盘_{self.trade_date}', 'Albest_big实盘',
                                                    'Albest_big实盘_sh', 'albest_big_pro_sh', 'albest_big_res_sh',
                                                    'Albest_big实盘_sz', 'albest_big_pro_sz', 'albest_big_res_sz',
                                                    'Albest_big实盘_cyb', 'albest_big_pro_cyb', 'albest_big_res_cyb',
                                                    'Albest_small实盘', 'Albest_small实盘_sh', 'albest_small_pro_sh', 'albest_small_res_sh',
                                                    'Albest_small实盘_sz', 'albest_small_pro_sz', 'albest_small_res_sz',
                                                    'Albest_small实盘_cyb', 'albest_small_pro_cyb', 'albest_small_res_cyb'])
        res_everest = sorted_columns(everest_result, [f'Everest实盘_{self.trade_date}', 'Everest_big实盘', 'Everest_big实盘_sh', 'everest_big_pro_sh',
                                                      'everest_big_res_sh', 'Everest_big实盘_sz', 'everest_big_pro_sz', 'everest_big_res_sz',
                                                      'Everest_big实盘_cyb', 'everest_big_pro_cyb', 'everest_big_res_cyb',
                                                      'Everest_small实盘', 'Everest_small实盘_sh', 'everest_small_pro_sh', 'everest_small_res_sh',
                                                      'Everest_small实盘_sz', 'everest_small_pro_sz', 'everest_small_res_sz',
                                                      'Everest_small实盘_cyb', 'everest_small_pro_cyb', 'everest_small_res_cyb'])
        sum_res_stock = pd.concat([res_albest, blank_col, res_everest], axis=1).T
        return sum_res_stock

    def compare_result_strategy_cb(self):
        kunlun_result = self.compare_result(strategy="Kunlun")
        res_kunlun = sorted_columns(kunlun_result, [f'Kunlun实盘_{self.trade_date}',
                                                    'Kunlun_mix_o32实盘', 'Kunlun_mix_o32实盘_sh', 'kunlun_mix_tp_pro_sh', 'kunlun_mix_tp_res_sh',
                                                    'Kunlun_mix_o45实盘_sz', 'kunlun_mix_JS_tp_pro_sz', 'kunlun_mix_JS_tp_res_sz',
                                                    'Kunlun_mix_o45实盘_cyb', 'kunlun_mix_JS_tp_pro_cyb', 'kunlun_mix_JS_tp_res_cyb',
                                                    'Kunlun_pure_o32实盘', 'Kunlun_pure_o32实盘_sh', 'kunlun_pure_tp_pro_sh', 'kunlun_pure_tp_res_sh',
                                                    'Kunlun_pure_o32实盘_sz', 'kunlun_pure_tp_pro_sz', 'kunlun_pure_tp_res_sz',
                                                    'Kunlun_pure_o32实盘_cyb', 'kunlun_pure_tp_pro_cyb', 'kunlun_pure_tp_res_cyb',
                                                    'Kunlun_pure_o45实盘',
                                                    'Kunlun_pure_o45实盘_sz', 'kunlun_pure_JS_tp_pro_sz', 'kunlun_pure_JS_tp_res_sz',
                                                    'Kunlun_pure_o45实盘_cyb', 'kunlun_pure_JS_tp_pro_cyb', 'kunlun_pure_JS_tp_res_cyb',
                                                    ])
        return res_kunlun.T

    def compare_result(self, strategy):
        select_cols = ["总盈利", "交易次数", "获利次数", "胜率", "平均收益率", "交易总市值",
                       "获利收益率", "亏损收益率", "盈亏比", "最大单笔亏损", "平均持仓时间"]
        sp_result = load_sp_daily_result(self.trade_date, strategy)
        sp_result = sp_result[sp_result['日期'] == self.trade_date].T
        sp_result.columns = [f'{strategy}实盘']
        sp_result = sp_format(sp_result.loc[select_cols])
        bt_path = f'/data/user/011668/BT_Track/Total/bt-{self.trade_date}'
        bt_result = get_bt_summary_result(bt_path)
        bt_result = bt_format(bt_result.loc[select_cols])
        compare_result = pd.concat([sp_result, bt_result], axis=1)
        return compare_result


def get_bt_summary_result(bt_path, classify=None):
    bt_file_list = os.listdir(bt_path)
    res = []
    for bt_file in bt_file_list:
        sub_dir = f'{classify}/' if classify is not None else ''
        print(f'{bt_path}/{bt_file}/{sub_dir}result_daily.xls')
        bt_file_data = pd.read_excel(f'{bt_path}/{bt_file}/{sub_dir}result_daily.xls', sheet_name="result_daily").loc[0]
        bt_file_data = pd.DataFrame(bt_file_data)
        bt_file_data.columns = [bt_file.split('-')[-1]]
        res.append(bt_file_data)
    bt_result = pd.concat(res, axis=1)
    return bt_result


def sorted_columns(data_df, col_names):
    """DataFrame的列名按照特定顺序排列（如果没有则跳过）"""
    sel_cols = [x for x in col_names if x in data_df.columns]
    return data_df[sel_cols]


def sp_format(sp_result):
    """实盘格式与BT格式调整一致"""
    sp_result.loc["总盈利"] = sp_result.loc["总盈利"].apply(int)
    sp_result.loc["交易次数"] = sp_result.loc["交易次数"].apply(int)
    sp_result.loc["获利次数"] = sp_result.loc["获利次数"].apply(int)
    sp_result.loc["胜率"] = [f'{round(x * 100)}%' for x in sp_result.loc["胜率"]]
    sp_result.loc["平均收益率"] = [round(x, 2) for x in sp_result.loc["平均收益率"]]
    sp_result.loc["交易总市值"] = sp_result.loc["交易总市值"].apply(int)
    sp_result.loc["获利收益率"] = [round(x, 2) for x in sp_result.loc["获利收益率"]]
    sp_result.loc["亏损收益率"] = [round(x, 2) for x in sp_result.loc["亏损收益率"]]
    sp_result.loc["盈亏比"] = [round(x, 2) for x in sp_result.loc["盈亏比"]]
    sp_result.loc["最大单笔亏损"] = [round(x, 2) for x in sp_result.loc["最大单笔亏损"]]
    sp_result.loc["平均持仓时间"] = [round(x, 2) for x in sp_result.loc["平均持仓时间"]]
    return sp_result


def bt_format(bt_result):
    """实盘格式与BT格式调整一致"""
    bt_result.loc["总盈利"] = bt_result.loc["总盈利"].apply(int)
    bt_result.loc["交易总市值"] = bt_result.loc["交易总市值"].apply(int)

    def holding_time_resolve(x):
        holding_time_list = x.split(":")
        holding_time = 60 * int(holding_time_list[0]) + int(holding_time_list[1]) + round(int(holding_time_list[2]) / 60, 2)
        return holding_time

    bt_result.loc["平均持仓时间"] = bt_result.loc["平均持仓时间"].apply(holding_time_resolve)
    return bt_result


def download_sp_file(trade_date, strategy):
    for portfolio in strategy:
        sp_file = get_sp_file(trade_date, portfolio)
        if not os.path.exists(sp_file) or os.path.getsize(sp_file) == 0:
            raise ValueError(f'{trade_date}-{portfolio}实盘文件不存在')


if __name__ == '__main__':
    main()
