"""多个策略的回测报告——update @2021.8.20"""

import time
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager, gridspec
from DataAPI.DataTools import get_index_data
from DataAPI.TradingDay import trading_day
from Analyzer.BTAnalyzer.LayerAnalysis import LayerAnalysis
from Utils.UtilsTime import minute_t2m


myfont = font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf')
myfont_legend = font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf', size=8)


class MultiStrategyReport:
    def __init__(self, st_date, ed_date, abs_path_list, tags, index_code):
        self.st_date = st_date
        self.ed_date = ed_date
        self.abs_path_list = abs_path_list
        self.tags = tags
        self.index_code = index_code
        self.color_all = ['#0072BC', 'darkorange', '#ED1C24', "mediumpurple", "darkgreen",
                          'salmon', 'magenta', 'wheat', 'burlywood', 'lightsteelblue', 'purple']

    def generate_report(self, split_by_month=False, is_print=False, sp_strategy='', classify=''):
        period_all, period_name, period_text = split_date_monthly(self.st_date, self.ed_date, split_by_month=split_by_month)
        sheet_name_list = ['']
        if classify == 'ls':
            sheet_name_list = ['_long', '_short']
        elif classify == 'market':
            sheet_name_list = ['_6', '_0', '_3']
        for sheet_name in sheet_name_list:
            data_dict = self.get_data_dict(period_all, sp_strategy, sheet_name=sheet_name)
            out_res = self.get_seperate_data(data_dict, period_all, period_name, is_print)
            self.plot_seperate_bar(out_res, period_name, period_text, sheet_name)
            if sheet_name != sheet_name_list[-1]:
                time.sleep(2)

    def layer_analysis(self):
        # 分层对比结果
        layer_result, index_all = [], []
        for i in range(len(self.abs_path_list)):
            abs_path = self.abs_path_list[i]
            asset_class = 'cb' if 'Kunlun' in abs_path else 'stock'
            single_res = LayerAnalysis(abs_path, asset_class).start()
            index_all = list(single_res.index)
            single_res['classify'] = self.tags[i]
            single_res = single_res.reset_index().set_index(['index', 'classify'])
            layer_result.append(single_res)
        layer_df = pd.concat(layer_result)
        layer_df_sorted = []
        for index_ in index_all:
            layer_df_sorted.append(layer_df.loc[([index_], )])
        layer_df_sorted = pd.concat(layer_df_sorted)
        return layer_df_sorted

    def get_seperate_data(self, data_dict, period_all, period_name, is_print=False):
        self.tags = list(data_dict.keys())

        daily_earn_df = pd.concat([x['总盈利'] for x in data_dict.values()], axis=1).loc[int(self.st_date):int(self.ed_date)]
        daily_earn_df.columns = self.tags

        total_earn_df = pd.DataFrame(index=period_name, columns=self.tags)
        ave_ret_df, ave_amt_df, ave_count_df = total_earn_df.copy(), total_earn_df.copy(), total_earn_df.copy()
        ave_win_rate_df, ave_holding_time_df, ave_win_loss_rate_df = total_earn_df.copy(), total_earn_df.copy(), total_earn_df.copy()
        for i in range(len(period_all)):
            for tag in self.tags:
                ts_data = data_dict[tag].loc[period_all[i][0]: period_all[i][1]]
                ts_total_earn = ts_data["总盈利"].sum() / 1e4  # 总盈利（万）
                ts_daily_amt = ts_data["交易总市值"].mean() / 1e8  # 交易额（亿）
                ts_daily_num = ts_data["交易次数"].mean()  # 交易次数
                ts_ret = (ts_data["交易次数"] * ts_data["平均收益率"]).sum() / ts_data["交易次数"].sum()
                ts_win_rate = np.nanmean([int(x.replace("%", "")) for x in ts_data["胜率"]]) / 100
                ts_win_loss_rate = ts_data['盈亏比'].mean()
                ts_holding_time = ts_data['holding_time'].mean()
                total_earn_df.at[period_name[i], tag] = ts_total_earn
                ave_ret_df.at[period_name[i], tag] = ts_ret
                ave_amt_df.at[period_name[i], tag] = ts_daily_amt
                ave_count_df.at[period_name[i], tag] = ts_daily_num
                ave_win_rate_df.at[period_name[i], tag] = ts_win_rate
                ave_win_loss_rate_df.at[period_name[i], tag] = ts_win_loss_rate
                ave_holding_time_df.at[period_name[i], tag] = ts_holding_time
        if is_print:
            print('总盈利', total_earn_df[self.tags[-1]] / total_earn_df[self.tags[0]] - 1)
            print('平均每笔收益率', ave_ret_df[self.tags[-1]] / ave_ret_df[self.tags[0]] - 1)
            print('日均交易额', ave_amt_df[self.tags[-1]] / ave_amt_df[self.tags[0]] - 1)
            print('日均交易次数', ave_count_df[self.tags[-1]] / ave_count_df[self.tags[0]] - 1)
            print('日均交易胜率', ave_win_rate_df[self.tags[-1]] / ave_win_rate_df[self.tags[0]] - 1)
            print('超额收益为正的天数占比为', (daily_earn_df[self.tags[-1]] - daily_earn_df[self.tags[0]] > 0).sum() / daily_earn_df.shape[0])
        out_res = {'daily_earn_df': daily_earn_df, 'total_earn_df': total_earn_df, 'ave_ret_df': ave_ret_df,
                   'ave_amt_df': ave_amt_df, 'ave_count_df': ave_count_df, 'ave_win_rate_df': ave_win_rate_df,
                   'ave_win_loss_rate_df': ave_win_loss_rate_df, 'ave_holding_time_df': ave_holding_time_df}
        return out_res

    def get_data_dict(self, period_all, sp_strategy='', sheet_name=''):
        data_dict = dict()
        for i, path in enumerate(self.abs_path_list):
            if isinstance(path, str):
                daily_data_all = pd.read_excel(f'{path}/result_daily.xls', sheet_name=f'result_daily{sheet_name}', index_col=0)
            else:
                daily_data_all = combine_daily_sum(path, sheet_name=sheet_name)
            daily_data_all['holding_time'] = [minute_t2m(x) for x in daily_data_all['平均持仓时间']]
            data_dict.update({self.tags[i]: daily_data_all})

        if sp_strategy != '':
            from SP.UtilsSP.resolve_result import get_resolve_result
            sp_data = get_resolve_result(period_all[0][0].replace('-', ''), period_all[0][1].replace('-', ''), strategy=sp_strategy, market='hs300')
            sp_data.index = [f'{str(x)[0:4]}-{str(x)[4:6]}-{str(x)[6:8]}' for x in sp_data.index]
            sp_data = sp_data.rename(columns={'平均持仓时间': 'holding_time'})
            data_dict.update({'sp': sp_data})
        return data_dict

    def plot_seperate_bar(self, out_res, period_name, period_text, sheet_name):
        sheet_name_dict = {'': '', '_long': '做多', '_short': '做空', '_0': '深圳主板', '_3': '创业板', '_6': '上海主板'}
        s_name = sheet_name_dict[sheet_name]
        total_earn_df = out_res['total_earn_df']
        fig = plt.figure(figsize=(18, 8.5))
        # fig = plt.figure(figsize=(24, 8.5))
        if total_earn_df.shape[1] > 2:
            gs = gridspec.GridSpec(4, 2)
        else:
            gs = gridspec.GridSpec(4, 3)

        ax1 = fig.add_subplot(gs[0:1, 1:2])
        self.cumprofit_with_index(ax1, out_res['daily_earn_df'])

        ax2 = fig.add_subplot(gs[0:1, 0:1])
        self.compare_plot(ax2, total_earn_df, period_name, title_text=f'{period_text} {s_name}按月统计总盈利（万）', decimal=0)

        ax3 = fig.add_subplot(gs[1:2, 0:1])
        self.compare_plot(ax3, out_res['ave_ret_df'], period_name, title_text=f'{period_text} {s_name}按月统计每笔平均收益率（‰）', decimal=2)

        ax4 = fig.add_subplot(gs[1:2, 1:2])
        self.compare_plot(ax4, out_res['ave_amt_df'], period_name, title_text=f'{period_text} {s_name}按月统计日均交易额（亿）', decimal=2)

        ax5 = fig.add_subplot(gs[2:3, 0:1])
        self.compare_plot(ax5, out_res['ave_count_df'], period_name, title_text=f'{period_text} {s_name}按月统计日均交易次数', decimal=0)

        ax6 = fig.add_subplot(gs[2:3, 1:2])
        self.compare_plot(ax6, out_res['ave_win_rate_df'], period_name, title_text=f'{period_text} {s_name}按月统计日均交易胜率', decimal=2)

        ax10 = fig.add_subplot(gs[3:4, 0:1])
        self.compare_plot(ax10, out_res['ave_win_loss_rate_df'], period_name, title_text=f'{period_text} {s_name}按月统计日均交易盈亏比', decimal=2)

        ax11 = fig.add_subplot(gs[3:4, 1:2])
        self.compare_plot(ax11, out_res['ave_holding_time_df'], period_name, title_text=f'{period_text} {s_name}按月统计平均持仓时间', decimal=2)

        if total_earn_df.shape[1] <= 2:
            daily_earn_df = out_res['daily_earn_df']
            ax7 = fig.add_subplot(gs[1:2, 2:3])
            self.daily_profit_bar(ax7, daily_earn_df, idx=0)

            ax8 = fig.add_subplot(gs[0:1, 2:3])
            self.daily_profit_bar(ax8, daily_earn_df, idx=1)

            ax9 = fig.add_subplot(gs[2:3, 2:3])
            self.daily_excess_profit(ax9, daily_earn_df)

            ax12 = fig.add_subplot(gs[3:4, 2:3])
            self.daily_index_bar(ax12, daily_earn_df.index)
        # plt.savefig('/data/user/011668/cp.png')
        plt.show()

    def plot_seperate_bar2(self, out_res, period_name, period_text):
        """画2个柱状图（临时使用）"""
        total_earn_df = out_res['total_earn_df']
        fig = plt.figure(figsize=(12, 3))
        gs = gridspec.GridSpec(1, 2)
        ax1 = fig.add_subplot(gs[0:1, 1:2])
        self.cumprofit_with_index(ax1, out_res['daily_earn_df'], key_date='2021-03-26')
        ax2 = fig.add_subplot(gs[0:1, 0:1])
        self.compare_plot(ax2, total_earn_df, period_name, title_text=f'{period_text} 按月统计总盈利（万）', decimal=0)
        plt.show()

    def compare_plot(self, ax, data_df, period_name, title_text="", decimal=0):
        x = range(data_df.shape[0])
        bar_width = 1 / (data_df.shape[1] + 1)
        for j in range(data_df.shape[1]):
            y_select = data_df.iloc[:, j].values
            index = np.arange(len(y_select))
            ax.bar(index + bar_width * j, y_select, bar_width, color=self.color_all[j], label=self.tags[j])

            for a, b in zip(x, y_select):
                text_b = int(b) if decimal == 0 else round(b, decimal)
                if b >= 0:
                    plt.text(a + bar_width * j, b, text_b, ha='center', va='bottom', fontdict={'size': 6})
                else:
                    plt.text(a + bar_width * j, b, text_b, ha='center', va='top', fontdict={'size': 6})
        plt.xticks(np.arange(len(period_name)) + bar_width * 0.5 * (len(self.tags) - 1), period_name, fontproperties=myfont)
        # ncols = data_df.shape[1] if data_df.shape[1] <= 4 else math.ceil(data_df.shape[1] / 2)
        ncols = data_df.shape[1]
        plt.legend(ncol=ncols, loc='best', prop=myfont_legend)
        plt.title(title_text, fontproperties=myfont)
        y_lim_min, y_lim_max = data_df.min().min(), data_df.max().max()
        if ncols == data_df.shape[1]:
            ax.set_ylim(-0.2 * y_lim_max + 1.2 * y_lim_min, 1.4 * y_lim_max - 0.4 * y_lim_min)
        else:
            ax.set_ylim(-0.2 * y_lim_max + 1.2 * y_lim_min, 1.6 * y_lim_max - 0.6 * y_lim_min)
        plt.tight_layout()

    def cumprofit_with_index(self, ax, daily_earn_df, key_date=None):
        """略累计收益与相应的指数对比，index：沪深300对应000300.SH，中证500对应000905.SH"""
        acc_earn_df = daily_earn_df.cumsum() / 1e4
        all_date = [str(x) for x in daily_earn_df.index]

        index_close = get_index_data(self.index_code, self.st_date, self.ed_date, ['close']).loc[all_date, 'close']
        name_code_map = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "000832.SH": "中证转债", "399006.SZ": "创业板指"}
        index_name = name_code_map[self.index_code]

        y_lim_min, y_lim_max = index_close.min(), index_close.max()
        ax.fill_between(range(len(all_date)), -0.2 * y_lim_max + 1.2 * y_lim_min, index_close, color='lightgray', alpha=0.8)
        ax2 = ax.twinx()
        lns = []
        for i in range(len(self.tags)):
            lns1 = ax2.plot(range(len(all_date)), acc_earn_df[self.tags[i]], '-', label=self.tags[i], color=self.color_all[i])
            lns += lns1
        if key_date is not None:
            label_pos = np.argwhere(np.array(all_date) <= key_date)[-1][0]
            # x_adj = acc_earn_df.loc[key_date:][self.tags[0]] - (acc_earn_df.loc[key_date][self.tags[0]] - acc_earn_df.loc[key_date][self.tags[1]])
            # ax2.plot(range(label_pos, len(all_date)), x_adj, '--', color=self.color_all[0])
            plt.vlines(label_pos, -999999, 99999, color='gray')

        ax.yaxis.set_ticks_position('right')
        ax2.yaxis.set_ticks_position('left')
        labs = [l.get_label() for l in lns]
        ncols = len(self.tags) if len(self.tags) <= 4 else math.ceil(len(self.tags) / 2)
        ax.legend(lns, labs, prop=myfont_legend, ncol=ncols)
        y_lim_min2, y_lim_max2 = acc_earn_df.min().min(), acc_earn_df.max().max()
        if ncols == len(self.tags):
            ax.set_ylim(-0.2 * y_lim_max + 1.2 * y_lim_min, 1.4 * y_lim_max - 0.4 * y_lim_min)
            ax2.set_ylim(-0.2 * y_lim_max2 + 1.2 * y_lim_min2, 1.4 * y_lim_max2 - 0.4 * y_lim_min2)
        else:
            ax.set_ylim(-0.2 * y_lim_max + 1.2 * y_lim_min, 1.6 * y_lim_max - 0.6 * y_lim_min)
            ax2.set_ylim(-0.2 * y_lim_max2 + 1.2 * y_lim_min2, 1.6 * y_lim_max2 - 0.6 * y_lim_min2)
        n = max(4, daily_earn_df.shape[0])
        show_idx = [0, int(round(n * 0.33 - 1, 0)), int(round(n * 0.67 - 1, 0)), n - 1]
        plt.xticks(show_idx, [all_date[i] for i in show_idx])
        plt.title(f'策略累计收益（万元，左）与{index_name}指数（右）对比', fontproperties=myfont)
        plt.tight_layout()

    def daily_profit_bar(self, ax, daily_earn_df, idx=0):
        """策略每日收益与每日超额收益"""
        all_date = daily_earn_df.index
        ax.bar(range(len(all_date)), daily_earn_df[self.tags[idx]] / 1e4, label=self.tags[idx], color=self.color_all[idx])
        plt.legend(prop=myfont_legend)
        n = max(4, daily_earn_df.shape[0])
        show_idx = [0, int(round(n * 0.33 - 1, 0)), int(round(n * 0.67 - 1, 0)), n - 1]
        plt.xticks(show_idx, [all_date.values[i] for i in show_idx])
        plt.title(f'{self.tags[idx]}每日收益柱状图（万）', fontproperties=myfont)
        plt.tight_layout()

    def daily_excess_profit(self, ax, daily_earn_df):
        all_date = [str(x) for x in daily_earn_df.index]
        diff_profit = daily_earn_df[self.tags[1]] - daily_earn_df[self.tags[0]]
        ax.bar(all_date, diff_profit / 1e4)
        n = max(4, daily_earn_df.shape[0])
        show_idx = [0, int(round(n * 0.33 - 1, 0)), int(round(n * 0.67 - 1, 0)), n - 1]
        plt.xticks(show_idx, [all_date[i] for i in show_idx])
        plt.title(f'{self.tags[1]}相对{self.tags[0]}每日超额收益柱状图（万）', fontproperties=myfont)
        plt.tight_layout()

    def daily_index_bar(self, ax, all_date):
        all_date = [str(x) for x in all_date]
        if self.index_code in ['000832.SH']:
            index_close = get_index_data(self.index_code, '20200101', self.ed_date, ['close', 'open'])
            index_pct = (index_close['close'] / index_close['open'] - 1)[[x.replace('-', '') for x in all_date]]
        else:
            index_close = get_index_data(self.index_code, self.st_date, self.ed_date, ['close', 'pre_close'])
            index_close['pct'] = index_close['close'] / index_close['pre_close'] - 1
            index_pct = index_close['pct'][[str(x) for x in all_date]]
        name_code_map = {"000300.SH": "沪深300", "000905.SH": "中证500", "000852.SH": "中证1000", "000832.SH": "中证转债", "399006.SZ": "创业板指"}
        index_name = name_code_map[self.index_code]

        ax.bar(all_date, index_pct * 100)
        n = max(4, len(all_date))
        show_idx = [0, int(round(n * 0.33 - 1, 0)), int(round(n * 0.67 - 1, 0)), n - 1]
        plt.xticks(show_idx, [all_date[i] for i in show_idx])
        plt.title(f'{index_name}每日涨跌幅（%）', fontproperties=myfont)
        plt.tight_layout()


# -----------------------------------------------------------------------------------------------
# ----------------------------------- Helper Funcs -----------------------------------
def split_date_monthly(st_date, ed_date, split_by_month=False):
    st_date_int = int(st_date.replace("-", ""))
    ed_date_int = int(ed_date.replace("-", ""))
    monthly_date = trading_day(st_date_int, ed_date_int, freq="M")
    period_all = [[st_date, ed_date]]
    period_name = [f"{st_date[4:6]}-{ed_date[4:6]}月"]
    for m_date in monthly_date:
        period_name.append("{}月".format(int(str(m_date)[4:6])))
        period_all.append(["{}{}01".format(str(m_date)[0:4], str(m_date)[4:6]),
                           "{}{}{}".format(str(m_date)[0:4], str(m_date)[4:6], str(m_date)[6:8])])
    period_all[1][0] = st_date
    period_all[-1][-1] = ed_date
    period_text = "{}-{} ".format(period_all[0][0].replace("-", "."), period_all[0][1].replace("-", "."))
    if not split_by_month:
        period_all, period_name = period_all[:1], period_name[:1]
    return period_all, period_name, period_text


def combine_daily_sum(abs_path_list, sheet_name=''):
    """将多个文件夹里的daily sum文件合并到一个文件中"""
    daily_sum_list = []
    for abs_path in abs_path_list:
        result_daily = pd.read_excel(f'{abs_path}/result_daily.xls', sheet_name=f'result_daily{sheet_name}', index_col=0)
        daily_sum_list.append(result_daily)
    daily_sum_df = pd.concat(daily_sum_list)
    return daily_sum_df


def combine_code_sum(abs_path_list):
    """将多个文件夹里的按股票汇总的收益，合并起来"""
    code_sum_list = []
    for abs_path in abs_path_list:
        code_res = pd.read_excel(abs_path + "/TotalSummary.xls", sheet_name="TotalSummary", index_col=0)[['afterCostProfit']]
        code_sum_list.append(code_res)
    code_sum_df = pd.concat(code_sum_list, axis=1).sum(axis=1)
    return code_sum_df


def compare_res(dir_list, col_names=None):
    res = []
    for dir_ in dir_list:
        print(f'{dir_}/result_daily.xls')
        bt_file_data = pd.read_excel(f'{dir_}/result_daily.xls', sheet_name="result_daily").loc[0]
        bt_file_data = pd.DataFrame(bt_file_data)
        res.append(bt_file_data)
    res = pd.concat(res, axis=1)
    if col_names is not None:
        res.columns = col_names
    return res
