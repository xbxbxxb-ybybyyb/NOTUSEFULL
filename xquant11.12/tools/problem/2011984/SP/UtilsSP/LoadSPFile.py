"""
获取实盘与BT的交易原始文件
（1）load_sp_detail_result：获取实盘每笔交易结果
（2）load_sp_daily_result：获取实盘按日汇总结果
（3）load_sp_result_by_stock：获取实盘交易的按股票汇总结果
"""

import os
import pandas as pd
from DataAPI.ARootPath import RootPath
from DataAPI.TradingDay import trading_day
from Utils.UtilsTime import time_delta
from Utils.UtilsFile import FTP_OP
from Utils.UtilsCode import code_t


# sp_no_trading = {
#     'Albest': ['20210701'],
#     'Everest': ['20210701', '20220121', '20220124', '20210125'],
#     'Kunlun': [],
#     'Kunlun_mix': [],
#     'Kunlun_pure': ['20210916', '20210917']
# }


def strategy_sp_trading(strategy, trade_date):
    trade_date = str(trade_date)
    if strategy == 'Albest':
        if trade_date in ['20210701']:
            return False
    elif strategy == 'Everest':
        if trade_date in ['20210701']:
            return False
        elif trade_date >= '20220121':
            return False
    elif strategy == 'Kunlun_mix':
        return True
    elif strategy == 'Kunlun_pure':
        if trade_date in ['20210916', '20210917']:
            return False
    return True


def load_sp_detail_result(trade_date, portfolio="Albest", is_adjust=False):
    """获取实盘每笔交易结果，is_adjust为True的话，则时间往后延1s"""
    strategy = portfolio.split('_')[0]
    detail_path = f'{RootPath().get_sp_data_path()}/OriginSplitData/{strategy}/{trade_date}'
    os.makedirs(detail_path, exist_ok=True)
    strategy_file = f'{detail_path}/trade_detail.csv'
    if os.path.exists(strategy_file):
        sp_result = pd.read_csv(strategy_file)
    else:
        sp_file = get_sp_file(trade_date, strategy)
        if sp_file is None:
            return
        data_sp = pd.read_excel(sp_file, sheet_name=['委托明细', '持仓收益汇总'])
        sp_result = data_sp['委托明细']
        sp_result.to_csv(strategy_file, index=False)
        data_sp['持仓收益汇总'].to_csv(f'{detail_path}/profit_by_date.csv', index=False)

    # 策略的子组合
    if portfolio == 'Kunlun_mix':
        mix_p = list(set(sp_result['组合名称']).intersection({5160204, 2000000301, 2000000401}))
        sp_result = sp_result.set_index('组合名称').loc[mix_p].reset_index()
    elif portfolio == 'Kunlun_pure':
        pure_p = list(set(sp_result['组合名称']).intersection({5160205, 2000000300, 2000000400}))
        sp_result = sp_result.set_index('组合名称').loc[pure_p].reset_index()
    elif portfolio in ['Albest_hs300', 'Everest_hs300']:
        sp_result = sp_result[sp_result['组合名称'] == 5161206]

    if is_adjust:  # 如果时间整体往后延迟1s
        sp_result['委托时间'] = [time_delta(x, 1) for x in sp_result['委托时间']]
    # 如果委托时间位于11:30:00~13:00:00之间，则处理为13:00:00；位于15:00:00之后，则处理为15:00:00
    sp_result.loc[(sp_result['委托时间'] > '11:30:00') & (sp_result['委托时间'] < '13:00:00'), '委托时间'] = '13:00:01'
    sp_result.loc[sp_result['委托时间'] > '15:00:00', '委托时间'] = '15:00:00'
    return sp_result


def load_sp_daily_result(trade_date, strategy="Albest"):
    """获取实盘按日汇总结果"""
    sp_result_file = f'/data/user/011668/SP_Data/OriginSplitData/{strategy}/{trade_date}'
    if not os.path.exists(sp_result_file):
        sp_file = get_sp_file(trade_date, strategy)
        sheet_name_dict = {'Albest': '持仓收益汇总', 'Everest': '持仓收益汇总', 'Kunlun': '持仓收益汇总',
                           'Kunlun_mix': '2000000301汇总', 'Kunlun_pure': '5160205汇总',
                           'Kunlun_mix_o32': '5160204汇总', 'Kunlun_pure_o32': '5160205汇总',
                           'Kunlun_mix_o45': '2000000301汇总', 'Kunlun_pure_o45': '2000000300汇总',
                           'Albest_1206': '5161206汇总', 'Everest_1206': '5161206汇总'
                           }
        all_sheet_name = pd.ExcelFile(sp_file).sheet_names
        if sheet_name_dict[strategy] not in all_sheet_name:
            print(f'不存在组合：{strategy} {sheet_name_dict[strategy]}')
            return pd.DataFrame(columns=['日期', '总盈利'])
        sp_result = pd.read_excel(sp_file, sheet_name=sheet_name_dict[strategy])
        if sp_result['日期'].values[-1] == '汇总':
            sp_result = sp_result.iloc[:-1, :]
        if sp_result['日期'].values[0] == sp_result['日期'].values[-1]:
            sp_result = sp_result.iloc[1:, :]
        sp_result = sp_result.sort_values(by='日期')
        if len(set(sp_result['日期'])) != sp_result.shape[0]:
            raise ValueError('日期重复，请检查')
        os.makedirs(sp_result_file, exist_ok=True)
        sp_result.to_csv(f'{sp_result_file}/profit_by_date.csv', index=False)
    else:
        sp_result = pd.read_csv(f'{sp_result_file}/profit_by_date.csv')
    return sp_result


def load_sp_result_by_stock(trade_date, portfolio="Albest"):
    """获取实盘交易的按股票汇总结果"""
    stock_data_path = f'{RootPath().get_sp_data_path()}/OriginSplitData/{portfolio}/{trade_date}'
    os.makedirs(stock_data_path, exist_ok=True)
    stock_data_file = f'{stock_data_path}/profit_by_code.csv'
    if os.path.exists(stock_data_file):
        stock_result = pd.read_csv(stock_data_file)
    else:
        sp_file = get_sp_file(trade_date, portfolio.split('_')[0])
        sheet_name_dict = {'Albest': '组合证券', 'Everest': '组合证券', 'Everest1S': '组合证券', 'Kunlun': '组合证券',
                           'Albest_l2p': '组合证券', 'Everest_l2p': '组合证券',
                           'Kunlun_mix_o32': '组合证券5160204', 'Kunlun_pure_o32': '组合证券5160205',
                           'Kunlun_mix_o45': '组合证券2000000301', 'Kunlun_pure_o45': '组合证券2000000300'}
        if portfolio in ['Kunlun_mix', 'Kunlun_pure']:
            all_sheet_name = pd.ExcelFile(sp_file).sheet_names
            kunlun_dict = {'Kunlun_mix': ['Kunlun_mix_o32', 'Kunlun_mix_o45'], 'Kunlun_pure': ['Kunlun_pure_o32', 'Kunlun_pure_o45']}
            sheet_name_kunlun = [sheet_name_dict[x] for x in kunlun_dict[portfolio]]
            sheet_name_s = list(set(all_sheet_name).intersection(sheet_name_kunlun))
            stock_result_dict = pd.read_excel(sp_file, sheet_name=sheet_name_s)
            stock_result = pd.concat([stock_result_dict[s] for s in sheet_name_s])
        else:
            stock_result = pd.read_excel(sp_file, sheet_name=sheet_name_dict[portfolio])
        stock_result['证券代码'] = [code_t(x) for x in stock_result['证券代码']]
        stock_result.to_csv(stock_data_file, index=False)
    return stock_result


def get_sp_file(trade_date, strategy="Albest", ftp='60'):
    """获取实盘交易的路径文件，如果没有，则从ftp下载"""
    strategy = strategy.split('_')[0]
    # if str(trade_date) in sp_no_trading[strategy]:
    #     return
    sp_path = RootPath().get_sp_trading_path(strategy)
    file_name_dict = {'Albest': 'algo', 'Everest': 'easy', 'Everest1S': 'easy', 'Kunlun': 'CB'}
    file_name = f'{trade_date}_T0_{file_name_dict[strategy]}.xlsx'
    sp_file = "{}/{}".format(sp_path, file_name)
    if not os.path.exists(sp_file) or os.path.getsize(sp_file) == 0:
        os.makedirs(sp_path, exist_ok=True)
        if ftp == '60':
            ftp = FTP_OP(host="168.8.2.60", username="zsd", password="zsd")
            ftp.downloadFile("011668/T0/", sp_path, target_file=file_name)
        else:
            ftp = FTP_OP(host="168.8.2.68", username="xquant", password="Xquant-32")
            ftp.downloadFile("XQuant/011668/T0/", sp_path, target_file=file_name)
    if os.path.exists(sp_file) and os.path.getsize(sp_file) != 0:
        print("{}-{} 实盘文件 √".format(strategy, trade_date))
    else:
        print("{}-{} 实盘文件 ×".format(strategy, trade_date))
    return sp_file


def get_stock_cumsum_profit(st_date, ed_date, strategy):
    """获取一段区间内，策略内的股票累计收益结果"""
    date_list = trading_day(st_date, ed_date)
    res_all = list()
    for trade_date in date_list:
        stock_res = load_sp_result_by_stock(trade_date, strategy)
        stock_res = stock_res[['证券代码', '盈利']].set_index('证券代码')
        res_all.append(stock_res)
    res_df = pd.concat(res_all, axis=1)
    res_sum = res_df.sum(axis=1).sort_values(ascending=False)
    return res_sum


def get_stock_cumsum_res(st_date, ed_date, select_code_list=None):
    """股票收益按票汇总"""
    date_list = trading_day(st_date, ed_date)
    res_all = list()
    for trade_date in date_list:
        if trade_date == '20210701':
            continue
        res_albest = load_sp_result_by_stock(trade_date, 'Albest')[['证券代码', '盈利', '收盘市值']]
        res_everest = load_sp_result_by_stock(trade_date, 'Everest')[['证券代码', '盈利', '收盘市值']]
        res_stock = pd.concat([res_albest, res_everest]).groupby('证券代码').sum()
        res_stock['交易天数'] = res_stock['收盘市值'] != 0
        res_all.append(res_stock)
    res_df1 = pd.concat(res_all).groupby('证券代码').sum()
    res_df2 = pd.concat(res_all).groupby('证券代码').mean()
    res_df = pd.concat([res_df1[['交易天数', '盈利']].rename(columns={'盈利': '总盈利'}), res_df2[['盈利', '收盘市值']]], axis=1)
    res_df['收益率'] = [f'{round(x * 100, 2)}%' for x in res_df['盈利'] / res_df['收盘市值'] * 250]
    res_df['盈利'] = [round(x) for x in res_df['盈利']]
    res_df['收盘市值'] = [round(x / 1e4) for x in res_df['收盘市值']]
    res_df = res_df.rename(columns={'盈利': '日均盈利（元）', '收盘市值': '日均市值（万）', '收益率': '年化收益率'})
    if select_code_list is not None:
        res_df = res_df.loc[select_code_list].dropna(axis=0)
    return res_df
