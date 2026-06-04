"""针对bt结果分层统计分析——update @2021.9.9"""

import pandas as pd
from DataAPI.DataView import load_pickle_file
from DataAPI.DataToolsCbond import get_cbond_stock_map
from DataAPI.GetCodeVol import get_target_industry, get_industry_info
from Utils.UtilsCode import get_code_market


class LayerAnalysis:
    def __init__(self, abs_path, asset_class):
        self.abs_path = abs_path
        self.asset_class = asset_class
        self.sb_stock_map = dict()  # 转债与股票对应的列表
        self.industry_base_date = None
        self.res_order, self.res_trade = self.pre_process()
        self.all_industry_name = get_industry_info('CITICS', 1)['industry_name'].to_list()  # 所有行业名称

    def pre_process(self):
        order_df = load_pickle_file(f'{self.abs_path}/CombineData/orders.pickle')
        trade_df = load_pickle_file(f'{self.abs_path}/CombineData/trades.pickle')
        trade_df = trade_df.rename(columns={'afterCostProfit': 'profit', 'cumAmount': 'amt', 'returnRate': 'ret', 'endTime': 'ed_time'})
        self.industry_base_date = trade_df['date'].max().replace('-', '')
        return order_df, trade_df

    def start(self):
        if self.asset_class == 'cb':
            self.sb_stock_map = get_cbond_stock_map(self.res_trade['code'].to_list())
        data_morning_afternoon = self.layer_morning_afternoon()
        data_market = self.layer_market()
        layer_df = pd.concat([data_morning_afternoon, data_market])
        if self.asset_class == 'stock':
            data_sector = self.layer_sector()
            data_long_short = self.layer_long_short()
            layer_df = pd.concat([data_long_short, layer_df, data_sector])
        layer_df.at['总计', 'profit'] = self.res_trade['profit'].sum()
        layer_df.at['总计', 'amt'] = self.res_trade['amt'].sum()
        layer_df.at['总计', 'trade_nums'] = self.res_trade.shape[0]
        layer_df.at['总计', 'ret'] = layer_df.at['总计', 'profit'] / layer_df.at['总计', 'amt'] if layer_df.at['总计', 'amt'] != 0 else 0
        layer_df.at['总计', 'win_rate'] = sum(self.res_trade['profit'] > 0) / self.res_trade.shape[0]
        layer_df['profit'] = layer_df['profit'].apply(int)
        layer_df['amt'] = layer_df['amt'].apply(int)
        layer_df['ret'] = [round(x * 1000, 2) for x in layer_df['ret']]
        layer_df['win_rate'] = [round(x, 4) for x in layer_df['win_rate']]
        return layer_df

    def layer_long_short(self):
        """按多空分层"""
        trade_data = self.res_trade[['direction', 'profit', 'amt', 'ret']]
        res_df = self.layer_stat(trade_data, 'direction')
        res_df = res_df.loc[['long', 'short']]
        return res_df

    def layer_morning_afternoon(self):
        """按上下午分层"""
        trade_data = self.res_trade[['ed_time', 'profit', 'amt', 'ret']]
        trade_data.loc[trade_data['ed_time'] < '12:00:00', 'day_period'] = '上午'
        trade_data.loc[trade_data['ed_time'] > '12:00:00', 'day_period'] = '下午'
        res_df = self.layer_stat(trade_data, 'day_period')
        res_df = res_df.loc[['上午', '下午']]
        return res_df

    def layer_market(self):
        """按股票所属市场分层"""
        trade_data = self.res_trade[['code', 'profit', 'amt', 'ret']]
        market_map = {'stock_kcb': '科创板', 'stock_sh': '上海主板', 'stock_sz': '深圳主板', 'stock_cyb': '创业板'}
        trade_data['market'] = [market_map[get_code_market(self.get_stock_code(code))] for code in trade_data['code']]
        res_df = self.layer_stat(trade_data, 'market')
        res_df = res_df.loc[['上海主板', '深圳主板', '创业板', '科创板']]
        res_df = res_df.dropna(axis=0, how='all')
        return res_df

    def layer_sector(self):
        """按行业分层"""
        trade_data = self.res_trade[['code', 'profit', 'amt', 'ret']]
        all_code = [self.get_stock_code(x) for x in list(set(trade_data['code']))]
        industry_info = get_target_industry(all_code, self.industry_base_date).set_index('stock')['industry_name']
        trade_data['industry'] = [industry_info[self.get_stock_code(x)] for x in trade_data['code']]
        res_df = self.layer_stat(trade_data, 'industry')
        res_df = res_df.loc[self.all_industry_name].fillna(0).sort_values(by='profit')
        return res_df

    @staticmethod
    def layer_stat(trade_data, classify_col_name):
        classify_names = list(set(trade_data[classify_col_name]))
        res_df = pd.DataFrame(index=classify_names, columns=['profit', 'amt', 'trade_nums', 'ret', 'win_rate'])
        for name in classify_names:
            classify_df = trade_data[trade_data[classify_col_name] == name]
            res_df.at[name, 'profit'] = classify_df['profit'].sum()
            res_df.at[name, 'amt'] = classify_df['amt'].sum()
            res_df.at[name, 'trade_nums'] = classify_df.shape[0]
            res_df.at[name, 'ret'] = res_df.at[name, 'profit'] / res_df.at[name, 'amt'] if res_df.at[name, 'amt'] != 0 else 0
            res_df.at[name, 'win_rate'] = sum(classify_df['profit'] > 0) / classify_df.shape[0]
        return res_df.rename(index={'long ': 'long'})

    def get_stock_code(self, code):
        """获取对应的正股代码"""
        if self.asset_class == 'cb':
            return self.sb_stock_map[code]
        return code
