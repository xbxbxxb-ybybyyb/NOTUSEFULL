"""收益分析的绘图程序"""

import matplotlib.font_manager
import matplotlib.pyplot as plt


myfont = matplotlib.font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf')
myfont_legend = matplotlib.font_manager.FontProperties(fname='/data/user/011668/Utils/msyh.ttf', size=8)


def plot_last_n_days_profit(ax, data_df, title_text=''):
    """
    过去N日的每日收益（柱状图，左）与累计收益（折线图，右）
    data_df为pd.DataFrame，index为日期(eg. '20210101')，包含2个columns，['daily_profit', 'acc_profit']，代表每日盈利和累计盈利（单元：元）
    """
    data_df = data_df / 1e4  # 单位转换为万元
    all_date = data_df.index

    lns = []
    lns1 = ax.bar(x=range(len(all_date)), height=data_df['daily_profit'], color='darkorange', tick_label='每日盈利（左）')
    lns += lns1
    ax2 = ax.twinx()
    lns2 = ax2.plot(range(len(all_date)), data_df['acc_profit'], '-', color='#1f77b4', label='累计盈利（万，右）')
    lns += lns2
    labs = [l.get_label() for l in lns]
    n = data_df.shape[0]
    show_idx = [0, int(round(n * 0.33 - 1, 0)), int(round(n * 0.67 - 1, 0)), n - 1]
    plt.xticks(show_idx, [all_date.values[i] for i in show_idx])
    ax.legend(lns, labs, ncol=4, prop=myfont_legend)
    for tl in ax.get_yticklabels():
        tl.set_color('darkorange')
    for tl in ax2.get_yticklabels():
        tl.set_color("#1f77b4")
    if title_text == '':
        title_text = '每日盈利（万，左）与累计盈利（万，右）'
    plt.title(title_text, fontproperties=myfont)
    plt.tight_layout()

