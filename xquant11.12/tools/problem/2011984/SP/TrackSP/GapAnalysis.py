"""实盘交易与bt交易的差异分析程序——update @2021.3.1"""

import os
import numpy as np
import pandas as pd
from DataAPI.DataView import file_list_dir, load_excel_file
from SP.UtilsSP.LoadSPFile import load_sp_result_by_stock, load_sp_detail_result


def main():
    trade_date = 20220421
    # strategy = 'Kunlun_mix'
    # suffix_list = ['mix_JS_pro_sh', 'mix_JS_res_sh']
    strategy = 'Everest1S'
    suffix_list = ['everest1s_pro_sz', 'everest1s_res_sz']
    gap = StockGapSum(strategy, trade_date, suffix_list)
    compare_by_code = gap.compare_by_code()
    print(compare_by_code.sum())
    
    # compare_by_code['gap'] = compare_by_code['Res盈利'] - compare_by_code['实盘盈利']
    compare_by_code['gap'] = compare_by_code['Pro盈利'] - compare_by_code['实盘盈利']
    compare_by_code = compare_by_code.sort_values(by='gap', ascending=False)
    compare_single_code = gap.gap_single_stock(list(compare_by_code.index)[0: 10])
    return compare_single_code


class StockGapSum:
    def __init__(self, strategy, trade_date, suffix_list):
        self.strategy = strategy
        self.trade_date = trade_date
        self.path_list = self.get_bt_path(suffix_list)
        self.names = ['Pro', 'Res']

    def compare_by_code(self):
        sp_result = load_sp_result_by_stock(self.trade_date, self.strategy)[["证券代码", "盈利", "交易金额"]].set_index("证券代码")
        bt_result_list = []
        all_code = []
        for path in self.path_list:
            bt_result = pd.read_excel(f'/data/user/011668/{path}/TotalSummary.xls', index_col=0)[["afterCostProfit", "aveDailyCumAmount"]]
            all_code += list(bt_result.index)
            bt_result_list.append(bt_result)
        all_code = list(set(all_code))
        sp_result = sp_result.loc[all_code]
        col_names = ['实盘盈利'] + [f'{x}盈利' for x in self.names] + ['实盘交易额'] + [f'{x}交易额' for x in self.names]
        compare_by_stock = pd.DataFrame(0, index=all_code, columns=col_names)
        for i in range(sp_result.shape[0]):
            code = sp_result.index[i]
            print(code)
            if not np.isnan(sp_result.at[code, "盈利"].sum()):
                compare_by_stock.at[code, "实盘盈利"] = sp_result.at[code, "盈利"].sum()
                compare_by_stock.at[code, "实盘交易额"] = sp_result.at[code, "交易金额"].sum()
        for i_, bt_result in enumerate(bt_result_list):
            for i in range(bt_result.shape[0]):
                code = bt_result.index[i]
                compare_by_stock.at[code, f"{self.names[i_]}盈利"] = bt_result.at[code, "afterCostProfit"]
                compare_by_stock.at[code, f"{self.names[i_]}交易额"] = bt_result.at[code, "aveDailyCumAmount"]

        compare_by_stock["gap"] = abs(compare_by_stock[f"{self.names[0]}盈利"] - compare_by_stock["实盘盈利"])
        compare_by_stock = compare_by_stock.sort_values(by="gap", ascending=False)
        compare_by_stock["gap"] = compare_by_stock["Pro盈利"] - compare_by_stock["实盘盈利"]
        return compare_by_stock

    def gap_single_stock(self, code_list):
        out_dict = dict()
        sp_res = load_sp_detail_result(self.trade_date, self.strategy, is_adjust=True)
        sp_res = sp_res[sp_res['委托时间'] > '09:30:00']
        for code in code_list:
            code_sp = sp_res[sp_res['证券代码'] == int(code.split('.')[0])]
            code_sp['direction'] = ['long ' if x == '买入' else 'short' for x in code_sp['委托方向']]
            code_sp = code_sp[['direction', '委托时间', '委托数量', '委托价格', '累计成交数量']]
            code_sp = code_sp.groupby(['direction', '委托时间', '委托价格']).sum().reset_index().set_index('委托时间')
            code_sp.columns = ['direction', 'price', 'quantity', 'cumQty']
            code_sp.columns = [f'{x}_sp' for x in code_sp.columns]
            code_sp['price_sp'] = code_sp['price_sp'].apply(lambda x: round(x, 3))

            code_pro = load_excel_file(f'{self.path_list[0]}/{code}/result_all.xlsx')
            code_pro['time'] = [x.split('-')[1] for x in code_pro['orderTime']]
            code_pro = code_pro[['time', 'direction', 'price', 'quantity', 'cumQty']]
            code_pro = code_pro.groupby(['time', 'direction', 'price']).sum().reset_index().set_index('time')
            code_pro.columns = [f'{x}_pro' for x in code_pro.columns]
            if len(set(code_pro.index)) != code_pro.shape[0]:
                code_pro = self.duplicated_index_process(code_pro)
            code_pro['price_pro'] = code_pro['price_pro'].apply(lambda x: round(x, 3))

            compare_df = pd.concat([code_sp, code_pro], axis=1)
            compare_df = compare_df[['direction_sp', 'direction_pro', 'price_sp', 'price_pro',
                                     'quantity_sp', 'quantity_pro', 'cumQty_sp', 'cumQty_pro']].fillna('-')
            for idx in ['direction', 'price', 'quantity']:
                compare_df[idx] = compare_df[f'{idx}_sp'] == compare_df[f'{idx}_pro']

            out_dict.update({code: compare_df})
        return out_dict

    def get_bt_path(self, suffix_list):
        bt_path = 'BT_Track/{}/bt-{}/'.format(self.strategy.split('_')[0], self.trade_date)
        all_file = file_list_dir(bt_path)
        out_dir_list = []
        for suffix in suffix_list:
            for file in all_file:
                if suffix in file:
                    out_dir_list.append(f'{bt_path}/{file}')
        if len(out_dir_list) != len(suffix_list):
            raise ValueError('长度不一致，请检查')
        return out_dir_list

    @staticmethod
    def duplicated_index_process(data_df):
        """对于index相同的行进行合并"""
        data_df['amt'] = data_df['price_pro'] * data_df['quantity_pro']
        code_pro1 = data_df.reset_index().groupby(['time', 'direction_pro']).sum()
        code_pro1['price_pro'] = code_pro1['amt'] / code_pro1['quantity_pro']
        code_pro1 = code_pro1[['price_pro', 'quantity_pro', 'cumQty_pro']].reset_index().set_index('time')
        return code_pro1


if __name__ == '__main__':
    main()
