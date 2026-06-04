"""bt回测的结果分析程序——update @2021.8.20"""

import os
import numpy as np
import pandas as pd
from DataAPI.DataView import file_list_dir, file_exist, load_excel_file, load_pickle_file, save_pickle_file
from Utils.UtilsCode import code_list_market
from Utils.UtilsTime import minute_t2m, minute_m2t


class AnalyzeResult:
    def __init__(self, output_dir, select_code_list=None, exclude_code_list=None, save_dir=''):
        self.output_dir = output_dir
        self.result_dir = f'/data/user/011668/{output_dir}'
        self.save_dir = f'{self.result_dir}/{save_dir}'
        os.makedirs(self.save_dir, exist_ok=True)

        self.select_code_list = select_code_list
        self.exclude_code_list = exclude_code_list
        self.code_list = self.__get_code_list()

    def analyze(self, is_classify=False):
        self.combine_data()
        self.summary_date_code(is_classify)
        self.code_matrix()

    def summary_date_code(self, is_classify):
        summary_code_df = load_pickle_file(f'{self.save_dir}/CombineData/summary.pickle').sort_values(by='afterCostProfit', ascending=False)
        trade_df = load_pickle_file(f'{self.save_dir}/CombineData/trades.pickle')
        total_size = summary_code_df['initAmount'].sum()
        summary_date_df = self.summary_by_date(trade_df, total_size)
        summary_code_df.to_excel(f'{self.save_dir}/TotalSummary.xls', sheet_name='TotalSummary')

        if is_classify:
            code_classify = code_list_market(self.code_list)
            is_stock = not self.code_list[0].startswith('1')
            summary_by_date_long_df, summary_by_date_short_df = None, None
            if is_stock:  # 股票策略才进行多空端汇总
                summary_by_date_long_df = self.summary_by_date(trade_df[trade_df['direction'] == 'long '], total_size)
                summary_by_date_short_df = self.summary_by_date(trade_df[trade_df['direction'] == 'short'], total_size)
            trade_df['classify'] = trade_df['code'].map(code_classify)
            summary_code_df['classify'] = summary_code_df.index.map(code_classify)
            total_size_classify = summary_code_df[['classify', 'initAmount']].groupby('classify').sum()['initAmount'].to_dict()
            classify_all = set(trade_df['classify'])

            with pd.ExcelWriter(f'{self.save_dir}/result_daily.xls') as writer:
                summary_date_df.to_excel(writer, sheet_name='result_daily', index=False)
                if is_stock:
                    summary_by_date_long_df.to_excel(writer, sheet_name='result_daily_long', index=False)
                    summary_by_date_short_df.to_excel(writer, sheet_name='result_daily_short', index=False)
                if '6' in classify_all:
                    summary_by_date_sh_df = self.summary_by_date(trade_df[trade_df['classify'] == '6'], total_size_classify['6'])
                    summary_by_date_sh_df.to_excel(writer, sheet_name='result_daily_6', index=False)
                if '0' in classify_all:
                    summary_by_date_sz0_df = self.summary_by_date(trade_df[trade_df['classify'] == '0'], total_size_classify['0'])
                    summary_by_date_sz0_df.to_excel(writer, sheet_name='result_daily_0', index=False)
                if '3' in classify_all:
                    summary_by_date_sz3_df = self.summary_by_date(trade_df[trade_df['classify'] == '3'], total_size_classify['3'])
                    summary_by_date_sz3_df.to_excel(writer, sheet_name='result_daily_3', index=False)
        else:
            summary_date_df.to_excel(f'{self.save_dir}/result_daily.xls', sheet_name='result_daily', index=False)

    @staticmethod
    def summary_by_date(orders_data, total_size):
        date_list = sorted(set(orders_data["date"]))
        sum_data_by_date = []
        for trade_date in date_list:
            daily_data = orders_data[orders_data["date"] == trade_date]

            after_cost_profit = sum(daily_data["afterCostProfit"])
            trigger_times = daily_data.shape[0]
            win_times = sum(daily_data["afterCostProfit"] > 0)
            win_rate = win_times / trigger_times if trigger_times != 0 else 0
            daily_open_amount = sum(daily_data["cumAmount"])

            after_cost_profit_earn = sum(daily_data[daily_data["afterCostProfit"] > 0]["afterCostProfit"])
            after_cost_profit_loss = sum(daily_data[daily_data["afterCostProfit"] < 0]["afterCostProfit"])
            daily_open_amount_earn = sum(daily_data[daily_data["afterCostProfit"] > 0]["cumAmount"])
            daily_open_amount_loss = sum(daily_data[daily_data["afterCostProfit"] < 0]["cumAmount"])
            earn_return_rate = after_cost_profit_earn / daily_open_amount_earn if daily_open_amount_earn != 0 else 0
            loss_return_rate = after_cost_profit_loss / daily_open_amount_loss if daily_open_amount_loss != 0 else 0
            earn_loss_rate = round(-after_cost_profit_earn / after_cost_profit_loss, 2) if after_cost_profit_loss != 0 else "nan"

            hold_time = list(daily_data["holdTime"])
            for m in range(len(hold_time)):
                hold_time[m] = minute_t2m(hold_time[m])
            ave_hold_time = np.mean(hold_time)
            ave_hold_time = minute_m2t(ave_hold_time)

            daily_info_data = [trade_date, total_size, after_cost_profit, trigger_times, win_times,
                               str(int(win_rate * 100)) + "%",
                               round(after_cost_profit / daily_open_amount * 1000, 2),
                               str(int(daily_open_amount / total_size * 100)) + "%", daily_open_amount,
                               round(after_cost_profit / total_size * 1000, 2),
                               round(earn_return_rate * 1000, 2), round(loss_return_rate * 1000, 2), earn_loss_rate,
                               round(min(0, min(daily_data["returnRate"])) * 1000, 2), ave_hold_time]
            sum_data_by_date.append(daily_info_data)
        sum_df = pd.DataFrame(sum_data_by_date, columns=['日期', '总市值', '总盈利', '交易次数', '获利次数', '胜率',
                                                         '平均收益率', '利用率', '交易总市值', '市值收益率', '获利收益率',
                                                         '亏损收益率', '盈亏比', '最大单笔亏损', '平均持仓时间'])
        return sum_df

    def code_matrix(self):
        # 个股【总盈利、平均收益率、市值收益率、盈亏比】矩阵
        daily_df = load_pickle_file(f'{self.save_dir}/CombineData/daily.pickle').set_index(['日期', 'code'])
        profit_matrix = daily_df['总盈利'].unstack()
        ret_trade_matrix = daily_df['平均收益率'].unstack()
        ret_mv_df = daily_df['市值收益率'].unstack()
        amt_trade_matrix = daily_df['交易总市值'].unstack()
        win_loss_ratio_df = daily_df['盈亏比'].unstack()
        with pd.ExcelWriter(f'{self.save_dir}/daily_split.xlsx') as writer:
            profit_matrix.to_excel(writer, sheet_name='profit')
            ret_trade_matrix.to_excel(writer, sheet_name='ret_trade')
            ret_mv_df.to_excel(writer, sheet_name='ret_mv')
            amt_trade_matrix.to_excel(writer, sheet_name='amt_trade')
            win_loss_ratio_df.to_excel(writer, sheet_name='win_loss_ratio')

    def combine_data(self):
        order_list, trade_list, daily_list, summary_list = [], [], [], []
        for code in self.code_list:
            try:
                code_data = load_excel_file(f'{self.output_dir}/{code}/result_all.xlsx',
                                            sheet_name=['detailedOrders', 'orders', 'dailyInfo', 'summary'])
            except:
                print(f'{code} DATA NOT FOUND')
                continue
            data_order, data_trade = code_data['detailedOrders'], code_data['orders']
            data_order['time'] = [x.split('-')[1] for x in data_order['orderTime']]
            data_order['date'] = [f'20{a}{b}{c}' for (b, c, a) in [x.split('-')[0].split('/') for x in data_order['orderTime']]]
            data_order = data_order.rename(columns={'quantity': 'vol', 'orderAmount': 'amt',
                                                    'avgPrice': 'price_trade', 'cumQty': 'vol_trade', 'cumAmount': 'amt_trade'})
            data_order = data_order[['tradeNo', 'code', 'date', 'time', 'direction', 'price', 'vol', 'amt', 'price_trade', 'vol_trade', 'amt_trade']]
            data_trade['date'] = [x.replace('-', '') for x in data_trade['date']]
            order_list.append(data_order)
            trade_list.append(data_trade)

            data_daily, data_summary = code_data['dailyInfo'], code_data['summary']
            data_daily['code'] = code
            data_summary.index = [code]
            daily_list.append(data_daily)
            summary_list.append(data_summary)
        order_df = pd.concat(order_list)
        trade_df = pd.concat(trade_list)
        daily_df = pd.concat(daily_list)
        summary_df = pd.concat(summary_list)
        os.makedirs(f'{self.result_dir}/CombineData', exist_ok=True)
        save_pickle_file(self.code_list, f'{self.result_dir}/CombineData/code_list.pickle')
        save_pickle_file(order_df, f'{self.result_dir}/CombineData/orders.pickle')
        save_pickle_file(trade_df, f'{self.result_dir}/CombineData/trades.pickle')
        save_pickle_file(daily_df, f'{self.result_dir}/CombineData/daily.pickle')
        save_pickle_file(summary_df, f'{self.result_dir}/CombineData/summary.pickle')

    def __get_code_list(self):
        if self.select_code_list is not None:
            return self.select_code_list
        file_list = file_list_dir(self.output_dir)
        code_list = list(filter(lambda x: x.endswith('.SH') or x.endswith('.SZ'), file_list))
        if self.exclude_code_list is not None:
            return list(set(code_list) - set(self.exclude_code_list))
        return code_list

    def transfer_file(self):
        """将文件从HDFS上传到NAS上"""
        result_dir_code = f'{self.result_dir}/CodeResult'
        os.makedirs(result_dir_code, exist_ok=True)

        from xquant.xqutils.xqfile import Pyfile
        py = Pyfile()
        for i, code in enumerate(self.code_list):
            hdfs_file = f'{self.output_dir}/{code}/result_all.xlsx'
            py.download(result_dir_code, hdfs_file)
            os.rename(f'{result_dir_code}/result_all.xlsx', f'{result_dir_code}/{code}.xlsx')
