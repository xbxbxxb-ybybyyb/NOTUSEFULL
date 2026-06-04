"""实盘解析交易的收益情况————update @2021.12.22"""

import pandas as pd
from DataAPI.ARootPath import RootPath
from DataAPI.DataView import load_json_file, file_exist
from DataAPI.TradingDay import trading_day


def get_resolve_result(st_date, ed_date, strategy, market='all', select_code_list=None, exclude_code_list=None):
    date_list = trading_day(st_date, ed_date)
    res_list = []
    for trade_date in date_list:
        resolve_res = summary_resolve_result(trade_date, strategy, market, select_code_list, exclude_code_list)
        res_list.append(resolve_res)
    res_df = pd.concat(res_list, axis=1)
    res_df.columns = date_list
    return res_df.T


def summary_sp_data(sp_data):
    total_profit = sp_data['profit'].sum()  # 总盈利
    trade_nums = sp_data.shape[0]  # 交易次数
    win_nums = sp_data[sp_data['profit'] > 0].shape[0]  # 获利次数
    win_rate = win_nums / trade_nums  # 胜率
    mv_trade = (sp_data['buy_amt'].sum() + sp_data['sell_amt'].sum()) / 2  # 交易总市值
    ret_mean = total_profit / mv_trade * 1000  # 平均收益率
    ret_win = sp_data.loc[sp_data['ret'] > 0, 'ret'].mean() * 1000  # 获利收益率
    ret_loss = sp_data.loc[sp_data['ret'] < 0, 'ret'].mean() * 1000  # 亏损收益率
    win_loss_rate = -ret_win / ret_loss  # 盈亏比
    max_loss_rate = sp_data['ret'].min() * 1000  # 最大单笔亏损
    ave_holding_time = sp_data['holding_time'].mean()  # 平均持仓时间
    sp_summary = {'总盈利': int(total_profit), '交易次数': int(trade_nums), '获利次数': int(win_nums), '胜率': f'{round(win_rate * 100)}%',
                  '平均收益率': round(ret_mean, 2), '交易总市值': int(mv_trade), '获利收益率': round(ret_win, 2), '亏损收益率': round(ret_loss, 2),
                  '盈亏比': round(win_loss_rate, 2), '最大单笔亏损': round(max_loss_rate, 2), '平均持仓时间': round(ave_holding_time, 2)}
    sp_summary_series = pd.Series(sp_summary)
    return sp_summary_series


def summary_resolve_result(trade_date, strategy, market='all', select_code_list=None, exclude_code_list=None):
    """汇总实盘解析出来的交易结果"""
    resolve_path = RootPath().get_sp_trading_resolve_path(strategy)
    sp_resolve_file = f'{resolve_path}/{trade_date}_trade.csv'
    sp_data = pd.read_csv(sp_resolve_file, index_col=['code'])
    if select_code_list is not None:
        sp_data = sp_data.loc[select_code_list]
    if exclude_code_list is not None:
        sp_data = sp_data.loc[[x not in exclude_code_list for x in sp_data.index]]
    if market == 'sz':
        sp_data = sp_data.loc[list(set([x for x in sp_data.index if x.startswith('12')]))]
    elif market in ['hs300', 'zz500']:
        from DataAPI.GetCodeVol import get_index_code
        code_list300 = get_index_code(market)
        sp_data = sp_data.loc[code_list300]
    elif market in ['50601']:
        sp_data = sp_data[sp_data['portfolio'] == int(market)]
    sp_summary_series = summary_sp_data(sp_data)
    return sp_summary_series


def get_sp_resolve_summary_result(trade_date, strategy="Albest"):
    """获取实盘解析交易的汇总结果"""
    if strategy in ['Albest', 'Everest']:
        strategy_code_list = load_json_file(f'/data/user/011668/SP_Data/SP_Params/{strategy}_sp/CodeList/code_list_{trade_date}.json')
        res_list = []
        for sub2 in ['sh', 'sz', 'cyb']:
            code_list_sub = list(strategy_code_list[f'code_list_{sub2}'].keys())
            if len(code_list_sub) > 0:
                res_sub = pd.DataFrame(summary_resolve_result(trade_date, strategy, select_code_list=code_list_sub),
                                         columns=[f'{strategy}实盘_{sub2}'])
                res_list.append(res_sub)
        res_df = pd.concat(res_list, axis=1)
        return res_df
    elif strategy == 'Kunlun':
        resolve_path = RootPath().get_sp_trading_resolve_path('Kunlun_portfolio')
        res_list = []
        for sub1 in ['mix', 'pure']:
            for sub2 in ['o32', 'o45']:
                for sub3 in ['sh', 'sz', 'cyb']:
                    sub_all = f'{sub1}_{sub2}_{sub3}'
                    p_dict = {'mix_o32_sh': '5160204', 'mix_o32_sz': '', 'mix_o32_cyb': '',
                              'mix_o45_sh': '2000000401', 'mix_o45_sz': '2000000301', 'mix_o45_cyb': '2000000301',
                              'pure_o32_sh': '5160205', 'pure_o32_sz': '5160205', 'pure_o32_cyb': '5160205',
                              'pure_o45_sh': '2000000400', 'pure_o45_sz': '', 'pure_o45_cyb': '',
                              }
                    sub_p = p_dict[sub_all]
                    if sub_p != '' and file_exist(f'{resolve_path}/{trade_date}_{sub_p}_trade.csv'):
                        sp_data = pd.read_csv(f'{resolve_path}/{trade_date}_{sub_p}_trade.csv', index_col=['code'])
                        if sub3 in ['sz', 'cyb']:
                            code_list = load_json_file(f'/data/user/011668/SP_Data/SP_Params/Kunlun_sp/CodeList/code_list_{sub1}_{trade_date}.json')
                            sp_data = sp_data.loc[code_list[sub2][sub3]]
                        res_sub = summary_sp_data(sp_data)
                        res_sub_df = pd.DataFrame(res_sub, columns=[f'Kunlun_{sub1}_{sub2}实盘_{sub3}'])
                        res_list.append(res_sub_df)
        res_df = pd.concat(res_list, axis=1)
        return res_df
