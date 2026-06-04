from matplotlib import pyplot as plt
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import numpy as np
import os

def align_yaxis(ax1, v1, ax2, v2):
    # 取得AX1和AX2的範圍
    miny1, maxy1 = ax1.get_ylim()
    miny2, maxy2 = ax2.get_ylim()
    print("調整前", miny1, maxy1, miny2, maxy2)
    # 確保 v1 一定出現在AX1
    if v1 > maxy1:
        maxy1 = v1
    elif v1 < miny1:
        miny1 = v1
    # 確保 v2 一定出現在AX2
    if v2 > maxy2:
        maxy2 = v2
    elif v2 < miny2:
        miny2 = v2
    # 與V上下距離
    upy1 = abs(maxy1 - v1)
    downy1 = abs(v1 - miny1)
    upy2 = abs(maxy2 - v2)
    downy2 = abs(v2 - miny2)
    print("調整中", miny1, maxy1, miny2, maxy2)

    # 有解
    if upy1 > 0 and downy1 > 0:
        up_ratio = upy2 / upy1
        down_ratio = downy2 / downy1
        # 調整AX2
        if up_ratio > down_ratio:  # 如果上方需延伸較多，則對齊最大值，依上方比例去調整最小值。
            miny2 = v2 - downy1 * up_ratio
        elif down_ratio > up_ratio:
            maxy2 = v2 + upy1 * down_ratio
        else:
            pass
    # 調整AX2無解，則調整AX1。注意比例是AX2/AX1，故調整AX1時，調整比例需要變成倒數。
    elif upy2 > 0 and downy2 > 0:
        # 因為upy1或downy2為0才會來到這裡，若除其中一項將會發生除零的錯誤。
        up_ratio = upy1 / upy2
        down_ratio = downy1 / downy2
        if up_ratio > down_ratio:
            miny1 = v1 - downy2 * up_ratio
        elif down_ratio > up_ratio:
            maxy1 = v1 + upy2 * down_ratio
        else:
            pass
    # 調整AX1與AX2都無解，則不調整
    else:
        print("無法調整或不需調整")
        pass
    # 重新調整AX1和AX2
    print("調整後", miny1, maxy1, miny2, maxy2)
    ax1.set_ylim(miny1, maxy1)
    ax2.set_ylim(miny2, maxy2)
    return None


def plot_signal_backtest_results(stats_df, pnl_stats_df, save_file_name = "./", ylim = [-150, 150]):
    fig = plt.figure(figsize=(20, 10))
    grid = plt.GridSpec(3, 3, wspace=0.1, hspace=0.00)
    ax1 = plt.subplot(grid[0:2, 0:3])

    # ax1=plt.subplot(2,1,1)
    ax1.bar(stats_df.index, stats_df["R_1_num"])
    ax1.bar(stats_df.index, stats_df["R_2_num"], bottom=stats_df["R_1_num"])
    ax1.bar(stats_df.index, -stats_df["D_1_num"])
    ax1.bar(stats_df.index, -stats_df["D_2_num"], bottom=-stats_df["D_1_num"])
    ax1.set_ylim(ylim[0], ylim[1])

    ax2 = ax1.twinx()  #
    ax2.plot(stats_df.index, stats_df["R_1_auc"], label="R_1_acc")
    ax2.plot(stats_df.index, stats_df["R_2_auc"], label="R_2_acc")

    ax2.plot(stats_df.index, -stats_df["D_1_auc"], label="D_1_acc")
    ax2.plot(stats_df.index, -stats_df["D_2_auc"], label="D_2_acc")

    align_yaxis(ax1, 0, ax2, 0)

    ax2.axhline(np.mean(stats_df["R_1_auc"]), color="green")  # 横线

    ax2.axhline(-np.mean(stats_df["D_1_auc"]), color="green")  # 横线

    yminorFormatter = FormatStrFormatter('%1.1f')  # 设置y轴标签文本的格式
    yminorLocator = MultipleLocator(0.1)  # 将此y轴次刻度标签设置为0.1的倍数
    ax2.yaxis.set_minor_locator(yminorLocator)
    ax2.yaxis.set_minor_formatter(yminorFormatter)
    ax2.yaxis.grid(True, which='minor')

    plt.legend()
    ax1.grid(True)

    ax3 = plt.subplot(grid[2:3, 0:3], sharex=ax1)
    ax3.plot(pnl_stats_df.index, pnl_stats_df.pnl.cumsum())
    ax3.grid(True)
    ax3.tick_params(axis='x', rotation=90)

    ax4 = ax3.twinx()
    ax4.plot(pnl_stats_df.index, pnl_stats_df.rate, color="blue")
    ax4.axhline(0, color="green")  # 横线

    print("保存信号回测评价数据：", save_file_name)
    plt.savefig(os.path.join(save_file_name),dpi=300)