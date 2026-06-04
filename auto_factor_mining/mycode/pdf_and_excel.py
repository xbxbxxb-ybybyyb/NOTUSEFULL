import os
import re
import numpy as np
import threading
import multiprocessing as mp
import pandas as pd
import argparse
import sys
import pickle 
import time
import warnings
from operator import itemgetter
warnings.filterwarnings('ignore')
sys.path.append('./gplearn_my/')

import gplearn_my
from fitness import _fitness_map
from customized_utils import gplearn_offical_alpha

import matplotlib
matplotlib.use('Agg')
import matplotlib.backends.backend_pdf
from matplotlib import pyplot as plt
import matplotlib.pyplot as plt
from PIL import Image
import pydotplus
from xquant.factordata import FactorData
s = FactorData()

def pie_prepare(a,column_name):
    """为了画饼图，把10位之后得数据合并s
        Input：
            a: df, 数据DataFrame
            column_name：str, 数据DataFrame的列名
        Return：
            b：df, 包含绘制饼图所需信息
    """
    a[column_name] = round(a[column_name],4)
    b = a[column_name].value_counts().to_frame(name='cnt')
    b.index.name='value' 
    other = sum(b['cnt'].iloc[10:])
    b = b.iloc[0:10].reset_index()
    b = b.append({'value':'others','cnt':other}, ignore_index=True).set_index('value')
    return b

def draw_tree(inputs, est_gp):
    """绘制因子树图
        Input：
            inputs: str, 路径，main出来的文件夹，应当含有预先保存的pickle文件及 对应关系的csv
            est_gp：obj, 因子挖掘存储对象，里面包含所需信息
    """
    for f in os.listdir(inputs):
        if 'factor_res' in f and '.csv' in f:
            map_file = f
    df = pd.read_csv(inputs + map_file)    
    
    df = df[["Factor","Formula"]]
    dic = df.set_index("Formula")["Factor"].to_dict()
    
    if not os.path.exists(inputs + '/tree'):
        os.mkdir(inputs + '/tree')
        
    cnt = 0    
    for i in (est_gp._best_programs):
        graph = i.export_graphviz()
        graph = pydotplus.graphviz.graph_from_dot_data(graph)
        #a = Image(graph.create_png())
        filename = inputs + 'tree/' + str(dic[str(i)]) + '.jpg'
        graph.write_png(filename)
        cnt += 1
    print("在 " + inputs + 'tree 路径下生成因子树：' + str(cnt))

def eval_one_factor(inputs, factor, data_info, df_target):
    """评价一个因子，计算各个指标
        Input：
            inputs: df, 数据DataFrame
            factor：str, 因子名
            data_info：list, 长度为3的list，包含数据名，开始日期，结束日期, 例如 ["valid", "20180601", "20190531"] 
            df_target:   df,   包含1Day_Return，valid等信息
        Return：
            lres：dic, 包含一个因子所有评价指标序列，可供画图使用     
    """
    tree_file = inputs + "tree/" + factor + ".jpg" 
    tree_img = Image.open(tree_file)   

    df = pd.read_pickle(inputs + factor + ".pkl")
    df = pd.DataFrame(df.stack())
    df_name = factor + '_' + data_info[0]
    df.columns = [df_name]
    df = df.iloc[(df.index.get_level_values("mddate")>=int(data_info[1])) & 
                 (df.index.get_level_values("mddate")<=int(data_info[2]))]

    # 分布图， 饼图
    factor_hist = df[df_name]
    edge = np.percentile(abs(np.array(factor_hist.fillna(0))), 99.5)
    pie_data = pie_prepare(df,df_name)
    
    df = df.merge(df_target,  how='left', left_index=True, right_index=True)
    # IC
    ic_series = _fitness_map["apearson"](df, df_name, "series").fillna(0)
    # ICRank
    rankic_series = _fitness_map["aspearman"](df, df_name, "series").fillna(0)
    # ER
    er_series, nan_ratio, final_samples_num = gplearn_offical_alpha(df, df_name, "series")
    er_series = er_series.fillna(0)

    # 指数标的
    time_sta = list(df.reset_index()["mddate"])[0]
    time_end = list(df.reset_index()["mddate"])[-1]
    trend = list(s.get_factor_value('Basic_factor', ["000985.CSI"], 
        mddate= s.tradingday(time_sta, time_end),
        factor_names = ["close"], fill_na=True)["close"])

    lres = {}
    a = df[[df_name]].unstack()
    lres[df_name + '@' + 'A_' + df_name] = a.iloc[:, 1:200].reset_index(drop=True)
    iistd = a.std().sort_values()
    lres[df_name + '@' + 'B_ii_heteroscedasticity'] = list(iistd)#heteroscedasticity
    lres[df_name + '@' + 'C_IC='    +('%.4f'%(ic_series.mean()))]     = list(ic_series.cumsum())
    lres[df_name + '@' + 'D_RankIC='+('%.4f'%(rankic_series.mean()))] = list(rankic_series.cumsum())
    
    lres[df_name + '@' + 'E_gt_0_count'] = list(a.gt(0).sum(axis=1))
    lres[df_name + '@' + 'F_lt_0_count'] = list(a.lt(0).sum(axis=1))
    lres[df_name + '@' + 'G_mean'] = list(a.mean(axis=1))
    lres[df_name + '@' + 'H_std'] = list(a.std(axis=1))
    
    lres[df_name + '@' + 'I_ExcessReturn='+('%.6f'%(er_series.mean()))] = list(er_series.cumsum())
    lres[df_name + '@' + 'J_factor_hist' + '__' + str(edge)] = list(factor_hist.fillna(0))                                                                    
    lres[df_name + '@' + 'K_tree'] = tree_img
    lres[df_name + '@' + 'L_risklevelstd3'] = []            

    lres[df_name + '@' + 'M_zz_all'] = trend
    lres[df_name + '@' + 'N_pie_chart'] = pie_data
    lres[df_name + '@' + 'O_risklevelstd3'] = []
    lres[df_name + '@' + 'P_risklevelstd4'] = []
    
    return lres
    
def multiprocess_eval(threadID, thread_num, factor_base, inputs, factor, data_info, df_target):
    """多线程并发函数
    """
    eval_dic = {}
    cnt = -1
    for i in range(len(factor_base)):
        cnt = cnt + 1
        if (cnt % thread_num != threadID):continue
        eval_dic[factor_base[i]] = eval_one_factor(inputs, factor, data_info, df_target)
    return eval_dic

def run_eval(thread_num, factor_base, inputs, data_info, df_target):
    """调用multiprocess_eval, 并汇总结果
        Input：
            thread_num:  int,  并发数量
            factor_base：list, 包含因子名的list
            inputs：     str,  输入路径
            data_info：  list, 长度为3的list，包含数据名，开始日期，结束日期, 例如 ["valid", "20180601", "20190531"] 
            df_target:   df,   包含1Day_Return，valid等信息
        Return：
            allmap：      dict, 存储结果的字典，每个键值是因子名，key是该因子的每个评价指标的详细数据，用于绘图         
    """
    pool = mp.Pool(thread_num)
    tasks = []
    for i in range(len(factor_base)):
        tasks.append(
            pool.apply_async(multiprocess_eval, args=(
                i, len(factor_base) ,factor_base, inputs, factor_base[i], data_info, df_target))
        )
    pool.close()
    time1 = time.time()
    res = []
    allmap = {}
    for t in range(len(tasks)):
        t = tasks[t]
        localres =  t.get()
        for k in localres.keys():
            allmap[k] = localres[k]    
    time2 = time.time()
    print('计算耗时:' + str((time2-time1)/60) + 'min')
    return allmap    

def draw_pdf(allmap, pdf_path):
    """画图，并存到PDF
        Input：
            allmap:       dic,  因子测评详细信息，用于画图，每个key是一个因子
            pdf_path:    str,  输出PDF路径
        Return:
            None
    """
    sz = 4
    with matplotlib.backends.backend_pdf.PdfPages(pdf_path) as pdf:
        for i in allmap:
            fig = plt.figure(figsize=(15, 15))
            fig.tight_layout()
            n = -1
            for j in allmap[i]:
                n += 1
                feature = allmap[i][j]
                if n == 9: 
                    #print('柱图',i,j,n,type(allmap[i][j]))
                    edge = float(j.split('__')[1])
                    plt.subplot(sz, sz, n + 1)
                    plt.hist(feature ,bins = 20, range=(-edge, edge))
                    plt.title(j.split('@')[1])
                    plt.grid()

                elif n == 13:
                    #print('饼图',i,j,n,type(allmap[i][j]))
                    y = np.array(feature['cnt'])
                    labels = list(feature.index)
                    plt.subplot(sz, sz, n + 1)
                    plt.pie(y, labels = labels)
                    plt.title(j.split('@')[1])

                elif n == 10:  
                    #print('树图',i,j,n,type(allmap[i][j]))
                    plt.subplot(sz/2, sz/2, 4)
                    plt.imshow(feature,aspect='auto')
                    plt.title(j.split('@')[1])

                elif n in [0,1,2,3,4,5,6,7, 8, 12]:
                    #print('其他',i,j,n,type(allmap[i][j]))
                    plt.subplot(sz, sz, n + 1)
                    plt.plot(feature)
                    plt.grid()
                    plt.title(j.split('@')[1])
                else:   # 其他的格子不画
                    pass
            plt.rcParams.update({'font.size': 8})
            #plt.show()
            pdf.savefig(fig)

def eval_csv_report(allmap, data_type):
    """用于记录各个因子统计指标，并返回df，方便存csv
        Input：
            allmap:       dic,  因子测评详细信息，用于画图，每个key是一个因子
            data_type:    str,  数据种类（test，valid...），用于命名
        Return:
            res: df,  包含各个因子测评指标
    """
    res = pd.DataFrame()
    for factor in allmap:
        tmp = []
        for k in allmap[factor]:
            if "=" not in k:
                continue
            col = data_type + "_" + k.split("=")[0].split("_")[-1]
            val = k.split("=")[-1]
            tmp.append([col, val])
        res = res.append({"Factor": factor,
                          tmp[0][0]:tmp[0][1],
                          tmp[1][0]:tmp[1][1],
                          tmp[2][0]:tmp[2][1],
                         }, ignore_index=True)
    return res


def summary(est_gp, decap_file, inputs, thread_num, all_data, data_info, factor_info):
    """测评因子，画图出报告
        Input：
            est_gp:       obj,  因子挖掘结果
            decap_file:   df,   包含标的信息
            inputs:       str,  文件根路径
            thread_num:   int,  并发数
            all_data:     df,  全数据
            data_info:    dic, 包含想要测评的数据信息，每个key是个数据集名字，value是一个list记录该数据起止时间
            factor_info: df,  仅包含因子名和因子公式的DataFrame
        Return:
            factor_info: df,  包含各个因子测评指标 
    """
    df_target = all_data[["1Day_return"]].reset_index()
    df_target['mddate'] = df_target['mddate'].astype('int64')
    df_target = df_target.set_index(["mddate","stock"])
    #decap_file = est_gp.decap_file
    df_target = df_target.merge(decap_file,  how='left', left_index=True, right_index=True) 

    draw_tree(inputs, est_gp)

    factor_base = []
    for f in os.listdir(inputs):
        if f.endswith(".pkl") and "FactorAlpha" in f:
            factor_base.append(f.split(".")[0])
    factor_base.sort(key=lambda x: int(str(re.findall("\d+",x)[0])))

    for data_type in data_info:
        print("===== summary " + data_type)
        di = [data_type, data_info[data_type][0], data_info[data_type][1]]

        # 计算各个指标
        allmap = run_eval(thread_num, factor_base, inputs, di, df_target)

        # 出报告
        report = eval_csv_report(allmap, data_type).set_index("Factor")

        # 出PDF
        if "valid" in data_type or "test" in data_type:
            pdf_path = inputs + data_type + "_report.pdf"
            draw_pdf(allmap, pdf_path)

        factor_info = pd.merge(factor_info, report, how = 'left', on = 'Factor')
        factor_info.to_csv(inputs + "report.csv")
    return factor_info

