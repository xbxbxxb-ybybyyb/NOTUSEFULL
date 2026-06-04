"""每日跟踪，多日汇总程序——update @2021.4.27"""

import os
import numpy as np
from DataAPI.TradingDay import trading_day
from SP.UtilsSP.LoadSPFile import load_sp_result_by_stock
from Utils.MultiTasks import main_multiprocess
from Utils.UtilsCode import code_list_market
import pandas as pd


def main():
    gap_df_albest = BigSum('20211117', '20211206', 'Albest').sum_result_classify()
    gap_df_everest = BigSum('20211117', '20211206', 'Everest').sum_result_classify()
    # gap_df_kunlun = BigSum('20211101', '20211222', 'Kunlun_mix').sum_result_classify()
    save_path = '/data/user/011668/other/bt_result.xls'
    writer = pd.ExcelWriter(save_path, engine='xlsxwriter')
    gap_df_albest.to_excel(writer, sheet_name='Albest')
    gap_df_everest.to_excel(writer, sheet_name='Everest')
    writer.save()
    
    strategy = 'Everest'
    data_df = pd.read_excel(save_path, sheet_name=strategy, index_col=0)
    plot_result(data_df, strategy)


def main2():
    save_path = '/data/user/011668/other/bt_result.xls'

    gap_df_kunlun = BigSum('20210601', '20210903', 'Albest').sum_result_classify()
    writer = pd.ExcelWriter(save_path, engine='xlsxwriter')
    gap_df_kunlun.to_excel(writer, sheet_name='Kunlun')
    writer.save()

    # strategy = 'Everest'
    # data_df = pd.read_excel(save_path, sheet_name=strategy, index_col=0)
    # plot_result(data_df, strategy)


class BigSum:
    def __init__(self, st_date, ed_date, portfolio):
        self.portfolio = portfolio
        self.all_trading_days = trading_day(st_date, ed_date)
        self.sp_path = f'/data/user/011668/BT_Results/summary/{portfolio}/'

    def sum_result(self):
        profit_sum = []
        for trade_date in self.all_trading_days:
            single_data = pd.read_csv('{}/{}.csv'.format(self.sp_path, trade_date), index_col=0)
            single_data.columns = ["实盘", "production", "research"]
            profit_sum.append(single_data.loc['总盈利'].apply(float).apply(int))
        profit_sum_df = pd.concat(profit_sum, axis=1)
        profit_sum_df.columns = self.all_trading_days
        profit_sum_df = profit_sum_df.T
        profit_sum_df["gap"] = profit_sum_df["research"] - profit_sum_df["实盘"]
        return profit_sum_df

    def sum_result_classify_local(self, all_trading_days):
        gap_list = []
        for trade_date in all_trading_days:
            try:
                sp_res_by_stock = load_sp_result_by_stock(trade_date, self.portfolio)[['证券代码', '盈利']]
                code_map = code_list_market(list(sp_res_by_stock['证券代码']))
                sp_res_by_stock['type'] = sp_res_by_stock['证券代码'].map(code_map)
                sp_res_group = sp_res_by_stock.groupby(by='type').sum()['盈利']

                bt_pro_by_stock = self.get_bt_result_by_stock(trade_date, 'pro')
                if bt_pro_by_stock is not None:
                    bt_pro_by_stock = bt_pro_by_stock[['afterCostProfit']]
                    bt_pro_by_stock['type'] = bt_pro_by_stock.index.map(code_map)
                    bt_pro_group = bt_pro_by_stock.groupby(by='type').sum()['afterCostProfit']
                else:
                    bt_pro_group = [np.nan, np.nan, np.nan]

                bt_res_by_stock = self.get_bt_result_by_stock(trade_date, 'res')
                if bt_res_by_stock is not None:
                    bt_res_by_stock = bt_res_by_stock[['afterCostProfit']]
                    bt_res_by_stock['type'] = bt_res_by_stock.index.map(code_map)
                    bt_res_group = bt_res_by_stock.groupby(by='type').sum()['afterCostProfit']
                else:
                    bt_res_group = [np.nan, np.nan, np.nan]

                res_list = [trade_date] + list(sp_res_group) + list(bt_pro_group) + list(bt_res_group)
                gap_list.append(res_list)
                print('Finish: {}'.format(trade_date))
            except:
                print('Error: {}'.format(trade_date))
                continue
        return gap_list

    def sum_result_classify(self, process_nums=1):
        """按照股票代码进行差异汇总，上证/深证，主板/创业板"""
        if process_nums == 1:  # local
            gap_list = self.sum_result_classify_local(self.all_trading_days)
        else:  # multiprocessing
            gap_list = main_multiprocess(self.sum_result_classify_local, self.all_trading_days, process_nums)
        gap_df = pd.DataFrame(gap_list, columns=['date', 'sp0', 'sp3', 'sp6', 'pro0', 'pro3', 'pro6', 'res0', 'res3', 'res6']).\
            sort_values(by='date').set_index('date')
        gap_df.loc['sum'] = gap_df.dropna().sum(axis=0)
        for i_ in ['sp', 'pro', 'res']:
            gap_df[i_] = gap_df[[i_ + '0', i_ + '3', i_ + '6']].sum(axis=1)
        gap_df = gap_df[[f'{x}{y}' for y in ['', '0', '3', '6'] for x in ['sp', 'pro', 'res']]]
        return gap_df

    def get_bt_result_by_stock(self, trade_date, bt_type):
        if self.portfolio in ['Albest', 'Everest']:
            bt_path = f'/data/user/011668/BT_Track/{self.portfolio}/bt-{trade_date}'
            data_list = []
            for dir_ in os.listdir(bt_path):
                if get_file_type(dir_) == bt_type:
                    data = pd.read_excel(f'{bt_path}/{dir_}/TotalSummary.xls', index_col=0)
                    data_list.append(data)
        else:
            bt_path = f'/data/user/011668/BT_Track/Kunlun/bt-{trade_date}'
            data_list = []
            t = self.portfolio.split('_')[1]
            for dir_ in os.listdir(bt_path):
                if f'_{t}_{bt_type}' in dir_ or f'_{t}_JS_{bt_type}' in dir_ or f'_{bt_type}_{t}' in dir_ or \
                        f'_{t}_tp_{bt_type}' in dir_ or f'_{t}_JS_tp_{bt_type}' in dir_:
                    data = pd.read_excel(f'{bt_path}/{dir_}/TotalSummary.xls', index_col=0)
                    data_list.append(data)
        if len(data_list) > 0:
            return pd.concat(data_list)
        return None


def get_file_type(file_name):
    file_suffix = file_name.split('-')[-1]
    if '_pro' in file_suffix and '_res' in file_suffix:
        raise ValueError
    if '_pro' in file_suffix:
        return 'pro'
    elif '_res' in file_suffix:
        return 'res'


def plot_result(data_df, strategy, plot_method=1):
    import matplotlib.pyplot as plt
    from matplotlib import gridspec
    from Utils.UtilsPlot import plot_bar

    period_list = [['20210101', '20210430'], ['20210101', '20210131'], ['20210201', '20210228'], ['20210301', '20210331'],
                   ['20210401', '20210430'], ['20210501', '20210517']]

    # 不分市场
    if plot_method == 1:
        data_sum = pd.DataFrame()
        for [st_date, ed_date] in period_list:
            data_period = data_df.loc[st_date: ed_date].sum() / 1e4
            period_name = f'{int(st_date[4:6])}.{int(st_date[6:8])}-{int(ed_date[4:6])}.{int(ed_date[6:8])}'
            data_sum[period_name] = data_period[['sp', 'pro', 'res']]

        fig = plt.figure(figsize=(6, 3))
        ax = fig.add_subplot(111)
        plot_bar(ax, data_sum.T, title_text=f'{strategy} {period_list[0][0]}-{period_list[-1][-1]} 实盘与回测收益比对')
        plt.show()

    # 区分上交易、深交所和创业板
    else:
        fig = plt.figure(figsize=(12, 8))
        gs = gridspec.GridSpec(3, 2)
        for pos, [st_date, ed_date] in enumerate(period_list):
            data_sum = data_df.loc[st_date: ed_date].sum() / 1e4
            data_sum = pd.DataFrame(np.array(data_sum).reshape((4, 3)), index=['all', '0', '3', '6'], columns=['sp', 'pro', 'res'])
            pos_x, pos_y = pos // 2, pos % 2
            ax = fig.add_subplot(gs[pos_x:(pos_x + 1), pos_y:(pos_y + 1)])
            plot_bar(ax, data_sum, title_text=f'{strategy} {st_date}-{ed_date}  实盘与回测收益比对')
        plt.show()


if __name__ == '__main__':
    main()
