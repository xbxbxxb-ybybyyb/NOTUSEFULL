"""BT结果分层统计"""

import pandas as pd
from DataAPI.DataTools import get_stock_daily_result
from DataAPI.GetCodeVol import get_index_code
from Utils.UtilsPlot import plot_bar
import matplotlib.pyplot as plt
from matplotlib import gridspec, font_manager


myfont = font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf')


def price_layer(x):
    if x < 10:
        return '0-10'
    elif x < 20:
        return '10-20'
    elif x < 30:
        return '20-30'
    elif x < 50:
        return '30-50'
    else:
        return '50+'


def get_res_combine(abs_path_list, tags, is_add_index=False):
    res_combine_list = []
    res_sum_code = []
    for i, abs_path in enumerate(abs_path_list):
        code_data = pd.read_excel(f'{abs_path}/TotalSummary.xls', index_col=0)[['afterCostProfit']].rename(columns={'afterCostProfit': tags[i]})
        res_sum_code.append(code_data)
    res_sum_code = pd.concat(res_sum_code, axis=1)
    stock_close = get_stock_daily_result(list(res_sum_code.index), ['20220228'], ['close']).loc['20220228']
    res_sum_code = pd.concat([res_sum_code, stock_close], axis=1)
    res_sum_code['market'] = [x[0] for x in res_sum_code.index]
    res_sum_code['price'] = res_sum_code['close'].map(lambda x: price_layer(x))
    res_sum_code['market'] = res_sum_code['market'].map({'0': 'sz', '3': 'cyb', '6': 'sh'})
    res_market = res_sum_code[tags + ['market']].groupby('market').sum()
    res_price = res_sum_code[tags + ['price']].groupby('price').sum()
    res_combine_list = [res_market, res_price]

    if is_add_index:
        code300 = get_index_code('hs300', '20220104')
        code500 = get_index_code('zz500', '20220104')
        code1000 = get_index_code('zz1000', '20220104')
        for i in res_sum_code.index:
            if i in code300:
                res_sum_code.at[i, 'index'] = 'hs300'
            if i in code500:
                res_sum_code.at[i, 'index'] = 'zz500'
            if i in code1000:
                res_sum_code.at[i, 'index'] = 'zz1000'
        res_index = res_sum_code[tags + ['index']].groupby('index').sum()
        res_combine_list.append(res_index)

    res_combine = pd.concat(res_combine_list) / 1e4
    return res_combine


def plot_layer(abs_path_list, tags, is_add_index=False, title_text=None):
    res_combine = get_res_combine(abs_path_list, tags, is_add_index=is_add_index)
    fig = plt.figure(figsize=(6, 3))
    gs = gridspec.GridSpec(1, 1)
    ax1 = fig.add_subplot(gs[0:1, 0:1])
    plot_bar(ax1, res_combine)
    if title_text is not None:
        plt.title(title_text, fontproperties=myfont)
    plt.tight_layout()
    plt.show()
