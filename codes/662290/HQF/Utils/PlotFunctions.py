import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from reportlab.platypus import Image
from reportlab.lib.units import inch
import time


def autolabel(rects):  # 为柱状图标上数字
    for i_rect in rects:
        height = i_rect.get_height()
        if height >= 0:
            plt.text(i_rect.get_x(), 1.03 * height, '%.4f' % float(height), fontsize=3)
        else:
            plt.text(i_rect.get_x(), 0.97 * height, '%.4f' % float(height), fontsize=3)


def plot_group_bar2(input_list, title_name, pic_name, report_address, bar_with_number=True, x_label=None):
    plt.figure(figsize=(6, 2), dpi=300)
    rect = plt.bar(range(input_list.__len__()), input_list)
    plt.xticks(np.arange(input_list.__len__()), list(np.arange(input_list.__len__())), fontsize=3, rotation=30)
    plt.yticks(fontsize=5)
    plt.title(title_name, fontsize=5)
    if bar_with_number:
        autolabel(rect)
    if x_label is not None:
        plt.xticks(np.arange(x_label.__len__()), x_label, fontsize=3)
    file_name = os.path.join(report_address, pic_name)
    plt.savefig(file_name, format='png')
    im = Image(file_name, 9 * inch, 3 * inch)
    return im


def plot_series(series_intput, x_label, y_label, pic_title, pic_name, report_address, legend_location='best'):
    time_stamp_list = series_intput[0].index
    data_list = []
    for i in range(series_intput.__len__()):
        temp_data = series_intput[i].values.tolist()
        data_list.append(temp_data)
    index = []
    index_number = []
    x_number = []
    for i, time_stamp in enumerate(time_stamp_list):
        x_number.append(i)
        if i % int(time_stamp_list.__len__() / 6) == 0:
            index_number.append(i)
            timearray = time.localtime(time_stamp)
            index.append(time.strftime('%Y%m%d', timearray))
    x_number = np.array(x_number)
    plt.figure(figsize=(6, 2), dpi=300)
    for i in range(series_intput.__len__()):
        plt.plot(x_number, np.array(data_list[i]), linewidth=0.3, label=x_label[i])
    plt.xticks(index_number, index, fontsize=5, rotation=0)
    plt.ylabel(y_label, fontsize=5)
    plt.title(pic_title, fontsize=5)
    plt.yticks(fontsize=5)
    plt.legend(loc=legend_location, fontsize=4)
    file_name = os.path.join(report_address, pic_name)
    plt.savefig(file_name, format='png')
    im = Image(file_name, 9 * inch, 3 * inch)
    return im


def plot_one_series(series_intput, x_label, y_label, pic_title, pic_name, report_address):
    time_stamp_list = series_intput.index
    data = series_intput.values.tolist()
    index = []
    index_number = []
    x_number = []
    for i, time_stamp in enumerate(time_stamp_list):
        x_number.append(i)
        if i % int(time_stamp_list.__len__() / 6) == 0:
            index_number.append(i)
            timearray = time.localtime(time_stamp)
            index.append(time.strftime('%Y%m%d', timearray))
    x_number = np.array(x_number)
    plt.figure(figsize=(6, 2), dpi=300)
    plt.plot(x_number, np.array(data), color='red', linewidth=0.3, label=x_label)
    plt.xticks(index_number, index, fontsize=5, rotation=0)
    plt.ylabel(y_label, fontsize=5)
    plt.title(pic_title, fontsize=5)
    plt.yticks(fontsize=5)
    plt.legend(loc='best', fontsize=5)
    file_name = os.path.join(report_address, pic_name)
    plt.savefig(file_name, format='png')
    im = Image(file_name, 9 * inch, 3 * inch)
    return im


def plot_boxplot(input, pic_name, report_address):
    input1 = input[0]
    input2 = input[1]
    input3 = input[2]
    input1 = input1.values.flatten()
    input1 = pd.DataFrame(input1[np.isfinite(input1)])
    input2 = input2.values.flatten()
    input2 = pd.DataFrame(input2[np.isfinite(input2)])
    input3 = input3.values.flatten()
    input3 = pd.DataFrame(input3[np.isfinite(input3)])
    plt.figure(figsize=(4.5, 1.8), dpi=300)
    img1 = plt.subplot(131)
    input1.boxplot(sym='o',  # 异常点形状
                   vert=True,  # 是否垂直
                   whis=1.5,  # IQR
                   patch_artist=False,  # 上下四分位框是否填充
                   meanline=False, showmeans=True,  # 是否有均值线及其形状
                   showbox=True,  # 是否显示箱线
                   showfliers=True,  # 是否显示异常值
                   notch=False,  # 中间箱体是否缺口
                   return_type='dict')  # 返回类型为字典
    img1.set_title('boxplot of raw factor', fontsize=8)
    plt.yticks(size=6)
    plt.xticks(size=6)
    img2 = plt.subplot(132)
    input2.boxplot(sym='o',  # 异常点形状
                   vert=True,  # 是否垂直
                   whis=1.5,  # IQR
                   patch_artist=False,  # 上下四分位框是否填充
                   meanline=False, showmeans=True,  # 是否有均值线及其形状
                   showbox=True,  # 是否显示箱线
                   showfliers=True,  # 是否显示异常值
                   notch=False,  # 中间箱体是否缺口
                   return_type='dict')  # 返回类型为字典
    img2.set_title('boxplot of factor', fontsize=8)
    plt.yticks(size=6)
    plt.xticks(size=6)
    img3 = plt.subplot(133)
    input3.boxplot(sym='o',  # 异常点形状
                   vert=True,  # 是否垂直
                   whis=1.5,  # IQR
                   patch_artist=False,  # 上下四分位框是否填充
                   meanline=False, showmeans=True,  # 是否有均值线及其形状
                   showbox=True,  # 是否显示箱线
                   showfliers=True,  # 是否显示异常值
                   notch=False,  # 中间箱体是否缺口
                   return_type='dict')  # 返回类型为字典
    img3.set_title('boxplot of neutralized factor', fontsize=8)
    plt.yticks(size=6)
    plt.xticks(size=6)
    file_name = os.path.join(report_address, pic_name)
    plt.savefig(file_name, format='png')
    im = Image(file_name, 6 * inch, 2 * inch)
    return im